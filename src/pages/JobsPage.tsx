import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Cpu,
  RefreshCw,
  Clock,
  CheckCircle2,
  AlertCircle,
  Activity,
  Layers,
  ArrowRight,
} from 'lucide-react';
import { api } from '../services/api';
import { Header } from '../components/Header';
import { JobStatus } from '../types';

export const JobsPage: React.FC = () => {
  const navigate = useNavigate();
  const [statusFilter, setStatusFilter] = useState<JobStatus | ''>('');
  const [page, setPage] = useState(1);

  const { data, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['jobs', page, statusFilter],
    queryFn: () =>
      api.getJobs({
        page,
        pageSize: 15,
        status: statusFilter || undefined,
      }),
    refetchInterval: 3000,
  });

  const formatDate = (iso?: string | null) => {
    if (!iso) return '—';
    try {
      return new Date(iso).toLocaleTimeString(undefined, {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      });
    } catch {
      return iso;
    }
  };

  return (
    <div className="flex-1 flex flex-col h-screen overflow-hidden bg-slate-50/50">
      <Header
        title="Processing Queue & Worker Status"
        subtitle="Asynchronous background pipeline for text extraction, chunking, and vector embedding"
        action={
          <button
            onClick={() => refetch()}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-xs font-medium text-slate-700 shadow-2xs transition-colors cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isFetching ? 'animate-spin text-indigo-600' : 'text-slate-500'}`} />
            <span>Refresh</span>
          </button>
        }
      />

      <div className="flex-1 overflow-y-auto p-8 space-y-6">
        {/* Worker Info Callout */}
        <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-2xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-slate-900 flex items-center justify-center text-white shrink-0">
              <Cpu className="w-5 h-5 text-indigo-400" />
            </div>
            <div>
              <div className="text-xs font-semibold text-slate-900 flex items-center gap-2">
                <span>PostgreSQL-Backed Worker Queue</span>
                <span className="flex items-center gap-1 text-[11px] text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md font-mono">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  Active
                </span>
              </div>
              <p className="text-[11px] text-slate-500 mt-0.5">
                Safe transactional claiming via <code className="bg-slate-100 px-1 py-0.5 rounded font-mono text-slate-700">FOR UPDATE SKIP LOCKED</code> with automatic recovery of stalled jobs.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value as any);
                setPage(1);
              }}
              className="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-700 font-medium focus:outline-none focus:border-indigo-500"
            >
              <option value="">All Statuses</option>
              <option value="pending">Pending</option>
              <option value="processing">Processing</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
            </select>
          </div>
        </div>

        {/* Jobs Table */}
        <div className="rounded-2xl bg-white border border-slate-200 shadow-2xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50/75 border-b border-slate-100 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                <tr>
                  <th className="py-3.5 px-5">Job ID</th>
                  <th className="py-3.5 px-4">Document</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-4">Attempts</th>
                  <th className="py-3.5 px-4">Enqueued</th>
                  <th className="py-3.5 px-4">Started</th>
                  <th className="py-3.5 px-4">Heartbeat</th>
                  <th className="py-3.5 px-5">Completed</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {isLoading ? (
                  <tr>
                    <td colSpan={8} className="py-12 text-center text-slate-400">
                      Loading job records...
                    </td>
                  </tr>
                ) : !data || data.items.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="py-16 text-center text-slate-400">
                      No background jobs found.
                    </td>
                  </tr>
                ) : (
                  data.items.map((job) => (
                    <tr key={job.id} className="hover:bg-slate-50/70 transition-colors">
                      <td className="py-3.5 px-5 font-mono text-[11px] text-slate-500">
                        {job.id.slice(0, 8)}...
                      </td>
                      <td className="py-3.5 px-4">
                        {job.document_title ? (
                          <button
                            onClick={() => navigate(`/documents/${job.document_id}`)}
                            className="font-medium text-indigo-600 hover:text-indigo-800 text-left transition-colors cursor-pointer"
                          >
                            {job.document_title}
                          </button>
                        ) : (
                          <span className="font-mono text-[11px] text-slate-400">{job.document_id.slice(0, 8)}</span>
                        )}
                        {job.error_message && (
                          <div className="text-[10px] text-rose-600 font-mono mt-0.5 truncate max-w-xs" title={job.error_message}>
                            {job.error_message}
                          </div>
                        )}
                      </td>
                      <td className="py-3.5 px-4">
                        <span
                          className={`inline-flex items-center gap-1.5 font-mono text-[11px] px-2 py-0.5 rounded-md font-medium capitalize ${
                            job.status === 'completed'
                              ? 'bg-emerald-50 text-emerald-700'
                              : job.status === 'processing'
                              ? 'bg-amber-50 text-amber-700 animate-pulse'
                              : job.status === 'failed'
                              ? 'bg-rose-50 text-rose-700'
                              : 'bg-slate-100 text-slate-600'
                          }`}
                        >
                          {job.status === 'completed' && <CheckCircle2 className="w-3 h-3 text-emerald-600" />}
                          {job.status === 'processing' && <Clock className="w-3 h-3 text-amber-600" />}
                          {job.status === 'failed' && <AlertCircle className="w-3 h-3 text-rose-600" />}
                          <span>{job.status}</span>
                        </span>
                      </td>
                      <td className="py-3.5 px-4 font-mono text-slate-700">
                        {job.attempt_count} / {job.max_attempts}
                      </td>
                      <td className="py-3.5 px-4 font-mono text-slate-500 text-[11px]">
                        {formatDate(job.created_at)}
                      </td>
                      <td className="py-3.5 px-4 font-mono text-slate-500 text-[11px]">
                        {formatDate(job.started_at)}
                      </td>
                      <td className="py-3.5 px-4 font-mono text-slate-500 text-[11px]">
                        {formatDate(job.heartbeat_at)}
                      </td>
                      <td className="py-3.5 px-5 font-mono text-slate-500 text-[11px]">
                        {formatDate(job.finished_at)}
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
                Page <span className="font-semibold text-slate-700">{data.page}</span> of{' '}
                <span className="font-semibold text-slate-700">{data.total_pages}</span> ({data.total} jobs)
              </div>
              <div className="flex items-center gap-1.5">
                <button
                  disabled={page <= 1}
                  onClick={() => setPage((p) => p - 1)}
                  className="px-2.5 py-1 border border-slate-200 rounded-lg disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-50"
                >
                  Previous
                </button>
                <button
                  disabled={page >= data.total_pages}
                  onClick={() => setPage((p) => p + 1)}
                  className="px-2.5 py-1 border border-slate-200 rounded-lg disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-50"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
