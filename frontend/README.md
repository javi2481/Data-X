# Data-X Frontend (Next.js)

Interfaz de usuario moderna para la plataforma Data-X. Construida con Next.js 15, TypeScript, Tailwind CSS y shadcn/ui.

## Características

- **Dashboard Interactivo**: Workspace para la gestión de sesiones y análisis.
- **Visualización Dinámica**: Gráficos integrados con Recharts basados en la configuración del backend.
- **Trazabilidad (Provenance)**: Panel lateral para visualizar los pasos del pipeline de datos.
- **Experiencia AI**: Interfaz optimizada para mostrar resúmenes narrativos inteligentes.

## Instalación

1. Instalar dependencias:
   ```bash
   npm install
   ```

2. Configurar variables de entorno:
   ```bash
   cp .env.example .env.local
   # Asegúrate de que NEXT_PUBLIC_API_BASE_URL apunte al backend (ej: http://localhost:8000)
   ```

## Desarrollo

Ejecutar el servidor de desarrollo:
```bash
npm run dev
```

Abrir [http://localhost:3000](http://localhost:3000) en el navegador.

## Estructura

- `src/app`: Rutas de la aplicación (Landing, Workspace).
- `src/components`: Componentes de UI y lógica visual (ArtifactRenderer, FileUploader).
- `src/lib`: Cliente API y utilidades.
- `src/types`: Contratos TypeScript sincronizados con el backend.
