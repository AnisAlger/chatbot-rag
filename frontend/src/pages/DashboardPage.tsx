import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FileText,
  MessageSquare,
  Upload,
  Layers,
  ArrowRight,
  Clock,
  Sparkles,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { documentsApi } from '../api/documentsApi';
import { conversationsApi } from '../api/conversationsApi';
import { DocumentItem } from '../types/document';
import { ConversationSummary } from '../types/conversation';

export const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [docsRes, convsRes] = await Promise.all([
          documentsApi.listDocuments(),
          conversationsApi.listConversations(),
        ]);
        setDocuments(docsRes.documents);
        setConversations(convsRes);
      } catch (err) {
        console.error('Failed to load dashboard data:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const totalChunks = documents.reduce((acc, doc) => acc + (doc.chunk_count || 0), 0);
  const totalPages = documents.reduce((acc, doc) => acc + (doc.page_count || 0), 0);

  const startNewChat = async () => {
    try {
      const conv = await conversationsApi.createConversation({ title: 'New Conversation' });
      navigate(`/chat?id=${conv.id}`);
    } catch (err) {
      console.error(err);
      navigate('/chat');
    }
  };

  return (
    <div className="page-container">
      {/* Welcome Banner */}
      <div
        className="glass-panel"
        style={{
          padding: 'clamp(20px, 4vw, 32px)',
          marginBottom: '28px',
          background: 'radial-gradient(ellipse at bottom right, rgba(99, 102, 241, 0.15) 0%, var(--bg-card) 60%)',
          display: 'flex',
          flexDirection: 'row',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '20px',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <span className="badge badge-success" style={{ gap: '6px' }}>
              <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--success)' }} />
              System Operational
            </span>
          </div>
          <h1 style={{ fontSize: 'clamp(1.35rem, 4vw, 1.85rem)', fontWeight: 800, marginBottom: '8px' }}>
            Welcome, {user?.full_name || user?.email?.split('@')[0]}
          </h1>
          <p style={{ color: 'var(--text-secondary)', maxWidth: '600px', fontSize: 'clamp(0.85rem, 2.5vw, 0.95rem)' }}>
            Upload PDFs to your private knowledge base, extract verifiable facts, and ask questions
            grounded strictly in source citations.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          <button onClick={() => navigate('/documents')} className="btn-secondary">
            <Upload size={16} />
            <span>Upload Document</span>
          </button>
          <button onClick={startNewChat} className="btn-primary">
            <Sparkles size={16} />
            <span>New Chat Session</span>
          </button>
        </div>
      </div>

      {/* Metrics Grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 200px), 1fr))',
          gap: '16px',
          marginBottom: '28px',
        }}
      >
        <div className="glass-panel" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
            <span style={{ fontSize: '0.85rem', fontWeight: 600, textTransform: 'uppercase' }}>Documents</span>
            <FileText size={20} color="var(--accent-primary)" />
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 700, margin: '12px 0 4px 0' }}>
            {documents.length}
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            {totalPages} total pages extracted
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
            <span style={{ fontSize: '0.85rem', fontWeight: 600, textTransform: 'uppercase' }}>Indexed Chunks</span>
            <Layers size={20} color="#8B5CF6" />
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 700, margin: '12px 0 4px 0' }}>
            {totalChunks}
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            Vector embeddings generated
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
            <span style={{ fontSize: '0.85rem', fontWeight: 600, textTransform: 'uppercase' }}>Conversations</span>
            <MessageSquare size={20} color="#EC4899" />
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 700, margin: '12px 0 4px 0' }}>
            {conversations.length}
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            Active Q&A threads
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
            <span style={{ fontSize: '0.85rem', fontWeight: 600, textTransform: 'uppercase' }}>Isolation</span>
            <CheckCircle2 size={20} color="var(--success)" />
          </div>
          <div style={{ fontSize: '1.25rem', fontWeight: 700, margin: '16px 0 4px 0' }}>
            User Guard Enforced
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            Strict multi-tenant security
          </div>
        </div>
      </div>

      {/* Two Column Layout: Recent Documents & Recent Conversations */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
          gap: '24px',
        }}
      >
        {/* Recent Documents Card */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: '16px',
            }}
          >
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Recent Documents</h3>
            <button
              onClick={() => navigate('/documents')}
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--accent-primary)',
                fontSize: '0.85rem',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
              }}
            >
              <span>View All</span>
              <ArrowRight size={14} />
            </button>
          </div>

          {documents.length === 0 ? (
            <div
              style={{
                padding: '36px 16px',
                textAlign: 'center',
                color: 'var(--text-muted)',
                fontSize: '0.9rem',
              }}
            >
              <FileText size={36} style={{ margin: '0 auto 12px auto', opacity: 0.4 }} />
              <p>No documents uploaded yet.</p>
              <button
                onClick={() => navigate('/documents')}
                className="btn-secondary"
                style={{ marginTop: '12px', fontSize: '0.85rem' }}
              >
                Upload your first PDF
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {documents.slice(0, 4).map((doc) => (
                <div
                  key={doc.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '12px 14px',
                    borderRadius: 'var(--radius-md)',
                    background: 'var(--bg-input)',
                    border: '1px solid var(--border-color)',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px', overflow: 'hidden' }}>
                    <FileText size={20} color="var(--accent-primary)" style={{ flexShrink: 0 }} />
                    <div style={{ overflow: 'hidden' }}>
                      <div
                        style={{
                          fontWeight: 600,
                          fontSize: '0.9rem',
                          whiteSpace: 'nowrap',
                          textOverflow: 'ellipsis',
                          overflow: 'hidden',
                        }}
                      >
                        {doc.filename}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        {doc.page_count} pages • {(doc.file_size_bytes / 1024).toFixed(0)} KB
                      </div>
                    </div>
                  </div>

                  <span
                    className={`badge ${
                      doc.status === 'indexed'
                        ? 'badge-success'
                        : doc.status === 'failed'
                        ? 'badge-error'
                        : 'badge-warning'
                    }`}
                  >
                    {doc.status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent Conversations Card */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: '16px',
            }}
          >
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Recent Conversations</h3>
            <button
              onClick={() => navigate('/chat')}
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--accent-primary)',
                fontSize: '0.85rem',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
              }}
            >
              <span>Go to Chat</span>
              <ArrowRight size={14} />
            </button>
          </div>

          {conversations.length === 0 ? (
            <div
              style={{
                padding: '36px 16px',
                textAlign: 'center',
                color: 'var(--text-muted)',
                fontSize: '0.9rem',
              }}
            >
              <MessageSquare size={36} style={{ margin: '0 auto 12px auto', opacity: 0.4 }} />
              <p>No active conversations yet.</p>
              <button
                onClick={startNewChat}
                className="btn-primary"
                style={{ marginTop: '12px', fontSize: '0.85rem' }}
              >
                Start your first chat
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {conversations.slice(0, 4).map((conv) => (
                <div
                  key={conv.id}
                  onClick={() => navigate(`/chat?id=${conv.id}`)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '12px 14px',
                    borderRadius: 'var(--radius-md)',
                    background: 'var(--bg-input)',
                    border: '1px solid var(--border-color)',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = 'var(--accent-primary)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = 'var(--border-color)';
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px', overflow: 'hidden' }}>
                    <MessageSquare size={18} color="var(--text-secondary)" style={{ flexShrink: 0 }} />
                    <div style={{ overflow: 'hidden' }}>
                      <div
                        style={{
                          fontWeight: 600,
                          fontSize: '0.9rem',
                          whiteSpace: 'nowrap',
                          textOverflow: 'ellipsis',
                          overflow: 'hidden',
                        }}
                      >
                        {conv.title}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        {conv.message_count} messages
                      </div>
                    </div>
                  </div>

                  <ArrowRight size={16} color="var(--text-muted)" />
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
