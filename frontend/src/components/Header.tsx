import React from 'react';
import { 
  Play, 
  Sparkles, 
  Code2, 
  RefreshCw
} from 'lucide-react';
import type { SampleProgram } from '../types/compiler';

interface HeaderProps {
  samples: SampleProgram[];
  selectedSampleId: string;
  onSelectSample: (sample: SampleProgram) => void;
  onAnalyze: () => void;
  onAIFix: () => void;
  isAnalyzing: boolean;
  isFixing: boolean;
  hasErrors: boolean;
  apiHealthy: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  samples,
  selectedSampleId,
  onSelectSample,
  onAnalyze,
  onAIFix,
  isAnalyzing,
  isFixing,
  hasErrors,
  apiHealthy,
}) => {
  const isBusy = isAnalyzing || isFixing;

  return (
    <header className="h-16 border-b border-zinc-800/80 bg-zinc-950/80 backdrop-blur-xl px-4 sm:px-6 flex items-center justify-between sticky top-0 z-30 select-none font-sans shrink-0 shadow-lg shadow-black/40">
      {/* Top-Left: Distinctive CE701 Brand & Product Identity */}
      <div className="flex items-center space-x-3 sm:space-x-4">
        {/* Minimalist Geometric Compiler Logo */}
        <div className="flex items-center space-x-3 group">
          <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-zinc-900 via-zinc-900/90 to-zinc-950 border border-zinc-750/80 shadow-[inset_0_1px_0_rgba(255,255,255,0.1)] group-hover:border-blue-500/50 transition-colors">
            {/* Ambient subtle glow */}
            <div className="absolute inset-0 rounded-xl bg-blue-500/10 blur-xs opacity-50 group-hover:opacity-100 transition-opacity" />
            
            {/* Geometric compiler pipeline SVG mark */}
            <svg 
              className="w-5 h-5 text-blue-400 relative z-10 transition-transform duration-200 group-hover:scale-105" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              strokeWidth="2" 
              strokeLinecap="round" 
              strokeLinejoin="round"
            >
              {/* Lexer token diamond */}
              <polygon points="6 3 10 7 6 11 2 7" className="text-blue-400 stroke-blue-400" />
              {/* Parser AST branch */}
              <path d="M10 7h4l3 5" className="stroke-indigo-400" />
              <circle cx="17" cy="12" r="2" fill="currentColor" className="text-indigo-400" />
              {/* Intermediate Code arrows */}
              <path d="M17 14v4l-4 3" className="stroke-teal-400" />
              <rect x="9" y="19" width="4" height="4" rx="1" className="fill-teal-500/20 stroke-teal-400" />
            </svg>
          </div>

          <div className="flex flex-col">
            <div className="flex items-baseline space-x-1.5">
              <span className="font-mono text-lg font-black tracking-tight text-white leading-none">
                CE701
              </span>
              <span className="w-1.5 h-1.5 rounded-full bg-blue-500 shrink-0" />
              <span className="text-sm font-semibold tracking-tight text-zinc-200 leading-none">
                CompilerLab
              </span>
            </div>
            <div className="flex items-center space-x-1.5 mt-1">
              <span className="text-[10px] uppercase font-mono tracking-wider font-semibold text-zinc-500">
                Compiler Construction Workbench
              </span>
            </div>
          </div>
        </div>

        <div className="h-6 w-px bg-zinc-800/80 hidden md:block" />

        {/* Secondary Controls: Sample Program Switcher */}
        <div className="hidden sm:flex items-center space-x-2 bg-zinc-900/70 backdrop-blur-sm border border-zinc-800/90 hover:border-zinc-700/80 rounded-xl px-3 py-1.5 text-xs text-zinc-300 transition-colors shadow-xs">
          <Code2 className="w-3.5 h-3.5 text-zinc-400 shrink-0" />
          <span className="text-[11px] text-zinc-500 font-mono hidden lg:inline">Sample:</span>
          <select
            value={selectedSampleId}
            onChange={(e) => {
              const s = samples.find((x) => x.id === e.target.value);
              if (s) onSelectSample(s);
            }}
            disabled={isBusy}
            className="bg-transparent text-zinc-200 outline-none cursor-pointer font-sans text-xs pr-1 focus:ring-0 disabled:opacity-50"
          >
            {samples.map((s) => (
              <option key={s.id} value={s.id} className="bg-zinc-900 text-zinc-200">
                {s.title}
              </option>
            ))}
          </select>
        </div>

        {/* Secondary: Engine Status Indicator */}
        <div 
          className="hidden md:flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-zinc-900/60 border border-zinc-800/80 text-[11px] font-mono shadow-xs"
          title={apiHealthy ? 'Compiler engine online (port 8000)' : 'Compiler engine offline'}
        >
          <span className={`w-2 h-2 rounded-full shrink-0 ${apiHealthy ? 'bg-emerald-400 ring-2 ring-emerald-500/20 animate-pulse' : 'bg-rose-500 ring-2 ring-rose-500/20'}`} />
          <span className="text-zinc-400 text-[11px]">{apiHealthy ? 'engine online' : 'offline'}</span>
        </div>
      </div>

      {/* Top-Right: Prominent Primary Action Buttons */}
      <div className="flex items-center space-x-3">
        {/* Primary Action 1: Analyze Code */}
        <button
          onClick={onAnalyze}
          disabled={isBusy}
          className={`h-11 px-5 sm:px-6 rounded-xl text-sm font-bold tracking-tight transition-all duration-150 flex items-center space-x-2.5 select-none active:scale-[0.98] cursor-pointer shadow-md ${
            isAnalyzing
              ? 'bg-zinc-800 text-zinc-400 border border-zinc-700/80 cursor-wait'
              : 'bg-gradient-to-r from-blue-600 via-indigo-600 to-indigo-700 hover:from-blue-500 hover:via-indigo-500 hover:to-indigo-600 text-white border border-blue-400/40 shadow-indigo-950/70 hover:shadow-indigo-900/80 hover:shadow-lg shadow-[inset_0_1px_0_rgba(255,255,255,0.2)] focus:ring-2 focus:ring-blue-500/40'
          }`}
          title="Run complete compilation pipeline: Lexer, Parser, Scoped Symbols, and TAC IR"
        >
          {isAnalyzing ? (
            <RefreshCw className="w-4 h-4 animate-spin text-zinc-300" />
          ) : (
            <Play className="w-4 h-4 fill-current text-white/95" />
          )}
          <span>{isAnalyzing ? 'Analyzing passes...' : 'Analyze Code'}</span>
        </button>

        {/* Primary Action 2: Fix with AI */}
        <button
          onClick={onAIFix}
          disabled={isBusy}
          className={`h-11 px-5 sm:px-6 rounded-xl text-sm font-bold tracking-tight transition-all duration-150 flex items-center space-x-2.5 select-none active:scale-[0.98] cursor-pointer shadow-md ${
            isFixing
              ? 'bg-zinc-900 text-zinc-400 border border-zinc-800 cursor-wait'
              : hasErrors
              ? 'bg-gradient-to-r from-emerald-600 via-emerald-600 to-teal-600 hover:from-emerald-500 hover:via-emerald-500 hover:to-teal-500 text-white border border-emerald-400/40 shadow-emerald-950/70 hover:shadow-emerald-900/80 hover:shadow-lg shadow-[inset_0_1px_0_rgba(255,255,255,0.2)] focus:ring-2 focus:ring-emerald-500/40'
              : 'bg-zinc-900/90 hover:bg-zinc-850 text-emerald-400 hover:text-emerald-300 border border-emerald-500/35 hover:border-emerald-400/60 shadow-emerald-950/30 shadow-[inset_0_1px_0_rgba(255,255,255,0.06)]'
          }`}
          title="Diagnose syntax errors using AI/heuristics and review proposed fix in diff viewer"
        >
          {isFixing ? (
            <RefreshCw className="w-4 h-4 animate-spin text-emerald-400" />
          ) : (
            <Sparkles className="w-4 h-4 text-emerald-300 transition-transform duration-200 group-hover:scale-110" />
          )}
          <span>{isFixing ? 'Generating repair...' : 'Fix with AI'}</span>
        </button>
      </div>
    </header>
  );
};
