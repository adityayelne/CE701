import React, { useState } from 'react';
import { 
  ChevronRight, 
  ChevronDown, 
  Search, 
  FolderTree, 
  Tag,
  Maximize2,
  Minimize2
} from 'lucide-react';
import type { ASTNode } from '../../types/compiler';

interface ASTTabProps {
  root: ASTNode | null | undefined;
}

interface TreeNodeProps {
  node: ASTNode;
  level: number;
  search: string;
  selectedNode: ASTNode | null;
  onSelectNode: (node: ASTNode) => void;
  expandAll: boolean;
  isLastChild: boolean;
}

const TreeNode: React.FC<TreeNodeProps> = ({
  node,
  level,
  search,
  selectedNode,
  onSelectNode,
  expandAll,
}) => {
  const [collapsed, setCollapsed] = useState(false);
  const hasChildren = node.children && node.children.length > 0;
  const isSelected = selectedNode?.id === node.id;

  const matchesSearch =
    search.trim() !== '' &&
    (node.type.toLowerCase().includes(search.toLowerCase()) ||
      node.label.toLowerCase().includes(search.toLowerCase()));

  const getNodeColor = (type: string) => {
    switch (type) {
      case 'TranslationUnit':
        return 'text-sky-400 bg-sky-950/60 border-sky-800/60';
      case 'FunctionDeclaration':
        return 'text-indigo-400 bg-indigo-950/60 border-indigo-800/60';
      case 'VariableDeclaration':
        return 'text-emerald-400 bg-emerald-950/60 border-emerald-800/60';
      case 'BinaryExpression':
        return 'text-amber-400 bg-amber-950/60 border-amber-800/60';
      case 'IfStatement':
      case 'WhileStatement':
      case 'ForStatement':
        return 'text-purple-400 bg-purple-950/60 border-purple-800/60';
      case 'ReturnStatement':
        return 'text-rose-400 bg-rose-950/60 border-rose-800/60';
      case 'Literal':
        return 'text-yellow-300 bg-yellow-950/60 border-yellow-800/60';
      case 'Identifier':
        return 'text-cyan-300 bg-cyan-950/60 border-cyan-800/60';
      default:
        return 'text-zinc-300 bg-zinc-800/80 border-zinc-700/60';
    }
  };

  const isNodeCollapsed = expandAll ? false : collapsed;

  return (
    <div className="flex flex-col relative">
      <div
        onClick={() => onSelectNode(node)}
        className={`flex items-center space-x-1.5 py-1 px-2 rounded font-mono text-xs cursor-pointer transition-colors group relative ${
          isSelected
            ? 'bg-zinc-800 text-white font-medium border border-zinc-700'
            : matchesSearch
            ? 'bg-amber-950/60 text-amber-200 border border-amber-500/50'
            : 'hover:bg-zinc-900/80 text-zinc-300'
        }`}
        style={{ paddingLeft: `${Math.max(6, level * 16)}px` }}
      >
        {/* Toggle Expand / Leaf Dot */}
        {hasChildren ? (
          <button
            onClick={(e) => {
              e.stopPropagation();
              setCollapsed(!collapsed);
            }}
            className="p-0.5 hover:bg-zinc-800 rounded text-zinc-500 hover:text-zinc-300 shrink-0"
          >
            {isNodeCollapsed ? (
              <ChevronRight className="w-3.5 h-3.5" />
            ) : (
              <ChevronDown className="w-3.5 h-3.5" />
            )}
          </button>
        ) : (
          <span className="w-3.5 h-3.5 flex items-center justify-center text-zinc-600 shrink-0 text-[10px]">
            •
          </span>
        )}

        {/* Node Grammar Badge */}
        <span
          className={`px-1.5 py-0.2 rounded text-[10px] font-bold border uppercase tracking-wider shrink-0 ${getNodeColor(
            node.type
          )}`}
        >
          {node.type}
        </span>

        {/* Node Label */}
        <span className="font-semibold text-zinc-100 truncate max-w-sm">
          {node.label}
        </span>

        {/* Line Reference if present */}
        {node.line && (
          <span className="text-[10px] text-zinc-500 font-sans ml-auto shrink-0">
            L{node.line}:{node.column}
          </span>
        )}
      </div>

      {/* Children Subtrees with SVG connectors */}
      {hasChildren && !isNodeCollapsed && (
        <div className="flex flex-col border-l border-zinc-800/80 ml-3 pl-1">
          {node.children.map((child, idx) => (
            <TreeNode
              key={child.id}
              node={child}
              level={level + 1}
              search={search}
              selectedNode={selectedNode}
              onSelectNode={onSelectNode}
              expandAll={expandAll}
              isLastChild={idx === node.children.length - 1}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export const ASTTab: React.FC<ASTTabProps> = ({ root }) => {
  const [search, setSearch] = useState('');
  const [selectedNode, setSelectedNode] = useState<ASTNode | null>(null);
  const [expandAll, setExpandAll] = useState(true);

  if (!root) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8 text-center text-zinc-500 font-mono text-xs">
        <FolderTree className="w-8 h-8 text-zinc-700 mb-2 stroke-[1.5]" />
        <p className="text-zinc-300 font-medium text-sm">AST Not Generated</p>
        <p className="text-zinc-500 mt-1 max-w-sm font-sans text-xs">
          Analyze C code to parse the token stream into a hierarchical Abstract Syntax Tree.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col md:flex-row h-full gap-3 font-mono text-xs">
      {/* Left Tree Explorer */}
      <div className="flex-1 bg-zinc-950 border border-zinc-800 rounded-md flex flex-col overflow-hidden min-h-0">
        {/* Tree Toolbar */}
        <div className="h-9 bg-zinc-900/90 border-b border-zinc-800 px-2.5 flex items-center justify-between select-none shrink-0">
          <div className="relative flex-1 max-w-xs">
            <Search className="w-3.5 h-3.5 text-zinc-500 absolute left-2 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search AST nodes..."
              className="w-full bg-zinc-950 border border-zinc-800 rounded pl-7 pr-2 py-1 text-xs text-zinc-200 outline-none focus:border-zinc-700 font-mono"
            />
          </div>

          <div className="flex items-center space-x-2 font-sans">
            <button
              onClick={() => setExpandAll(!expandAll)}
              className="flex items-center space-x-1 px-2 py-1 rounded text-[11px] bg-zinc-900 border border-zinc-800 text-zinc-400 hover:text-white transition-colors"
            >
              {expandAll ? <Minimize2 className="w-3 h-3" /> : <Maximize2 className="w-3 h-3" />}
              <span>{expandAll ? 'Collapse' : 'Expand'}</span>
            </button>
          </div>
        </div>

        {/* Tree Render View */}
        <div className="flex-1 p-2.5 overflow-auto bg-zinc-950 space-y-0.5">
          <TreeNode
            node={root}
            level={0}
            search={search}
            selectedNode={selectedNode}
            onSelectNode={setSelectedNode}
            expandAll={expandAll}
            isLastChild={true}
          />
        </div>
      </div>

      {/* Right Node Inspector Panel */}
      <div className="w-full md:w-72 bg-zinc-900/60 border border-zinc-800 rounded-md p-3 flex flex-col space-y-2.5 shrink-0 overflow-auto">
        <div className="flex items-center space-x-2 text-zinc-200 font-semibold text-xs border-b border-zinc-800 pb-2 select-none">
          <Tag className="w-3.5 h-3.5 text-sky-400" />
          <span>AST Node Details</span>
        </div>

        {selectedNode ? (
          <div className="space-y-2.5 text-xs font-mono">
            <div className="bg-zinc-950 p-2 rounded border border-zinc-800 space-y-0.5">
              <span className="text-[10px] text-zinc-500 block uppercase font-sans">Node ID:</span>
              <span className="text-sky-300 font-bold">{selectedNode.id}</span>
            </div>

            <div className="bg-zinc-950 p-2 rounded border border-zinc-800 space-y-0.5">
              <span className="text-[10px] text-zinc-500 block uppercase font-sans">Grammar Type:</span>
              <span className="text-white font-bold">{selectedNode.type}</span>
            </div>

            <div className="bg-zinc-950 p-2 rounded border border-zinc-800 space-y-0.5">
              <span className="text-[10px] text-zinc-500 block uppercase font-sans">Label:</span>
              <span className="text-zinc-200 break-words">{selectedNode.label}</span>
            </div>

            <div className="bg-zinc-950 p-2 rounded border border-zinc-800 space-y-0.5">
              <span className="text-[10px] text-zinc-500 block uppercase font-sans">Coordinates:</span>
              <span className="text-zinc-400">
                Line {selectedNode.line ?? '-'}, Col {selectedNode.column ?? '-'}
              </span>
            </div>

            <div className="bg-zinc-950 p-2 rounded border border-zinc-800 space-y-1">
              <span className="text-[10px] text-zinc-500 block uppercase font-sans">Attributes:</span>
              {Object.keys(selectedNode.attributes).length === 0 ? (
                <span className="text-zinc-600 text-[11px]">None</span>
              ) : (
                <div className="space-y-1 text-[11px]">
                  {Object.entries(selectedNode.attributes).map(([k, v]) => (
                    <div key={k} className="flex justify-between border-b border-zinc-850 pb-0.5">
                      <span className="text-zinc-400">{k}:</span>
                      <span className="text-amber-300">{String(v)}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="bg-zinc-950 p-2 rounded border border-zinc-800">
              <span className="text-[10px] text-zinc-500 block uppercase font-sans">Children Subtrees:</span>
              <span className="text-emerald-400 font-bold">{selectedNode.children.length} direct nodes</span>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-center text-zinc-500 text-xs p-4 select-none">
            <p>Select any node in the AST hierarchy to inspect its grammar attributes and source coordinates.</p>
          </div>
        )}
      </div>
    </div>
  );
};
