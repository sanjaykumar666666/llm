import React from 'react';
import { ShieldAlert, Info, Sun, Moon, Sparkles, Cpu } from 'lucide-react';

export function Header({ theme, toggleTheme, onOpenAbout }) {
  return (
    <header className="app-header">
      <div className="brand-section">
        <div className="brand-logo">
          <ShieldAlert size={22} />
        </div>
        <div>
          <h1 className="brand-title">AIERA Shield Firewall</h1>
          <p className="brand-subtitle">
            AI-Powered Multimodal Privacy Risk Detection & Protection System
          </p>
        </div>
      </div>

      <div className="header-badges">
        <div className="status-pill">
          <span className="pulse-dot"></span>
          Real-Time Keystroke Firewall
        </div>

        <div style={{ display: 'flex', gap: '0.4rem' }}>
          <span className="cat-tag" style={{ display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
            <Cpu size={12} /> BERT + Naive Bayes
          </span>
          <span className="cat-tag" style={{ display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
            <Sparkles size={12} /> SBERT + Cosine
          </span>
        </div>

        <button onClick={onOpenAbout} className="btn-icon">
          <Info size={16} />
          About Project
        </button>

        <button onClick={toggleTheme} className="btn-icon">
          {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
          {theme === 'dark' ? 'Light Mode' : 'Dark Mode'}
        </button>
      </div>
    </header>
  );
}
