import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ToastProvider } from './components/Toast';
import { Sidebar } from './components/Sidebar';
import { DashboardPage } from './pages/DashboardPage';
import { LibraryPage } from './pages/LibraryPage';
import { DocumentDetailPage } from './pages/DocumentDetailPage';
import { ChatPage } from './pages/ChatPage';
import { JobsPage } from './pages/JobsPage';
import { SettingsPage } from './pages/SettingsPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5000,
      retry: 1,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <BrowserRouter>
          <div className="flex h-screen w-screen overflow-hidden bg-white text-slate-900 font-sans antialiased">
            <Sidebar />
            <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
              <Routes>
                <Route path="/" element={<DashboardPage />} />
                <Route path="/library" element={<LibraryPage />} />
                <Route path="/documents/:id" element={<DocumentDetailPage />} />
                <Route path="/chat" element={<ChatPage />} />
                <Route path="/jobs" element={<JobsPage />} />
                <Route path="/settings" element={<SettingsPage />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </main>
          </div>
        </BrowserRouter>
      </ToastProvider>
    </QueryClientProvider>
  );
}
