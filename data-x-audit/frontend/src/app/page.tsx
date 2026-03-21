import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { ShieldCheck, ArrowRight, BarChart3, History as HistoryIcon } from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="flex flex-col min-h-screen bg-background">
      <main className="flex-1">
        {/* Hero Section */}
        <section className="w-full py-20 md:py-32 lg:py-48 bg-gradient-to-b from-primary/5 via-background to-background relative overflow-hidden">
          <div className="absolute inset-0 bg-grid-slate-200 [mask-image:linear-gradient(0deg,#fff,rgba(255,255,255,0.6))] -z-10" />
          <div className="container px-4 md:px-6 mx-auto relative">
            <div className="flex flex-col items-center space-y-8 text-center">
              <div className="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 border-transparent bg-primary text-primary-foreground mb-4">
                Data-X v1.0 Release Candidate
              </div>
              <div className="space-y-4">
                <h1 className="text-4xl font-extrabold tracking-tighter sm:text-5xl md:text-6xl lg:text-7xl/none bg-clip-text text-transparent bg-gradient-to-r from-foreground to-foreground/70">
                  Data-X: Inteligencia para tus datos
                </h1>
                <p className="mx-auto max-w-[800px] text-muted-foreground md:text-xl lg:text-2xl leading-relaxed">
                  Plataforma integral para ingesta inteligente de <span className="text-foreground font-semibold">CSV, XLSX y PDF</span> con <span className="text-foreground font-semibold">Docling</span>, 
                  análisis estadístico avanzado y resúmenes narrativos impulsados por <span className="text-foreground font-semibold">IA</span>.
                </p>
              </div>
              <div className="flex flex-col sm:flex-row gap-4">
                <Link href="/workspace">
                  <Button size="lg" className="h-12 px-8 text-lg font-bold gap-2 shadow-lg shadow-primary/20">
                    Comenzar Análisis <ArrowRight className="w-5 h-5" />
                  </Button>
                </Link>
                <Button variant="outline" size="lg" className="h-12 px-8 text-lg font-medium">
                  Ver Documentación
                </Button>
              </div>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section className="w-full py-20 lg:py-32 border-t">
          <div className="container px-4 md:px-6 mx-auto">
            <div className="flex flex-col items-center justify-center space-y-4 text-center mb-16">
              <h2 className="text-3xl font-bold tracking-tighter sm:text-4xl md:text-5xl">El Pipeline de Datos Perfecto (v3.0)</h2>
              <p className="max-w-[700px] text-muted-foreground md:text-lg">
                Arquitectura Medallion (Bronze/Silver) con hallazgos inteligentes y visualizaciones automáticas.
              </p>
            </div>
            <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
              <Card className="border-none shadow-none bg-muted/50">
                <CardHeader>
                  <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                    <ShieldCheck className="w-6 h-6 text-primary" />
                  </div>
                  <CardTitle>Análisis Automatizado</CardTitle>
                  <CardDescription className="text-base">
                    Nuestros <span className="font-semibold">Findings</span> inteligentes detectan automáticamente duplicados, nulos, cardinalidad extrema y anomalías de calidad.
                  </CardDescription>
                </CardHeader>
              </Card>
              <Card className="border-none shadow-none bg-muted/50">
                <CardHeader>
                  <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                    <BarChart3 className="w-6 h-6 text-primary" />
                  </div>
                  <CardTitle>Visualización Clara</CardTitle>
                  <CardDescription className="text-base">
                    Generación automática de <span className="font-semibold">ChartSpecs</span> agnósticos, ofreciendo la mejor representación visual para cada tipo de dato.
                  </CardDescription>
                </CardHeader>
              </Card>
              <Card className="border-none shadow-none bg-muted/50">
                <CardHeader>
                  <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                    <HistoryIcon className="w-6 h-6 text-primary" />
                  </div>
                  <CardTitle>Trazabilidad Completa</CardTitle>
                  <CardDescription className="text-base">
                    Provenance integrada en cada paso del flujo Medallion. Conoce exactamente qué transformaciones se aplicaron a tu dataset.
                  </CardDescription>
                </CardHeader>
              </Card>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t py-12 bg-muted/20">
        <div className="container px-4 md:px-6 mx-auto flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex flex-col gap-2">
            <span className="font-bold text-xl">Data-X</span>
            <p className="text-xs text-muted-foreground">© 2026 Data-X Labs. Todos los derechos reservados.</p>
          </div>
          <nav className="flex gap-8">
            <Link className="text-sm hover:text-primary transition-colors font-medium" href="/workspace">Workspace</Link>
            <Link className="text-sm hover:text-primary transition-colors font-medium" href="/docs">Documentación</Link>
            <Link className="text-sm hover:text-primary transition-colors font-medium" href="#">Privacidad</Link>
          </nav>
        </div>
      </footer>
    </div>
  );
}
