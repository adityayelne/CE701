import React, { useState, useEffect, useCallback } from 'react';
import { 
  Layers, 
  Database, 
  FolderTree, 
  Cpu, 
  AlertCircle, 
  RefreshCw 
} from 'lucide-react';

import { Header } from './components/Header';
import { SourceEditor } from './components/SourceEditor';
import { DiffModal } from './components/DiffModal';
import { LexicalTab } from './components/Visualizations/LexicalTab';
import { SymbolTableTab } from './components/Visualizations/SymbolTableTab';
import { ASTTab } from './components/Visualizations/ASTTab';
import { IntermediateCodeTab } from './components/Visualizations/IntermediateCodeTab';
import { DiagnosticsTab } from './components/Visualizations/DiagnosticsTab';
import { StatusBar } from './components/StatusBar';

import type { 
  AnalysisResult, 
  DiagnosisAndFixResponse, 
  SampleProgram, 
  CompilerMetrics 
} from './types/compiler';
import { 
  fetchHealth, 
  fetchSamples, 
  analyzeCode, 
  diagnoseAndFix 
} from './services/api';

const DEFAULT_METRICS: CompilerMetrics = {
  token_count: 0,
  ast_node_count: 0,
  ast_max_depth: 0,
  symbol_count: 0,
  tac_count: 0,
  basic_block_count: 0,
  error_count: 0,
  analysis_time_ms: 0,
};

type ActiveTab = 'diagnostics' | 'tokens' | 'symbols' | 'ast' | 'ir';

