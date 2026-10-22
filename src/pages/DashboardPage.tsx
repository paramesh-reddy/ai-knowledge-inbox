import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Files,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Layers,
  ArrowRight,
  Upload,
  FilePlus,
  MessageSquare,
  RefreshCw,
  FileText,
  Calendar,
} from 'lucide-react';
import { api } from '../services/api';
import { Header } from '../components/Header';
import { useToast } from '../components/Toast';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const { showToast } = useToast();

  const { data: stats, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['stats'],
    queryFn: api.getDashboardStats,
    refetchInterval: 4000,
  });

  const statCards = [
    {
      label: 'Total Knowledge Items',
      value: stats?.total_documents ?? 0,
      icon: Files,
      color: 'text-slate-900',
      bg: 'bg-slate-100',
      sub: `${stats?.total_chunks ?? 0} vector chunks`,
    },
    {
      label: 'Ready for Retrieval',
      value: stats?.completed_documents ?? 0,
      icon: CheckCircle2,
      color: 'text-emerald-700',
      bg: 'bg-emerald-50',
      sub: 'Searchable with Gemini',
    },
    {
      label: 'Actively Processing',
      value: stats?.processing_documents ?? 0,
      icon: Clock,
      color: 'text-amber-700',
      bg: 'bg-amber-50',
      sub: 'Background worker running',
      pulse: (stats?.processing_documents ?? 0) > 0,
    },
    {
      label: 'Requires Attention',
      value: stats?.failed_documents ?? 0,
      icon: AlertTriangle,
      color: 'text-rose-700',
      bg: 'bg-rose-50',
      sub: 'Retryable from Library',
    },
  ];

  return (
    <div className="flex-1 flex flex-col h-screen overflow-hidden bg-slate-50/50">
      <Header
        title="Knowledge Dashboard"
        subtitle="Live metrics, ingestion status, and recent knowledge activity"
        action={
          <button
            onClick={() => refetch()}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-xs font-medium text-slate-700 shadow-2xs transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isFetching ? 'animate-spin text-indigo-600' : 'text-slate-500'}`} />
            <span>Sync</span>
          </button>
        }
      />

      <div className="flex-1 overflow-y-auto p-8 space-y-8">
        {/* Quick Action Banner */}
        <div className="bg-gradient-to-r from-slate-900 to-slate-800 rounded-2xl p-6 text-white shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <h2 className="text-lg font-semibold tracking-tight">AI Knowledge Inbox</h2>
            <p className="text-slate-300 text-xs max-w-xl leading-relaxed">
              Upload PDF manuals, Markdown notes, or text files. The separate Python worker chunks documents, generates
              vector embeddings, and grounds Gemini AI answers with verified source citations.
            </p>
          </div>
          <div className="flex items-center gap-2.5 shrink-0">
            <button
              onClick={() => navigate('/library?action=upload')}
              className="flex items-center gap-2 px-3.5 py-2 bg-indigo-500 hover:bg-indigo-600 text-white rounded-xl text-xs font-medium shadow-xs transition-colors cursor-pointer"
            >
              <Upload className="w-3.5 h-3.5" />
              <span>Upload Document</span>
            </button>
            <button
              onClick={() => navigate('/library?action=note')}
              className="flex items-center gap-2 px-3.5 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-xl text-xs font-medium transition-colors cursor-pointer"
            >
              <FilePlus className="w-3.5 h-3.5" />
              <span>Create Note</span>
            </button>
            <button
              onClick={() => navigate('/chat')}
              className="flex items-center gap-2 px-3.5 py-2 bg-white/10 hover:bg-white/15 text-white border border-white/20 rounded-xl text-xs font-medium transition-colors cursor-pointer"
            >
              <MessageSquare className="w-3.5 h-3.5 text-indigo-300" />
              <span>Ask AI</span>
            </button>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {statCards.map((c, i) => {
            const Icon = c.icon;
            return (
              <div
                key={i}
                className="p-5 rounded-2xl bg-white border border-slate-200 shadow-2xs flex flex-col justify-between"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-slate-500">{c.label}</span>
                  <div className={`p-2 rounded-xl ${c.bg}`}>
                    <Icon className={`w-4 h-4 ${c.color} ${c.pulse ? 'animate-spin' : ''}`} />
                  </div>
                </div>
                <div className="mt-4">
                  <div className="text-2xl font-bold text-slate-900 tracking-tight font-mono">
                    {isLoading ? '...' : c.value}
                  </div>
                  <div className="text-xs text-slate-400 mt-1">{c.sub}</div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Two Columns: Recent Documents & Recent Job Activity */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recent Documents Card */}
          <div className="rounded-2xl bg-white border border-slate-200 shadow-2xs overflow-hidden flex flex-col">
            <div className="p-5 border-b border-slate-100 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold text-slate-900">Recent Knowledge Documents</h3>
                <p className="text-xs text-slate-500 mt-0.5">Recently indexed documents and notes</p>
              </div>
              <button
                onClick={() => navigate('/library')}
                className="text-xs text-indigo-600 hover:text-indigo-800 font-medium flex items-center gap-1 transition-colors cursor-pointer"
              >
                <span>View Library</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>

            <div className="divide-y divide-slate-100 flex-1">
              {isLoading ? (
                <div className="p-8 text-center text-xs text-slate-400">Loading documents...</div>
              ) : !stats?.recent_documents || stats.recent_documents.length === 0 ? (
                <div className="p-10 text-center flex flex-col items-center justify-center">
                  <FileText className="w-8 h-8 text-slate-300 mb-2" />
                  <p className="text-xs text-slate-600 font-medium">No documents uploaded yet</p>
                  <p className="text-[11px] text-slate-400 mt-0.5">Upload a PDF or write a note to get started.</p>
                  <button
                    onClick={() => navigate('/library?action=upload')}
                    className="mt-3 px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-medium cursor-pointer"
                  >
                    Upload First Document
                  </button>
                </div>
              ) : (
                stats.recent_documents.map((doc) => (
                  <div
                    key={doc.id}
                    onClick={() => navigate(`/documents/${doc.id}`)}
                    className="p-4 hover:bg-slate-50/80 transition-colors flex items-center justify-between cursor-pointer"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <div className="w-9 h-9 rounded-xl bg-slate-100 flex items-center justify-center text-slate-600 shrink-0 font-mono text-[11px] font-semibold uppercase">
                        {doc.file_type}
                      </div>
                      <div className="min-w-0">
                        <div className="text-sm font-medium text-slate-900 truncate">{doc.title}</div>
                        <div className="flex items-center gap-2 text-xs text-slate-400 mt-0.5">
                          <span>{doc.original_filename}</span>
                          <span>•</span>
                          <span>{doc.chunk_count} chunks</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2.5 shrink-0">
                      <span
                        className={`text-[11px] font-mono px-2 py-0.5 rounded-md font-medium capitalize ${
                          doc.processing_status === 'completed'
                            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                            : doc.processing_status === 'processing'
                            ? 'bg-amber-50 text-amber-700 border border-amber-200 animate-pulse'
                            : doc.processing_status === 'failed'
                            ? 'bg-rose-50 text-rose-700 border border-rose-200'
                            : 'bg-slate-100 text-slate-600 border border-slate-200'
                        }`}
                      >
                        {doc.processing_status}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Recent Processing Jobs Card */}
          <div className="rounded-2xl bg-white border border-slate-200 shadow-2xs overflow-hidden flex flex-col">
            <div className="p-5 border-b border-slate-100 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold text-slate-900">Background Worker Activity</h3>
                <p className="text-xs text-slate-500 mt-0.5">Asynchronous extraction, chunking, and embedding queue</p>
              </div>
              <button
                onClick={() => navigate('/jobs')}
                className="text-xs text-indigo-600 hover:text-indigo-800 font-medium flex items-center gap-1 transition-colors cursor-pointer"
              >
                <span>All Jobs</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>

            <div className="divide-y divide-slate-100 flex-1">
              {isLoading ? (
                <div className="p-8 text-center text-xs text-slate-400">Loading worker activity...</div>
              ) : !stats?.recent_jobs || stats.recent_jobs.length === 0 ? (
                <div className="p-10 text-center flex flex-col items-center justify-center">
                  <Layers className="w-8 h-8 text-slate-300 mb-2" />
                  <p className="text-xs text-slate-600 font-medium">No background jobs queued yet</p>
                  <p className="text-[11px] text-slate-400 mt-0.5">The worker processes jobs automatically upon upload.</p>
                </div>
              ) : (
                stats.recent_jobs.map((job) => (
                  <div key={job.id} className="p-4 flex items-center justify-between text-xs">
                    <div className="min-w-0 pr-2">
                      <div className="font-medium text-slate-900 truncate">
                        {job.document_title || `Document ${job.document_id.slice(0, 8)}`}
                      </div>
                      <div className="text-slate-400 text-[11px] font-mono mt-0.5">
                        Job: {job.id.slice(0, 8)} • Attempt {job.attempt_count}/{job.max_attempts}
                      </div>
                    </div>
                    <div className="shrink-0 flex items-center gap-2">
                      <span
                        className={`font-mono text-[11px] px-2 py-0.5 rounded-md font-medium capitalize ${
                          job.status === 'completed'
                            ? 'bg-emerald-50 text-emerald-700'
                            : job.status === 'processing'
                            ? 'bg-amber-50 text-amber-700 animate-pulse'
                            : job.status === 'failed'
                            ? 'bg-rose-50 text-rose-700'
                            : 'bg-slate-100 text-slate-600'
                        }`}
                      >
                        {job.status}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
