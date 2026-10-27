import React, { useState, useMemo } from 'react';
import { 
  Search, 
  Layers
} from 'lucide-react';
import type { Token } from '../../types/compiler';

interface LexicalTabProps {
  tokens: Token[];
}

export const LexicalTab: React.FC<LexicalTabProps> = ({ tokens }) => {
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedToken, setSelectedToken] = useState<Token | null>(null);

  const categories = useMemo(() => {
    const cats = new Set<string>();
    tokens.forEach((t) => cats.add(t.category));
    return ['all', ...Array.from(cats)];
  }, [tokens]);

  const filteredTokens = useMemo(() => {
    return tokens.filter((t) => {
      const matchesCat = selectedCategory === 'all' || t.category === selectedCategory;
      const matchesSearch =
        t.value.toLowerCase().includes(search.toLowerCase()) ||
        t.type.toLowerCase().includes(search.toLowerCase()) ||
        t.description.toLowerCase().includes(search.toLowerCase());
      return matchesCat && matchesSearch;
    });
  }, [tokens, selectedCategory, search]);

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'keyword':
        return 'text-purple-400 bg-purple-950/50 border-purple-800/60';
      case 'identifier':
        return 'text-sky-400 bg-sky-950/50 border-sky-800/60';
      case 'literal':
        return 'text-amber-300 bg-amber-950/50 border-amber-800/60';
      case 'operator':
        return 'text-rose-400 bg-rose-950/50 border-rose-800/60';
      case 'delimiter':
        return 'text-zinc-400 bg-zinc-800/60 border-zinc-700/60';
      case 'preprocessor':
        return 'text-blue-400 bg-blue-950/50 border-blue-800/60';
      case 'comment':
        return 'text-emerald-400 bg-emerald-950/50 border-emerald-800/60';
      default:
        return 'text-zinc-300 bg-zinc-800 border-zinc-700';
    }
  };

  if (tokens.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8 text-center text-zinc-500 font-mono text-xs">
        <Layers className="w-8 h-8 text-zinc-700 mb-2 stroke-[1.5]" />
        <p className="text-zinc-300 font-medium text-sm">No Tokens Generated</p>
        <p className="text-zinc-500 mt-1 max-w-sm font-sans text-xs">
          Click &apos;Analyze Code&apos; to scan source code into a linear token stream.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full space-y-2.5 font-mono text-xs">
      {/* Search and Category Filters */}
      <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-zinc-800 shrink-0">
        <div className="relative flex-1 min-w-[180px] max-w-xs">
          <Search className="w-3.5 h-3.5 text-zinc-500 absolute left-2.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Filter lexeme or type..."
            className="w-full bg-zinc-900 border border-zinc-800 rounded pl-8 pr-2.5 py-1 text-xs text-zinc-200 placeholder-zinc-500 outline-none focus:border-zinc-700 font-mono"
          />
        </div>

        {/* Category Filter Pills */}
        <div className="flex items-center flex-wrap gap-1 font-sans">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-2 py-0.5 rounded text-[11px] font-medium capitalize transition-colors ${
                selectedCategory === cat
                  ? 'bg-zinc-200 text-zinc-950 font-semibold'
                  : 'bg-zinc-900 text-zinc-400 hover:text-zinc-200 border border-zinc-800'
              }`}
            >
              {cat}
            </button>
          ))}
          <span className="text-[11px] text-zinc-500 ml-1">
            ({filteredTokens.length}/{tokens.length})
          </span>
        </div>
      </div>

      {/* Main Token Stream Table */}
      <div className="flex-1 bg-zinc-950 border border-zinc-800 rounded-md overflow-hidden flex flex-col min-h-0">
        <div className="overflow-auto flex-1">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-zinc-900/90 border-b border-zinc-800 text-zinc-400 font-mono text-[11px] sticky top-0 z-10 select-none">
                <th className="py-2 px-3 w-12 text-center text-zinc-500">#</th>
                <th className="py-2 px-3 font-semibold">Lexeme</th>
                <th className="py-2 px-3 font-semibold">Token Type</th>
                <th className="py-2 px-3">Category</th>
                <th className="py-2 px-3 text-center">Line</th>
                <th className="py-2 px-3 text-center">Col</th>
                <th className="py-2 px-3 text-center">Len</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-850/60 font-mono text-xs">
              {filteredTokens.map((t, idx) => {
                const isSelected = selectedToken === t;
                return (
                  <tr
                    key={idx}
                    onClick={() => setSelectedToken(t)}
                    className={`hover:bg-zinc-900/60 cursor-pointer transition-colors ${
                      isSelected ? 'bg-zinc-900 text-white font-medium' : 'text-zinc-300'
                    }`}
                  >
                    <td className="py-1.5 px-3 text-center text-zinc-600 text-[11px]">
                      {idx + 1}
                    </td>
                    <td className="py-1.5 px-3 font-bold text-zinc-100 max-w-[200px] truncate">
                      {t.value}
                    </td>
                    <td className="py-1.5 px-3 text-zinc-300 font-mono text-[11px]">
                      {t.type}
                    </td>
                    <td className="py-1.5 px-3">
                      <span className={`px-1.5 py-0.2 rounded text-[10px] font-bold border uppercase tracking-wide ${getCategoryColor(t.category)}`}>
                        {t.category}
                      </span>
                    </td>
                    <td className="py-1.5 px-3 text-center text-zinc-400 text-[11px]">
                      {t.line}
                    </td>
                    <td className="py-1.5 px-3 text-center text-zinc-400 text-[11px]">
                      {t.column}
                    </td>
                    <td className="py-1.5 px-3 text-center text-zinc-500 text-[11px]">
                      {t.length}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Selected Token Details Footer */}
        {selectedToken && (
          <div className="h-8 bg-zinc-900 border-t border-zinc-800 px-3 flex items-center justify-between text-[11px] text-zinc-300 select-none shrink-0 font-sans">
            <div className="flex items-center space-x-3 truncate">
              <span className="font-mono font-bold text-white">&apos;{selectedToken.value}&apos;</span>
              <span className="text-zinc-500">•</span>
              <span className="text-zinc-400">{selectedToken.description}</span>
              <span className="text-zinc-500">•</span>
              <span className="font-mono text-zinc-400">Regex: /{selectedToken.regex_pattern}/</span>
            </div>
            <button
              onClick={() => setSelectedToken(null)}
              className="text-zinc-500 hover:text-zinc-300 text-xs ml-2"
            >
              ✕
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
