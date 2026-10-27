import React, { useState } from 'react';
import { 
  Cpu, 
  Table, 
  Workflow, 
  Copy, 
  Check, 
  Terminal,
  ArrowRight
} from 'lucide-react';
import type { TACInstruction, BasicBlock } from '../../types/compiler';

interface IntermediateCodeTabProps {
  instructions: TACInstruction[];
  blocks: BasicBlock[];
}

export const IntermediateCodeTab: React.FC<IntermediateCodeTabProps> = ({
  instructions,
  blocks,
}) => {
  const [viewMode, setViewMode] = useState<'linear' | 'quadruples' | 'blocks'>('linear');
  const [copied, setCopied] = useState(false);
  const [selectedInstruction, setSelectedInstruction] = useState<TACInstruction | null>(null);

  const tacText = instructions.map((i) => `${i.id.toString().padStart(3, ' ')}: ${i.representation}`).join('\n');

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(tacText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // fallback
    }
  };

  const getOpBadge = (op: string) => {
    switch (op) {
      case 'LABEL':
        return 'bg-purple-950/70 text-purple-300 border-purple-800/60';
      case 'GOTO':
      case 'IF_FALSE':
      case 'IF_EQ':
      case 'IF_NE':
      case 'IF_LT':
      case 'IF_LE':
      case 'IF_GT':
      case 'IF_GE':
        return 'bg-amber-950/70 text-amber-300 border-amber-800/60';
      case 'CALL':
      case 'PARAM':
      case 'RETURN':
        return 'bg-blue-950/70 text-blue-300 border-blue-800/60';
      case 'ASSIGN':
        return 'bg-emerald-950/70 text-emerald-300 border-emerald-800/60';
      default:
        return 'bg-zinc-800 text-zinc-300 border-zinc-700';
    }
  };

  if (instructions.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8 text-center text-zinc-500 font-mono text-xs">
        <Cpu className="w-8 h-8 text-zinc-700 mb-2 stroke-[1.5]" />
        <p className="text-zinc-300 font-medium text-sm">Intermediate Code Not Generated</p>
        <p className="text-zinc-500 mt-1 max-w-sm font-sans text-xs">
          Analyze C code to generate linear Three-Address Code (TAC), quadruples, and basic block control flow graphs.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full space-y-2.5 font-mono text-xs">
      {/* View Mode Switcher & Copy Controls */}
      <div className="flex items-center justify-between pb-2 border-b border-zinc-800 select-none shrink-0">
        <div className="flex items-center bg-zinc-900 border border-zinc-800 rounded p-0.5 font-sans">
          <button
            onClick={() => setViewMode('linear')}
            className={`flex items-center space-x-1.5 px-2.5 py-1 rounded text-xs transition-colors ${
              viewMode === 'linear'
                ? 'bg-zinc-200 text-zinc-950 font-semibold'
                : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            <Terminal className="w-3.5 h-3.5" />
            <span>TAC ({instructions.length})</span>
          </button>
          <button
            onClick={() => setViewMode('quadruples')}
            className={`flex items-center space-x-1.5 px-2.5 py-1 rounded text-xs transition-colors ${
              viewMode === 'quadruples'
                ? 'bg-zinc-200 text-zinc-950 font-semibold'
                : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            <Table className="w-3.5 h-3.5" />
            <span>Quadruples</span>
          </button>
          <button
            onClick={() => setViewMode('blocks')}
            className={`flex items-center space-x-1.5 px-2.5 py-1 rounded text-xs transition-colors ${
              viewMode === 'blocks'
                ? 'bg-zinc-200 text-zinc-950 font-semibold'
                : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            <Workflow className="w-3.5 h-3.5" />
            <span>CFG Blocks ({blocks.length})</span>
          </button>
        </div>

        <button
          onClick={handleCopy}
          className="flex items-center space-x-1.5 px-2.5 py-1 rounded text-xs text-zinc-300 hover:text-white bg-zinc-900 border border-zinc-800 transition-colors font-sans"
          title="Copy TAC representation"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-emerald-400 font-medium">Copied</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5 text-zinc-400" />
              <span>Copy TAC</span>
            </>
          )}
        </button>
      </div>

      {/* Mode 1: Linear Three-Address Code View */}
      {viewMode === 'linear' && (
        <div className="flex-1 bg-zinc-950 border border-zinc-800 rounded-md overflow-hidden flex flex-col min-h-0">
          <div className="flex-1 overflow-auto p-1.5 space-y-0.5">
            {instructions.map((ins) => {
              const isSelected = selectedInstruction?.id === ins.id;
              const isLabel = ins.op === 'LABEL';

              return (
                <div
                  key={ins.id}
                  onClick={() => setSelectedInstruction(ins)}
                  className={`flex items-center px-2.5 py-1 rounded cursor-pointer transition-colors ${
                    isSelected
                      ? 'bg-zinc-800 border border-zinc-700 text-white font-medium'
                      : isLabel
                      ? 'bg-zinc-900/90 text-purple-300 font-bold border-l-2 border-purple-500'
                      : 'hover:bg-zinc-900/60 text-zinc-300'
                  }`}
                >
                  <span className="w-8 text-zinc-600 select-none text-[11px]">
                    {ins.id}
                  </span>
                  <span className="w-12 font-mono text-[10px] text-zinc-500">
                    [{ins.basic_block}]
                  </span>
                  <span
                    className={`px-1.5 py-0.2 rounded text-[10px] uppercase font-bold mr-2 border ${getOpBadge(
                      ins.op
                    )}`}
                  >
                    {ins.op}
                  </span>
                  <span className="flex-1 font-semibold text-zinc-100">
                    {ins.representation}
                  </span>
                  {ins.line_reference && (
                    <span className="text-[10px] text-zinc-600 font-sans ml-2">
                      L{ins.line_reference}
                    </span>
                  )}
                </div>
              );
            })}
          </div>

          {/* Selected instruction description footer */}
          {selectedInstruction && (
            <div className="h-8 bg-zinc-900 border-t border-zinc-800 px-3 flex items-center justify-between text-[11px] text-zinc-300 select-none shrink-0 font-sans">
              <div className="flex items-center space-x-2 truncate">
                <span className="font-mono font-bold text-white">#{selectedInstruction.id}: {selectedInstruction.representation}</span>
                <span className="text-zinc-600">•</span>
                <span className="text-zinc-400">{selectedInstruction.explanation}</span>
              </div>
              <button
                onClick={() => setSelectedInstruction(null)}
                className="text-zinc-500 hover:text-zinc-300 text-xs ml-2"
              >
                ✕
              </button>
            </div>
          )}
        </div>
      )}

      {/* Mode 2: Quadruples Table View */}
      {viewMode === 'quadruples' && (
        <div className="flex-1 bg-zinc-950 border border-zinc-800 rounded-md overflow-hidden flex flex-col min-h-0">
          <div className="overflow-auto flex-1 font-mono text-xs">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-zinc-900/90 border-b border-zinc-800 text-zinc-400 text-[11px] sticky top-0 z-10 select-none">
                  <th className="py-2 px-3 w-12 text-center text-zinc-500">#</th>
                  <th className="py-2 px-3">Operator</th>
                  <th className="py-2 px-3">Arg 1</th>
                  <th className="py-2 px-3">Arg 2</th>
                  <th className="py-2 px-3">Result / Target</th>
                  <th className="py-2 px-3">Block</th>
                  <th className="py-2 px-3">Representation</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-850/60">
                {instructions.map((ins) => (
                  <tr
                    key={ins.id}
                    onClick={() => setSelectedInstruction(ins)}
                    className="hover:bg-zinc-900/60 cursor-pointer transition-colors text-zinc-300"
                  >
                    <td className="py-1.5 px-3 text-center text-zinc-600 text-[11px]">{ins.id}</td>
                    <td className="py-1.5 px-3">
                      <span className={`px-1.5 py-0.2 rounded text-[10px] uppercase font-bold border ${getOpBadge(ins.op)}`}>
                        {ins.op}
                      </span>
                    </td>
                    <td className="py-1.5 px-3 text-sky-400 font-semibold">{ins.arg1 ?? '-'}</td>
                    <td className="py-1.5 px-3 text-sky-400 font-semibold">{ins.arg2 ?? '-'}</td>
                    <td className="py-1.5 px-3 text-emerald-400 font-bold">{ins.result ?? '-'}</td>
                    <td className="py-1.5 px-3 text-zinc-400 text-[11px]">{ins.basic_block}</td>
                    <td className="py-1.5 px-3 text-zinc-100 font-semibold">{ins.representation}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Mode 3: Control Flow Graph (CFG) Basic Blocks View */}
      {viewMode === 'blocks' && (
        <div className="flex-1 overflow-auto p-1 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 min-h-0">
          {blocks.map((b) => (
            <div
              key={b.id}
              className="bg-zinc-900 border border-zinc-800 rounded-md p-3 flex flex-col justify-between shadow-xs hover:border-zinc-700 transition-colors space-y-2.5"
            >
              <div>
                <div className="flex items-center justify-between border-b border-zinc-800 pb-2">
                  <div className="flex items-center space-x-2">
                    <span className="w-2 h-2 rounded-full bg-sky-400" />
                    <span className="font-mono font-bold text-zinc-100 text-xs">
                      {b.id}: {b.label}
                    </span>
                  </div>
                  <span className="text-[10px] text-zinc-500 font-sans">
                    {b.instruction_ids.length} instrs
                  </span>
                </div>

                {/* Instructions inside Block */}
                <div className="mt-2 bg-zinc-950 rounded p-2 border border-zinc-850 font-mono text-[11px] space-y-0.5 max-h-36 overflow-y-auto">
                  {b.instruction_ids.map((id) => {
                    const ins = instructions[id];
                    return (
                      <div key={id} className="text-zinc-300 truncate">
                        <span className="text-zinc-600 mr-2 text-[10px] select-none">{id}:</span>
                        <span className="text-zinc-100">{ins?.representation}</span>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* CFG Predecessors and Successors Connections */}
              <div className="pt-2 border-t border-zinc-800/80 grid grid-cols-2 gap-2 text-[10px] font-mono">
                <div>
                  <span className="text-zinc-500 block font-sans">Predecessors:</span>
                  <div className="flex flex-wrap gap-1 mt-0.5">
                    {b.predecessors.length > 0 ? (
                      b.predecessors.map((p) => (
                        <span key={p} className="bg-zinc-800 text-sky-300 px-1.5 py-0.2 rounded border border-zinc-700">
                          {p}
                        </span>
                      ))
                    ) : (
                      <span className="text-zinc-600">Entry</span>
                    )}
                  </div>
                </div>

                <div>
                  <span className="text-zinc-500 block font-sans">Successors:</span>
                  <div className="flex flex-wrap gap-1 mt-0.5">
                    {b.successors.length > 0 ? (
                      b.successors.map((s) => (
                        <span key={s} className="bg-zinc-800 text-emerald-300 px-1.5 py-0.2 rounded border border-zinc-700 flex items-center space-x-0.5">
                          <span>{s}</span>
                          <ArrowRight className="w-2.5 h-2.5" />
                        </span>
                      ))
                    ) : (
                      <span className="text-zinc-600">Exit</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
