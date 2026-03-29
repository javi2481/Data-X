import React from 'react';

export default function LoadingScreen() {
  return (
    <div className="loading-screen" data-testid="loading-screen">
      <div className="loading-logo">🔍</div>
      <div className="loading-text">Cargando reporte de auditoría...</div>
      <div className="loading-bar">
        <div className="loading-bar-fill" />
      </div>
    </div>
  );
}
