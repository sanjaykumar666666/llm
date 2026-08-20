import React from 'react';
import { BookOpen, Database, Sparkles, Cpu, Layers, ArrowRight, ShieldCheck, CheckCircle2 } from 'lucide-react';

export function ResearchDatasetsView() {
  return (
    <div className="card" style={{ padding: '1.5rem', flex: 1, overflowY: 'auto', gap: '1.25rem' }}>
      <div style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: '0.75rem' }}>
        <h2 style={{ fontSize: '1.2rem', fontWeight: '800', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <BookOpen style={{ color: 'var(--accent-cyan)' }} /> Research Methodology, Algorithms & Datasets
        </h2>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
          Academic documentation of algorithmic principles, problem statement, research gap, and cross-dataset semantic matching.
        </p>
      </div>

      {/* Problem & Research Gap */}
      <div style={{ background: 'var(--bg-input)', border: '1px solid var(--border-color)', borderRadius: '12px', padding: '1rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        <h3 style={{ fontSize: '0.95rem', fontWeight: '700', color: 'var(--text-primary)' }}>
          📌 Problem Statement & Research Gap
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', fontSize: '0.82rem' }}>
          <div style={{ background: 'var(--bg-card)', padding: '0.85rem', borderRadius: '8px', borderLeft: '3px solid var(--risk-high-text)' }}>
            <strong style={{ color: 'var(--risk-high-text)' }}>Problem:</strong>
            <p style={{ color: 'var(--text-secondary)', marginTop: '0.3rem' }}>
              Users frequently paste sensitive personal, financial, credentials, healthcare, or proprietary enterprise data into commercial LLM prompts without realizing the privacy and compliance risks.
            </p>
          </div>
          <div style={{ background: 'var(--bg-card)', padding: '0.85rem', borderRadius: '8px', borderLeft: '3px solid var(--accent-cyan)' }}>
            <strong style={{ color: 'var(--accent-cyan)' }}>Research Gap:</strong>
            <p style={{ color: 'var(--text-secondary)', marginTop: '0.3rem' }}>
              Existing approaches treat privacy detection, prompt injection scanning, and explainable AI as isolated post-hoc tasks. A lightweight pre-LLM real-time keystroke protection layer with automated sanitization is needed.
            </p>
          </div>
        </div>
      </div>

      {/* Algorithms & Methods Grid */}
      <div>
        <h3 style={{ fontSize: '0.95rem', fontWeight: '700', color: 'var(--text-primary)', marginBottom: '0.65rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <Cpu size={16} style={{ color: 'var(--accent-primary)' }} /> Core Algorithms & Methods
        </h3>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.75rem' }}>
          <div className="arch-subbox">
            <strong style={{ color: 'var(--accent-cyan)' }}>1. Tokenization</strong>
            <span style={{ fontWeight: '600', color: 'var(--text-primary)' }}>Role: Preprocessing & Span Mapping</span>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
              Splits text into tokens while retaining character index offsets to highlight exact PII entity locations.
            </p>
          </div>
          <div className="arch-subbox">
            <strong style={{ color: 'var(--accent-cyan)' }}>2. BERT Embeddings</strong>
            <span style={{ fontWeight: '600', color: 'var(--text-primary)' }}>Role: Contextual Feature Extraction</span>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
              Bidirectional encoder transformer generating 768-dimensional contextual vector representations.
            </p>
          </div>
          <div className="arch-subbox">
            <strong style={{ color: 'var(--accent-cyan)' }}>3. Naïve Bayes</strong>
            <span style={{ fontWeight: '600', color: 'var(--text-primary)' }}>Role: Probabilistic Classification</span>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
              Computes prior and posterior probabilities using Bayes' Theorem for fast, scalable PII likelihood scoring.
            </p>
          </div>
          <div className="arch-subbox">
            <strong style={{ color: 'var(--accent-cyan)' }}>4. Sentence-BERT (SBERT)</strong>
            <span style={{ fontWeight: '600', color: 'var(--text-primary)' }}>Role: Semantic Embeddings</span>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
              Siamese network mapping full sentences into semantically dense vector spaces for policy matching.
            </p>
          </div>
          <div className="arch-subbox">
            <strong style={{ color: 'var(--accent-cyan)' }}>5. Cosine Similarity</strong>
            <span style={{ fontWeight: '600', color: 'var(--text-primary)' }}>Role: Vector Distance Metric</span>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
              Calculates normalized dot product between prompt embeddings and enterprise privacy benchmarks.
            </p>
          </div>
          <div className="arch-subbox">
            <strong style={{ color: 'var(--accent-cyan)' }}>6. SHAP (Shapley Values)</strong>
            <span style={{ fontWeight: '600', color: 'var(--text-primary)' }}>Role: Explainable AI (XAI)</span>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
              Calculates game-theoretic token contribution weights to highlight risk words in red/orange heatmaps.
            </p>
          </div>
        </div>
      </div>

      {/* Dataset & Cross-Dataset SBERT Matching */}
      <div style={{ background: 'var(--bg-input)', border: '1px solid var(--border-color)', borderRadius: '12px', padding: '1rem' }}>
        <h3 style={{ fontSize: '0.95rem', fontWeight: '700', color: 'var(--text-primary)', marginBottom: '0.65rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <Database size={16} style={{ color: '#a855f7' }} /> Benchmark Datasets & SBERT Cosine Matching
        </h3>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.75rem', marginBottom: '1rem', fontSize: '0.78rem' }}>
          <div style={{ background: 'var(--bg-card)', padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
            <strong style={{ color: 'var(--accent-cyan)' }}>Dataset 1: Privacy Prompt DB</strong>
            <p style={{ color: 'var(--text-secondary)', marginTop: '0.2rem' }}>Contains prompt text, PII labels, and sensitive entity category annotations.</p>
          </div>
          <div style={{ background: 'var(--bg-card)', padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
            <strong style={{ color: 'var(--accent-cyan)' }}>Dataset 2: Injection Attack DB</strong>
            <p style={{ color: 'var(--text-secondary)', marginTop: '0.2rem' }}>Contains adversarial override patterns, jailbreaks, and injection directives.</p>
          </div>
          <div style={{ background: 'var(--bg-card)', padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
            <strong style={{ color: 'var(--accent-cyan)' }}>Dataset 3: Evaluation Benchmark</strong>
            <p style={{ color: 'var(--text-secondary)', marginTop: '0.2rem' }}>Contains actual ground truth vs predicted risk scores for metric validation.</p>
          </div>
        </div>

        {/* Cross-Dataset Visual Flow */}
        <div style={{ background: 'var(--bg-card)', padding: '0.85rem', borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'space-around', fontSize: '0.78rem', border: '1px dashed var(--border-color)' }}>
          <span style={{ fontWeight: '700', color: 'var(--accent-cyan)' }}>Dataset A + Dataset B</span>
          <ArrowRight size={16} />
          <span style={{ fontWeight: '700', color: '#a855f7' }}>SBERT Embeddings</span>
          <ArrowRight size={16} />
          <span style={{ fontWeight: '700', color: 'var(--risk-medium-text)' }}>Cosine Similarity</span>
          <ArrowRight size={16} />
          <span style={{ fontWeight: '700', color: 'var(--risk-safe-text)' }}>Semantic Policy Match</span>
        </div>
      </div>
    </div>
  );
}
