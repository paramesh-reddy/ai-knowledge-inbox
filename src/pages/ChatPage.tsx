import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Send,
  Sparkles,
  Bot,
  User,
  BookOpen,
  ChevronDown,
  ChevronUp,
  FileText,
  AlertCircle,
  PlusCircle,
  MessageSquare,
  RefreshCw,
  ExternalLink,
  ShieldCheck,
} from 'lucide-react';
import { api } from '../services/api';
import { Header } from '../components/Header';
import { useToast } from '../components/Toast';
import { CitationItem, ChatMessage, ChatSession } from '../types';

export const ChatPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [question, setQuestion] = useState('');
  const [expandedCitations, setExpandedCitations] = useState<Record<string, boolean>>({});

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Suggested prompt pills
  const suggestedQuestions = [
    'What are the key architectural decisions and SLA requirements?',
    'Summarize the core concepts described across all documents.',
    'What happens when background job processing fails?',
    'Are there any security and data isolation guidelines mentioned?',
  ];

  // Fetch chat sessions
  const { data: sessions, refetch: refetchSessions } = useQuery({
    queryKey: ['chatSessions'],
    queryFn: api.getChatSessions,
  });

  // Set initial active session if available and none selected
  useEffect(() => {
    if (!activeSessionId && sessions && sessions.length > 0) {
      setActiveSessionId(sessions[0].id);
    }
  }, [sessions, activeSessionId]);

  // Fetch messages for active session
  const { data: messages, isLoading: isLoadingMessages, refetch: refetchMessages } = useQuery({
    queryKey: ['sessionMessages', activeSessionId],
    queryFn: () => (activeSessionId ? api.getSessionMessages(activeSessionId) : Promise.resolve([])),
    enabled: !!activeSessionId,
  });

  // Auto-scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Ask question mutation
  const askMutation = useMutation({
    mutationFn: (q: string) => api.askQuestion(q, activeSessionId),
    onSuccess: (data) => {
      setActiveSessionId(data.session_id);
      setQuestion('');
      queryClient.invalidateQueries({ queryKey: ['sessionMessages', data.session_id] });
      queryClient.invalidateQueries({ queryKey: ['chatSessions'] });
      if (!data.has_evidence) {
        showToast('No relevant document evidence found for this query', 'info');
      }
    },
    onError: (err: any) => {
      showToast(err.message || 'Error generating answer', 'error');
    },
  });

  const handleSend = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const clean = question.trim();
    if (!clean || askMutation.isPending) return;
    askMutation.mutate(clean);
  };

  const toggleCitation = (msgId: string) => {
    setExpandedCitations((prev) => ({
      ...prev,
      [msgId]: !prev[msgId],
    }));
  };

  const handleNewChat = () => {
    setActiveSessionId(null);
  };

  return (
    <div className="flex-1 flex flex-col h-screen overflow-hidden bg-slate-50/50">
      <Header
        title="Ask AI (Grounded RAG)"
        subtitle="Conversational answers strictly grounded in your indexed knowledge with verifiable citations"
      />

      <div className="flex-1 flex overflow-hidden">
        {/* Sessions Sidebar */}
        <div className="w-64 border-r border-slate-200 bg-white flex flex-col shrink-0 hidden md:flex">
          <div className="p-3 border-b border-slate-100 flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-700">Conversations</span>
            <button
              onClick={handleNewChat}
              className="flex items-center gap-1 px-2.5 py-1 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-[11px] font-medium transition-colors cursor-pointer"
            >
              <PlusCircle className="w-3 h-3" />
              <span>New Chat</span>
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {!sessions || sessions.length === 0 ? (
              <div className="p-4 text-center text-xs text-slate-400">No previous sessions</div>
            ) : (
              sessions.map((s) => (
                <button
                  key={s.id}
                  onClick={() => setActiveSessionId(s.id)}
                  className={`w-full text-left p-2.5 rounded-xl text-xs transition-colors cursor-pointer flex items-center justify-between ${
                    activeSessionId === s.id
                      ? 'bg-slate-100 text-slate-900 font-medium'
                      : 'text-slate-600 hover:bg-slate-50'
                  }`}
                >
                  <div className="truncate flex-1 mr-2">{s.title}</div>
                  <span className="text-[10px] text-slate-400 font-mono shrink-0">
                    {s.message_count}
                  </span>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Chat Main Area */}
        <div className="flex-1 flex flex-col h-full bg-white relative">
          {/* Messages Feed */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {(!messages || messages.length === 0) && !askMutation.isPending ? (
              <div className="max-w-xl mx-auto my-auto text-center py-16 space-y-6">
                <div className="w-12 h-12 rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 mx-auto">
                  <Sparkles className="w-6 h-6" />
                </div>
                <div>
                  <h2 className="text-base font-semibold text-slate-900">Ask Anything About Your Knowledge Base</h2>
                  <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto leading-relaxed">
                    Gemini retrieves the most relevant passages using vector search and generates a factual, grounded
                    response. Citations link directly back to source documents and page numbers.
                  </p>
                </div>

                <div className="space-y-2 text-left pt-2">
                  <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 text-center">
                    Suggested Questions
                  </div>
                  <div className="grid grid-cols-1 gap-2">
                    {suggestedQuestions.map((q, i) => (
                      <button
                        key={i}
                        onClick={() => {
                          setQuestion(q);
                          askMutation.mutate(q);
                        }}
                        className="p-3 rounded-xl border border-slate-200 bg-slate-50/60 hover:bg-slate-100/80 text-xs text-slate-700 text-left transition-colors cursor-pointer flex items-center justify-between group"
                      >
                        <span>{q}</span>
                        <Send className="w-3.5 h-3.5 text-slate-400 group-hover:text-indigo-600 transition-colors" />
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              messages?.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex gap-3 max-w-3xl ${
                    msg.role === 'user' ? 'ml-auto flex-row-reverse' : 'mr-auto'
                  }`}
                >
                  <div
                    className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 ${
                      msg.role === 'user'
                        ? 'bg-slate-900 text-white'
                        : 'bg-indigo-50 border border-indigo-100 text-indigo-600'
                    }`}
                  >
                    {msg.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                  </div>

                  <div className={`space-y-2 ${msg.role === 'user' ? 'text-right' : 'text-left'}`}>
                    <div
                      className={`p-4 rounded-2xl text-xs leading-relaxed whitespace-pre-wrap ${
                        msg.role === 'user'
                          ? 'bg-slate-900 text-white rounded-tr-none'
                          : 'bg-slate-50 border border-slate-200 text-slate-800 rounded-tl-none shadow-2xs'
                      }`}
                    >
                      {msg.content}
                    </div>

                    {/* Citations Box for Assistant Responses */}
                    {msg.role === 'assistant' && msg.citations && msg.citations.length > 0 && (
                      <div className="rounded-xl border border-slate-200 bg-slate-50/50 overflow-hidden text-xs">
                        <button
                          onClick={() => toggleCitation(msg.id)}
                          className="w-full px-3.5 py-2 flex items-center justify-between text-slate-700 font-medium hover:bg-slate-100/60 transition-colors cursor-pointer"
                        >
                          <div className="flex items-center gap-1.5 text-indigo-700">
                            <BookOpen className="w-3.5 h-3.5" />
                            <span>Source Citations ({msg.citations.length})</span>
                          </div>
                          {expandedCitations[msg.id] ? (
                            <ChevronUp className="w-3.5 h-3.5 text-slate-400" />
                          ) : (
                            <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
                          )}
                        </button>

                        {expandedCitations[msg.id] && (
                          <div className="p-3 border-t border-slate-200 space-y-2.5 bg-white">
                            {msg.citations.map((cite, cIdx) => (
                              <div
                                key={cIdx}
                                className="p-2.5 rounded-lg border border-slate-100 bg-slate-50/75 space-y-1"
                              >
                                <div className="flex items-center justify-between text-[11px]">
                                  <button
                                    onClick={() => navigate(`/documents/${cite.document_id}`)}
                                    className="font-medium text-indigo-600 hover:text-indigo-800 flex items-center gap-1 transition-colors cursor-pointer"
                                  >
                                    <span>{cite.document_title}</span>
                                    <ExternalLink className="w-3 h-3" />
                                  </button>
                                  <div className="flex items-center gap-2 text-slate-400 font-mono">
                                    {cite.page_number && (
                                      <span className="text-slate-600 font-semibold bg-slate-200/60 px-1.5 py-0.5 rounded">
                                        Page {cite.page_number}
                                      </span>
                                    )}
                                    {cite.similarity_score && (
                                      <span>Match: {(cite.similarity_score * 100).toFixed(0)}%</span>
                                    )}
                                  </div>
                                </div>
                                <div className="text-[11px] text-slate-600 font-mono italic leading-normal">
                                  "{cite.excerpt}"
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}

            {/* In-Flight Thinking Indicator */}
            {askMutation.isPending && (
              <div className="flex gap-3 mr-auto max-w-2xl">
                <div className="w-8 h-8 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 shrink-0">
                  <Bot className="w-4 h-4 animate-spin" />
                </div>
                <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 text-xs text-slate-500 rounded-tl-none flex items-center gap-2">
                  <RefreshCw className="w-3.5 h-3.5 animate-spin text-indigo-600" />
                  <span>Retrieving vector embeddings and grounding answer with Gemini...</span>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input Box Footer */}
          <div className="p-4 border-t border-slate-200 bg-white">
            <form onSubmit={handleSend} className="max-w-3xl mx-auto flex items-center gap-2">
              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask a question about your documents..."
                className="flex-1 px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all"
                disabled={askMutation.isPending}
              />
              <button
                type="submit"
                disabled={!question.trim() || askMutation.isPending}
                className="px-4 py-2.5 bg-slate-900 hover:bg-slate-800 disabled:opacity-40 text-white rounded-xl text-xs font-medium flex items-center gap-1.5 transition-colors cursor-pointer shrink-0"
              >
                <span>Ask</span>
                <Send className="w-3.5 h-3.5" />
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};