export const App: React.FC = () => {
  const [samples, setSamples] = useState<SampleProgram[]>([]);
  const [selectedSampleId, setSelectedSampleId] = useState<string>('factorial');
  const [sourceCode, setSourceCode] = useState<string>('');
  const [activeTab, setActiveTab] = useState<ActiveTab>('tokens');
  const [highlightedLine, setHighlightedLine] = useState<{ line: number; ts: number } | null>(null);

  // Analysis result state
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  // AI Fix and Diff modal state
  const [diffData, setDiffData] = useState<DiagnosisAndFixResponse | null>(null);
  const [isFixing, setIsFixing] = useState(false);
  const [isDiffOpen, setIsDiffOpen] = useState(false);

  // Health check
  const [apiHealthy, setApiHealthy] = useState(false);

  // Load samples and initial health check
  useEffect(() => {
    fetchHealth()
      .then(() => setApiHealthy(true))
      .catch(() => setApiHealthy(false));

    fetchSamples()
      .then((data) => {
        setSamples(data);
        if (data.length > 0) {
          const initial = data[0];
          setSelectedSampleId(initial.id);
          setSourceCode(initial.code);
          handleAnalyze(initial.code);
        }
      })
      .catch((err) => {
        console.error('Failed to fetch samples', err);
      });
  }, []);

  const handleAnalyze = useCallback(async (codeToAnalyze?: string) => {
    const code = codeToAnalyze !== undefined ? codeToAnalyze : sourceCode;
    if (!code.trim()) return;

    setIsAnalyzing(true);
    setAnalysisError(null);
    setHighlightedLine(null);

    try {
      const result = await analyzeCode(code);
      setAnalysisResult(result);
      setApiHealthy(true);
      // Auto-switch to diagnostics tab if errors were detected
      if (result.errors && result.errors.length > 0) {
        setActiveTab('diagnostics');
      }
    } catch (err: any) {
      console.error('Analysis error:', err);
      setAnalysisError(err.message || 'Compiler analysis request failed');
    } finally {
      setIsAnalyzing(false);
    }
  }, [sourceCode]);

  const handleAIFix = async () => {
    if (!sourceCode.trim() || isFixing) return;
    setIsFixing(true);

    try {
      const data = await diagnoseAndFix(sourceCode);
      setDiffData(data);
      setIsDiffOpen(true);
      setApiHealthy(true);
    } catch (err: any) {
      console.error('AI Fix error:', err);
      alert(`AI diagnosis failed: ${err.message}`);
    } finally {
      setIsFixing(false);
    }
  };

  const handleSelectSample = (sample: SampleProgram) => {
    setSelectedSampleId(sample.id);
    setSourceCode(sample.code);
    setHighlightedLine(null);
    handleAnalyze(sample.code);
  };

  const handleApplyFix = (correctedCode: string) => {
    setSourceCode(correctedCode);
    setHighlightedLine(null);
    handleAnalyze(correctedCode);
  };

  const handleClearCode = () => {
    setSourceCode('');
    setAnalysisResult(null);
    setHighlightedLine(null);
  };

  const errors = analysisResult?.errors || [];
  const metrics = analysisResult?.metrics || DEFAULT_METRICS;

  return (
    <div className="h-screen flex flex-col bg-zinc-950 bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(59,130,246,0.06),rgba(255,255,255,0))] text-zinc-100 font-sans overflow-hidden">
      {/* Top Header Toolbar */}
      <Header
        samples={samples}
        selectedSampleId={selectedSampleId}
        onSelectSample={handleSelectSample}
        onAnalyze={() => handleAnalyze()}
        onAIFix={handleAIFix}
        isAnalyzing={isAnalyzing}
        isFixing={isFixing}
        hasErrors={errors.length > 0}
        apiHealthy={apiHealthy}
      />

      {/* Main Workspace (2-Column Balanced Workbench) */}
      <main className="flex-1 p-3.5 grid grid-cols-1 lg:grid-cols-12 gap-3.5 overflow-hidden min-h-0">
        {/* Left Column: C Source Code Editor (5 cols on lg) */}
        <section className="lg:col-span-5 flex flex-col h-full min-h-0 overflow-hidden">
          <SourceEditor
            code={sourceCode}
            onChange={(newCode) => {
              setSourceCode(newCode);
              setHighlightedLine(null);
            }}
            errors={errors}
            onClear={handleClearCode}
            highlightedLine={highlightedLine}
          />
        </section>

        {/* Right Column: Tabbed Analysis Area (7 cols on lg) */}
        <section className="lg:col-span-7 flex flex-col h-full min-h-0 bg-zinc-950/90 backdrop-blur-sm border border-zinc-800/80 rounded-xl overflow-hidden shadow-sm">
          {/* Refined Segmented Tab Bar with Glassmorphism */}
          <div className="h-10 bg-zinc-900/75 backdrop-blur-sm border-b border-zinc-800/80 px-2.5 flex items-center justify-between select-none shrink-0 font-mono text-xs">
            <div className="flex items-center space-x-1.5 overflow-x-auto">
              {/* Diagnostics Tab */}
              <button
                onClick={() => setActiveTab('diagnostics')}
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs transition-all duration-150 cursor-pointer ${
                  activeTab === 'diagnostics'
                    ? 'bg-zinc-800/90 text-zinc-100 font-semibold shadow-xs border border-zinc-700/80'
                    : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/40'
                }`}
              >
                <AlertCircle className={`w-3.5 h-3.5 ${errors.length > 0 ? 'text-rose-400' : 'text-zinc-500'}`} />
                <span>Diagnostics</span>
                {errors.length > 0 && (
                  <span className="px-1.5 py-0.2 rounded-md text-[10px] font-bold bg-rose-950 text-rose-300 border border-rose-800/60 font-mono shadow-xs">
                    {errors.length}
                  </span>
                )}
              </button>

              {/* Tokens Tab */}
              <button
                onClick={() => setActiveTab('tokens')}
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs transition-all duration-150 cursor-pointer ${
                  activeTab === 'tokens'
                    ? 'bg-zinc-800/90 text-zinc-100 font-semibold shadow-xs border border-zinc-700/80'
                    : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/40'
                }`}
              >
                <Layers className="w-3.5 h-3.5 text-zinc-400" />
                <span>Tokens ({analysisResult?.tokens.length ?? 0})</span>
              </button>

              {/* Symbol Table Tab */}
              <button
                onClick={() => setActiveTab('symbols')}
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs transition-all duration-150 cursor-pointer ${
                  activeTab === 'symbols'
                    ? 'bg-zinc-800/90 text-zinc-100 font-semibold shadow-xs border border-zinc-700/80'
                    : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/40'
                }`}
              >
                <Database className="w-3.5 h-3.5 text-zinc-400" />
                <span>Symbols ({analysisResult?.symbol_table.length ?? 0})</span>
              </button>

              {/* AST Tab */}
              <button
                onClick={() => setActiveTab('ast')}
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs transition-all duration-150 cursor-pointer ${
                  activeTab === 'ast'
                    ? 'bg-zinc-800/90 text-zinc-100 font-semibold shadow-xs border border-zinc-700/80'
                    : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/40'
                }`}
              >
                <FolderTree className="w-3.5 h-3.5 text-zinc-400" />
                <span>AST ({analysisResult?.metrics.ast_node_count ?? 0})</span>
              </button>

              {/* Intermediate Code Tab */}
              <button
                onClick={() => setActiveTab('ir')}
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs transition-all duration-150 cursor-pointer ${
                  activeTab === 'ir'
                    ? 'bg-zinc-800/90 text-zinc-100 font-semibold shadow-xs border border-zinc-700/80'
                    : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/40'
                }`}
              >
                <Cpu className="w-3.5 h-3.5 text-zinc-400" />
                <span>TAC ({analysisResult?.intermediate_code.length ?? 0})</span>
              </button>
            </div>
          </div>

          {/* Tab Content Display Area */}
          <div className="flex-1 p-3.5 overflow-hidden min-h-0 bg-zinc-950/70">
            {isAnalyzing ? (
              <div className="h-full flex flex-col items-center justify-center text-xs text-zinc-400 space-y-3 font-mono">
                <RefreshCw className="w-6 h-6 animate-spin text-blue-400" />
                <span>Analyzing lexical, syntactic, semantic, and intermediate code passes...</span>
              </div>
            ) : analysisError ? (
              <div className="h-full flex flex-col items-center justify-center text-center p-6 text-rose-300 font-mono">
                <AlertCircle className="w-8 h-8 text-rose-400 mb-2" />
                <h3 className="font-semibold text-xs mb-1">Analysis Failed</h3>
                <p className="text-xs text-zinc-400">{analysisError}</p>
              </div>
            ) : (
              <>
                {activeTab === 'diagnostics' && (
                  <DiagnosticsTab
                    errors={errors}
                    onAIFix={handleAIFix}
                    isFixing={isFixing}
                    onSelectLine={(line) => setHighlightedLine({ line, ts: Date.now() })}
                  />
                )}
                {activeTab === 'tokens' && (
                  <LexicalTab tokens={analysisResult?.tokens || []} />
                )}
                {activeTab === 'symbols' && (
                  <SymbolTableTab symbols={analysisResult?.symbol_table || []} />
                )}
                {activeTab === 'ast' && (
                  <ASTTab 
                    root={analysisResult?.ast} 
                    onSelectLine={(line) => setHighlightedLine({ line, ts: Date.now() })}
                  />
                )}
                {activeTab === 'ir' && (
                  <IntermediateCodeTab
                    instructions={analysisResult?.intermediate_code || []}
                    blocks={analysisResult?.basic_blocks || []}
                  />
                )}
              </>
            )}
          </div>
        </section>
      </main>

      {/* Bottom Telemetry Status Bar */}
      <StatusBar metrics={metrics} errors={errors} />

      {/* AI Diff & Diagnostic Modal */}
      <DiffModal
        data={diffData}
        isOpen={isDiffOpen}
        onClose={() => setIsDiffOpen(false)}
        onApplyFix={handleApplyFix}
      />
    </div>
  );
};

export default App;
