import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  BookOpen,
  MessageSquare,
  Cpu,
  Settings,
  Sparkles,
  Inbox,
  Activity,
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';

export const Sidebar: React.FC = () => {
  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: api.getHealth,
    refetchInterval: 10000,
  });

  const { data: stats } = useQuery({
    queryKey: ['stats'],
    queryFn: api.getDashboardStats,
    refetchInterval: 5000,
  });

  const navItems = [
    {
      to: '/',
      label: 'Dashboard',
      icon: LayoutDashboard,
      badge: stats ? `${stats.total_documents}` : undefined,
    },
    {
      to: '/library',
      label: 'Knowledge Library',
      icon: BookOpen,
      badge: stats && stats.processing_documents > 0 ? `${stats.processing_documents} active` : undefined,
      badgeHighlight: stats && stats.processing_documents > 0,
    },
    {
      to: '/chat',
      label: 'Ask AI',
      icon: MessageSquare,
      badge: 'RAG',
    },
    {
      to: '/jobs',
      label: 'Processing Jobs',
      icon: Cpu,
      badge: stats && stats.failed_documents > 0 ? `${stats.failed_documents} failed` : undefined,
      badgeAlert: stats && stats.failed_documents > 0,
    },
    {
      to: '/settings',
      label: 'Health & Settings',
      icon: Settings,
    },
  ];

  return (
    <aside className="w-64 bg-white border-r border-slate-200 flex flex-col h-screen shrink-0 select-none">
      {/* Brand Header */}
      <div className="p-5 border-b border-slate-100 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-slate-900 flex items-center justify-center text-white shadow-sm">
            <Inbox className="w-5 h-5 text-indigo-400" />
          </div>
          <div>
            <div className="font-semibold text-slate-900 text-sm tracking-tight leading-none flex items-center gap-1.5">
              Knowledge Inbox
            </div>
            <div className="text-[11px] text-slate-500 font-mono mt-1">Turium AI Assessment</div>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        <div className="px-3 py-1.5 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
          Navigation
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                  isActive
                    ? 'bg-slate-100 text-slate-900 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                }`
              }
            >
              <div className="flex items-center gap-2.5">
                <Icon className="w-4 h-4 text-slate-500" />
                <span>{item.label}</span>
              </div>
              {item.badge && (
                <span
                  className={`text-[11px] px-2 py-0.5 rounded-md font-mono font-medium ${
                    item.badgeAlert
                      ? 'bg-rose-100 text-rose-700'
                      : item.badgeHighlight
                      ? 'bg-amber-100 text-amber-800 animate-pulse'
                      : 'bg-slate-100 text-slate-600'
                  }`}
                >
                  {item.badge}
                </span>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Backend Status Footer */}
      <div className="p-3 border-t border-slate-100 bg-slate-50/50">
        <div className="p-3 rounded-xl bg-white border border-slate-200 shadow-2xs space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-500 font-medium flex items-center gap-1.5">
              <span
                className={`w-2 h-2 rounded-full ${
                  health?.database_connected ? 'bg-emerald-500 ring-2 ring-emerald-100' : 'bg-rose-500'
                }`}
              />
              FastAPI Core
            </span>
            <span className="font-mono text-[11px] text-slate-600">
              {health ? health.database_type.split(' ')[0] : 'Connecting...'}
            </span>
          </div>

          <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1 border-t border-slate-100">
            <span>Model:</span>
            <span className="font-mono text-slate-700 font-medium truncate max-w-[110px]" title={health?.configured_model}>
              {health?.configured_model || 'gemini-3.8'}
            </span>
          </div>
        </div>
      </div>
    </aside>
  );
};
