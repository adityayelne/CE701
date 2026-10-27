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
  return (
    <header className="h-[68px] border-b border-zinc-800/80 bg-zinc-950/85 backdrop-blur-md px-4 sm:px-6 flex items-center justify-between sticky top-0 z-30 select-none font-sans shrink-0 shadow-sm">
      {/* Top-Left: Distinctive CE701 Brand & Product Identity */}
      <div className="flex items-center space-x-3 sm:space-x-4">
        {/* Minimalist Geometric Compiler Logo */}
        <div className="flex items-center space-x-3">
          <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-zinc-900 via-zinc-900 to-zinc-950 border border-zinc-700/60 shadow-inner group">
            {/* Ambient subtle glow behind logo */}
            <div className="absolute inset-0 rounded-xl bg-indigo-500/10 blur-xs transition-opacity group-hover:opacity-100 opacity-60" />
            <svg 
              className="w-5 h-5 text-indigo-400 relative z-10 transition-transform duration-200 group-hover:scale-105" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              strokeWidth="2" 
              strokeLinecap="round" 
              strokeLinejoin="round"
            >
              <polyline points="4 17 10 11 4 5" />
              <line x1="12" y1="19" x2="20" y2="19" />
              <circle cx="17" cy="9" r="2" fill="currentColor" className="text-blue-400" />
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
                C Translation Workbench
              </span>
            </div>
          </div>
        </div>

        <div className="h-6 w-px bg-zinc-800/80 hidden md:block" />

        {/* Secondary Controls: Sample Program Switcher */}
        <div className="hidden sm:flex items-center space-x-1.5 bg-zinc-900/80 backdrop-blur-sm border border-zinc-800/90 hover:border-zinc-700/80 rounded-lg px-2.5 py-1.5 text-xs text-zinc-300 transition-colors shadow-xs">
          <Code2 className="w-3.5 h-3.5 text-zinc-400 shrink-0" />
          <span className="text-[11px] text-zinc-500 font-mono hidden lg:inline">Sample:</span>
          <select
            value={selectedSampleId}
            onChange={(e) => {
              const s = samples.find((x) => x.id === e.target.value);
              if (s) onSelectSample(s);
            }}
            className="bg-transparent text-zinc-200 outline-none cursor-pointer font-sans text-xs pr-1 focus:ring-0"
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
          className="hidden md:flex items-center space-x-1.5 px-2 py-1 rounded-md bg-zinc-900/50 border border-zinc-850/80 text-[11px]"
          title={apiHealthy ? 'CompilerLab engine connected on port 8000' : 'CompilerLab engine offline'}
        >
          <span className={`w-2 h-2 rounded-full shrink-0 ${apiHealthy ? 'bg-emerald-400 shadow-sm shadow-emerald-400/50 ring-2 ring-emerald-500/20' : 'bg-rose-500 ring-2 ring-rose-500/20'}`} />
          <span className="text-zinc-400 text-[11px] font-mono">{apiHealthy ? 'online' : 'offline'}</span>
        </div>
      </div>

      {/* Top-Right: Prominent Primary Action Buttons */}
      <div className="flex items-center space-x-3 sm:space-x-3.5">
        {/* Primary Action 1: Analyze Code */}
        <button
          onClick={onAnalyze}
          disabled={isAnalyzing}
          className={`h-11 sm:h-12 px-5 sm:px-6 rounded-xl text-sm sm:text-base font-bold tracking-tight transition-all duration-150 flex items-center space-x-2.5 select-none active:scale-[0.98] cursor-pointer shadow-md ${
            isAnalyzing
              ? 'bg-zinc-800 text-zinc-400 border border-zinc-700/80 cursor-wait'
              : 'bg-gradient-to-r from-blue-600 via-indigo-600 to-indigo-700 hover:from-blue-500 hover:via-indigo-500 hover:to-indigo-600 text-white border border-blue-400/30 shadow-indigo-950/60 hover:shadow-indigo-900/70 hover:shadow-lg'
          }`}
          title="Run complete compilation pipeline: Lexer, Parser, Scoped Symbols, and TAC IR"
        >
          {isAnalyzing ? (
            <RefreshCw className="w-4 h-4 sm:w-5 sm:h-5 animate-spin text-zinc-300" />
          ) : (
            <Play className="w-4 h-4 sm:w-4.5 sm:h-4.5 fill-current text-white/90" />
          )}
          <span>{isAnalyzing ? 'Analyzing passes...' : 'Analyze Code'}</span>
        </button>

        {/* Primary Action 2: Fix with AI */}
        <button
          onClick={onAIFix}
          disabled={isFixing}
          className={`h-11 sm:h-12 px-5 sm:px-6 rounded-xl text-sm sm:text-base font-bold tracking-tight transition-all duration-150 flex items-center space-x-2.5 select-none active:scale-[0.98] cursor-pointer shadow-md ${
            isFixing
              ? 'bg-zinc-900 text-zinc-400 border border-zinc-800 cursor-wait'
              : hasErrors
              ? 'bg-gradient-to-r from-emerald-600 via-emerald-600 to-teal-600 hover:from-emerald-500 hover:via-emerald-500 hover:to-teal-500 text-white border border-emerald-400/40 shadow-emerald-950/60 hover:shadow-emerald-900/70 hover:shadow-lg'
              : 'bg-zinc-900/90 hover:bg-zinc-850 text-emerald-400 hover:text-emerald-300 border border-emerald-500/35 hover:border-emerald-400/60 shadow-emerald-950/30'
          }`}
          title="Diagnose syntax errors using AI/heuristics and review proposed fix in diff viewer"
        >
          {isFixing ? (
            <RefreshCw className="w-4 h-4 sm:w-5 sm:h-5 animate-spin text-emerald-400" />
          ) : (
            <Sparkles className="w-4 h-4 sm:w-4.5 sm:h-4.5 text-emerald-300 transition-transform duration-200 group-hover:scale-110" />
          )}
          <span>{isFixing ? 'Generating repair...' : 'Fix with AI'}</span>
        </button>
      </div>
    </header>
  );
};
