import React, { useState } from 'react';
import { X, Copy, Check, FileText, Bookmark } from 'lucide-react';
import { Citation } from '../types/conversation';

interface CitationModalProps {
  citation: Citation | null;
  onClose: () => void;
}

export const CitationModal: React.FC<CitationModalProps> = ({ citation, onClose }) => {
  const [copied, setCopied] = useState<boolean>(false);

  if (!citation) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(citation.excerpt);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0, 0, 0, 0.6)',
        backdropFilter: 'blur(8px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 100,
        padding: '20px',
      }}
      onClick={onClose}
    >
      <div
        className="glass-panel animate-fade-in"
        style={{
          width: '100%',
          maxWidth: '560px',
          maxHeight: '90vh',
          overflowY: 'auto',
          background: 'var(--bg-secondary)',
          border: '1px solid var(--border-color)',
          borderRadius: 'var(--radius-lg)',
          padding: 'clamp(16px, 4vw, 24px)',
          display: 'flex',
          flexDirection: 'column',
          gap: '16px',
          boxShadow: 'var(--shadow-lg)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                padding: '8px',
                borderRadius: 'var(--radius-md)',
                background: 'rgba(99, 102, 241, 0.15)',
                color: 'var(--accent-primary)',
                flexShrink: 0,
              }}
            >
              <Bookmark size={20} />
            </div>
            <div>
              <h3 style={{ fontSize: 'clamp(1rem, 3.5vw, 1.15rem)', fontWeight: 600 }}>Source Passage Citation</h3>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Verified document segment used in the generated answer
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-muted)',
              cursor: 'pointer',
              padding: '6px',
              borderRadius: 'var(--radius-sm)',
              flexShrink: 0,
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Metadata Badges */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', alignItems: 'center' }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '4px 10px',
              borderRadius: 'var(--radius-full)',
              background: 'var(--bg-input)',
              border: '1px solid var(--border-color)',
              fontSize: '0.8rem',
              fontWeight: 500,
              wordBreak: 'break-word',
              maxWidth: '100%',
            }}
          >
            <FileText size={14} color="var(--accent-primary)" style={{ flexShrink: 0 }} />
            <span style={{ overflow: 'hidden', textOverflow: 'ellipsis' }}>{citation.filename}</span>
          </div>

          <div
            className="badge badge-success"
            style={{ fontSize: '0.8rem', padding: '4px 10px' }}
          >
            Page {citation.page}
          </div>

          <div
            style={{
              fontSize: '0.75rem',
              color: 'var(--text-muted)',
              fontFamily: 'monospace',
              wordBreak: 'break-all',
            }}
          >
            Chunk: {citation.chunk_id}
          </div>
        </div>

        {/* Passage Content */}
        <div
          style={{
            background: 'var(--bg-input)',
            border: '1px solid var(--border-color)',
            borderRadius: 'var(--radius-md)',
            padding: '16px',
            fontSize: '0.9rem',
            lineHeight: '1.6',
            color: 'var(--text-primary)',
            maxHeight: 'min(40vh, 260px)',
            overflowY: 'auto',
            fontStyle: 'normal',
            wordBreak: 'break-word',
          }}
        >
          "{citation.excerpt}"
        </div>

        {/* Actions */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', flexWrap: 'wrap' }}>
          <button onClick={handleCopy} className="btn-secondary" style={{ fontSize: '0.85rem' }}>
            {copied ? <Check size={16} color="var(--success)" /> : <Copy size={16} />}
            <span>{copied ? 'Copied' : 'Copy Excerpt'}</span>
          </button>
          <button onClick={onClose} className="btn-primary" style={{ fontSize: '0.85rem' }}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
