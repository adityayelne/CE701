import React from 'react';
import type { CompilerMetrics, CompilerError } from '../types/compiler';

interface StatusBarProps {
  metrics: CompilerMetrics;
  errors: CompilerError[];
}

export const StatusBar: React.FC<StatusBarProps> = ({ metrics, errors }) => {
  const hasErrors = errors.length > 0;

  return (
    <footer className="h-7 bg-zinc-950/85 backdrop-blur-md border-t border-zinc-800/80 px-4 flex items-center justify-between text-[11px] font-mono text-zinc-500 select-none shrink-0">
      {/* Left: Compiler Pass Metrics */}
      <div className="flex items-center space-x-3 overflow-x-auto">
        <div className="flex items-center space-x-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-blue-500 shrink-0" />
          <span className="text-zinc-400 font-bold font-mono">CE701 Engine</span>
        </div>
        <span className="text-zinc-700">|</span>
        <span>Tokens: <strong className="text-zinc-200">{metrics.token_count}</strong></span>
        <span className="text-zinc-700">•</span>
        <span>AST Nodes: <strong className="text-zinc-200">{metrics.ast_node_count}</strong> (depth {metrics.ast_max_depth})</span>
        <span className="text-zinc-700">•</span>
        <span>Symbols: <strong className="text-zinc-200">{metrics.symbol_count}</strong></span>
        <span className="text-zinc-700">•</span>
        <span>TAC: <strong className="text-zinc-200">{metrics.tac_count}</strong></span>
      </div>

      {/* Right: Errors Status & Analysis Time */}
      <div className="flex items-center space-x-3">
        {hasErrors ? (
          <span className="text-rose-400 font-semibold flex items-center space-x-1">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-500" />
            <span>{errors.length} diagnostic{errors.length === 1 ? '' : 's'}</span>
          </span>
        ) : (
          <span className="text-emerald-400 font-semibold flex items-center space-x-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            <span>0 diagnostics</span>
          </span>
        )}
        <span className="text-zinc-700">|</span>
        <span className="text-zinc-400">{metrics.analysis_time_ms} ms</span>
      </div>
    </footer>
  );
};
