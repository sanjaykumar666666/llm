import React from 'react';
import { Layers, ArrowRight, ArrowDown, Cpu, Sparkles, ShieldCheck, Database, FileText, Image, Video, CheckCircle } from 'lucide-react';

export function ArchitectureView() {
  return (
    <div className="card" style={{ padding: '1.5rem', flex: 1, overflowY: 'auto', gap: '1.25rem' }}>
      <div style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: '0.75rem' }}>
        <h2 style={{ fontSize: '1.2rem', fontWeight: '800', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Layers style={{ color: 'var(--accent-primary)' }} /> System Architecture & Multimodal Pipeline
        </h2>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
          Real-time pre-LLM security firewall layer with tokenization, BERT embeddings, Naïve Bayes classification, SBERT cosine matching, and SHAP explainability.
        </p>
      </div>

      {/* Visual Pipeline Diagram */}
      <div style={{ background: 'var(--bg-input)', border: '1px solid var(--border-color)', borderRadius: '14px', padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        
        {/* Step 1: Multimodal Input Layer */}
        <div>
          <div style={{ fontSize: '0.8rem', fontWeight: '700', color: 'var(--accent-cyan)', uppercase: 'true', letterSpacing: '0.05em', marginBottom: '0.6rem' }}>
            STEP 1: MULTIMODAL INPUT LAYER
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
            <div className="arch-box" style={{ borderColor: 'var(--accent-primary)' }}>
              <FileText size={20} style={{ color: 'var(--accent-primary)' }} />
              <strong>TEXT PROMPT</strong>
              <span>Keystroke text stream</span>
            </div>
            <div className="arch-box" style={{ borderColor: 'var(--accent-cyan)' }}>
              <Image size={20} style={{ color: 'var(--accent-cyan)' }} />
              <strong>IMAGE OCR</strong>
              <span>Document & ID scan</span>
            </div>
            <div className="arch-box" style={{ borderColor: '#a855f7' }}>
              <Video size={20} style={{ color: '#a855f7' }} />
              <strong>VIDEO KEYFRAMES</strong>
              <span>Timeline frame OCR</span>
            </div>
          </div>
        </div>

        <div style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
          <ArrowDown size={20} />
        </div>

        {/* Step 2: Preprocessing & OCR Layer */}
        <div>
          <div style={{ fontSize: '0.8rem', fontWeight: '700', color: 'var(--accent-cyan)', letterSpacing: '0.05em', marginBottom: '0.6rem' }}>
            STEP 2: PREPROCESSING & OCR EXTRACTION
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
            <div className="arch-subbox">
              <strong>Span Tokenization</strong>
              <span>Preserves character offsets</span>
            </div>
            <div className="arch-subbox">
              <strong>Tesseract OCR</strong>
              <span>Bounding box text scan</span>
            </div>
            <div className="arch-subbox">
              <strong>Keyframe Sampler</strong>
              <span>Interval frame scanner</span>
            </div>
          </div>
        </div>

        <div style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
          <ArrowDown size={20} />
        </div>

        {/* Step 3: Feature Extraction & Classification */}
        <div>
          <div style={{ fontSize: '0.8rem', fontWeight: '700', color: 'var(--accent-cyan)', letterSpacing: '0.05em', marginBottom: '0.6rem' }}>
            STEP 3: FEATURE EXTRACTION & ML CLASSIFICATION
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
            <div className="arch-box" style={{ borderColor: 'var(--accent-cyan)' }}>
              <Cpu size={20} style={{ color: 'var(--accent-cyan)' }} />
              <strong>BERT Embeddings</strong>
              <span>768-dim contextual vector</span>
            </div>
            <div className="arch-box" style={{ borderColor: 'var(--risk-medium-text)' }}>
              <Database size={20} style={{ color: 'var(--risk-medium-text)' }} />
              <strong>Naïve Bayes</strong>
              <span>Bayesian PII probability</span>
            </div>
            <div className="arch-box" style={{ borderColor: '#a855f7' }}>
              <Sparkles size={20} style={{ color: '#a855f7' }} />
              <strong>SBERT Cosine Match</strong>
              <span>Policy benchmark similarity</span>
            </div>
          </div>
        </div>

        <div style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
          <ArrowDown size={20} />
        </div>

        {/* Step 4: Unified Privacy Risk Engine */}
        <div style={{ background: 'var(--bg-card)', border: '2px solid var(--accent-primary)', borderRadius: '12px', padding: '1.1rem', textAlign: 'center' }}>
          <div style={{ fontSize: '1rem', fontWeight: '800', color: 'var(--accent-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
            <ShieldCheck size={22} /> UNIFIED PRIVACY RISK ENGINE
          </div>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginTop: '0.3rem' }}>
            Combines ensemble ML scores, entity severity weights, and Shannon entropy into a 0–100 Risk Score.
          </p>
        </div>

        <div style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
          <ArrowDown size={20} />
        </div>

        {/* Step 5: SHAP Explainability & Decision Engine */}
        <div>
          <div style={{ fontSize: '0.8rem', fontWeight: '700', color: 'var(--accent-cyan)', letterSpacing: '0.05em', marginBottom: '0.6rem' }}>
            STEP 5: SHAP EXPLAINABILITY & DECISION GATE
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div className="arch-box" style={{ borderColor: 'var(--risk-medium-text)' }}>
              <strong>SHAP / LIME Attribution</strong>
              <span>Word-level risk token heatmaps</span>
            </div>
            <div className="arch-box" style={{ borderColor: 'var(--risk-safe-text)' }}>
              <strong>Decision Engine</strong>
              <span>ALLOW / WARN / SANITIZE / BLOCK</span>
            </div>
          </div>
        </div>

        <div style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
          <ArrowDown size={20} />
        </div>

        {/* Final Step: LLM Application */}
        <div style={{ background: 'var(--risk-safe-bg)', border: '1px solid var(--risk-safe-border)', borderRadius: '10px', padding: '0.85rem', textAlign: 'center', color: 'var(--risk-safe-text)', fontWeight: '700' }}>
          ✓ SAFE PROMPT FORWARDED TO LLM GATEWAY (GEMINI / LOCAL SYNTHESIS)
        </div>
      </div>
    </div>
  );
}
