import type {
  AnalysisResult,
  DiagnosisAndFixResponse,
  ConceptExplanation,
  SampleProgram
} from '../types/compiler';

const API_BASE = '/api';

export async function fetchHealth(): Promise<{ status: string; service: string; ai_provider: string }> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error(`Health check failed: ${res.statusText}`);
  return res.json();
}

export async function fetchSamples(): Promise<SampleProgram[]> {
  const res = await fetch(`${API_BASE}/samples`);
  if (!res.ok) throw new Error(`Failed to fetch samples: ${res.statusText}`);
  return res.json();
}

export async function analyzeCode(sourceCode: string): Promise<AnalysisResult> {
  const res = await fetch(`${API_BASE}/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ source_code: sourceCode }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Analysis failed: ${res.statusText}`);
  }
  return res.json();
}

export async function diagnoseAndFix(sourceCode: string): Promise<DiagnosisAndFixResponse> {
  const res = await fetch(`${API_BASE}/ai/diagnose-and-fix`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ source_code: sourceCode }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Diagnosis failed: ${res.statusText}`);
  }
  return res.json();
}

export async function explainConcept(conceptId: string, contextCode?: string): Promise<ConceptExplanation> {
  const res = await fetch(`${API_BASE}/ai/explain-concept`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ concept_id: conceptId, context_code: contextCode }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Concept explanation failed: ${res.statusText}`);
  }
  return res.json();
}
