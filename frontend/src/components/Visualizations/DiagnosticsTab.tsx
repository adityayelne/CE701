import React from 'react';
import { AlertCircle, CheckCircle2, Sparkles, CornerDownRight, ExternalLink } from 'lucide-react';
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
  if (errors.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8 text-center text-zinc-500 font-mono text-xs">
        <CheckCircle2 className="w-8 h-8 text-emerald-400 mb-2 stroke-[1.5]" />
        <p className="text-zinc-200 font-medium text-sm">No Diagnostics Emitted</p>
        <p className="text-zinc-400 mt-1 max-w-sm font-sans text-xs">
          Source code parsed cleanly without lexical, syntax, or semantic diagnostics under C grammar rules.
        </p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col space-y-3 font-mono text-xs">
      {/* Header bar with quick action */}
      <div className="flex items-center justify-between pb-2 border-b border-zinc-800">
        <div className="flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 text-red-400" />
          <span className="font-semibold text-zinc-200 font-sans">
            {errors.length} Compiler Diagnostic{errors.length === 1 ? '' : 's'} Detected
          </span>
        </div>
        <button
          onClick={onAIFix}
          disabled={isFixing}
          className="flex items-center space-x-2 px-4 py-1.5 rounded-lg bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white shadow-sm hover:shadow-emerald-950/50 transition-all text-xs font-sans font-bold cursor-pointer active:scale-[0.98]"
        >
          <Sparkles className="w-3.5 h-3.5 text-emerald-200" />
          <span>{isFixing ? 'Diagnosing...' : 'Fix with AI'}</span>
        </button>
      </div>

      {/* Diagnostics List */}
      <div className="flex-1 overflow-auto space-y-2.5 pr-1">
        {errors.map((err, idx) => (
          <div
            key={idx}
            onClick={() => onSelectLine && onSelectLine(err.line)}
            className="p-3 rounded-md bg-zinc-900 border border-zinc-800 space-y-2 text-xs hover:border-zinc-700 transition-colors cursor-pointer group"
          >
            <div className="flex items-center justify-between text-[11px]">
              <div className="flex items-center space-x-2">
                <span
                  className={`px-1.5 py-0.2 rounded text-[10px] uppercase font-bold border ${
                    err.stage === 'syntax'
                      ? 'bg-red-950/70 text-red-300 border-red-800/60'
                      : err.stage === 'semantic'
                      ? 'bg-amber-950/70 text-amber-300 border-amber-800/60'
                      : 'bg-zinc-800 text-zinc-300 border-zinc-700'
                  }`}
                >
                  {err.stage}
                </span>
                <span className="text-zinc-400 font-mono">
                  Line <strong className="text-zinc-200">{err.line}</strong>, Col <strong className="text-zinc-200">{err.column}</strong>
                </span>
              </div>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  if (onSelectLine) onSelectLine(err.line);
                }}
                className="flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-zinc-800 hover:bg-zinc-700 text-zinc-300 hover:text-white border border-zinc-750 hover:border-zinc-500 transition-all text-[11px] font-sans font-medium cursor-pointer shadow-xs active:scale-[0.96]"
                title={`Jump to and select line ${err.line} in code editor`}
              >
                <span>Inspect in editor</span>
                <ExternalLink className="w-3 h-3 text-blue-400 shrink-0" />
              </button>
            </div>

            <p className="text-zinc-100 font-sans font-medium text-xs leading-relaxed">{err.message}</p>

            {err.snippet && (
              <div className="bg-zinc-950 rounded px-2.5 py-1 text-zinc-300 border border-zinc-800/80 font-mono text-[11px] overflow-x-auto">
                <span className="text-zinc-600 select-none mr-2">Context:</span>
                <span className="text-red-300">{err.snippet}</span>
              </div>
            )}

            {err.suggestion && (
              <div className="flex items-start space-x-1.5 text-[11px] text-zinc-400 pt-0.5 font-sans bg-zinc-950/40 p-2 rounded border border-zinc-800/40">
                <CornerDownRight className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                <span><strong className="text-zinc-300 font-medium">Parser Recommendation:</strong> {err.suggestion}</span>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
