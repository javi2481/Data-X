"use client";

import { useState, useRef, DragEvent } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Upload, File, X, CheckCircle2 } from 'lucide-react';
import { Progress } from '@/components/ui/progress';
import { toast } from 'sonner';

import { api } from '@/lib/api';
import { SessionResponse } from '@/types/contracts';

interface FileUploaderProps {
  onUploadComplete: (session: SessionResponse) => void;
  onUploadError: (error: unknown) => void;
}

const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB
const ALLOWED_EXTENSIONS = ['.csv', '.xlsx', '.xls', '.pdf', '.docx'];

export function FileUploader({ onUploadComplete, onUploadError }: FileUploaderProps) {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [progress, setProgress] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateFile = (file: File): boolean => {
    const extension = '.' + file.name.split('.').pop()?.toLowerCase();
    
    if (!ALLOWED_EXTENSIONS.includes(extension)) {
      toast.error(`Tipo de archivo no soportado. Usa: ${ALLOWED_EXTENSIONS.join(', ')}`);
      return false;
    }

    if (file.size > MAX_FILE_SIZE) {
      toast.error('El archivo es demasiado grande. Máximo 50MB.');
      return false;
    }

    return true;
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      if (validateFile(selectedFile)) {
        setFile(selectedFile);
        toast.info(`Archivo seleccionado: ${selectedFile.name}`);
      } else {
        if (fileInputRef.current) fileInputRef.current.value = '';
      }
    }
  };

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      if (validateFile(droppedFile)) {
        setFile(droppedFile);
        toast.info(`Archivo seleccionado: ${droppedFile.name}`);
      }
    }
  };

  const removeFile = () => {
    setFile(null);
    setProgress(0);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setProgress(10);
    
    const toastId = toast.loading('Subiendo y procesando archivo...');

    try {
      // FE-002: Progreso simulado con límite de tiempo
      const MAX_PROGRESS_TIME = 30000; // 30 segundos máximo para progreso simulado
      const startTime = Date.now();
      const interval = setInterval(() => {
        const elapsed = Date.now() - startTime;
        if (elapsed > MAX_PROGRESS_TIME) {
          clearInterval(interval);
          setProgress(90); // Máximo 90% hasta que complete la llamada real
        } else {
          setProgress((prev) => (prev < 90 ? prev + 10 : prev));
        }
      }, 500);

      const data = await api.createSession(file);

      clearInterval(interval);
      setProgress(100);

      toast.success('Sesión creada correctamente', { id: toastId });
      onUploadComplete(data);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Error al procesar el archivo';
      toast.error(errorMessage, { id: toastId });
      onUploadError(err);
      setProgress(0);
    } finally {
      setUploading(false);
    }
  };

  return (
    <Card className={`w-full max-w-xl mx-auto border-dashed transition-all duration-200 ${isDragging ? 'border-primary bg-primary/5 scale-[1.02]' : ''}`}>
      <CardContent className="pt-6">
        {!file ? (
          <div 
            className="flex flex-col items-center justify-center py-10 px-4 border-2 border-dashed rounded-lg cursor-pointer hover:bg-muted/50 transition-colors"
            onClick={() => fileInputRef.current?.click()}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <Upload className={`w-10 h-10 mb-4 transition-colors ${isDragging ? 'text-primary' : 'text-muted-foreground'}`} />
            <p className="text-sm font-medium">
              {isDragging ? 'Suelta el archivo aquí' : 'Haz clic para subir o arrastra un archivo'}
            </p>
            <p className="text-xs text-muted-foreground mt-1">Soporta CSV, XLSX, XLS, PDF y DOCX (Max. 50MB)</p>
            <input 
              type="file" 
              className="hidden" 
              ref={fileInputRef}
              onChange={handleFileChange}
              accept=".csv,.xlsx,.xls,.pdf,.docx"
            />
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-muted rounded-md">
              <div className="flex items-center gap-3">
                <File className="w-8 h-8 text-primary" />
                <div className="flex flex-col">
                  <span className="text-sm font-medium truncate max-w-[200px]">{file.name}</span>
                  <span className="text-xs text-muted-foreground">{(file.size / 1024).toFixed(1)} KB</span>
                </div>
              </div>
              {!uploading && (
                <Button variant="ghost" size="icon" onClick={removeFile}>
                  <X className="w-4 h-4" />
                </Button>
              )}
            </div>

            {uploading && (
              <div className="space-y-2">
                <div className="flex justify-between text-xs">
                  <span>Procesando...</span>
                  <span>{progress}%</span>
                </div>
                <Progress value={progress} className="h-2" />
              </div>
            )}

            {progress === 100 && (
              <div className="flex items-center gap-2 text-sm text-green-600 font-medium">
                <CheckCircle2 className="w-4 h-4" />
                Archivo procesado correctamente
              </div>
            )}

            {!uploading && progress < 100 && (
              <Button className="w-full" onClick={handleUpload}>
                Procesar Datos
              </Button>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
