"""
PipelineOrchestrator: Bronze → Silver → Gold pipeline for the ARQ worker.

Called exclusively from app/worker.py via run_pipeline_task().
"""
import os
import structlog
from datetime import datetime
from typing import Any, Dict, List

from app.repositories.mongo import session_repo
from app.services.ingest import IngestService
from app.services.normalization import NormalizationService
from app.services.profiler import ProfilerService
from app.services.docling_quality_gate import DoclingQualityGate
from app.services.finding_builder import FindingBuilder
from app.services.chart_spec_generator import ChartSpecGenerator
from app.services.eda_extended import EDAExtendedService
from app.services.llm_service import LLMService
from app.services.schema_validator import SchemaValidator
from app.services.statistical_tests import StatisticalTestsService
from app.services.docling_chunking_service import get_docling_chunking_service
from app.services.embedding_service import EmbeddingService

logger = structlog.get_logger(__name__)


class PipelineOrchestrator:
    """
    Orquesta el pipeline completo Bronze → Silver → Gold para una sesión.
    Llamado exclusivamente desde el worker ARQ (app/worker.py).
    """

    def __init__(self):
        logger.info("Initializing IngestService")
        self.ingest_service = IngestService()
        logger.info("Initializing NormalizationService")
        self.normalization_service = NormalizationService()
        logger.info("Initializing ProfilerService")
        self.profiler_service = ProfilerService()
        logger.info("Initializing DoclingQualityGate")
        self.quality_gate = DoclingQualityGate()
        logger.info("Initializing FindingBuilder")
        self.finding_builder = FindingBuilder()
        logger.info("Initializing ChartSpecGenerator")
        self.chart_spec_generator = ChartSpecGenerator()
        logger.info("Initializing EDAExtendedService")
        self.eda_service = EDAExtendedService()
        logger.info("Initializing LLMService")
        self.llm_service = LLMService()
        logger.info("Initializing SchemaValidator")
        self.schema_validator = SchemaValidator()
        logger.info("Initializing StatisticalTestsService")
        self.stat_tests_service = StatisticalTestsService()
        logger.info("Initializing DoclingChunkingService")
        self.docling_chunking_service = get_docling_chunking_service()
        logger.info("Initializing EmbeddingService")
        self.embedding_service = EmbeddingService()
        logger.info("PipelineOrchestrator initialized successfully")

    async def run_full_pipeline(
        self,
        session_id: str,
        file_path: str,
        filename: str,
        content_type: str,
        table_index: int = 0,
    ) -> None:
        """
        Ejecuta Bronze → Silver → Gold y actualiza el estado de la sesión en MongoDB.
        Limpia el archivo temporal al finalizar (éxito o error).
        """
        try:
            with open(file_path, "rb") as f:
                file_bytes = f.read()

            # ─── BRONZE ───────────────────────────────────────────────
            await session_repo.update_session(session_id, {
                "status": "processing",
                "progress_message": "Bronze: Ingestando documento...",
            })

            # Ingest first, then evaluate quality from the conversion metadata
            ingest_result = await self.ingest_service.ingest_file(
                file_bytes, filename, content_type, table_index
            )

            # DoclingQualityGate.evaluate() takes the conversion_metadata dict
            conversion_metadata = ingest_result.get("conversion_metadata", {})
            quality_result = self.quality_gate.evaluate(conversion_metadata)

            # ingest_result returns "dataframe" key (not "df")
            df = self.normalization_service.normalize(ingest_result["dataframe"])

            source_metadata = ingest_result.get("source_metadata", {})
            schema_info = ingest_result.get("schema_info", {})

            bronze_doc: Dict[str, Any] = {
                "session_id": session_id,
                "original_filename": filename,
                "ingestion_source": conversion_metadata.get("method", "unknown"),
                "quality_decision": quality_result.get("status", "accept"),
                "schema_version": conversion_metadata.get("schema_version", "v1"),
                "narrative_context": conversion_metadata.get("narrative_context"),
                "tables": conversion_metadata.get("tables", []),
                "document_metadata": conversion_metadata.get("document_metadata", {}),
                "provenance_refs": conversion_metadata.get("provenance_refs", []),
                "document_payload": conversion_metadata.get("document_payload"),
                "source_metadata": source_metadata,
                "schema_info": schema_info,
                "created_at": datetime.utcnow().isoformat(),
            }
            # save_bronze takes only the doc dict (session_id is inside it)
            await session_repo.save_bronze(bronze_doc)

            # ─── SILVER ───────────────────────────────────────────────
            await session_repo.update_session(session_id, {
                "progress_message": "Silver: Perfilando datos y detectando hallazgos...",
            })

            # profiler.profile() returns {col_name: col_profile, ...}
            raw_profile = self.profiler_service.profile(df)

            # Build dataset_overview and column_profiles for downstream use
            column_profiles: List[Dict[str, Any]] = list(raw_profile.values())
            dataset_overview: Dict[str, Any] = {
                "row_count": len(df),
                "column_count": len(df.columns),
                "original_filename": filename,
                "columns": list(df.columns),
            }

            stat_tests = self.stat_tests_service.run_all_tests(df)

            # EDA: compute correlations and outliers (EDAExtendedService has no .run())
            correlations = self.eda_service.compute_correlations(df)
            outliers = self.eda_service.detect_all_outliers(df)
            distributions = self.eda_service.analyze_distributions(df)

            eda_results: Dict[str, Any] = {
                "correlations": correlations,
                "outliers": outliers,
                "distributions": distributions,
            }

            # FindingBuilder uses build_all_findings() not build_findings()
            findings: List[Any] = self.finding_builder.build_all_findings(
                df,
                eda_results=eda_results,
                test_results=stat_tests,
            )

            # ChartSpecGenerator uses generate_all_charts() not generate()
            chart_specs = self.chart_spec_generator.generate_all_charts(
                df, findings=findings, eda_results=eda_results
            )

            # DoclingChunkingService.build_chunks() is synchronous, not async
            chunks: List[Any] = self.docling_chunking_service.build_chunks(
                session_id=session_id,
                document_payload=bronze_doc.get("document_payload"),
                narrative_context=bronze_doc.get("narrative_context") or "",
                tables=bronze_doc.get("tables", []),
            )

            findings_dicts: List[Dict[str, Any]] = [
                f.model_dump() if hasattr(f, "model_dump") else dict(f)
                for f in findings
            ]
            chunks_dicts: List[Dict[str, Any]] = [
                c.model_dump() if hasattr(c, "model_dump") else (c if isinstance(c, dict) else dict(c))
                for c in chunks
            ]

            await self.embedding_service.index_hybrid_sources(
                findings=findings_dicts,
                chunks=chunks_dicts,
            )

            silver_doc: Dict[str, Any] = {
                "session_id": session_id,
                "dataset_overview": dataset_overview,
                "column_profiles": column_profiles,
                "findings": findings_dicts,
                "chart_specs": [
                    c.model_dump() if hasattr(c, "model_dump") else (c if isinstance(c, dict) else dict(c))
                    for c in chart_specs
                ],
                "data_preview": df.head(50).to_dict(orient="records"),
                "statistical_tests": stat_tests,
                "eda_results": eda_results,
                "created_at": datetime.utcnow().isoformat(),
            }
            # save_silver takes only the doc dict
            await session_repo.save_silver(silver_doc)

            # ─── GOLD ─────────────────────────────────────────────────
            await session_repo.update_session(session_id, {
                "progress_message": "Gold: Enriqueciendo con IA...",
            })

            # LLMService has no .enrich() — use generate_executive_summary()
            report_data = {
                "dataset_overview": dataset_overview,
                "findings": findings_dicts,
            }
            summary_result = await self.llm_service.generate_executive_summary(report_data)

            # Enrich individual findings (up to 10 to limit cost)
            enriched_explanations: Dict[str, Any] = {}
            dataset_context = {
                "original_filename": filename,
                "row_count": dataset_overview.get("row_count", 0),
                "column_count": dataset_overview.get("column_count", 0),
                "narrative_context": bronze_doc.get("narrative_context"),
            }
            total_cost = summary_result.get("cost_usd", 0.0)
            llm_calls = 1

            for finding in findings_dicts[:10]:
                try:
                    enriched = await self.llm_service.generate_enriched_explanation(
                        finding=finding,
                        dataset_context=dataset_context,
                    )
                    fid = finding.get("finding_id", "")
                    if fid:
                        enriched_explanations[fid] = enriched.get("explanation")
                    total_cost += enriched.get("cost_usd", 0.0)
                    llm_calls += 1
                except Exception as enrich_err:
                    logger.warning("finding_enrich_failed", error=str(enrich_err))

            # save_gold takes only the doc dict
            await session_repo.save_gold({
                "session_id": session_id,
                "executive_summary": summary_result.get("summary"),
                "enriched_explanations": enriched_explanations,
                "llm_cost_usd": total_cost,
                "llm_model_used": summary_result.get("model", ""),
                "llm_calls_count": llm_calls,
                "created_at": datetime.utcnow().isoformat(),
            })

            # ─── FINALIZAR ────────────────────────────────────────────
            await session_repo.update_session(session_id, {
                "status": "ready",
                "quality_decision": quality_result.get("status", "accept"),
                "finding_count": len(findings_dicts),
                "progress_message": "Pipeline completado exitosamente.",
            })

            logger.info("pipeline_complete", session_id=session_id, findings=len(findings_dicts))

        except Exception as e:
            logger.error("pipeline_failed", session_id=session_id, error=str(e))
            await session_repo.update_session(session_id, {
                "status": "error",
                "progress_message": f"Error en el pipeline: {str(e)}",
            })
            raise

        finally:
            try:
                os.unlink(file_path)
            except OSError:
                pass
