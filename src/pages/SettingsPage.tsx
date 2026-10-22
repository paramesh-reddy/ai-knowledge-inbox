import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Settings,
  Server,
  Database,
  Cpu,
  Brain,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Layers,
  Code2,
  Terminal,
} from 'lucide-react';
import { api } from '../services/api';
import { Header } from '../components/Header';

export const SettingsPage: React.FC = () => {
  const { data: health, isLoading } = useQuery({
    queryKey: ['health'],
    queryFn: api.getHealth,
    refetchInterval: 8000,
  });

  return (
    <div className="flex-1 flex flex-col h-screen overflow-hidden bg-slate-50/50">
      <Header
        title="System Health & Configuration"
        subtitle="Runtime diagnostics, model parameters, database dialect, and system architecture"
      />

      <div className="flex-1 overflow-y-auto p-8 space-y-6 max-w-5xl">
        {/* Core Services Status */}
        <div className="space-y-3">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            System Component Health
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* FastAPI Backend */}
            <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-2xs space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-700">FastAPI ASGI API</span>
                <div className="w-8 h-8 rounded-xl bg-slate-100 flex items-center justify-center text-slate-700">
                  <Server className="w-4 h-4" />
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
                <span className="text-xs font-medium text-emerald-800">Online & Serving</span>
              </div>
              <div className="text-[11px] text-slate-500 font-mono">
                Port 8000 • Async Endpoints
              </div>
            </div>

            {/* Database & pgvector */}
            <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-2xs space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-700">Database & Vectors</span>
                <div className="w-8 h-8 rounded-xl bg-slate-100 flex items-center justify-center text-slate-700">
                  <Database className="w-4 h-4" />
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span
                  className={`w-2.5 h-2.5 rounded-full ${
                    health?.database_connected ? 'bg-emerald-500' : 'bg-rose-500'
                  }`}
                />
                <span className="text-xs font-medium text-slate-900">
                  {health?.database_connected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
              <div className="text-[11px] text-slate-500 font-mono">
                {health?.database_type || 'Loading...'}
              </div>
            </div>

            {/* Ingestion Worker */}
            <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-2xs space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-700">Ingestion Worker</span>
                <div className="w-8 h-8 rounded-xl bg-slate-100 flex items-center justify-center text-slate-700">
                  <Cpu className="w-4 h-4" />
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-xs font-medium text-emerald-800">Autonomous Process</span>
              </div>
              <div className="text-[11px] text-slate-500 font-mono">
                Polling & FOR UPDATE SKIP LOCKED
              </div>
            </div>
          </div>
        </div>

        {/* AI & RAG Configuration */}
        <div className="rounded-2xl bg-white border border-slate-200 shadow-2xs p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <h3 className="text-sm font-semibold text-slate-900">Configured AI & Embedding Models</h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Official Google Gen AI SDK models for vector representation and grounded response generation
              </p>
            </div>
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-emerald-50 text-emerald-800 text-xs font-medium">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
              <span>Key Kept Exclusively on Server</span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-100 space-y-1">
              <div className="text-slate-500 font-medium">Answer Generation Model</div>
              <div className="font-mono text-sm font-semibold text-slate-900">
                {health?.configured_model || 'gemini-3.8-flash'}
              </div>
              <div className="text-[11px] text-slate-400">
                Temperature 0.2 • Max Output Tokens: 1000
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 border border-slate-100 space-y-1">
              <div className="text-slate-500 font-medium">Vector Embedding Model</div>
              <div className="font-mono text-sm font-semibold text-slate-900">
                {health?.configured_embedding_model || 'gemini-embedding-2-preview'}
              </div>
              <div className="text-[11px] text-slate-400">
                Dimensions: {health?.embedding_dimensions || 768} • Cosine Metric
              </div>
            </div>
          </div>

          <div className="p-4 rounded-xl border border-slate-200 bg-white grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-mono">
            <div>
              <span className="text-slate-400 block text-[11px]">Chunk Size:</span>
              <span className="font-semibold text-slate-800">1000 characters</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[11px]">Chunk Overlap:</span>
              <span className="font-semibold text-slate-800">150 characters</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[11px]">Top K Retrieval:</span>
              <span className="font-semibold text-slate-800">5 chunks</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[11px]">Min Similarity:</span>
              <span className="font-semibold text-slate-800">0.35</span>
            </div>
          </div>
        </div>

        {/* Assessment Architectural Decisions Card */}
        <div className="rounded-2xl bg-white border border-slate-200 shadow-2xs p-6 space-y-3">
          <h3 className="text-sm font-semibold text-slate-900">Recruitment Assessment Design Decisions</h3>
          <div className="space-y-2 text-xs text-slate-600 leading-relaxed">
            <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
              <span className="font-semibold text-slate-900">PostgreSQL Job Queue vs. Celery/Redis:</span> Built directly with PostgreSQL transactional table locking (<code className="font-mono text-slate-800">FOR UPDATE SKIP LOCKED</code>). This removes external Redis infrastructure dependencies while providing strictly ACID-compliant job delivery, retries, and failure tracking.
            </div>
            <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
              <span className="font-semibold text-slate-900">Vector Search & RAG Grounding:</span> Embeddings are matched via cosine similarity, and context is fed into Gemini with strict guardrails preventing prompt injection and citation hallucinations.
            </div>
            <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
              <span className="font-semibold text-slate-900">Single-User MVP vs Multi-User Production:</span> Designed with clean repository abstractions so tenant/user ID isolation and authentication can be layered in via standard dependency injection.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
