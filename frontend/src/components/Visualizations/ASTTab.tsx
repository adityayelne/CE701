import React, { useState } from 'react';
import { 
  ChevronRight, 
  ChevronDown, 
  Search, 
  FolderTree, 
  Tag,
  Maximize2,
  Minimize2,
  ExternalLink,
  Compass
} from 'lucide-react';
import type { ASTNode } from '../../types/compiler';

interface ASTTabProps {
  root: ASTNode | null | undefined;
  onSelectLine?: (line: number) => void;
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

const getNodeBadge = (type: string) => {
  switch (type) {
    case 'TranslationUnit':
      return {
        bg: 'bg-blue-950/70',
        text: 'text-blue-300',
        border: 'border-blue-700/60',
        dot: 'bg-blue-400',
      };
    case 'FunctionDeclaration':
    case 'FunctionDefinition':
      return {
        bg: 'bg-indigo-950/70',
        text: 'text-indigo-300',
        border: 'border-indigo-700/60',
        dot: 'bg-indigo-400',
      };
    case 'VariableDeclaration':
      return {
        bg: 'bg-emerald-950/70',
        text: 'text-emerald-300',
        border: 'border-emerald-700/60',
        dot: 'bg-emerald-400',
      };
    case 'BinaryExpression':
      return {
        bg: 'bg-amber-950/70',
        text: 'text-amber-300',
        border: 'border-amber-700/60',
        dot: 'bg-amber-400',
      };
    case 'IfStatement':
    case 'WhileStatement':
    case 'ForStatement':
      return {
        bg: 'bg-purple-950/70',
        text: 'text-purple-300',
        border: 'border-purple-700/60',
        dot: 'bg-purple-400',
      };
    case 'ReturnStatement':
      return {
        bg: 'bg-rose-950/70',
        text: 'text-rose-300',
        border: 'border-rose-700/60',
        dot: 'bg-rose-400',
      };
    case 'Literal':
      return {
        bg: 'bg-yellow-950/70',
        text: 'text-yellow-300',
        border: 'border-yellow-700/60',
        dot: 'bg-yellow-400',
      };
    case 'Identifier':
      return {
        bg: 'bg-cyan-950/70',
        text: 'text-cyan-300',
        border: 'border-cyan-700/60',
        dot: 'bg-cyan-400',
      };
    default:
      return {
        bg: 'bg-zinc-850',
        text: 'text-zinc-300',
        border: 'border-zinc-700/70',
        dot: 'bg-zinc-400',
      };
  }
};

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

  const badge = getNodeBadge(node.type);
  const isNodeCollapsed = expandAll ? false : collapsed;

