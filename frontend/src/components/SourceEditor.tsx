import React, { useRef, useState, useEffect } from 'react';
import { 
  Copy, 
  Check, 
  Trash2, 
  FileCode, 
  AlertCircle
} from 'lucide-react';
import type { CompilerError } from '../types/compiler';

export type HighlightTarget = number | { line: number; ts?: number } | null;

interface SourceEditorProps {
  code: string;
  onChange: (newCode: string) => void;
  errors: CompilerError[];
  onClear: () => void;
  highlightedLine?: HighlightTarget;
}

export const SourceEditor: React.FC<SourceEditorProps> = ({
  code,
  onChange,
  errors,
  onClear,
  highlightedLine,
}) => {
  const [copied, setCopied] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const gutterRef = useRef<HTMLDivElement>(null);

  const lines = code.split('\n');
  const errorLines = new Map<number, CompilerError>();
  errors.forEach((err) => {
    if (!errorLines.has(err.line)) {
      errorLines.set(err.line, err);
    }
  });

  const activeLineNumber = typeof highlightedLine === 'object' && highlightedLine !== null
    ? highlightedLine.line
    : typeof highlightedLine === 'number'
    ? highlightedLine
    : null;

  // Jump to and select line in editor when activeLineNumber or highlightedLine changes
  useEffect(() => {
    if (!activeLineNumber || !textareaRef.current) return;
    const textarea = textareaRef.current;
    const allLines = code.split('\n');
    if (activeLineNumber < 1 || activeLineNumber > allLines.length) return;

    // Calculate start and end character offset of the target line
    let startIndex = 0;
    for (let i = 0; i < activeLineNumber - 1; i++) {
      startIndex += allLines[i].length + 1; // +1 for '\n'
    }
    const lineContent = allLines[activeLineNumber - 1] || '';
    const endIndex = startIndex + lineContent.length;

    // Focus editor and set selection highlight
    textarea.focus();
    try {
      textarea.setSelectionRange(startIndex, endIndex);
    } catch {
      // Ignore if browser restricts selection
    }

    // Smoothly scroll to the target line (24px line height)
    const lineHeight = 24;
    const targetScroll = Math.max(0, (activeLineNumber - 4) * lineHeight);
    textarea.scrollTo({ top: targetScroll, behavior: 'smooth' });
    if (gutterRef.current) {
      gutterRef.current.scrollTo({ top: targetScroll, behavior: 'smooth' });
    }
  }, [highlightedLine, activeLineNumber, code]);

  // Synchronize scrolling from textarea to line numbers gutter
  const handleScroll = (e: React.UIEvent<HTMLTextAreaElement>) => {
    if (gutterRef.current) {
      gutterRef.current.scrollTop = e.currentTarget.scrollTop;
    }
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback
    }
  };

  const lineCount = lines.length;
  const charCount = code.length;

  return (
    <div className="flex flex-col h-full bg-zinc-950/90 backdrop-blur-sm border border-zinc-800/80 rounded-xl overflow-hidden font-mono shadow-sm">
      {/* Editor Header Toolbar with Glassmorphism */}
      <div className="h-10 bg-zinc-900/75 backdrop-blur-sm border-b border-zinc-800/80 px-3.5 flex items-center justify-between select-none text-xs">
        <div className="flex items-center space-x-2.5">
          <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-zinc-800/90 border border-zinc-700/60 text-zinc-200 shadow-xs">
            <FileCode className="w-3.5 h-3.5 text-blue-400" />
            <span className="font-semibold text-xs tracking-tight">source.c</span>
          </div>

          <span className="text-[11px] text-zinc-500 font-sans">
            {lineCount} {lineCount === 1 ? 'line' : 'lines'} • {charCount} chars
          </span>

          {errors.length > 0 && (
            <span className="flex items-center space-x-1 text-[11px] px-2 py-0.5 rounded-full bg-rose-950/80 text-rose-300 border border-rose-800/60 font-sans shadow-xs">
              <AlertCircle className="w-3 h-3 text-rose-400 shrink-0" />
              <span>{errors.length} error{errors.length > 1 ? 's' : ''}</span>
            </span>
          )}

          {activeLineNumber && (
            <span className="flex items-center space-x-1 text-[11px] px-2 py-0.5 rounded-full bg-amber-950/80 text-amber-300 border border-amber-800/60 font-sans shadow-xs animate-in fade-in duration-100">
              <span>Inspecting Line {activeLineNumber}</span>
            </span>
          )}
        </div>

        <div className="flex items-center space-x-1.5 font-sans">
          {/* Copy Button */}
          <button
            onClick={handleCopy}
            disabled={!code.trim()}
            className="flex items-center space-x-1.5 px-2.5 py-1 rounded-md text-xs text-zinc-300 hover:text-white hover:bg-zinc-800/80 border border-transparent hover:border-zinc-700/60 transition-all disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
            title="Copy source code to clipboard"
          >
            {copied ? (
              <>
                <Check className="w-3.5 h-3.5 text-emerald-400" />
                <span className="text-emerald-400 font-medium text-[11px]">Copied</span>
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5 text-zinc-400" />
                <span className="text-[11px]">Copy</span>
              </>
            )}
          </button>

          {/* Clear Button */}
          <button
            onClick={onClear}
            disabled={!code.trim()}
            className="flex items-center space-x-1.5 px-2.5 py-1 rounded-md text-xs text-zinc-400 hover:text-rose-400 hover:bg-zinc-800/80 border border-transparent hover:border-zinc-700/60 transition-all disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
            title="Clear editor code"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span className="text-[11px]">Clear</span>
          </button>
        </div>
      </div>

      {/* Editor Body */}
      <div className="flex-1 relative flex overflow-hidden text-xs sm:text-sm bg-zinc-950/60">
        {/* Synchronized Line Numbers Column */}
        <div 
          ref={gutterRef}
          className="w-12 bg-zinc-950/80 border-r border-zinc-800/70 text-zinc-600 select-none text-right py-3.5 pr-2.5 text-xs font-mono leading-6 flex flex-col items-end shrink-0 overflow-hidden"
        >
          {lines.map((_, idx) => {
            const lineNum = idx + 1;
            const hasErr = errorLines.has(lineNum);
            const isHighlighted = activeLineNumber === lineNum;

            return (
              <div
                key={lineNum}
                className={`w-full text-right h-6 flex items-center justify-end px-1 transition-all duration-150 ${
                  isHighlighted
                    ? 'text-amber-300 font-bold bg-amber-500/25 border-r-2 border-amber-400 shadow-sm'
                    : hasErr
                    ? 'text-rose-400 font-bold bg-rose-950/40 border-r-2 border-rose-500'
                    : 'text-zinc-600 hover:text-zinc-400'
                }`}
                title={hasErr ? `Line ${lineNum}: ${errorLines.get(lineNum)?.message}` : `Line ${lineNum}`}
              >
                {isHighlighted ? (
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-400 mr-1 shrink-0 animate-ping" />
                ) : hasErr ? (
                  <span className="w-1.5 h-1.5 rounded-full bg-rose-400 mr-1 shrink-0" />
                ) : null}
                <span>{lineNum}</span>
              </div>
            );
          })}
        </div>

        {/* Text Area with Scroll Sync */}
        <div className="flex-1 relative bg-transparent">
          <textarea
            ref={textareaRef}
            value={code}
            onChange={(e) => onChange(e.target.value)}
            onScroll={handleScroll}
            spellCheck={false}
            placeholder="// Paste or write C source code here to analyze..."
            className="w-full h-full bg-transparent text-zinc-100 p-3.5 text-xs sm:text-sm font-mono leading-6 resize-none outline-none focus:ring-0 border-0 selection:bg-indigo-600/40 selection:text-white overflow-auto"
            style={{ tabSize: 4 }}
          />

          {/* Empty state hint */}
          {!code.trim() && (
            <div className="absolute inset-0 flex flex-col items-center justify-center p-6 text-center text-zinc-600 select-none pointer-events-none">
              <FileCode className="w-9 h-9 text-zinc-800 mb-2 stroke-[1.5]" />
              <p className="text-xs font-sans text-zinc-400 font-medium">Editor is empty</p>
              <p className="text-[11px] font-sans text-zinc-500 mt-1">Select a sample program from the header or write C code.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
