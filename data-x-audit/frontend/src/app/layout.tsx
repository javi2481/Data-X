import type { Metadata } from "next";
import { Inter } from "next/font/google";
import Link from 'next/link';
import "./globals.css";
import { ThemeProvider } from "@/components/theme-provider";
import { Toaster } from "sonner";
import { ModeToggle } from "@/components/ModeToggle";
import { UserMenu } from "@/components/UserMenu";

const inter = Inter({
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Data-X | Análisis de datos",
  description: "Plataforma de análisis de datos determinístico",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es" suppressHydrationWarning>
      <body className={`${inter.className} antialiased min-h-screen flex flex-col transition-colors duration-300`}>
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
            <div className="container flex h-16 items-center px-4 md:px-6 mx-auto">
              <Link href="/" className="flex items-center gap-2 font-bold text-xl mr-6">
                Data-X
              </Link>
              <nav className="flex items-center gap-6 text-sm font-medium flex-1">
                <Link href="/workspace" className="transition-colors hover:text-foreground/80 text-foreground/60">
                  Workspace
                </Link>
                <Link href="/docs" className="transition-colors hover:text-foreground/80 text-foreground/60">
                  Documentación
                </Link>
              </nav>
              <div className="flex items-center gap-4">
                <span className="text-xs text-muted-foreground hidden sm:inline-block">v0.1.0</span>
                <ModeToggle />
                <UserMenu />
              </div>
            </div>
          </header>
          <main className="flex-1">
            {children}
          </main>
          <Toaster richColors position="top-right" />
        </ThemeProvider>
      </body>
    </html>
  );
}
