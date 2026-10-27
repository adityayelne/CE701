import React, { useState } from 'react';
import { 
  X, 
  Copy, 
  Check, 
  ArrowRight, 
  AlertTriangle,
  Sparkles,
  ShieldCheck,
  ShieldAlert
} from 'lucide-react';
import type { DiagnosisAndFixResponse } from '../types/compiler';

interface DiffModalProps {
  data: DiagnosisAndFixResponse | null;
  isOpen: boolean;
  onClose: () => void;
  onApplyFix: (correctedCode: string) => void;
}

export const DiffModal: React.FC<DiffModalProps> = ({
  data,
  isOpen,
  onClose,
  onApplyFix,
}) => {
  const [copied, setCopied] = useState(false);

  if (!isOpen || !data) return null;

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(data.corrected_code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback
    }
  };

  const isAI = data.repair_origin === 'ai';
  const hasProviderIssue = data.provider_status && data.provider_status !== 'success';
  const isValidated = data.is_parser_validated && data.validation_status === 'PARSER_VALIDATED';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/75 backdrop-blur-md font-sans animate-in fade-in duration-150">
      <div className="bg-zinc-950/95 backdrop-blur-xl border border-zinc-700/70 rounded-2xl shadow-2xl shadow-black/90 w-full max-w-4xl h-[86vh] flex flex-col overflow-hidden">
        {/* Glassmorphic Header */}
        <div className="h-14 border-b border-zinc-800/80 px-5 flex items-center justify-between bg-zinc-900/80 backdrop-blur-sm select-none shrink-0">
          <div className="flex items-center space-x-3 overflow-x-auto">
            <div className="flex items-center space-x-2">
              <span className="font-mono text-sm font-bold text-white tracking-tight">
                Diagnostic & Repair Diff
              </span>
            </div>

            {/* Origin Badge: AI vs Heuristic */}
            {isAI ? (
              <span className="text-xs font-mono px-2.5 py-0.5 rounded-md bg-emerald-950/80 text-emerald-300 border border-emerald-700/60 shadow-xs flex items-center space-x-1">
                <Sparkles className="w-3 h-3 text-emerald-400" />
                <span>AI: {data.provider_used}</span>
              </span>
            ) : (
              <span className="text-xs font-mono px-2.5 py-0.5 rounded-md bg-amber-950/80 text-amber-300 border border-amber-700/60 shadow-xs flex items-center space-x-1">
                <AlertTriangle className="w-3 h-3 text-amber-400" />
                <span>Local Heuristic Fallback</span>
              </span>
            )}

            {/* Parser Validation Status Badge */}
            {isValidated ? (
              <span className="text-xs font-mono px-2.5 py-0.5 rounded-md bg-emerald-950/80 text-emerald-300 border border-emerald-700/60 shadow-xs flex items-center space-x-1">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                <span>Parser-Validated (0 Syntax Errors)</span>
              </span>
            ) : (
              <span className="text-xs font-mono px-2.5 py-0.5 rounded-md bg-rose-950/80 text-rose-300 border border-rose-700/60 shadow-xs flex items-center space-x-1">
                <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
                <span>Validation Failed ({data.residual_error_count ?? data.diagnostics.length} Syntax Errors Remain)</span>
              </span>
            )}
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-800/80 transition-colors cursor-pointer"
            title="Close dialog (preserve original source)"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-auto p-5 space-y-4 bg-zinc-950/70">
          {/* Provider Notice Banner (if 429, malformed response, or fallback) */}
          {hasProviderIssue && data.error_detail && (
            <div className="p-3.5 rounded-xl bg-amber-950/40 border border-amber-800/60 text-xs text-amber-300 space-y-1.5 shadow-xs">
              <div className="flex items-center space-x-2 font-semibold">
                <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
                <span>AI Provider Notice ({data.provider_status}): {data.error_detail}</span>
              </div>
              {data.recovery_guidance && (
                <p className="text-zinc-300 pl-6 text-[11px] leading-relaxed">
                  {data.recovery_guidance}
                </p>
              )}
            </div>
          )}

          {/* Validation Failure Warning & Residual Errors List */}
          {!isValidated && (
            <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800/70 text-xs text-rose-200 space-y-2.5 shadow-xs">
              <div className="flex items-center space-x-2 font-bold text-rose-300">
                <ShieldAlert className="w-4 h-4 text-rose-400 shrink-0" />
                <span>Parser Validation Failed: Syntax Errors Remain in Proposed Code</span>
              </div>
              <p className="text-zinc-300 text-[11px] leading-relaxed">
                This candidate repair was re-parsed by the compiler's lexical and syntax analyzers, but residual syntax errors were detected. The candidate is NOT marked as parser-validated.
              </p>
              {data.residual_errors && data.residual_errors.length > 0 && (
                <div className="p-2.5 rounded-lg bg-zinc-950/70 border border-rose-900/50 space-y-1 font-mono text-[11px]">
                  <div className="text-[10px] font-bold text-rose-400 uppercase tracking-wider mb-1">
                    Residual Parser Diagnostics ({data.residual_errors.length}):
                  </div>
                  {data.residual_errors.map((err, i) => (
                    <div key={i} className="flex items-start space-x-2 text-rose-300">
                      <span className="text-rose-400 font-semibold shrink-0">
                        Line {err.line}, Col {err.column}:
                      </span>
                      <span className="text-zinc-300 break-words">{err.message}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Problem & Fix Summary */}
          <div className="p-4 rounded-xl bg-zinc-900/70 border border-zinc-800/80 space-y-1.5 text-xs shadow-xs">
            <div className="font-semibold text-zinc-200">Analysis Summary:</div>
            <p className="text-zinc-300 leading-relaxed">{data.summary}</p>
            {data.explanation && (
              <p className="text-zinc-400 pt-2 text-[11px] border-t border-zinc-800/80 leading-relaxed font-sans">
                {data.explanation}
              </p>
            )}
          </div>

          {/* Diff View */}
          <div className="flex flex-col space-y-2 font-mono text-xs">
            <div className="flex items-center justify-between text-xs text-zinc-400 px-1 select-none">
              <div className="flex items-center space-x-3">
                <span className="flex items-center space-x-1.5">
                  <span className="w-2.5 h-2.5 rounded bg-rose-500/50 border border-rose-400" />
                  <span className="text-rose-300">Removed</span>
                </span>
                <span className="flex items-center space-x-1.5">
                  <span className="w-2.5 h-2.5 rounded bg-emerald-500/50 border border-emerald-400" />
                  <span className="text-emerald-300">Added</span>
                </span>
              </div>
              <span className="font-mono text-zinc-500">Unified Diff ({data.diff_lines.length} lines)</span>
            </div>

            <div className="border border-zinc-800/80 rounded-xl bg-zinc-900/60 backdrop-blur-xs overflow-x-auto divide-y divide-zinc-800/40 shadow-inner">
              {data.diff_lines.length === 0 ? (
                <div className="p-8 text-center text-zinc-500 font-sans">
                  No source code modifications required.
                </div>
              ) : (
                data.diff_lines.map((line, idx) => {
                  const isAdd = line.type === 'add';
                  const isRemove = line.type === 'remove';

                  return (
                    <div
                      key={idx}
                      className={`flex items-start px-3 py-1 leading-5 font-mono text-xs transition-colors ${
                        isAdd
                          ? 'bg-emerald-950/35 text-emerald-300'
                          : isRemove
                          ? 'bg-rose-950/35 text-rose-300'
                          : 'text-zinc-400'
                      }`}
                    >
                      <div className="w-8 text-right pr-2 text-zinc-600 select-none text-[11px]">
                        {line.old_line_number ?? ''}
                      </div>
                      <div className="w-8 text-right pr-2 text-zinc-600 select-none text-[11px] border-r border-zinc-800/80">
                        {line.new_line_number ?? ''}
                      </div>
                      <div className="w-6 text-center font-bold select-none text-xs">
                        {isAdd ? '+' : isRemove ? '-' : ' '}
                      </div>
                      <div className="flex-1 whitespace-pre pl-1 overflow-x-auto">
                        {line.content || ' '}
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>

        {/* Glassmorphic Footer Actions */}
        <div className="h-16 border-t border-zinc-800/80 px-5 flex items-center justify-between bg-zinc-900/80 backdrop-blur-sm select-none text-xs shrink-0">
          {/* Dynamic Validation Disclaimer */}
          <div className="flex items-center space-x-2 text-[11px] max-w-md hidden sm:flex">
            {isValidated ? (
              <>
                <ShieldCheck className="w-4 h-4 shrink-0 text-emerald-400" />
                <span className="text-zinc-300 truncate" title={data.validation_disclaimer}>
                  {data.validation_disclaimer}
                </span>
              </>
            ) : (
              <>
                <ShieldAlert className="w-4 h-4 shrink-0 text-rose-400" />
                <span className="text-rose-300 font-medium truncate" title={data.validation_disclaimer}>
                  {data.validation_disclaimer}
                </span>
              </>
            )}
          </div>

          {/* Action buttons */}
          <div className="flex items-center space-x-2.5 ml-auto">
            {/* Copy Code button */}
            <button
              onClick={handleCopy}
              className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-zinc-850 hover:bg-zinc-800 text-zinc-200 border border-zinc-750 transition-all cursor-pointer font-medium"
              title="Copy proposed code to clipboard for manual inspection"
            >
              {copied ? (
                <>
                  <Check className="w-3.5 h-3.5 text-emerald-400" />
                  <span className="text-emerald-400 font-semibold">Copied!</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5 text-zinc-400" />
                  <span>Copy Code</span>
                </>
              )}
            </button>

            {/* Safe Reject button */}
            <button
              onClick={onClose}
              className={`px-4 py-2 rounded-xl border transition-all cursor-pointer font-medium ${
                isValidated
                  ? 'bg-zinc-850 hover:bg-zinc-800 text-zinc-300 hover:text-white border-zinc-750'
                  : 'bg-zinc-800 hover:bg-zinc-750 text-white border-zinc-650 font-semibold shadow-xs'
              }`}
              title="Preserve original source code without changes"
            >
              Reject (Keep Original)
            </button>

            {/* Apply Action: Validated vs Unvalidated Warning */}
            {isValidated ? (
              <button
                onClick={() => {
                  onApplyFix(data.corrected_code);
                  onClose();
                }}
                className="flex items-center space-x-2 px-5 py-2 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold shadow-md shadow-emerald-950/60 hover:shadow-emerald-900/60 transition-all cursor-pointer active:scale-[0.98]"
              >
                <ShieldCheck className="w-4 h-4" />
                <span>Apply Validated Fix</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            ) : (
              <button
                onClick={() => {
                  if (window.confirm("Warning: This candidate repair failed parser validation and still contains syntax errors. Are you sure you want to apply unvalidated code to the editor?")) {
                    onApplyFix(data.corrected_code);
                    onClose();
                  }
                }}
                className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-rose-950/50 hover:bg-rose-900/60 text-rose-300 hover:text-rose-200 border border-rose-800/60 transition-all cursor-pointer font-medium text-xs"
                title="Caution: Candidate code contains residual syntax errors"
              >
                <AlertTriangle className="w-3.5 h-3.5 text-rose-400 shrink-0" />
                <span>Apply Unvalidated (Contains Errors)</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
