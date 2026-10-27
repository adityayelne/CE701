import React, { useState, useEffect } from 'react';
import { 
  GraduationCap, 
  BookOpen, 
  Sparkles, 
  CheckCircle2, 
  AlertTriangle, 
  Layers, 
  FolderTree, 
  Database, 
  Cpu,
  RefreshCw
} from 'lucide-react';
import type { ConceptExplanation } from '../types/compiler';
import { explainConcept } from '../services/api';

const CONCEPTS = [
  { id: 'lexical_analysis', label: '1. Lexical Analysis', icon: Layers },
  { id: 'syntax_analysis', label: '2. Parsing & AST', icon: FolderTree },
  { id: 'symbol_table', label: '3. Symbol Table & Scopes', icon: Database },
  { id: 'intermediate_code', label: '4. Three-Address Code', icon: Cpu },
];

export const ConceptExplainer: React.FC = () => {
  const [activeConceptId, setActiveConceptId] = useState('lexical_analysis');
  const [data, setData] = useState<ConceptExplanation | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    explainConcept(activeConceptId)
      .then((res) => {
        if (isMounted) setData(res);
      })
      .catch((err) => {
        console.error('Failed to load concept', err);
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [activeConceptId]);

  return (
    <div className="bg-[#161b22] border border-[#30363d] rounded-lg flex flex-col overflow-hidden h-full">
      {/* Panel Header */}
      <div className="h-11 bg-[#1c2128] border-b border-[#30363d] px-4 flex items-center justify-between select-none">
        <div className="flex items-center space-x-2">
          <GraduationCap className="w-4 h-4 text-cyan-400" />
          <span className="text-xs font-bold text-white uppercase tracking-wider font-mono">
            Compiler Construction Tutor
          </span>
        </div>
        <span className="text-[10px] text-cyan-300 bg-cyan-950/80 px-2 py-0.5 rounded border border-cyan-800/50">
          Educational Guide
        </span>
      </div>

      {/* Concept Selector Tabs */}
      <div className="flex items-center border-b border-[#30363d] bg-[#0d1117] px-2 py-1.5 overflow-x-auto select-none space-x-1">
        {CONCEPTS.map((c) => {
          const Icon = c.icon;
          const isActive = activeConceptId === c.id;
          return (
            <button
              key={c.id}
              onClick={() => setActiveConceptId(c.id)}
              className={`flex items-center space-x-1.5 px-3 py-1 rounded-md text-xs font-medium whitespace-nowrap transition-colors ${
                isActive
                  ? 'bg-[#21262d] text-cyan-400 shadow-sm border border-[#30363d]'
                  : 'text-[#8b949e] hover:text-[#c9d1d9]'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{c.label}</span>
            </button>
          );
        })}
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {loading ? (
          <div className="h-48 flex items-center justify-center text-xs text-[#8b949e] space-x-2">
            <RefreshCw className="w-4 h-4 animate-spin text-cyan-400" />
            <span>Loading compiler construction principle...</span>
          </div>
        ) : data ? (
          <div className="space-y-4 text-xs">
            {/* Title & Phase */}
            <div className="flex items-start justify-between border-b border-[#30363d] pb-3">
              <div>
                <span className="text-[10px] uppercase font-mono font-bold text-cyan-400 tracking-wider">
                  {data.phase}
                </span>
                <h3 className="text-sm font-bold text-white mt-0.5">
                  {data.title}
                </h3>
              </div>
            </div>

            {/* Summary */}
            <p className="text-[#c9d1d9] leading-relaxed text-xs bg-[#0d1117] p-3 rounded-lg border border-[#30363d]">
              {data.summary}
            </p>

            {/* Detailed Explanation */}
            <div>
              <h4 className="font-semibold text-white text-xs mb-1.5 flex items-center space-x-1.5">
                <BookOpen className="w-3.5 h-3.5 text-cyan-400" />
                <span>Compiler Theory & Mechanics</span>
              </h4>
              <p className="text-[#8b949e] leading-relaxed">
                {data.detailed_explanation}
              </p>
            </div>

            {/* Key Principles */}
            <div>
              <h4 className="font-semibold text-white text-xs mb-1.5 flex items-center space-x-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                <span>Core Architectural Principles</span>
              </h4>
              <div className="space-y-1.5">
                {data.key_principles.map((p, idx) => (
                  <div
                    key={idx}
                    className="flex items-start space-x-2 text-[#c9d1d9] bg-[#0d1117] p-2 rounded border border-[#21262d]"
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5 shrink-0" />
                    <span>{p}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Code Example if provided */}
            {data.code_example && (
              <div>
                <h4 className="font-semibold text-white text-xs mb-1.5 flex items-center space-x-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                  <span>Grammar / Transformation Pattern</span>
                </h4>
                <div className="bg-[#090d13] border border-[#30363d] rounded-lg p-3 font-mono text-[11px] text-cyan-300 whitespace-pre overflow-x-auto leading-relaxed">
                  {data.code_example}
                </div>
              </div>
            )}

            {/* Common Pitfalls */}
            {data.common_pitfalls && data.common_pitfalls.length > 0 && (
              <div>
                <h4 className="font-semibold text-white text-xs mb-1.5 flex items-center space-x-1.5">
                  <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
                  <span>Frequent Implementation Pitfalls</span>
                </h4>
                <div className="space-y-1">
                  {data.common_pitfalls.map((pitfall, idx) => (
                    <div
                      key={idx}
                      className="text-[#8b949e] bg-red-950/20 border border-red-900/30 p-2 rounded text-[11px]"
                    >
                      • {pitfall}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : null}
      </div>
    </div>
  );
};
