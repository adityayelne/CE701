import React, { useState, useMemo } from 'react';
import { 
  Database, 
  Search
} from 'lucide-react';
import type { SymbolEntry } from '../../types/compiler';

interface SymbolTableTabProps {
  symbols: SymbolEntry[];
}

export const SymbolTableTab: React.FC<SymbolTableTabProps> = ({ symbols }) => {
  const [search, setSearch] = useState('');
  const [selectedScope, setSelectedScope] = useState<string>('all');

  const scopes = useMemo(() => {
    const s = new Set<string>();
    symbols.forEach((sym) => s.add(sym.scope));
    return ['all', ...Array.from(s)];
  }, [symbols]);

  const filteredSymbols = useMemo(() => {
    return symbols.filter((sym) => {
      const matchesScope = selectedScope === 'all' || sym.scope === selectedScope;
      const matchesSearch =
        sym.name.toLowerCase().includes(search.toLowerCase()) ||
        sym.type.toLowerCase().includes(search.toLowerCase()) ||
        sym.kind.toLowerCase().includes(search.toLowerCase());
      return matchesScope && matchesSearch;
    });
  }, [symbols, selectedScope, search]);

  const totalBytes = useMemo(() => {
    return symbols.reduce((acc, s) => acc + s.memory_size, 0);
  }, [symbols]);

  const maxDepth = useMemo(() => {
    return Math.max(0, ...symbols.map((s) => s.scope_level));
  }, [symbols]);

  const getKindColor = (kind: string) => {
    switch (kind) {
      case 'function':
        return 'text-sky-400 bg-sky-950/60 border-sky-800/60';
      case 'variable':
        return 'text-emerald-400 bg-emerald-950/60 border-emerald-800/60';
      case 'parameter':
        return 'text-purple-400 bg-purple-950/60 border-purple-800/60';
      case 'constant':
        return 'text-amber-400 bg-amber-950/60 border-amber-800/60';
      default:
        return 'text-zinc-400 bg-zinc-800 border-zinc-700';
    }
  };

  if (symbols.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8 text-center text-zinc-500 font-mono text-xs">
        <Database className="w-8 h-8 text-zinc-700 mb-2 stroke-[1.5]" />
        <p className="text-zinc-300 font-medium text-sm">Symbol Table Empty</p>
        <p className="text-zinc-500 mt-1 max-w-sm font-sans text-xs">
          Analyze C code with declarations to inspect scoped identifiers, memory allocations, and reference counts.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full space-y-2.5 font-mono text-xs">
      {/* Top Search, Scope Filters, and Metrics Summary */}
      <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-zinc-800 shrink-0">
        <div className="relative flex-1 min-w-[180px] max-w-xs">
          <Search className="w-3.5 h-3.5 text-zinc-500 absolute left-2.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search identifier or type..."
            className="w-full bg-zinc-900 border border-zinc-800 rounded pl-8 pr-2.5 py-1 text-xs text-zinc-200 placeholder-zinc-500 outline-none focus:border-zinc-700 font-mono"
          />
        </div>

        {/* Scope selector tabs & Summary telemetry */}
        <div className="flex items-center flex-wrap gap-2 text-[11px] font-sans">
          <div className="flex items-center space-x-1">
            <span className="text-zinc-500">Scope:</span>
            {scopes.map((sc) => (
              <button
                key={sc}
                onClick={() => setSelectedScope(sc)}
                className={`px-2 py-0.5 rounded font-mono text-[11px] transition-colors ${
                  selectedScope === sc
                    ? 'bg-zinc-200 text-zinc-950 font-semibold'
                    : 'bg-zinc-900 text-zinc-400 hover:text-zinc-200 border border-zinc-800'
                }`}
              >
                {sc}
              </button>
            ))}
          </div>

          <span className="text-zinc-700">|</span>

          <span className="text-zinc-400 font-mono text-[11px]">
            {symbols.length} IDs • {totalBytes}B total • Depth {maxDepth}
          </span>
        </div>
      </div>

      {/* Structured Symbol Table */}
      <div className="flex-1 bg-zinc-950 border border-zinc-800 rounded-md overflow-hidden flex flex-col min-h-0">
        <div className="overflow-auto flex-1">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-zinc-900/90 border-b border-zinc-800 text-zinc-400 font-mono text-[11px] sticky top-0 z-10 select-none">
                <th className="py-2 px-3 font-semibold">Identifier</th>
                <th className="py-2 px-3 font-semibold">Data Type</th>
                <th className="py-2 px-3">Kind</th>
                <th className="py-2 px-3">Scope</th>
                <th className="py-2 px-3 text-center">Depth</th>
                <th className="py-2 px-3 text-center">Line</th>
                <th className="py-2 px-3 text-center">Size</th>
                <th className="py-2 px-3 text-center">Offset</th>
                <th className="py-2 px-3 text-center">Refs</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-850/60 font-mono text-xs">
              {filteredSymbols.map((s, idx) => (
                <tr
                  key={idx}
                  className="hover:bg-zinc-900/60 transition-colors text-zinc-300"
                >
                  <td className="py-1.5 px-3 font-bold text-zinc-100 flex items-center space-x-1.5">
                    {s.scope_level > 0 && (
                      <span className="text-zinc-600 text-[10px]">{'└─'.repeat(s.scope_level)}</span>
                    )}
                    <span>{s.name}</span>
                  </td>
                  <td className="py-1.5 px-3 text-zinc-300 font-semibold text-[11px]">
                    {s.type}
                  </td>
                  <td className="py-1.5 px-3">
                    <span className={`px-1.5 py-0.2 rounded text-[10px] font-bold border uppercase tracking-wider ${getKindColor(s.kind)}`}>
                      {s.kind}
                    </span>
                  </td>
                  <td className="py-1.5 px-3 text-zinc-400 text-[11px]">
                    {s.scope}
                  </td>
                  <td className="py-1.5 px-3 text-center text-zinc-400 text-[11px]">
                    {s.scope_level}
                  </td>
                  <td className="py-1.5 px-3 text-center text-zinc-400 text-[11px]">
                    {s.line_declared}
                  </td>
                  <td className="py-1.5 px-3 text-center text-emerald-400 text-[11px]">
                    {s.memory_size}B
                  </td>
                  <td className="py-1.5 px-3 text-center text-zinc-400 text-[11px]">
                    +{s.offset}
                  </td>
                  <td className="py-1.5 px-3 text-center">
                    <span className={`px-1.5 py-0.2 rounded text-[10px] font-bold ${s.references > 0 ? 'bg-zinc-800 text-zinc-200' : 'text-zinc-600'}`}>
                      {s.references}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
