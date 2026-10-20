import React, { useEffect, useState } from 'react';
import {
  User,
  Shield,
  Database,
  Layers,
  Sparkles,
  Moon,
  Sun,
  LogOut,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  Server
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import { healthApi, ReadyData } from '../api/healthApi';

export const SettingsPage: React.FC = () => {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();

  const [readyData, setReadyData] = useState<ReadyData | null>(null);
  const [loadingHealth, setLoadingHealth] = useState<boolean>(true);

  const fetchHealth = async () => {
    setLoadingHealth(true);
    try {
      const data = await healthApi.getReady();
      setReadyData(data);
    } catch (err) {
      console.error('Failed to probe /ready:', err);
    } finally {
      setLoadingHealth(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  return (
    <div style={{ padding: '32px 40px', maxWidth: '1000px', margin: '0 auto' }}>
      <div style={{ marginBottom: '32px' }}>
        <h1 style={{ fontSize: '1.85rem', fontWeight: 800 }}>Settings & Diagnostics</h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', marginTop: '4px' }}>
          Manage your account profile, appearance, and inspect backend AI pipeline readiness.
        </p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        {/* Account Profile Card */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
            <div
              style={{
                width: '40px',
                height: '40px',
                borderRadius: 'var(--radius-md)',
                background: 'rgba(99, 102, 241, 0.12)',
                color: 'var(--accent-primary)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <User size={22} />
            </div>
            <div>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Account Profile</h3>
              <p style={{ fontSize: '0.825rem', color: 'var(--text-muted)' }}>
                Your authenticated user identity and security scope
              </p>
            </div>
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '16px',
            }}
          >
            <div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
                Email Address
              </span>
              <div style={{ fontSize: '0.95rem', fontWeight: 600, marginTop: '2px' }}>
                {user?.email}
              </div>
            </div>

            <div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
                Full Name
              </span>
              <div style={{ fontSize: '0.95rem', fontWeight: 600, marginTop: '2px' }}>
                {user?.full_name || 'Not provided'}
              </div>
            </div>

            <div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
                User Identifier
              </span>
              <div style={{ fontSize: '0.85rem', fontFamily: 'monospace', color: 'var(--text-secondary)', marginTop: '2px' }}>
                {user?.id}
              </div>
            </div>

            <div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
                Member Since
              </span>
              <div style={{ fontSize: '0.95rem', fontWeight: 600, marginTop: '2px' }}>
                {user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
              </div>
            </div>
          </div>
        </div>

        {/* System & Architecture Diagnostics */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div
                style={{
                  width: '40px',
                  height: '40px',
                  borderRadius: 'var(--radius-md)',
                  background: 'rgba(16, 185, 129, 0.12)',
                  color: 'var(--success)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Server size={22} />
              </div>
              <div>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>AI & System Pipeline Readiness</h3>
                <p style={{ fontSize: '0.825rem', color: 'var(--text-muted)' }}>
                  Live operational diagnostic checks without secret exposure
                </p>
              </div>
            </div>

            <button onClick={fetchHealth} className="btn-secondary" style={{ padding: '6px 12px', fontSize: '0.8rem' }}>
              <RefreshCw size={14} className={loadingHealth ? 'animate-spin' : ''} />
              <span>Probe</span>
            </button>
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
              gap: '16px',
            }}
          >
            {/* Database Status */}
            <div
              style={{
                padding: '16px',
                borderRadius: 'var(--radius-md)',
                background: 'var(--bg-input)',
                border: '1px solid var(--border-color)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                <Database size={16} color="var(--accent-primary)" />
                <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>Database</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span
                  className={`badge ${
                    readyData?.database?.status === 'healthy' || readyData?.database?.status === 'degraded'
                      ? 'badge-success'
                      : 'badge-error'
                  }`}
                >
                  {readyData?.database?.status || 'Unknown'}
                </span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  ({readyData?.database?.mode})
                </span>
              </div>
            </div>

            {/* Vector Store */}
            <div
              style={{
                padding: '16px',
                borderRadius: 'var(--radius-md)',
                background: 'var(--bg-input)',
                border: '1px solid var(--border-color)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                <Layers size={16} color="#8B5CF6" />
                <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>Vector Store</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span className="badge badge-success">Active</span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  ({readyData?.vector_store?.type})
                </span>
              </div>
            </div>

            {/* Embedding Provider */}
            <div
              style={{
                padding: '16px',
                borderRadius: 'var(--radius-md)',
                background: 'var(--bg-input)',
                border: '1px solid var(--border-color)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                <Sparkles size={16} color="#EC4899" />
                <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>Embeddings</span>
              </div>
              <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                {readyData?.embedding_provider || 'Configured'}
              </div>
            </div>

            {/* LLM Status */}
            <div
              style={{
                padding: '16px',
                borderRadius: 'var(--radius-md)',
                background: 'var(--bg-input)',
                border: '1px solid var(--border-color)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                <Shield size={16} color="var(--warning)" />
                <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>OpenRouter LLM</span>
              </div>
              <div>
                <span
                  className={`badge ${
                    readyData?.llm_configured ? 'badge-success' : 'badge-warning'
                  }`}
                >
                  {readyData?.llm_configured ? 'API Key Configured' : 'Local Fallback / No Key'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Preferences & Appearance */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '16px' }}>
            Appearance & Preferences
          </h3>

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '14px 16px',
              borderRadius: 'var(--radius-md)',
              background: 'var(--bg-input)',
              border: '1px solid var(--border-color)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              {theme === 'dark' ? <Moon size={20} color="#6366F1" /> : <Sun size={20} color="#FBBF24" />}
              <div>
                <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>Interface Theme</div>
                <div style={{ fontSize: '0.775rem', color: 'var(--text-muted)' }}>
                  Currently using {theme === 'dark' ? 'Rich Dark' : 'Clean Light'} theme
                </div>
              </div>
            </div>

            <button onClick={toggleTheme} className="btn-secondary" style={{ fontSize: '0.85rem' }}>
              Switch to {theme === 'dark' ? 'Light' : 'Dark'}
            </button>
          </div>

          {/* Logout Section */}
          <div
            style={{
              marginTop: '24px',
              paddingTop: '20px',
              borderTop: '1px solid var(--border-color)',
              display: 'flex',
              justifyContent: 'flex-end',
            }}
          >
            <button onClick={logout} className="btn-danger" style={{ padding: '10px 18px' }}>
              <LogOut size={16} />
              <span>Log Out of Session</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
