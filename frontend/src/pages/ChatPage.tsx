import React, { useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Send,
  Plus,
  Trash2,
  Bookmark,
  Copy,
  Check,
  Bot,
  User,
  Sparkles,
  FileText,
  AlertCircle,
  MessageSquare
} from 'lucide-react';
import { conversationsApi } from '../api/conversationsApi';
import { documentsApi } from '../api/documentsApi';
import { CitationModal } from '../components/CitationModal';
import { Citation, ConversationDetail, ConversationSummary, Message } from '../types/conversation';
import { DocumentItem } from '../types/document';

export const ChatPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const urlConvId = searchParams.get('id');
  const urlDocId = searchParams.get('doc');

  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [activeConv, setActiveConv] = useState<ConversationDetail | null>(null);
  const [availableDocs, setAvailableDocs] = useState<DocumentItem[]>([]);
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>(urlDocId ? [urlDocId] : []);

  const [inputQuestion, setInputQuestion] = useState<string>('');
  const [isSending, setIsSending] = useState<boolean>(false);
  const [copiedMsgId, setCopiedMsgId] = useState<string | null>(null);

  // Selected citation for modal
  const [activeCitation, setActiveCitation] = useState<Citation | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Load conversations and available documents
  const loadInitialData = async () => {
    try {
      const [convs, docsRes] = await Promise.all([
        conversationsApi.listConversations(),
        documentsApi.listDocuments(),
      ]);
      setConversations(convs);
      setAvailableDocs(docsRes.documents);

      if (urlConvId) {
        loadConversation(urlConvId);
      } else if (convs.length > 0) {
        loadConversation(convs[0].id);
      } else {
        handleCreateNewConversation();
      }
    } catch (err) {
      console.error('Failed to load chat data:', err);
    }
  };

  useEffect(() => {
    loadInitialData();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [activeConv?.messages, isSending]);

  const loadConversation = async (id: string) => {
    try {
      const detail = await conversationsApi.getConversation(id);
      setActiveConv(detail);
      setSelectedDocIds(detail.selected_document_ids || []);
      setSearchParams({ id });
    } catch (err) {
      console.error('Failed to load conversation:', err);
    }
  };

  const handleCreateNewConversation = async () => {
    try {
      const newConv = await conversationsApi.createConversation({
        title: 'New Conversation',
        selected_document_ids: selectedDocIds,
      });
      setActiveConv(newConv);
      setConversations((prev) => [
        {
          id: newConv.id,
          title: newConv.title,
          selected_document_ids: newConv.selected_document_ids,
          created_at: newConv.created_at,
          updated_at: newConv.updated_at,
          message_count: 0,
        },
        ...prev,
      ]);
      setSearchParams({ id: newConv.id });
    } catch (err) {
      console.error('Failed to create new conversation:', err);
    }
  };

  const handleDeleteConversation = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await conversationsApi.deleteConversation(id);
      const remaining = conversations.filter((c) => c.id !== id);
      setConversations(remaining);
      if (activeConv?.id === id) {
        if (remaining.length > 0) {
          loadConversation(remaining[0].id);
        } else {
          handleCreateNewConversation();
        }
      }
    } catch (err) {
      console.error('Failed to delete conversation:', err);
    }
  };

  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputQuestion.trim() || !activeConv || isSending) return;

    const question = inputQuestion.trim();
    setInputQuestion('');

    // Optimistically append user message to UI
    const optimisticUserMsg: Message = {
      id: `temp_${Date.now()}`,
      conversation_id: activeConv.id,
      role: 'user',
      content: question,
      created_at: new Date().toISOString(),
    };

    setActiveConv((prev) =>
      prev ? { ...prev, messages: [...prev.messages, optimisticUserMsg] } : null
    );

    setIsSending(true);
    try {
      const res = await conversationsApi.sendMessage(activeConv.id, {
        content: question,
        selected_document_ids: selectedDocIds,
      });

      const assistantMsg: Message = {
        id: `asst_${Date.now()}`,
        conversation_id: activeConv.id,
        role: 'assistant',
        content: res.answer,
        citations: res.citations,
        retrieval_meta: res.retrieval,
        created_at: new Date().toISOString(),
      };

      setActiveConv((prev) =>
        prev ? { ...prev, messages: [...prev.messages, assistantMsg] } : null
      );

      // Refresh conversations list to update title if it changed
      const updatedList = await conversationsApi.listConversations();
      setConversations(updatedList);
    } catch (err: any) {
      const errorMsg: Message = {
        id: `err_${Date.now()}`,
        conversation_id: activeConv.id,
        role: 'assistant',
        content: `Error: ${err.message || 'Failed to retrieve grounded answer. Please verify backend service.'}`,
        created_at: new Date().toISOString(),
      };
      setActiveConv((prev) =>
        prev ? { ...prev, messages: [...prev.messages, errorMsg] } : null
      );
    } finally {
      setIsSending(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedMsgId(id);
    setTimeout(() => setCopiedMsgId(null), 2000);
  };

  const toggleDocSelection = (docId: string) => {
    setSelectedDocIds((prev) =>
      prev.includes(docId) ? prev.filter((id) => id !== docId) : [...prev, docId]
    );
  };

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      {/* Left Chat Sessions Column */}
      <aside
        style={{
          width: '280px',
          minWidth: '280px',
          background: 'var(--bg-secondary)',
          borderRight: '1px solid var(--border-color)',
          display: 'flex',
          flexDirection: 'column',
          padding: '20px 14px',
        }}
      >
        <button
          onClick={handleCreateNewConversation}
          className="btn-primary"
          style={{ width: '100%', marginBottom: '16px', gap: '8px' }}
        >
          <Plus size={18} />
          <span>New Chat</span>
        </button>

        <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '8px', paddingLeft: '8px' }}>
          Conversations ({conversations.length})
        </div>

        <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '6px' }}>
          {conversations.map((conv) => {
            const isActive = activeConv?.id === conv.id;
            return (
              <div
                key={conv.id}
                onClick={() => loadConversation(conv.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '10px 12px',
                  borderRadius: 'var(--radius-md)',
                  background: isActive ? 'var(--accent-glow)' : 'transparent',
                  border: `1px solid ${isActive ? 'var(--accent-primary)' : 'transparent'}`,
                  color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', overflow: 'hidden' }}>
                  <MessageSquare size={16} color={isActive ? 'var(--accent-primary)' : 'var(--text-muted)'} style={{ flexShrink: 0 }} />
                  <span
                    style={{
                      fontSize: '0.875rem',
                      fontWeight: isActive ? 600 : 500,
                      whiteSpace: 'nowrap',
                      textOverflow: 'ellipsis',
                      overflow: 'hidden',
                    }}
                  >
                    {conv.title}
                  </span>
                </div>

                <button
                  onClick={(e) => handleDeleteConversation(conv.id, e)}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: 'var(--text-muted)',
                    cursor: 'pointer',
                    padding: '2px',
                    opacity: isActive ? 1 : 0.4,
                  }}
                  title="Delete chat"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            );
          })}
        </div>
      </aside>

      {/* Main Chat Workspace Area */}
      <main style={{ flex: 1, display: 'flex', flexDirection: 'column', background: 'var(--bg-primary)', overflow: 'hidden' }}>
        {/* Chat Header with Document Filter Bar */}
        <div
          style={{
            padding: '14px 24px',
            borderBottom: '1px solid var(--border-color)',
            background: 'var(--bg-secondary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '12px',
          }}
        >
          <div>
            <h2 style={{ fontSize: '1.15rem', fontWeight: 700 }}>
              {activeConv?.title || 'Chat Workspace'}
            </h2>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Grounded Question-Answering with Verifiable PDF Citations
            </div>
          </div>

          {/* Document Filter Pills */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <FileText size={14} />
              <span>Query Scope:</span>
            </span>

            <button
              onClick={() => setSelectedDocIds([])}
              style={{
                padding: '4px 10px',
                borderRadius: 'var(--radius-full)',
                border: '1px solid var(--border-color)',
                background: selectedDocIds.length === 0 ? 'var(--accent-primary)' : 'var(--bg-input)',
                color: selectedDocIds.length === 0 ? '#FFFFFF' : 'var(--text-secondary)',
                fontSize: '0.775rem',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              All Documents ({availableDocs.length})
            </button>

            {availableDocs.map((doc) => {
              const isSelected = selectedDocIds.includes(doc.id);
              return (
                <button
                  key={doc.id}
                  onClick={() => toggleDocSelection(doc.id)}
                  style={{
                    padding: '4px 10px',
                    borderRadius: 'var(--radius-full)',
                    border: '1px solid var(--border-color)',
                    background: isSelected ? 'rgba(99, 102, 241, 0.2)' : 'var(--bg-input)',
                    borderColor: isSelected ? 'var(--accent-primary)' : 'var(--border-color)',
                    color: isSelected ? 'var(--accent-primary)' : 'var(--text-secondary)',
                    fontSize: '0.775rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    whiteSpace: 'nowrap',
                    maxWidth: '160px',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                  }}
                  title={doc.filename}
                >
                  {doc.filename}
                </button>
              );
            })}
          </div>
        </div>

        {/* Message Thread Area */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '24px 32px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {activeConv && activeConv.messages.length === 0 ? (
            <div
              style={{
                margin: 'auto',
                maxWidth: '540px',
                textAlign: 'center',
                padding: '36px 20px',
              }}
            >
              <div
                style={{
                  width: '64px',
                  height: '64px',
                  borderRadius: '50%',
                  background: 'var(--accent-glow)',
                  color: 'var(--accent-primary)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  margin: '0 auto 16px auto',
                }}
              >
                <Sparkles size={32} />
              </div>
              <h3 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: '8px' }}>
                Ask anything about your documents
              </h3>
              <p style={{ fontSize: '0.925rem', color: 'var(--text-secondary)', marginBottom: '24px' }}>
                Questions are answered strictly using retrieved passages from your uploaded PDFs. Every answer includes verifiable page numbers and excerpts.
              </p>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', textAlign: 'left' }}>
                {[
                  'What are the key findings or conclusions of this document?',
                  'Summarize the financial projections and growth metrics.',
                  'What operational risks or limitations are stated?',
                ].map((prompt, idx) => (
                  <button
                    key={idx}
                    onClick={() => {
                      setInputQuestion(prompt);
                      textareaRef.current?.focus();
                    }}
                    style={{
                      padding: '10px 14px',
                      borderRadius: 'var(--radius-md)',
                      background: 'var(--bg-card)',
                      border: '1px solid var(--border-color)',
                      color: 'var(--text-primary)',
                      fontSize: '0.85rem',
                      textAlign: 'left',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'var(--accent-primary)')}
                    onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'var(--border-color)')}
                  >
                    "{prompt}"
                  </button>
                ))}
              </div>
            </div>
          ) : (
            activeConv?.messages.map((msg) => {
              const isUser = msg.role === 'user';
              return (
                <div
                  key={msg.id}
                  style={{
                    display: 'flex',
                    flexDirection: isUser ? 'row-reverse' : 'row',
                    gap: '12px',
                    maxWidth: '85%',
                    alignSelf: isUser ? 'flex-end' : 'flex-start',
                  }}
                  className="animate-fade-in"
                >
                  {/* Avatar */}
                  <div
                    style={{
                      width: '34px',
                      height: '34px',
                      borderRadius: '50%',
                      background: isUser ? 'var(--accent-primary)' : 'var(--bg-secondary)',
                      border: '1px solid var(--border-color)',
                      color: isUser ? '#FFFFFF' : 'var(--accent-primary)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0,
                    }}
                  >
                    {isUser ? <User size={18} /> : <Bot size={18} />}
                  </div>

                  {/* Message Bubble */}
                  <div
                    style={{
                      background: isUser ? 'var(--accent-primary)' : 'var(--bg-secondary)',
                      color: isUser ? '#FFFFFF' : 'var(--text-primary)',
                      border: `1px solid ${isUser ? 'transparent' : 'var(--border-color)'}`,
                      borderRadius: 'var(--radius-lg)',
                      padding: '16px 20px',
                      boxShadow: 'var(--shadow-sm)',
                    }}
                  >
                    <div style={{ fontSize: '0.95rem', lineHeight: '1.6', whiteSpace: 'pre-wrap' }}>
                      {msg.content}
                    </div>

                    {/* Citations Badges */}
                    {!isUser && msg.citations && msg.citations.length > 0 && (
                      <div style={{ marginTop: '14px', paddingTop: '12px', borderTop: '1px solid var(--border-color)' }}>
                        <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                          <Bookmark size={13} color="var(--accent-primary)" />
                          <span>SOURCE CITATIONS ({msg.citations.length})</span>
                        </div>

                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                          {msg.citations.map((cit, cIdx) => (
                            <button
                              key={cIdx}
                              onClick={() => setActiveCitation(cit)}
                              style={{
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: '6px',
                                padding: '4px 10px',
                                borderRadius: 'var(--radius-full)',
                                background: 'var(--bg-input)',
                                border: '1px solid var(--border-color)',
                                color: 'var(--text-primary)',
                                fontSize: '0.775rem',
                                fontWeight: 500,
                                cursor: 'pointer',
                                transition: 'all 0.15s ease',
                              }}
                              onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'var(--accent-primary)')}
                              onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'var(--border-color)')}
                              title="Click to view extracted page passage"
                            >
                              <FileText size={12} color="var(--accent-primary)" />
                              <span>{cit.filename} (p. {cit.page})</span>
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Message Actions */}
                    {!isUser && (
                      <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '8px' }}>
                        <button
                          onClick={() => copyToClipboard(msg.content, msg.id)}
                          style={{
                            background: 'transparent',
                            border: 'none',
                            color: 'var(--text-muted)',
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '4px',
                            fontSize: '0.75rem',
                          }}
                        >
                          {copiedMsgId === msg.id ? (
                            <>
                              <Check size={13} color="var(--success)" />
                              <span style={{ color: 'var(--success)' }}>Copied</span>
                            </>
                          ) : (
                            <>
                              <Copy size={13} />
                              <span>Copy Answer</span>
                            </>
                          )}
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              );
            })
          )}

          {isSending && (
            <div style={{ display: 'flex', gap: '12px', alignItems: 'center', alignSelf: 'flex-start' }} className="animate-fade-in">
              <div
                style={{
                  width: '34px',
                  height: '34px',
                  borderRadius: '50%',
                  background: 'var(--bg-secondary)',
                  border: '1px solid var(--border-color)',
                  color: 'var(--accent-primary)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Bot size={18} />
              </div>
              <div
                style={{
                  background: 'var(--bg-secondary)',
                  border: '1px solid var(--border-color)',
                  borderRadius: 'var(--radius-lg)',
                  padding: '14px 18px',
                  fontSize: '0.875rem',
                  color: 'var(--text-secondary)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                }}
              >
                <span className="badge badge-warning animate-pulse-glow">Searching vector embeddings & synthesizing answer...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar Area */}
        <div style={{ padding: '16px 24px', background: 'var(--bg-secondary)', borderTop: '1px solid var(--border-color)' }}>
          <form
            onSubmit={handleSendMessage}
            style={{
              display: 'flex',
              alignItems: 'flex-end',
              gap: '10px',
              background: 'var(--bg-input)',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius-lg)',
              padding: '8px 12px',
            }}
          >
            <textarea
              ref={textareaRef}
              rows={2}
              className="input-field"
              placeholder="Ask a question about your documents... (Enter to send, Shift+Enter for new line)"
              value={inputQuestion}
              onChange={(e) => setInputQuestion(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isSending}
              style={{
                border: 'none',
                background: 'transparent',
                resize: 'none',
                boxShadow: 'none',
                padding: '6px',
                fontSize: '0.925rem',
              }}
            />

            <button
              type="submit"
              disabled={isSending || !inputQuestion.trim()}
              className="btn-primary"
              style={{
                padding: '10px',
                borderRadius: 'var(--radius-md)',
                flexShrink: 0,
              }}
              title="Send Message"
            >
              <Send size={18} />
            </button>
          </form>
          <div style={{ fontSize: '0.725rem', color: 'var(--text-muted)', textAlign: 'center', marginTop: '6px' }}>
            Answers are grounded strictly in your document embeddings.
          </div>
        </div>
      </main>

      {/* Citation Modal Popup */}
      <CitationModal citation={activeCitation} onClose={() => setActiveCitation(null)} />
    </div>
  );
};
