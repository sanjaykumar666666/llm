import React from 'react';
import { X, ShieldAlert, Cpu, Sparkles, Lock, ArrowRight, Layers } from 'lucide-react';

export function AboutProjectModal({ isOpen, onClose }) {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--border-color)', paddingBottom: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <div className="brand-logo" style={{ width: '32px', height: '32px' }}>
              <ShieldAlert size={18} />
            </div>
            <div>
              <h2 style={{ fontSize: '1.1rem', fontWeight: '700', color: 'var(--text-primary)' }}>
                About Project
              </h2>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                Academic Research & Development Prototype
              </p>
            </div>
          </div>
          <button onClick={onClose} className="btn-icon" style={{ padding: '0.35rem' }}>
            <X size={18} />
          </button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div>
            <h3 style={{ fontSize: '0.95rem', fontWeight: '700', color: 'var(--accent-cyan)', marginBottom: '0.3rem' }}>
              Project Title:
            </h3>
            <p style={{ fontSize: '0.9rem', fontWeight: '600', color: 'var(--text-primary)', background: 'var(--bg-input)', padding: '0.6rem 0.85rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
              “AI-Powered Multimodal Privacy Risk Detection and Protection System for LLM-Based Applications”
            </p>
          </div>

          <div style={{ background: 'var(--risk-safe-bg)', border: '1px solid var(--risk-safe-border)', padding: '0.85rem', borderRadius: '10px', color: 'var(--risk-safe-text)', fontSize: '0.88rem', lineHeight: '1.5' }}>
            <strong style={{ display: 'block', marginBottom: '0.2rem' }}>Core Mission:</strong>
            “This system provides a privacy protection layer before user inputs are processed by an LLM. It detects privacy-sensitive information in real time and can block or sanitize risky inputs.”
          </div>

          <div>
            <h4 style={{ fontSize: '0.85rem', fontWeight: '700', color: 'var(--text-primary)', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <Layers size={16} style={{ color: 'var(--accent-primary)' }} /> Pipeline Architecture & Model Flow
            </h4>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.6rem' }}>
              <div style={{ background: 'var(--bg-input)', padding: '0.6rem', borderRadius: '8px', fontSize: '0.78rem' }}>
                <strong style={{ color: 'var(--accent-cyan)' }}>1. Tokenization & OCR</strong>
                <p style={{ color: 'var(--text-secondary)', marginTop: '0.2rem' }}>Extracts text tokens from raw prompt, uploaded images, or video frames.</p>
              </div>
              <div style={{ background: 'var(--bg-input)', padding: '0.6rem', borderRadius: '8px', fontSize: '0.78rem' }}>
                <strong style={{ color: 'var(--accent-cyan)' }}>2. BERT Feature Extraction</strong>
                <p style={{ color: 'var(--text-secondary)', marginTop: '0.2rem' }}>Generates 768-dim contextual semantic representations of prompt text.</p>
              </div>
              <div style={{ background: 'var(--bg-input)', padding: '0.6rem', borderRadius: '8px', fontSize: '0.78rem' }}>
                <strong style={{ color: 'var(--accent-cyan)' }}>3. Naive Bayes Classifier</strong>
                <p style={{ color: 'var(--text-secondary)', marginTop: '0.2rem' }}>Computes probabilistic likelihood scores for PII & credentials.</p>
              </div>
              <div style={{ background: 'var(--bg-input)', padding: '0.6rem', borderRadius: '8px', fontSize: '0.78rem' }}>
                <strong style={{ color: 'var(--accent-cyan)' }}>4. SBERT & Cosine Similarity</strong>
                <p style={{ color: 'var(--text-secondary)', marginTop: '0.2rem' }}>Evaluates semantic distance against enterprise policy DB.</p>
              </div>
              <div style={{ background: 'var(--bg-input)', padding: '0.6rem', borderRadius: '8px', fontSize: '0.78rem' }}>
                <strong style={{ color: 'var(--accent-cyan)' }}>5. SHAP Explainability</strong>
                <p style={{ color: 'var(--text-secondary)', marginTop: '0.2rem' }}>Calculates Shapley values to highlight high-risk word tokens.</p>
              </div>
              <div style={{ background: 'var(--bg-input)', padding: '0.6rem', borderRadius: '8px', fontSize: '0.78rem' }}>
                <strong style={{ color: 'var(--accent-cyan)' }}>6. Decision Gate</strong>
                <p style={{ color: 'var(--text-secondary)', marginTop: '0.2rem' }}>Enforces Allow, Block, or Sanitize before LLM execution.</p>
              </div>
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', borderTop: '1px solid var(--border-color)', paddingTop: '1rem' }}>
          <button onClick={onClose} className="btn-primary">
            Close & Return to Application
          </button>
        </div>
      </div>
    </div>
  );
}
