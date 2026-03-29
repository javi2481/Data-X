export interface Artifact {
  artifact_type: string;
  title: string;
  data: unknown;
}

// ============================================
// Sprint 0: Docling-first Provenance Types
// ============================================

export interface BoundingBox {
  l: number;  // left
  t: number;  // top
  r: number;  // right
  b: number;  // bottom
  coord_origin: "TOPLEFT" | "BOTTOMLEFT";
}

export interface SourceLocation {
  page?: number;  // Número de página (1-indexed)
  bbox?: BoundingBox;  // Bounding box en la página
  heading?: string;  // Encabezado de sección
  section_path?: string[];  // Jerarquía de secciones
  table_id?: string;  // ID de tabla si aplica
  row_range?: [number, number];  // Rango de filas (start, end)
  cell_ref?: string;  // Referencia de celda ej: "A1:B5"
  char_offset?: [number, number];  // Offset de caracteres en el texto
}

export interface DocumentChunk {
  chunk_id: string;
  session_id: string;
  text: string;
  snippet: string;
  chunk_order: number;
  source_type: "section" | "table" | "page_reference" | "heading" | "list_item" | "figure_caption";
  source_id: string;
  location?: SourceLocation;
  token_count?: number;
  embedding_id?: string;
}

// ============================================
// Core Data Types
// ============================================

export interface Evidence {
  metric: string;
  value: number | string;
  context?: string;
  source_location?: SourceLocation;  // Sprint 0: Dónde se encontró esta evidencia
}

export interface Finding {
  finding_id: string;
  category:
    | "data_gap"
    | "reliability_risk"
    | "pattern"
    | "opportunity"
    | "quality_issue";
  severity: "critical" | "important" | "suggestion" | "insight";
  title: string;
  what: string;
  so_what: string;
  now_what: string;
  affected_columns: string[];
  evidence: Evidence[];
  confidence: "verified" | "high" | "moderate";
  // Sprint 0: Docling-first provenance
  source_locations?: SourceLocation[];
  source_chunk_ids?: string[];
  enriched_explanation?: string | null;
}

export interface AxisSpec {
  key: string;
  label: string;
  type: 'categorical' | 'numeric' | 'datetime';
}

export interface SeriesSpec {
  key: string;
  label: string;
  color_hint?: string;
}

export interface ChartSpec {
  chart_id: string;
  chart_type: 'bar' | 'line' | 'area' | 'pie' | 'histogram' | 'scatter';
  title: string;
  data: Record<string, string | number | boolean | null>[];
  x_axis: AxisSpec;
  y_axis?: AxisSpec;
  series: SeriesSpec[];
}

export interface DatasetOverview {
  row_count: number;
  column_count: number;
  numeric_columns: number;
  categorical_columns: number;
  datetime_columns: number;
  total_nulls: number;
  total_null_percent: number;
  duplicate_rows: number;
  duplicate_percent: number;
}

export interface ColumnProfile {
  name: string;
  dtype: string;
  count: number;
  null_count: number;
  null_percent: number;
  unique_count: number;
  cardinality: number;
  min?: number;
  max?: number;
  mean?: number;
  median?: number;
  std?: number;
  min_length?: number;
  max_length?: number;
  avg_length?: number;
  top_values?: Array<{ value: string; count: number }>;
}

export interface ProvenanceInfo {
  source: string;
  ingestion_method: string;
  quality_decision: string;
  processing_steps: string[];
  affected_columns: string[];
  schema_version?: string;
  provenance_refs?: EvidenceSource[];
}

export type SourceType = "finding" | "chunk" | "table" | "section" | "page_reference" | "heading";

export interface DocumentTableRef {
  table_id: string;
  index: number;
  row_count?: number;
  column_count?: number;
  headers?: string[];
  confidence?: number;
}

export interface EvidenceSource {
  source_type: SourceType;
  source_id: string;
  evidence_ref?: string;
  snippet?: string;
  score?: number;
  // Sprint 0: Docling-first provenance
  location?: SourceLocation;
  chunk_id?: string;
}

export interface AnalysisReport {
  session_id: string;
  status: 'completed' | 'partial' | 'error';
  dataset_overview: DatasetOverview;
  column_profiles: ColumnProfile[];
  findings: Finding[];
  chart_specs: ChartSpec[];
  data_preview: Record<string, string | number | boolean | null>[];
  executive_summary: string | null;
  explanations: Record<string, string>;
  enriched_explanations: Record<string, string>;
  provenance: ProvenanceInfo;
  document_context?: string | null;
  document_tables?: DocumentTableRef[];
  document_metadata?: Record<string, unknown>;
  selected_table_index?: number;
  llm_cost_usd?: number;
  llm_model_used?: string;
  llm_calls_count?: number;
  contract_version: string;
  generated_at: string;
}

export interface SessionResponse {
  session_id: string;
  status: 'created' | 'processing' | 'ready' | 'error';
  created_at: string;
  source_metadata: Record<string, unknown>;
  quality_decision?: string;
  dataset_overview?: DatasetOverview;
  finding_count?: number;
  contract_version: string;
}

export interface AnalyzeRequest {
  session_id: string;
  query: string;
}

export interface AnalyzeResponse {
  session_id: string;
  query: string;
  answer: string;
  relevant_findings: Finding[];
  sources: Array<string | EvidenceSource>;
  confidence: string;
  contract_version: string;
}

export interface SessionListItem {
  session_id: string;
  status: 'created' | 'processing' | 'ready' | 'error';
  created_at: string;
  filename: string;
  finding_count: number;
  quality_decision: string;
}

export interface PaginatedSessions {
  items: SessionListItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface ErrorResponse {
  error_code: string;
  message: string;
  details?: Record<string, unknown>;
}

export interface UserCreate {
  email: string;
  password: string;
  name: string;
}

export interface UserLogin {
  email: string;
  password: string;
}

export interface UserResponse {
  user_id: string;
  email: string;
  name: string;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: UserResponse;
}