  return (
    <div className="flex flex-col relative select-none">
      <div
        onClick={() => onSelectNode(node)}
        className={`flex items-center space-x-2 py-1.5 px-2.5 rounded-lg font-mono text-xs cursor-pointer transition-all duration-150 group relative my-0.5 ${
          isSelected
            ? 'bg-zinc-800 text-white font-medium border border-blue-500/70 shadow-sm shadow-blue-950/40'
            : matchesSearch
            ? 'bg-amber-950/60 text-amber-200 border border-amber-500/60'
            : 'hover:bg-zinc-900/90 text-zinc-300 border border-transparent hover:border-zinc-800'
        }`}
        style={{ paddingLeft: `${Math.max(8, level * 20)}px` }}
      >
        {/* Toggle Expand / Leaf Icon */}
        {hasChildren ? (
          <button
            onClick={(e) => {
              e.stopPropagation();
              setCollapsed(!collapsed);
            }}
            className="p-1 hover:bg-zinc-800 rounded text-zinc-400 hover:text-white shrink-0 transition-colors cursor-pointer"
            title={isNodeCollapsed ? 'Expand node' : 'Collapse node'}
          >
            {isNodeCollapsed ? (
              <ChevronRight className="w-3.5 h-3.5 text-zinc-400" />
            ) : (
              <ChevronDown className="w-3.5 h-3.5 text-zinc-300" />
            )}
          </button>
        ) : (
          <span className="w-5 h-5 flex items-center justify-center shrink-0">
            <span className={`w-1.5 h-1.5 rounded-full ${badge.dot} opacity-70`} />
          </span>
        )}

        {/* Node Grammar Type Badge */}
        <span
          className={`px-2 py-0.5 rounded-md text-[10px] font-bold border uppercase tracking-wider shrink-0 font-mono shadow-xs ${badge.bg} ${badge.text} ${badge.border}`}
        >
          {node.type}
        </span>

        {/* Node Human Label */}
        <span className="font-semibold text-zinc-100 truncate max-w-xs font-mono text-xs">
          {node.label}
        </span>

        {/* Source Coordinates */}
        {node.line && (
          <span className="text-[10px] text-zinc-500 font-mono ml-auto shrink-0 bg-zinc-900/80 px-1.5 py-0.5 rounded border border-zinc-800/80">
            L{node.line}:{node.column}
          </span>
        )}
      </div>

      {/* Children Subtrees with Visual Tree Connectors */}
      {hasChildren && !isNodeCollapsed && (
        <div className="flex flex-col border-l-2 border-zinc-800/70 ml-4 pl-1 relative">
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

export const ASTTab: React.FC<ASTTabProps> = ({ root, onSelectLine }) => {
  const [search, setSearch] = useState('');
  const [selectedNode, setSelectedNode] = useState<ASTNode | null>(null);
  const [expandAll, setExpandAll] = useState(true);

  if (!root) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8 text-center text-zinc-500 font-mono text-xs">
        <div className="w-12 h-12 rounded-2xl bg-zinc-900 border border-zinc-800 flex items-center justify-center mb-3 shadow-lg">
          <FolderTree className="w-6 h-6 text-zinc-600 stroke-[1.5]" />
        </div>
        <p className="text-zinc-200 font-semibold text-sm">AST Not Generated</p>
        <p className="text-zinc-400 mt-1 max-w-sm font-sans text-xs leading-relaxed">
          Analyze C source code to parse the token stream into a hierarchical Abstract Syntax Tree.
        </p>
      </div>
    );
  }

  // Count total nodes recursively
  const countNodes = (n: ASTNode): number => {
    let count = 1;
    if (n.children) {
      for (const child of n.children) count += countNodes(child);
    }
    return count;
  };
  const totalNodes = countNodes(root);

  return (
    <div className="flex flex-col md:flex-row h-full gap-3 font-mono text-xs overflow-hidden">
      {/* Left Column: Tree Explorer */}
      <div className="flex-1 bg-zinc-950/80 backdrop-blur-sm border border-zinc-800/80 rounded-xl flex flex-col overflow-hidden min-h-0 shadow-sm">
        {/* Tree Toolbar with Glassmorphism */}
        <div className="h-10 bg-zinc-900/80 backdrop-blur-sm border-b border-zinc-800/80 px-3 flex items-center justify-between select-none shrink-0 gap-2">
          {/* Search Input */}
          <div className="relative flex-1 max-w-xs">
            <Search className="w-3.5 h-3.5 text-zinc-500 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search AST nodes by type or label..."
              className="w-full bg-zinc-950/90 border border-zinc-800/90 focus:border-blue-500/70 rounded-lg pl-8 pr-2 py-1 text-xs text-zinc-200 outline-none font-mono placeholder:text-zinc-600 transition-colors"
            />
          </div>

          {/* Toolbar Right Controls */}
          <div className="flex items-center space-x-2 font-sans text-xs">
            <span className="text-[11px] text-zinc-500 font-mono hidden sm:inline">
              {totalNodes} nodes
            </span>

            <button
              onClick={() => setExpandAll(!expandAll)}
              className="flex items-center space-x-1.5 px-2.5 py-1 rounded-lg text-[11px] bg-zinc-850 hover:bg-zinc-800 border border-zinc-750 text-zinc-300 hover:text-white transition-all cursor-pointer font-medium"
              title={expandAll ? 'Collapse all tree subtrees' : 'Expand all tree subtrees'}
            >
              {expandAll ? <Minimize2 className="w-3 h-3 text-zinc-400" /> : <Maximize2 className="w-3 h-3 text-zinc-400" />}
              <span>{expandAll ? 'Collapse' : 'Expand'}</span>
            </button>
          </div>
        </div>

        {/* Tree View Scrolling Container */}
        <div className="flex-1 p-3 overflow-auto bg-zinc-950/60 space-y-0.5">
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

      {/* Right Column: Node Inspector Details Panel */}
      <div className="w-full md:w-80 bg-zinc-900/70 backdrop-blur-sm border border-zinc-800/80 rounded-xl p-3.5 flex flex-col space-y-3 shrink-0 overflow-auto shadow-sm">
        <div className="flex items-center justify-between text-zinc-200 font-semibold text-xs border-b border-zinc-800/80 pb-2.5 select-none font-sans">
          <div className="flex items-center space-x-2">
            <Tag className="w-4 h-4 text-blue-400" />
            <span>AST Node Inspector</span>
          </div>
          {selectedNode && (
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-zinc-800 text-zinc-400 border border-zinc-700">
              #{selectedNode.id}
            </span>
          )}
        </div>

        {selectedNode ? (
          <div className="space-y-3 text-xs font-mono">
            {/* Grammar Type Card */}
            <div className="bg-zinc-950/80 p-2.5 rounded-lg border border-zinc-800/80 space-y-1">
              <span className="text-[10px] text-zinc-500 uppercase font-sans font-semibold tracking-wider block">
                Grammar Production Type:
              </span>
              <span className="text-white font-bold text-xs block">
                {selectedNode.type}
              </span>
            </div>

            {/* Label Card */}
            <div className="bg-zinc-950/80 p-2.5 rounded-lg border border-zinc-800/80 space-y-1">
              <span className="text-[10px] text-zinc-500 uppercase font-sans font-semibold tracking-wider block">
                Node Label:
              </span>
              <span className="text-zinc-200 break-words block font-mono">
                {selectedNode.label}
              </span>
            </div>

            {/* Source Coordinates with Jump Action */}
            <div className="bg-zinc-950/80 p-2.5 rounded-lg border border-zinc-800/80 flex items-center justify-between">
              <div>
                <span className="text-[10px] text-zinc-500 uppercase font-sans font-semibold tracking-wider block">
                  Source Location:
                </span>
                <span className="text-zinc-300 font-mono text-xs">
                  {selectedNode.line ? `Line ${selectedNode.line}, Col ${selectedNode.column}` : 'Synthetic node'}
                </span>
              </div>
              {selectedNode.line && onSelectLine && (
                <button
                  type="button"
                  onClick={() => onSelectLine(selectedNode.line!)}
                  className="flex items-center space-x-1 px-2.5 py-1 rounded-md bg-zinc-850 hover:bg-zinc-800 text-zinc-300 hover:text-white border border-zinc-700 text-[11px] font-sans font-medium transition-all cursor-pointer shadow-xs active:scale-[0.96]"
                  title="Jump to line in source editor"
                >
                  <span>Editor</span>
                  <ExternalLink className="w-3 h-3 text-blue-400" />
                </button>
              )}
            </div>

            {/* Subtree Children Stats */}
            <div className="bg-zinc-950/80 p-2.5 rounded-lg border border-zinc-800/80 flex items-center justify-between">
              <span className="text-[10px] text-zinc-500 uppercase font-sans font-semibold tracking-wider">
                Direct Children:
              </span>
              <span className="text-emerald-400 font-bold font-mono">
                {selectedNode.children.length} subtrees
              </span>
            </div>

            {/* Node Attributes Table */}
            <div className="bg-zinc-950/80 p-2.5 rounded-lg border border-zinc-800/80 space-y-2">
              <span className="text-[10px] text-zinc-500 uppercase font-sans font-semibold tracking-wider block">
                Node Semantic Attributes:
              </span>
              {Object.keys(selectedNode.attributes).length === 0 ? (
                <span className="text-zinc-600 text-[11px] italic">No custom attributes</span>
              ) : (
                <div className="space-y-1.5 text-[11px]">
                  {Object.entries(selectedNode.attributes).map(([k, v]) => (
                    <div key={k} className="flex justify-between items-center border-b border-zinc-850/80 pb-1">
                      <span className="text-zinc-400 font-medium">{k}:</span>
                      <span className="text-amber-300 font-mono font-semibold">{String(v)}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-center text-zinc-500 text-xs p-4 select-none space-y-2">
            <Compass className="w-8 h-8 text-zinc-700 stroke-[1.5]" />
            <p className="text-zinc-400 font-medium">No Node Selected</p>
            <p className="text-zinc-600 text-[11px] leading-relaxed font-sans">
              Click any node in the AST hierarchy to inspect its grammar attributes and jump to its source code coordinates.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
