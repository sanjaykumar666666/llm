import React from 'react';
import { ShieldAlert, ShieldCheck, Search, Activity, Clock, Filter, Layers } from 'lucide-react';

export function PrivacyMonitorView({ analysisResult }) {
  const events = [
    {
      id: 'EVT-1092',
      timestamp: '12:49:15',
      modality: 'Text',
      promptPreview: 'My bank account number is 123456789 and my password is...',
      detected: ['Financial Information', 'Credentials', 'Account Number'],
      score: 100,
      action: 'BLOCK',
      confidence: '95%'
    },
    {
      id: 'EVT-1091',
      timestamp: '12:48:42',
      modality: 'Image OCR',
      promptPreview: 'OCR scan: DRIVER LICENSE ID: D9910482, DOB: 1992-05-14',
      detected: ['PII', 'Driver License ID', 'Address'],
      score: 85,
      action: 'BLOCK',
      confidence: '94%'
    },
    {
      id: 'EVT-1090',
      timestamp: '12:47:10',
      modality: 'Text',
      promptPreview: 'Hello, my email is student@university.edu',
      detected: ['PII', 'Email Address'],
      score: 20,
      action: 'ALLOW',
      confidence: '92%'
    },
    {
      id: 'EVT-1089',
      timestamp: '12:45:02',
      modality: 'Text',
      promptPreview: 'Explain the principles of quantum computing in simple terms',
      detected: [],
      score: 0,
      action: 'ALLOW',
      confidence: '98%'
    }
  ];

  return (
    <div className="card" style={{ padding: '1.5rem', flex: 1, overflowY: 'auto', gap: '1.25rem' }}>
      <div style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: '0.75rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h2 style={{ fontSize: '1.2rem', fontWeight: '800', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <ShieldAlert style={{ color: 'var(--risk-high-text)' }} /> Live Privacy Monitor & Firewall Telemetry
          </h2>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            Real-time audit log of continuous keystroke privacy evaluations, entity detections, and pre-LLM firewall decisions.
          </p>
        </div>
        <div className="status-pill">
          <span className="pulse-dot"></span> Firewall Stream Live
        </div>
      </div>

      {/* Active Analysis Event Card if present */}
      {analysisResult && analysisResult.text && (
        <div style={{ background: 'var(--bg-input)', border: '1px solid var(--border-active)', borderRadius: '12px', padding: '1rem' }}>
          <div style={{ fontSize: '0.78rem', fontWeight: '700', color: 'var(--accent-cyan)', marginBottom: '0.3rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <Activity size={14} /> ACTIVE REAL-TIME EVALUATION EVENT
          </div>
          <div style={{ fontSize: '0.9rem', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '0.4rem' }}>
            "{analysisResult.text}"
          </div>
          <div style={{ display: 'flex', gap: '1rem', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
            <span>Risk Score: <strong style={{ color: analysisResult.risk_score >= 65 ? 'var(--risk-high-text)' : 'var(--risk-safe-text)' }}>{analysisResult.risk_score}/100</strong></span>
            <span>Level: <strong>{analysisResult.risk_level}</strong></span>
            <span>Action: <strong>{analysisResult.action}</strong></span>
            <span>Confidence: <strong>{Math.round(analysisResult.confidence * 100)}%</strong></span>
          </div>
        </div>
      )}

      {/* Audit Log Table */}
      <div style={{ background: 'var(--bg-input)', border: '1px solid var(--border-color)', borderRadius: '12px', overflow: 'hidden' }}>
        <div style={{ padding: '0.75rem 1rem', borderBottom: '1px solid var(--border-color)', fontSize: '0.82rem', fontWeight: '700', color: 'var(--text-primary)' }}>
          Recent Keystroke Firewall Events
        </div>
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          {events.map((evt) => (
            <div 
              key={evt.id}
              style={{
                padding: '0.75rem 1rem',
                borderBottom: '1px solid var(--border-color)',
                display: 'grid',
                gridTemplateColumns: '90px 80px 1fr 180px 90px 70px',
                alignItems: 'center',
                gap: '0.75rem',
                fontSize: '0.8rem'
              }}
            >
              <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>{evt.id}</span>
              <span style={{ color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
                <Clock size={12} /> {evt.timestamp}
              </span>
              <span style={{ fontWeight: '500', color: 'var(--text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {evt.promptPreview}
              </span>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.2rem' }}>
                {evt.detected.length === 0 ? (
                  <span style={{ fontSize: '0.72rem', color: 'var(--risk-safe-text)' }}>Safe Query</span>
                ) : (
                  evt.detected.map((d, i) => (
                    <span key={i} className="cat-tag" style={{ fontSize: '0.68rem', padding: '0.1rem 0.35rem' }}>{d}</span>
                  ))
                )}
              </div>
              <span style={{ fontWeight: '700', color: evt.score >= 65 ? 'var(--risk-high-text)' : 'var(--risk-safe-text)' }}>
                {evt.score}/100
              </span>
              <span className={`risk-badge ${evt.action === 'BLOCK' ? 'risk-high' : 'risk-safe'}`} style={{ fontSize: '0.7rem', padding: '0.15rem 0.45rem' }}>
                {evt.action}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
