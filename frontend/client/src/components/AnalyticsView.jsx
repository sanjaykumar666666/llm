import React from 'react';
import { BarChart3, ShieldCheck, ShieldAlert, AlertTriangle, CheckCircle, PieChart, Activity } from 'lucide-react';

export function AnalyticsView() {
  return (
    <div className="card" style={{ padding: '1.5rem', flex: 1, overflowY: 'auto', gap: '1.25rem' }}>
      <div style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: '0.75rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h2 style={{ fontSize: '1.2rem', fontWeight: '800', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <BarChart3 style={{ color: 'var(--accent-primary)' }} /> Analytics & Performance Dashboard
          </h2>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            Real-time telemetry, risk evaluation statistics, category breakdown, and model evaluation metrics.
          </p>
        </div>
        <span className="status-pill">
          <Activity size={12} /> Live Telemetry Online
        </span>
      </div>

      {/* Metric Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '0.85rem' }}>
        <div className="arch-box" style={{ background: 'var(--bg-input)' }}>
          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>TOTAL PROMPTS</span>
          <strong style={{ fontSize: '1.4rem', color: 'var(--text-primary)' }}>1,428</strong>
        </div>
        <div className="arch-box" style={{ background: 'var(--risk-safe-bg)', borderColor: 'var(--risk-safe-border)' }}>
          <span style={{ fontSize: '0.72rem', color: 'var(--risk-safe-text)' }}>SAFE PROMPTS</span>
          <strong style={{ fontSize: '1.4rem', color: 'var(--risk-safe-text)' }}>1,150</strong>
        </div>
        <div className="arch-box" style={{ background: 'var(--risk-medium-bg)', borderColor: 'var(--risk-medium-border)' }}>
          <span style={{ fontSize: '0.72rem', color: 'var(--risk-medium-text)' }}>RISKY PROMPTS</span>
          <strong style={{ fontSize: '1.4rem', color: 'var(--risk-medium-text)' }}>278</strong>
        </div>
        <div className="arch-box" style={{ background: 'var(--risk-high-bg)', borderColor: 'var(--risk-high-border)' }}>
          <span style={{ fontSize: '0.72rem', color: 'var(--risk-high-text)' }}>BLOCKED</span>
          <strong style={{ fontSize: '1.4rem', color: 'var(--risk-high-text)' }}>182</strong>
        </div>
        <div className="arch-box" style={{ background: 'var(--risk-low-bg)', borderColor: 'var(--risk-low-border)' }}>
          <span style={{ fontSize: '0.72rem', color: 'var(--risk-low-text)' }}>SANITIZED</span>
          <strong style={{ fontSize: '1.4rem', color: 'var(--risk-low-text)' }}>96</strong>
        </div>
      </div>

      {/* Category Distribution Breakdown */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
        <div style={{ background: 'var(--bg-input)', border: '1px solid var(--border-color)', borderRadius: '12px', padding: '1rem' }}>
          <div style={{ fontSize: '0.85rem', fontWeight: '700', color: 'var(--text-primary)', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <PieChart size={16} style={{ color: 'var(--accent-cyan)' }} /> Detected Risk Category Distribution
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', marginBottom: '0.2rem' }}>
                <span>Financial Data (Account/Card)</span>
                <strong>38% (105)</strong>
              </div>
              <div className="gauge-track"><div className="gauge-fill" style={{ width: '38%', background: '#f43f5e' }} /></div>
            </div>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', marginBottom: '0.2rem' }}>
                <span>PII (Email/Phone/Aadhaar)</span>
                <strong>32% (89)</strong>
              </div>
              <div className="gauge-track"><div className="gauge-fill" style={{ width: '32%', background: '#f59e0b' }} /></div>
            </div>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', marginBottom: '0.2rem' }}>
                <span>Credentials (Password/Token)</span>
                <strong>18% (50)</strong>
              </div>
              <div className="gauge-track"><div className="gauge-fill" style={{ width: '18%', background: '#a855f7' }} /></div>
            </div>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', marginBottom: '0.2rem' }}>
                <span>Healthcare & Medical Records</span>
                <strong>8% (22)</strong>
              </div>
              <div className="gauge-track"><div className="gauge-fill" style={{ width: '8%', background: '#06b6d4' }} /></div>
            </div>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', marginBottom: '0.2rem' }}>
                <span>Confidential Internal Specs</span>
                <strong>4% (12)</strong>
              </div>
              <div className="gauge-track"><div className="gauge-fill" style={{ width: '4%', background: '#6366f1' }} /></div>
            </div>
          </div>
        </div>

        {/* Model Evaluation Performance Metrics */}
        <div style={{ background: 'var(--bg-input)', border: '1px solid var(--border-color)', borderRadius: '12px', padding: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
            <div style={{ fontSize: '0.85rem', fontWeight: '700', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <ShieldCheck size={16} style={{ color: 'var(--risk-safe-text)' }} /> ML Model Evaluation Metrics
            </div>
            <span className="cat-tag" style={{ borderColor: 'var(--risk-medium-border)', color: 'var(--risk-medium-text)' }}>
              Demo Metrics
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.85rem' }}>
            <div className="arch-subbox" style={{ textAlign: 'center', padding: '0.85rem' }}>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>ACCURACY</span>
              <strong style={{ fontSize: '1.4rem', color: 'var(--risk-safe-text)' }}>94.2%</strong>
              <span style={{ fontSize: '0.68rem', color: 'var(--text-secondary)' }}>Overall classification accuracy</span>
            </div>
            <div className="arch-subbox" style={{ textAlign: 'center', padding: '0.85rem' }}>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>PRECISION</span>
              <strong style={{ fontSize: '1.4rem', color: 'var(--accent-cyan)' }}>92.5%</strong>
              <span style={{ fontSize: '0.68rem', color: 'var(--text-secondary)' }}>Low false positive rate</span>
            </div>
            <div className="arch-subbox" style={{ textAlign: 'center', padding: '0.85rem' }}>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>RECALL</span>
              <strong style={{ fontSize: '1.4rem', color: 'var(--accent-primary)' }}>95.1%</strong>
              <span style={{ fontSize: '0.68rem', color: 'var(--text-secondary)' }}>High risk catch rate</span>
            </div>
            <div className="arch-subbox" style={{ textAlign: 'center', padding: '0.85rem' }}>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>F1-SCORE</span>
              <strong style={{ fontSize: '1.4rem', color: '#a855f7' }}>93.8%</strong>
              <span style={{ fontSize: '0.68rem', color: 'var(--text-secondary)' }}>Harmonized mean precision/recall</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
