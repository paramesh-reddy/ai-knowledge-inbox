import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ArrowLeft,
  RotateCcw,
  Trash2,
  FileText,
  Layers,
  Calendar,
  AlertCircle,
  CheckCircle2,
  Clock,
  Copy,
  Check,
} from 'lucide-react';
import { api } from '../services/api';
import { Header } from '../components/Header';
import { useToast } from '../components/Toast';

export const DocumentDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  const [copiedChunkId, setCopiedChunkId] = useState<string | null>(null);

  const { data: doc, isLoading, error, refetch } = useQuery({
    queryKey: ['document', id],
    queryFn: () => api.getDocument(id!),
    enabled: !!id,
    refetchInterval: (query) => {
      // Auto-poll if still pending or processing
      const status = query.state.data?.processing_status;
      return status === 'pending' || status === 'processing' ? 2000 : false;
    },
  });

  const retryMutation = useMutation({
    mutationFn: () => api.retryDocument(id!),
    onSuccess: () => {
      showToast('Document ingestion re-enqueued', 'info');
      refetch();
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      queryClient.invalidateQueries({ queryKey: ['stats'] });
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
    onError: (err: any) => {
      showToast(err.message || 'Retry failed', 'error');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => api.deleteDocument(id!),
    onSuccess: () => {
      showToast('Document deleted', 'success');
      navigate('/library');
    },
    onError: (err: any) => {
      showToast(err.message || 'Delete failed', 'error');
    },
  });

  const handleCopyChunk = (chunkId: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedChunkId(chunkId);
    setTimeout(() => setCopiedChunkId(null), 2000);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  if (isLoading) {
    return (
      <div className="flex-1 flex flex-col h-screen bg-slate-50/50">
        <Header title="Document Details" />
        <div className="flex-1 flex items-center justify-center text-xs text-slate-400">
          Loading document information...
        </div>
      </div>
    );
  }

  if (error || !doc) {
    return (
      <div className="flex-1 flex flex-col h-screen bg-slate-50/50">
        <Header title="Document Not Found" />
        <div className="flex-1 flex flex-col items-center justify-center p-8 space-y-3">
          <AlertCircle className="w-10 h-10 text-rose-500" />
          <h2 className="text-sm font-semibold text-slate-800">Document could not be loaded</h2>
          <p className="text-xs text-slate-500">The document may have been removed or does not exist.</p>
          <button
            onClick={() => navigate('/library')}
            className="mt-2 px-3.5 py-1.5 bg-slate-900 text-white rounded-lg text-xs font-medium cursor-pointer"
          >
            Back to Library
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col h-screen overflow-hidden bg-slate-50/50">
      <Header
        title={doc.title}
        subtitle={`${doc.original_filename} • ${doc.file_type.toUpperCase()} • ${formatFileSize(doc.file_size)}`}
        action={
          <div className="flex items-center gap-2">
            <button
              onClick={() => navigate('/library')}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 rounded-lg text-xs font-medium transition-colors cursor-pointer"
            >
              <ArrowLeft className="w-3.5 h-3.5 text-slate-500" />
              <span>Back</span>
            </button>
            {doc.processing_status === 'failed' && (
              <button
                onClick={() => retryMutation.mutate()}
                disabled={retryMutation.isPending}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-xs font-medium transition-colors cursor-pointer"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Retry Ingestion</span>
              </button>
            )}
            <button
              onClick={() => {
                if (confirm(`Are you sure you want to delete "${doc.title}"?`)) {
                  deleteMutation.mutate();
                }
              }}
              disabled={deleteMutation.isPending}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-white hover:bg-rose-50 text-rose-600 border border-rose-200 rounded-lg text-xs font-medium transition-colors cursor-pointer"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Delete</span>
            </button>
          </div>
        }
      />

      <div className="flex-1 overflow-y-auto p-8 space-y-6">
        {/* Document Metadata Card */}
        <div className="rounded-2xl bg-white border border-slate-200 shadow-2xs p-6 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-100">
            <div>
              <div className="flex items-center gap-2">
                <span
                  className={`inline-flex items-center gap-1.5 font-mono text-[11px] px-2.5 py-1 rounded-md font-medium capitalize ${
                    doc.processing_status === 'completed'
                      ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                      : doc.processing_status === 'processing'
                      ? 'bg-amber-50 text-amber-700 border border-amber-200 animate-pulse'
                      : doc.processing_status === 'failed'
                      ? 'bg-rose-50 text-rose-700 border border-rose-200'
                      : 'bg-slate-100 text-slate-600 border border-slate-200'
                  }`}
                >
                  {doc.processing_status === 'completed' && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />}
                  {doc.processing_status === 'processing' && <Clock className="w-3.5 h-3.5 text-amber-600" />}
                  {doc.processing_status === 'failed' && <AlertCircle className="w-3.5 h-3.5 text-rose-600" />}
                  <span>Status: {doc.processing_status}</span>
                </span>
                <span className="font-mono text-[11px] bg-slate-100 text-slate-700 px-2 py-0.5 rounded-md font-medium uppercase">
                  Format: {doc.file_type}
                </span>
              </div>
            </div>

            <div className="flex items-center gap-4 text-xs text-slate-500 font-mono">
              <div>
                <span className="text-slate-400">Total Chunks: </span>
                <span className="font-semibold text-slate-700">{doc.chunk_count}</span>
              </div>
              <div>
                <span className="text-slate-400">Created: </span>
                <span className="text-slate-700">{new Date(doc.created_at).toLocaleString()}</span>
              </div>
            </div>
          </div>

          {/* Failure Alert if Failed */}
          {doc.error_message && (
            <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-900 flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
              <div>
                <div className="font-semibold">Ingestion Error Details:</div>
                <div className="mt-0.5 leading-relaxed font-mono">{doc.error_message}</div>
              </div>
            </div>
          )}

          {/* Raw Preview if Available */}
          {doc.raw_content_preview && (
            <div className="space-y-1.5 pt-2">
              <div className="text-xs font-semibold text-slate-700">Raw Content Preview</div>
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs font-mono text-slate-800 whitespace-pre-wrap max-h-48 overflow-y-auto">
                {doc.raw_content_preview}
              </div>
            </div>
          )}
        </div>

        {/* Chunks Section */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-slate-900">Extracted Vector Chunks ({doc.chunks.length})</h3>
              <p className="text-xs text-slate-500">Each chunk is embedded with 768 dimensions for pgvector similarity search</p>
            </div>
          </div>

          {doc.chunks.length === 0 ? (
            <div className="rounded-2xl bg-white border border-slate-200 p-12 text-center text-xs text-slate-400">
              {doc.processing_status === 'processing'
                ? 'Worker is currently extracting and chunking text...'
                : 'No chunks generated for this document.'}
            </div>
          ) : (
            <div className="space-y-3">
              {doc.chunks.map((chunk) => (
                <div
                  key={chunk.id}
                  className="rounded-2xl bg-white border border-slate-200 shadow-2xs p-5 space-y-2 hover:border-slate-300 transition-colors"
                >
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-[11px] font-semibold text-slate-700 px-2 py-0.5 bg-slate-100 rounded-md">
                        Chunk #{chunk.chunk_index + 1}
                      </span>
                      {chunk.page_number && (
                        <span className="font-mono text-[11px] text-indigo-700 bg-indigo-50 border border-indigo-200 px-2 py-0.5 rounded-md font-medium">
                          Page {chunk.page_number}
                        </span>
                      )}
                      <span className="text-[11px] text-slate-400 font-mono">
                        ID: {chunk.id.slice(0, 8)}...
                      </span>
                    </div>

                    <button
                      onClick={() => handleCopyChunk(chunk.id, chunk.extracted_text)}
                      className="flex items-center gap-1 text-[11px] text-slate-400 hover:text-slate-700 transition-colors cursor-pointer"
                    >
                      {copiedChunkId === chunk.id ? (
                        <>
                          <Check className="w-3.5 h-3.5 text-emerald-600" />
                          <span className="text-emerald-600 font-medium">Copied</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3.5 h-3.5" />
                          <span>Copy Excerpt</span>
                        </>
                      )}
                    </button>
                  </div>

                  <div className="text-xs text-slate-800 leading-relaxed font-mono whitespace-pre-wrap bg-slate-50/60 p-3 rounded-xl border border-slate-100">
                    {chunk.extracted_text}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
