import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Upload,
  FilePlus,
  Search,
  Filter,
  RefreshCw,
  Trash2,
  ExternalLink,
  RotateCcw,
  FileText,
  FileCode,
  File,
  AlertCircle,
  CheckCircle2,
  Clock,
  X,
} from 'lucide-react';
import { api } from '../services/api';
import { Header } from '../components/Header';
import { useToast } from '../components/Toast';
import { DocumentStatus, FileType } from '../types';

export const LibraryPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [fileTypeFilter, setFileTypeFilter] = useState<FileType | ''>('');
  const [statusFilter, setStatusFilter] = useState<DocumentStatus | ''>('');
  const [page, setPage] = useState(1);

  // Modal states
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [isNoteOpen, setIsNoteOpen] = useState(false);
  const [noteTitle, setNoteTitle] = useState('');
  const [noteContent, setNoteContent] = useState('');
  const [dragActive, setDragActive] = useState(false);

  // Check URL searchParams action trigger
  useEffect(() => {
    const action = searchParams.get('action');
    if (action === 'upload') {
      setIsUploadOpen(true);
    } else if (action === 'note') {
      setIsNoteOpen(true);
    }
  }, [searchParams]);

  // Debounce search query
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search);
      setPage(1);
    }, 300);
    return () => clearTimeout(timer);
  }, [search]);

  // Query documents
  const { data, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['documents', page, debouncedSearch, fileTypeFilter, statusFilter],
    queryFn: () =>
      api.getDocuments({
        page,
        pageSize: 10,
        search: debouncedSearch || undefined,
        fileType: fileTypeFilter || undefined,
        status: statusFilter || undefined,
      }),
    refetchInterval: 4000,
  });

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: (file: File) => api.uploadFile(file),
    onSuccess: (doc) => {
      showToast(`Document "${doc.title}" queued for ingestion`, 'success');
      setIsUploadOpen(false);
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      queryClient.invalidateQueries({ queryKey: ['stats'] });
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
    onError: (err: any) => {
      showToast(err.message || 'Upload failed', 'error');
    },
  });

  // Note mutation
  const noteMutation = useMutation({
    mutationFn: ({ title, content }: { title: string; content: string }) =>
      api.createNote(title, content),
    onSuccess: (doc) => {
      showToast(`Note "${doc.title}" created and enqueued`, 'success');
      setIsNoteOpen(false);
      setNoteTitle('');
      setNoteContent('');
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      queryClient.invalidateQueries({ queryKey: ['stats'] });
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
    onError: (err: any) => {
      showToast(err.message || 'Note creation failed', 'error');
    },
  });

  // Retry mutation
  const retryMutation = useMutation({
    mutationFn: (id: string) => api.retryDocument(id),
    onSuccess: (doc) => {
      showToast(`Retrying ingestion for "${doc.title}"`, 'info');
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      queryClient.invalidateQueries({ queryKey: ['stats'] });
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
    onError: (err: any) => {
      showToast(err.message || 'Retry failed', 'error');
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.deleteDocument(id),
    onSuccess: () => {
      showToast('Document deleted successfully', 'success');
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      queryClient.invalidateQueries({ queryKey: ['stats'] });
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
    onError: (err: any) => {
      showToast(err.message || 'Delete failed', 'error');
    },
  });

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      uploadMutation.mutate(e.target.files[0]);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      uploadMutation.mutate(e.dataTransfer.files[0]);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formatDate = (iso: string) => {
    try {
      return new Date(iso).toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return iso;
    }
  };

  return (
    <div className="flex-1 flex flex-col h-screen overflow-hidden bg-slate-50/50">
      <Header
        title="Knowledge Library"
        subtitle="Manage uploaded documents, notes, chunks, and background processing status"
        action={
          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsUploadOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-medium shadow-xs transition-colors cursor-pointer"
            >
              <Upload className="w-3.5 h-3.5" />
              <span>Upload</span>
            </button>
            <button
              onClick={() => setIsNoteOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 rounded-lg text-xs font-medium shadow-2xs transition-colors cursor-pointer"
            >
              <FilePlus className="w-3.5 h-3.5 text-slate-500" />
              <span>New Note</span>
            </button>
          </div>
        }
      />

      <div className="flex-1 overflow-y-auto p-8 space-y-6">
        {/* Filter & Search Bar */}
        <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-2xs flex flex-col md:flex-row items-center gap-3 justify-between">
          <div className="relative flex-1 w-full md:max-w-md">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search documents by title or filename..."
              className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all"
            />
          </div>

          <div className="flex items-center gap-2 w-full md:w-auto">
            {/* File Type Filter */}
            <select
              value={fileTypeFilter}
              onChange={(e) => {
                setFileTypeFilter(e.target.value as any);
                setPage(1);
              }}
              className="px-3 py-2 bg-white border border-slate-200 rounded-xl text-xs text-slate-700 font-medium focus:outline-none focus:border-indigo-500"
            >
              <option value="">All Formats</option>
              <option value="pdf">PDF</option>
              <option value="txt">TXT</option>
              <option value="md">Markdown</option>
              <option value="note">Notes</option>
            </select>

            {/* Status Filter */}
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value as any);
                setPage(1);
              }}
              className="px-3 py-2 bg-white border border-slate-200 rounded-xl text-xs text-slate-700 font-medium focus:outline-none focus:border-indigo-500"
            >
              <option value="">All Statuses</option>
              <option value="completed">Completed</option>
              <option value="processing">Processing</option>
              <option value="pending">Pending</option>
              <option value="failed">Failed</option>
            </select>

            <button
              onClick={() => refetch()}
              className="p-2 border border-slate-200 bg-white hover:bg-slate-50 text-slate-600 rounded-xl transition-colors shrink-0"
              title="Refresh library"
            >
              <RefreshCw className={`w-4 h-4 ${isFetching ? 'animate-spin text-indigo-600' : ''}`} />
            </button>
          </div>
        </div>

        {/* Documents Table */}
        <div className="rounded-2xl bg-white border border-slate-200 shadow-2xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50/75 border-b border-slate-100 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                <tr>
                  <th className="py-3.5 px-5">Document</th>
                  <th className="py-3.5 px-4">Type</th>
                  <th className="py-3.5 px-4">Size</th>
                  <th className="py-3.5 px-4">Chunks</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-4">Indexed</th>
                  <th className="py-3.5 px-5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {isLoading ? (
                  <tr>
                    <td colSpan={7} className="py-12 text-center text-slate-400">
                      Loading documents...
                    </td>
                  </tr>
                ) : !data || data.items.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="py-16 text-center">
                      <div className="flex flex-col items-center justify-center">
                        <FileText className="w-8 h-8 text-slate-300 mb-2" />
                        <p className="text-xs font-medium text-slate-700">No documents found</p>
                        <p className="text-[11px] text-slate-400 mt-0.5">
                          {debouncedSearch || fileTypeFilter || statusFilter
                            ? 'Try clearing active search or filters.'
                            : 'Upload your first document or save a note.'}
                        </p>
                      </div>
                    </td>
                  </tr>
                ) : (
                  data.items.map((doc) => (
                    <tr
                      key={doc.id}
                      className="hover:bg-slate-50/70 transition-colors group"
                    >
                      <td className="py-3.5 px-5">
                        <div
                          onClick={() => navigate(`/documents/${doc.id}`)}
                          className="cursor-pointer"
                        >
                          <div className="font-medium text-slate-900 group-hover:text-indigo-600 transition-colors">
                            {doc.title}
                          </div>
                          <div className="text-slate-400 text-[11px] font-mono mt-0.5">
                            {doc.original_filename}
                          </div>
                        </div>
                      </td>
                      <td className="py-3.5 px-4">
                        <span className="font-mono text-[11px] uppercase bg-slate-100 text-slate-700 px-2 py-0.5 rounded-md font-medium">
                          {doc.file_type}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-slate-600 font-mono text-[11px]">
                        {formatFileSize(doc.file_size)}
                      </td>
                      <td className="py-3.5 px-4 font-mono text-slate-700">
                        {doc.chunk_count > 0 ? (
                          <span className="font-medium">{doc.chunk_count}</span>
                        ) : (
                          <span className="text-slate-400">—</span>
                        )}
                      </td>
                      <td className="py-3.5 px-4">
                        <span
                          className={`inline-flex items-center gap-1.5 font-mono text-[11px] px-2 py-0.5 rounded-md font-medium capitalize ${
                            doc.processing_status === 'completed'
                              ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                              : doc.processing_status === 'processing'
                              ? 'bg-amber-50 text-amber-700 border border-amber-200 animate-pulse'
                              : doc.processing_status === 'failed'
                              ? 'bg-rose-50 text-rose-700 border border-rose-200'
                              : 'bg-slate-100 text-slate-600 border border-slate-200'
                          }`}
                        >
                          {doc.processing_status === 'completed' && <CheckCircle2 className="w-3 h-3 text-emerald-600" />}
                          {doc.processing_status === 'processing' && <Clock className="w-3 h-3 text-amber-600" />}
                          {doc.processing_status === 'failed' && <AlertCircle className="w-3 h-3 text-rose-600" />}
                          <span>{doc.processing_status}</span>
                        </span>
                        {doc.error_message && (
                          <div className="text-[10px] text-rose-600 mt-1 max-w-xs truncate" title={doc.error_message}>
                            {doc.error_message}
                          </div>
                        )}
                      </td>
                      <td className="py-3.5 px-4 text-slate-500 font-mono text-[11px]">
                        {formatDate(doc.created_at)}
                      </td>
                      <td className="py-3.5 px-5 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            onClick={() => navigate(`/documents/${doc.id}`)}
                            className="p-1 text-slate-400 hover:text-slate-700 rounded-md transition-colors"
                            title="View document chunks"
                          >
                            <ExternalLink className="w-3.5 h-3.5" />
                          </button>
                          {doc.processing_status === 'failed' && (
                            <button
                              onClick={() => retryMutation.mutate(doc.id)}
                              disabled={retryMutation.isPending}
                              className="p-1 text-amber-600 hover:text-amber-800 rounded-md transition-colors"
                              title="Retry processing job"
                            >
                              <RotateCcw className="w-3.5 h-3.5" />
                            </button>
                          )}
                          <button
                            onClick={() => {
                              if (confirm(`Delete document "${doc.title}" and its vector chunks?`)) {
                                deleteMutation.mutate(doc.id);
                              }
                            }}
                            disabled={deleteMutation.isPending}
                            className="p-1 text-slate-400 hover:text-rose-600 rounded-md transition-colors"
                            title="Delete document"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {data && data.total_pages > 1 && (
            <div className="p-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
              <div>
                Showing page <span className="font-semibold text-slate-700">{data.page}</span> of{' '}
                <span className="font-semibold text-slate-700">{data.total_pages}</span> ({data.total} items)
              </div>
              <div className="flex items-center gap-1.5">
                <button
                  disabled={page <= 1}
                  onClick={() => setPage((p) => p - 1)}
                  className="px-2.5 py-1 border border-slate-200 rounded-lg disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-50 transition-colors"
                >
                  Previous
                </button>
                <button
                  disabled={page >= data.total_pages}
                  onClick={() => setPage((p) => p + 1)}
                  className="px-2.5 py-1 border border-slate-200 rounded-lg disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-50 transition-colors"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Upload Modal */}
      {isUploadOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-xl max-w-md w-full p-6 space-y-4 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold text-slate-900">Upload Document</h3>
                <p className="text-xs text-slate-500 mt-0.5">PDF, TXT, or Markdown (up to 10 MB)</p>
              </div>
              <button
                onClick={() => setIsUploadOpen(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-md"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div
              onDragOver={(e) => {
                e.preventDefault();
                setDragActive(true);
              }}
              onDragLeave={() => setDragActive(false)}
              onDrop={handleDrop}
              className={`border-2 border-dashed rounded-xl p-8 text-center transition-all flex flex-col items-center justify-center ${
                dragActive ? 'border-indigo-500 bg-indigo-50/50' : 'border-slate-200 bg-slate-50/50'
              }`}
            >
              <Upload className="w-8 h-8 text-slate-400 mb-3" />
              <p className="text-xs font-medium text-slate-700">Drag and drop file here, or click to browse</p>
              <p className="text-[11px] text-slate-400 mt-1">Supports .pdf, .txt, .md</p>

              <label className="mt-4 px-3.5 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-medium cursor-pointer transition-colors">
                <span>Select File</span>
                <input
                  type="file"
                  accept=".pdf,.txt,.md,.markdown"
                  onChange={handleFileUpload}
                  className="hidden"
                  disabled={uploadMutation.isPending}
                />
              </label>
            </div>

            {uploadMutation.isPending && (
              <div className="flex items-center justify-center gap-2 text-xs text-indigo-600 font-medium py-1">
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Uploading and scheduling background job...</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Note Creation Modal */}
      {isNoteOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-xl max-w-lg w-full p-6 space-y-4 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold text-slate-900">Create Knowledge Note</h3>
                <p className="text-xs text-slate-500 mt-0.5">Direct text input for notes, meeting logs, or facts</p>
              </div>
              <button
                onClick={() => setIsNoteOpen(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-md"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">Title</label>
                <input
                  type="text"
                  value={noteTitle}
                  onChange={(e) => setNoteTitle(e.target.value)}
                  placeholder="e.g. Distributed Consensus Notes"
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">Note Content</label>
                <textarea
                  rows={8}
                  value={noteContent}
                  onChange={(e) => setNoteContent(e.target.value)}
                  placeholder="Type or paste knowledge text here. It will be chunked and embedded by the worker..."
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-mono focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setIsNoteOpen(false)}
                className="px-3 py-1.5 border border-slate-200 rounded-lg text-xs font-medium text-slate-600 hover:bg-slate-50"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={!noteTitle.trim() || !noteContent.trim() || noteMutation.isPending}
                onClick={() =>
                  noteMutation.mutate({
                    title: noteTitle.trim(),
                    content: noteContent.trim(),
                  })
                }
                className="flex items-center gap-1.5 px-3.5 py-1.5 bg-slate-900 hover:bg-slate-800 disabled:opacity-50 text-white rounded-lg text-xs font-medium transition-colors"
              >
                {noteMutation.isPending && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
                <span>Save Note</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
