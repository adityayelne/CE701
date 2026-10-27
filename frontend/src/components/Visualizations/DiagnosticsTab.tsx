import React, { useState } from 'react';
import { 
  AlertCircle, 
  CheckCircle2, 
  Sparkles, 
  CornerDownRight, 
  ExternalLink,
  Flame,
  Info
} from 'lucide-react';
import type { CompilerError } from '../../types/compiler';

interface DiagnosticsTabProps {
  errors: CompilerError[];
  onAIFix: () => void;
  isFixing: boolean;
  onSelectLine?: (line: number) => void;
}

export const DiagnosticsTab: React.FC<DiagnosticsTabProps> = ({
  errors,
  onAIFix,
  isFixing,
  onSelectLine,
}) => {
  const [stageFilter, setStageFilter] = useState<'all' | 'syntax' | 'semantic' | 'lexical'>('all');

  if (errors.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8 text-center text-zinc-500 font-mono text-xs">
        <div className="w-12 h-12 rounded-2xl bg-emerald-950/50 border border-emerald-700/50 flex items-center justify-center mb-3 shadow-lg shadow-emerald-950/40">
          <CheckCircle2 className="w-6 h-6 text-emerald-400 stroke-[2]" />
        </div>
        <p className="text-zinc-200 font-semibold text-sm">Clean Compilation</p>
        <p className="text-zinc-400 mt-1 max-w-sm font-sans text-xs leading-relaxed">
          Source code parsed cleanly without lexical, syntax, or semantic diagnostics under C grammar rules.
        </p>
      </div>
    );
  }

  const syntaxCount = errors.filter(e => e.stage === 'syntax').length;
  const semanticCount = errors.filter(e => e.stage === 'semantic').length;
  const lexicalCount = errors.filter(e => e.stage === 'lexical').length;

  const filteredErrors = errors.filter(e => {
    if (stageFilter === 'all') return true;
    return e.stage === stageFilter;
  });

  return (
    <div className="h-full flex flex-col space-y-3 font-mono text-xs overflow-hidden">
      {/* Top Controls Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 pb-2.5 border-b border-zinc-800/80 shrink-0 select-none">
        <div className="flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
          <span className="font-bold text-zinc-100 font-sans text-xs">
            {errors.length} Compiler Diagnostic{errors.length === 1 ? '' : 's'} Emitted
          </span>
        </div>

        {/* Action Button: Fix with AI */}
        <button
          onClick={onAIFix}
          disabled={isFixing}
          className="flex items-center space-x-2 px-4 py-1.5 rounded-xl bg-gradient-to-r from-emerald-600 via-teal-600 to-emerald-700 hover:from-emerald-500 hover:via-teal-500 hover:to-emerald-600 text-white shadow-md shadow-emerald-950/60 hover:shadow-emerald-900/70 transition-all text-xs font-sans font-bold cursor-pointer active:scale-[0.98] border border-emerald-400/30 self-start sm:self-auto"
        >
          <Sparkles className="w-3.5 h-3.5 text-emerald-200" />
          <span>{isFixing ? 'Diagnosing...' : 'Fix with AI'}</span>
        </button>
      </div>

      {/* Filter Pills & Cascading Recovery Notice */}
      <div className="flex items-center justify-between gap-2 shrink-0 select-none">
        <div className="flex items-center space-x-1.5 overflow-x-auto text-[11px] font-sans">
          <button
            onClick={() => setStageFilter('all')}
            className={`px-2.5 py-1 rounded-lg border transition-all cursor-pointer font-medium ${
              stageFilter === 'all'
                ? 'bg-zinc-800 text-white border-zinc-650 shadow-xs'
                : 'bg-zinc-900/60 text-zinc-400 border-zinc-800 hover:text-zinc-200'
            }`}
          >
            All ({errors.length})
          </button>
          {syntaxCount > 0 && (
            <button
              onClick={() => setStageFilter('syntax')}
              className={`px-2.5 py-1 rounded-lg border transition-all cursor-pointer font-medium ${
                stageFilter === 'syntax'
                  ? 'bg-rose-950/70 text-rose-200 border-rose-700/80 shadow-xs'
                  : 'bg-zinc-900/60 text-zinc-400 border-zinc-800 hover:text-rose-300'
              }`}
            >
              Syntax ({syntaxCount})
            </button>
          )}
          {semanticCount > 0 && (
            <button
              onClick={() => setStageFilter('semantic')}
              className={`px-2.5 py-1 rounded-lg border transition-all cursor-pointer font-medium ${
                stageFilter === 'semantic'
                  ? 'bg-amber-950/70 text-amber-200 border-amber-700/80 shadow-xs'
                  : 'bg-zinc-900/60 text-zinc-400 border-zinc-800 hover:text-amber-300'
              }`}
            >
              Semantic ({semanticCount})
            </button>
          )}
          {lexicalCount > 0 && (
            <button
              onClick={() => setStageFilter('lexical')}
              className={`px-2.5 py-1 rounded-lg border transition-all cursor-pointer font-medium ${
                stageFilter === 'lexical'
                  ? 'bg-blue-950/70 text-blue-200 border-blue-700/80 shadow-xs'
                  : 'bg-zinc-900/60 text-zinc-400 border-zinc-800 hover:text-blue-300'
              }`}
            >
              Lexical ({lexicalCount})
            </button>
          )}
        </div>

        {errors.length > 2 && (
          <span className="text-[10px] text-zinc-500 font-sans hidden md:flex items-center space-x-1 shrink-0">
            <Info className="w-3 h-3 text-zinc-500" />
            <span>Resolving error #1 clears downstream cascade</span>
          </span>
        )}
      </div>

      {/* Diagnostics Cards List */}
      <div className="flex-1 overflow-auto space-y-2.5 pr-1">
        {filteredErrors.map((err, idx) => {
          const isPrimary = (idx === 0 && stageFilter === 'all');

          return (
            <div
              key={idx}
              onClick={() => onSelectLine && onSelectLine(err.line)}
              className={`p-3.5 rounded-xl border space-y-2 text-xs transition-all duration-150 cursor-pointer group shadow-xs ${
                isPrimary
                  ? 'bg-gradient-to-r from-amber-950/25 via-zinc-900/95 to-zinc-900/95 border-amber-600/50 hover:border-amber-500 shadow-amber-950/20'
                  : 'bg-zinc-900/80 border-zinc-800/80 hover:border-zinc-700'
              }`}
            >
              {/* Card Header: Stage, Line/Col coordinates, and Inspect Button */}
              <div className="flex items-center justify-between text-[11px]">
                <div className="flex items-center space-x-2">
                  {/* Primary Root Cause Badge for Error #1 */}
                  {isPrimary ? (
                    <span className="flex items-center space-x-1 px-2 py-0.5 rounded-md bg-amber-500/20 text-amber-300 border border-amber-500/50 text-[10px] font-bold tracking-wide">
                      <Flame className="w-3 h-3 text-amber-400 shrink-0" />
                      <span>Primary Root Cause</span>
                    </span>
                  ) : (
                    <span className="px-1.5 py-0.2 rounded text-[10px] bg-zinc-800 text-zinc-400 border border-zinc-700 font-mono">
                      #{idx + 1} Cascading
                    </span>
                  )}

                  <span
                    className={`px-1.5 py-0.2 rounded text-[10px] uppercase font-bold border ${
                      err.stage === 'syntax'
                        ? 'bg-rose-950/80 text-rose-300 border-rose-800/70'
                        : err.stage === 'semantic'
                        ? 'bg-amber-950/80 text-amber-300 border-amber-800/70'
                        : 'bg-zinc-800 text-zinc-300 border-zinc-700'
                    }`}
                  >
                    {err.stage}
                  </span>

                  <span className="text-zinc-400 font-mono text-[11px]">
                    Line <strong className="text-zinc-100">{err.line}</strong>, Col <strong className="text-zinc-100">{err.column}</strong>
                  </span>
                </div>

                {/* Inspect in Editor Button */}
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    if (onSelectLine) onSelectLine(err.line);
                  }}
                  className="flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 hover:text-white border border-zinc-700 hover:border-zinc-500 transition-all text-[11px] font-sans font-medium cursor-pointer shadow-xs active:scale-[0.96]"
                  title={`Jump to and highlight line ${err.line} in code editor`}
                >
                  <span>Inspect in editor</span>
                  <ExternalLink className="w-3 h-3 text-blue-400 shrink-0" />
                </button>
              </div>

              {/* Error Message */}
              <p className="text-zinc-100 font-sans font-semibold text-xs leading-relaxed">
                {err.message}
              </p>

              {/* Code Context Snippet */}
              {err.snippet && (
                <div className="bg-zinc-950/80 rounded-lg px-3 py-1.5 text-zinc-300 border border-zinc-850 font-mono text-[11px] overflow-x-auto flex items-center space-x-2">
                  <span className="text-zinc-500 select-none shrink-0 font-sans text-[10px] uppercase">Context:</span>
                  <span className="text-rose-300 font-semibold">{err.snippet}</span>
                </div>
              )}

              {/* Parser Recommendation / Guidance */}
              {err.suggestion && (
                <div className="flex items-start space-x-2 text-[11px] text-zinc-300 font-sans bg-zinc-950/50 p-2.5 rounded-lg border border-zinc-800/60 leading-relaxed">
                  <CornerDownRight className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                  <span>
                    <strong className="text-zinc-200 font-medium">Compiler Guidance: </strong>
                    {err.suggestion}
                  </span>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
