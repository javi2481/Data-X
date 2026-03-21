import React, { useState } from 'react';
import { Sparkles, ChevronDown, ChevronUp } from 'lucide-react';

interface EnrichedExplanationProps {
  explanation: string | null | undefined;
}

export const EnrichedExplanation: React.FC<EnrichedExplanationProps> = ({ explanation }) => {
  const [isOpen, setIsOpen] = useState(false);
  
  if (!explanation) return null;

  return (
    <div className="w-full mt-4">
      <button 
        onClick={(e) => {
          e.stopPropagation(); // Evitar cerrar el FindingCard si es colapsable
          setIsOpen(!isOpen);
        }}
        className="w-full py-2 px-3 bg-indigo-50 hover:bg-indigo-100 rounded-md text-indigo-700 text-sm font-medium transition-colors flex items-center justify-between"
      >
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4" />
          Explicación detallada (IA)
        </div>
        {isOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
      </button>
      
      {isOpen && (
        <div className="pt-3 px-1 text-gray-700 text-sm leading-relaxed whitespace-pre-wrap italic animate-in fade-in slide-in-from-top-1">
          {explanation}
        </div>
      )}
    </div>
  );
};
