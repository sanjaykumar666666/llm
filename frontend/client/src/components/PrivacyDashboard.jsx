import React, { useState } from 'react';
import { 
  ShieldCheck, ShieldAlert, AlertTriangle, ChevronDown, ChevronUp, 
  Copy, Check, FileCode, Search, BarChart3, Sparkles, HelpCircle 
} from 'lucide-react';

export function PrivacyDashboard({ analysisResult }) {
  const [copied, setCopied] = useState(false);
  const [isExplainExpanded, setIsExplainExpanded] = useState(true);

  if (!analysisResult || !analysisResult.text) {
    return (
      <div className="card dashboard-card-fixed" style={{ flex: 1, justifyContent: 'center', alignItems: 'center', textAlign: 'center' }}>
        <div style={{ background: 'var(--risk-safe-bg)', padding: '1rem', borderRadius: '50%', border: '1px solid var(--risk-safe-border)', marginBottom: '0.75rem' }}>
          <ShieldCheck size={40} style={{ color: 'var(--risk-safe-text)' }} />
        </div>
        <h3 style={{ fontSize: '1.05rem', fontWeight: '700', color: 'var(--text-primary)' }}>
          LIVE PRIVACY ANALYSIS
        </h3>
        <div className="risk-badge risk-safe" style={{ marginTop: '0.5rem', marginBottom: '0.75rem' }}>
          <span className="pulse-dot"></span> SAFE
        </div>
        <div style={{ fontSize: '1.3rem', fontWeight: '800', color: 'var(--risk-safe-text)' }}>
          Risk Score: 0 / 100
        </div>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', maxWidth: '300px', marginTop: '0.5rem' }}>
          Type a message in the chat to see real-time privacy risk analysis update continuously as you type.
        </p>
      </div>
    );
  }

  const {
    text = '',
    risk_score = 0,
    risk_level = 'SAFE',
    category = 'SAFE',
    detected_categories = [],
    detected_entities = [],
    sanitized_text = '',
    decision = 'ALLOW',
    action = 'ALLOW',
    confidence = 0.98,
    explanation = 'No sensitive information detected.',
    shap = null,
    sbert = null
  } = analysisResult;

  const getRiskClass = (lvl) => {
    switch (lvl) {
      case 'HIGH':
      case 'CRITICAL': return 'risk-high';
      case 'MEDIUM': return 'risk-medium';
      case 'LOW': return 'risk-low';
      default: return 'risk-safe';
    }
  };

  const getGaugeColor = (score) => {
    if (score >= 75) return 'linear-gradient(90deg, #f59e0b, #f43f5e)';
    if (score >= 40) return 'linear-gradient(90deg, #22d3ee, #f59e0b)';
    if (score >= 15) return 'linear-gradient(90deg, #34d399, #22d3ee)';
    return 'linear-gradient(90deg, #10b981, #34d399)';
  };

  const handleCopySanitized = () => {
    navigator.clipboard.writeText(sanitized_text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="card dashboard-grid dashboard-card-fixed">
      {/* Panel Header */}
      <div style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: '0.6rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <h3 style={{ fontSize: '0.95rem', fontWeight: '700', letterSpacing: '0.04em', textTransform: 'uppercase', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <ShieldAlert size={18} style={{ color: 'var(--accent-cyan)' }} /> LIVE PRIVACY ANALYSIS
        </h3>
        <span className="pulse-dot" title="Live Keystroke Scanner Active"></span>
      </div>

      {/* 1. Risk Status Badge */}
      <div className={`risk-header-card ${getRiskClass(risk_level)}`}>
        <div>
          <div style={{ fontSize: '0.72rem', textTransform: 'uppercase', opacity: 0.85 }}>Risk Status</div>
          <div style={{ fontSize: '1.2rem', fontWeight: '800' }}>
            {risk_level} RISK
          </div>
        </div>
        <div className={`risk-badge ${getRiskClass(risk_level)}`}>
          {action}
        </div>
      </div>

      {/* 2. Risk Score & Confidence Meter */}
      <div className="gauge-container">
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', fontWeight: '700' }}>
          <span>Risk Score</span>
          <span style={{ color: risk_score >= 75 ? 'var(--risk-high-text)' : 'var(--text-primary)' }}>
            {risk_score} / 100
          </span>
        </div>
        <div className="gauge-track">
          <div 
            className="gauge-fill" 
            style={{ width: `${risk_score}%`, background: getGaugeColor(risk_score) }} 
          />
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
          <span>Detection Confidence: <strong>{Math.round(confidence * 100)}%</strong></span>
          <span>Action: <strong>{action}</strong></span>
        </div>
      </div>

      {/* 3. Detected Sensitive Information List */}
      <div>
        <div style={{ fontSize: '0.8rem', fontWeight: '700', color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>
          Detected Sensitive Information ({detected_entities.length})
        </div>
        
        {detected_entities.length === 0 ? (
          <div style={{ background: 'var(--risk-safe-bg)', border: '1px solid var(--risk-safe-border)', padding: '0.5rem 0.75rem', borderRadius: '8px', fontSize: '0.78rem', color: 'var(--risk-safe-text)' }}>
            ✓ No sensitive PII, credentials, or financial account numbers detected.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
            {detected_entities.map((ent, idx) => (
              <div 
                key={idx} 
                style={{ 
                  background: 'var(--bg-input)', 
                  border: '1px solid var(--border-color)',
                  borderLeft: '3px solid var(--risk-high-text)',
                  borderRadius: '6px', 
                  padding: '0.45rem 0.65rem', 
                  fontSize: '0.78rem',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between'
                }}
              >
                <div>
                  <span style={{ fontWeight: '700', color: 'var(--risk-high-text)' }}>{ent.category}:</span>{' '}
                  <span>{ent.entity_type}</span>
                </div>
                <code style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                  {ent.value_preview}
                </code>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 4. Sanitized Prompt Preview */}
      <div style={{ background: 'var(--bg-input)', border: '1px solid var(--border-color)', borderRadius: '10px', padding: '0.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.3rem' }}>
          <span style={{ fontSize: '0.8rem', fontWeight: '700', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
            <FileCode size={14} style={{ color: 'var(--accent-primary)' }} /> Sanitized Preview
          </span>
          <button 
            onClick={handleCopySanitized} 
            className="btn-icon" 
            style={{ padding: '0.2rem 0.45rem', fontSize: '0.72rem' }}
          >
            {copied ? <Check size={12} /> : <Copy size={12} />}
            {copied ? 'Copied' : 'Copy'}
          </button>
        </div>

        <div style={{ background: 'var(--bg-card)', padding: '0.5rem', borderRadius: '6px', fontSize: '0.78rem', fontFamily: 'var(--font-mono)', color: 'var(--risk-safe-text)', minHeight: '38px', wordBreak: 'break-word' }}>
          {sanitized_text || text || '(Empty)'}
        </div>
      </div>

      {/* 5. Expandable "Why is this risky?" Explainability Accordion */}
      <div style={{ border: '1px solid var(--border-color)', borderRadius: '10px', overflow: 'hidden' }}>
        <button 
          onClick={() => setIsExplainExpanded(!isExplainExpanded)}
          style={{
            width: '100%',
            background: 'var(--bg-input)',
            border: 'none',
            padding: '0.65rem 0.85rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            fontSize: '0.82rem',
            fontWeight: '700',
            color: 'var(--text-primary)',
            cursor: 'pointer'
          }}
        >
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <HelpCircle size={15} style={{ color: 'var(--accent-cyan)' }} /> Why is this risky?
          </span>
          {isExplainExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </button>

        {isExplainExpanded && (
          <div style={{ padding: '0.75rem', background: 'var(--bg-card)', display: 'flex', flexDirection: 'column', gap: '0.6rem', fontSize: '0.78rem' }}>
            <p style={{ color: 'var(--text-secondary)', lineHeight: '1.4' }}>
              {explanation}
            </p>

            {/* SHAP Token Risk Heatmap */}
            {shap && shap.token_attributions && (
              <div>
                <div style={{ fontWeight: '700', color: 'var(--text-primary)', marginBottom: '0.3rem', fontSize: '0.75rem' }}>
                  Token Risk Heatmap (SHAP Attribution)
                </div>
                <div className="shap-token-box">
                  {shap.token_attributions.map((tok, i) => (
                    <span 
                      key={i} 
                      className={`shap-token ${tok.is_risk_factor ? (tok.shap_value > 0.4 ? 'shap-risk-high' : 'shap-risk-medium') : 'shap-safe'}`}
                      title={`SHAP Weight: +${tok.shap_value}`}
                    >
                      {tok.token}{' '}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* SBERT Benchmark Match */}
            {sbert && (
              <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '0.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ color: 'var(--text-muted)' }}>SBERT Benchmark:</span>
                <span style={{ fontWeight: '700', color: 'var(--accent-cyan)' }}>
                  {sbert.highest_similarity_percentage}% Match
                </span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
