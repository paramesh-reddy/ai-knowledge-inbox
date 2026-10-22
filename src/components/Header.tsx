import React from 'react';
import { Sparkles, Terminal, Database, ShieldCheck } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';

interface HeaderProps {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
}

export const Header: React.FC<HeaderProps> = ({ title, subtitle, action }) => {
  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: api.getHealth,
    staleTime: 30000,
  });

  return (
    <header className="h-16 border-b border-slate-200 bg-white px-8 flex items-center justify-between shrink-0">
      <div>
        <h1 className="text-lg font-semibold text-slate-900 tracking-tight leading-none">{title}</h1>
        {subtitle && <p className="text-xs text-slate-500 mt-1">{subtitle}</p>}
      </div>

      <div className="flex items-center gap-3">
        <div className="hidden lg:flex items-center gap-2 px-2.5 py-1 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-600">
          <Database className="w-3.5 h-3.5 text-slate-400" />
          <span className="font-mono text-[11px]">{health?.database_type || 'PostgreSQL / SQLite'}</span>
        </div>

        <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-emerald-50/80 border border-emerald-200/80 text-xs text-emerald-800 font-medium">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
          <span>Strict RAG Grounding</span>
        </div>

        {action && <div>{action}</div>}
      </div>
    </header>
  );
};
