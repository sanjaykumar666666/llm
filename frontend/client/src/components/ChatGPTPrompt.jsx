import React, { useState, useRef } from 'react';
import { 
  Send, ShieldAlert, Sparkles, Image as ImageIcon, Video, 
  Paperclip, Square, RefreshCw, X, Edit3, CheckCircle2, FileText, AlertTriangle, ShieldCheck 
} from 'lucide-react';
import { MultimodalUpload } from './MultimodalUpload';

export function ChatGPTPrompt({ 
  promptText, 
  setPromptText, 
  analysisResult, 
  messages, 
  setMessages,
  activeChatTitle 
}) {
  const [activeTab, setActiveTab] = useState('text'); // 'text' | 'image' | 'video'
  const [sending, setSending] = useState(false);
  const [pendingConfirmation, setPendingConfirmation] = useState(false);
  const textareaRef = useRef(null);

  // Credential & Secret Block Detection (Distinct from Personal Context)
  const isCredentialBlocked = analysisResult && (
    analysisResult.decision === 'BLOCK' ||
    analysisResult.has_critical_secret === true ||
    ['Password / Credential', 'API Key / Token', 'SECRET_DETECTED', 'PROMPT_INJECTION'].includes(analysisResult.category)
  );

  // Highly Personal Context Detection (Three-Level Model)
  const isHighlyPersonal = analysisResult && !isCredentialBlocked && (
    analysisResult.personal_context_level === 'HIGH_RISK' ||
    analysisResult.requires_user_confirmation === true ||
    ['Highly Personal Context', 'HIGHLY_PERSONAL_CONTEXT'].includes(analysisResult.category)
  );

  const isMildPersonal = analysisResult && !isCredentialBlocked && !isHighlyPersonal && (
    analysisResult.personal_context_level === 'WARNING' ||
    analysisResult.category === 'Personal Context'
  );

  const isSanitizedAvailable = analysisResult && analysisResult.sanitized_text && analysisResult.sanitized_text !== promptText && !isHighlyPersonal;

  const handleTextChange = (e) => {
    setPromptText(e.target.value);
    if (pendingConfirmation) {
      setPendingConfirmation(false);
    }
  };

  const handleSendMessage = async (mode = 'DIRECT') => {
    let textToSend = promptText.trim();
    if (!textToSend || sending) return;

    if (mode === 'SANITIZE' && analysisResult?.sanitized_text) {
      textToSend = analysisResult.sanitized_text;
    }

    // If highly personal and not explicitly confirmed yet, prompt confirmation first
    if (isHighlyPersonal && mode === 'DIRECT') {
      setPendingConfirmation(true);
      return;
    }

    const confirmedByUser = mode === 'CONFIRMED_CONTINUE';
    setSending(true);

    try {
      const res = await fetch('http://localhost:8000/api/v1/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          prompt: textToSend,
          confirmed_by_user: confirmedByUser
        })
      });

      if (!res.ok) {
        // Backend returned HTTP error -> Preserve input for retry, do NOT clear, do NOT call LLM
        setMessages(prev => [...prev, {
          id: Date.now(),
          sender: 'system',
          type: 'error',
          text: `⚠️ [Service Notice]: Backend security service returned status ${res.status}. Your message was not sent.`
        }]);
        return;
      }

      const data = await res.json();
      const decision = data.decision || 'ALLOW';

      if (decision === 'HIGH_PRIVACY_WARNING' || data.action === 'CONFIRMATION_REQUIRED') {
        // High personal context intercepted at backend before user confirmation
        setPendingConfirmation(true);
        return;
      }

      if (decision === 'BLOCK') {
        // 🔒 CREDENTIAL BLOCK BEHAVIOR:
        // 1. Immediately CLEAR input field
        setPromptText('');
        setPendingConfirmation(false);

        // 2. DO NOT add original message containing sensitive credentials to chat history
        // 3. Add only a safe security event (no private credentials logged)
        const blockReason = data.reason || "Credential / sensitive security information was detected.";
        setMessages(prev => [...prev, {
          id: Date.now(),
          sender: 'system',
          type: 'blocked',
          text: `🔒 Sensitive credentials blocked: ${blockReason} Your message was not sent to the AI.`,
          riskLevel: 'BLOCK',
          category: data.category || 'BLOCKED'
        }]);
      } else if (decision === 'WARN' || decision === 'SANITIZE') {
        // 🛡️ WARN / SANITIZE BEHAVIOR:
        setPromptText('');
        setPendingConfirmation(false);

        const sanitizedText = data.sanitized_prompt || data.masked_prompt || textToSend;

        setMessages(prev => [
          ...prev,
          {
            id: Date.now(),
            sender: 'user',
            text: sanitizedText,
            riskLevel: data.personal_context_level === 'HIGH_RISK' ? 'PERSONAL_CONTEXT' : 'SANITIZE',
            category: data.category || 'PRIVACY_WARNING'
          },
          {
            id: Date.now() + 1,
            sender: 'assistant',
            text: data.response || data.response_text || "Prompt processed with privacy protections."
          }
        ]);
      } else {
        // ✅ ALLOW BEHAVIOR:
        setPromptText('');
        setPendingConfirmation(false);

        setMessages(prev => [
          ...prev,
          {
            id: Date.now(),
            sender: 'user',
            text: textToSend,
            riskLevel: 'SAFE',
            category: 'SAFE'
          },
          {
            id: Date.now() + 1,
            sender: 'assistant',
            text: data.response || data.response_text || ""
          }
        ]);
      }
    } catch (err) {
      console.error('Chat error:', err);
      setMessages(prev => [...prev, {
        id: Date.now(),
        sender: 'system',
        type: 'error',
        text: "⚠️ [Connection Error]: Unable to reach backend security service. Please ensure the backend server is running and try again."
      }]);
    } finally {
      setSending(false);
      if (textareaRef.current) textareaRef.current.focus();
    }
  };

  const handleCancelPrompt = () => {
    setPromptText('');
    setPendingConfirmation(false);
    if (textareaRef.current) textareaRef.current.focus();
  };

  const handleEditPrompt = () => {
    setPendingConfirmation(false);
    if (textareaRef.current) textareaRef.current.focus();
  };

  return (
    <div className="card chat-container">
      {/* Top Bar showing active conversation topic & modality tabs */}
      <div className="chat-top-bar">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <div style={{ fontWeight: '600', fontSize: '0.95rem', color: 'var(--text-primary)' }}>
            {activeChatTitle || 'New Conversation'}
          </div>
          <button 
            className="btn-demo-attack"
            onClick={() => setPromptText("My database password is Super123! Please analyze this.")}
            title="Click to insert example credential attack prompt"
          >
            ⚡ Demo Credential Block
          </button>
          <button 
            className="btn-demo-attack"
            style={{ background: 'rgba(239, 68, 68, 0.15)', borderColor: '#ef4444', color: '#fca5a5' }}
            onClick={() => setPromptText("I want to tell you everything that happened in my five-year relationship, including private events involving my partner and family.")}
            title="Click to insert example highly personal context prompt"
          >
            🔴 Demo Personal Context
          </button>
        </div>

        <div className="tab-row" style={{ borderBottom: 'none', paddingBottom: 0 }}>
          <button 
            className={`tab-btn ${activeTab === 'text' ? 'active' : ''}`}
            onClick={() => setActiveTab('text')}
          >
            <FileText size={14} /> Text
          </button>
          <button 
            className={`tab-btn ${activeTab === 'image' ? 'active' : ''}`}
            onClick={() => setActiveTab('image')}
          >
            <ImageIcon size={14} /> Image OCR
          </button>
          <button 
            className={`tab-btn ${activeTab === 'video' ? 'active' : ''}`}
            onClick={() => setActiveTab('video')}
          >
            <Video size={14} /> Video OCR
          </button>
        </div>
      </div>

      {/* Messages Thread */}
      <div className="messages-area">
        {messages.map(msg => (
          <div 
            key={msg.id} 
            className={`message-bubble ${
              msg.sender === 'user' 
                ? 'message-user' 
                : msg.sender === 'system' 
                  ? (msg.type === 'error' ? 'message-system-error' : 'message-system') 
                  : 'message-assistant'
            }`}
          >
            {msg.sender === 'user' && msg.riskLevel && msg.riskLevel !== 'SAFE' && (
              <div style={{ fontSize: '0.72rem', opacity: 0.85, marginBottom: '0.2rem', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                <ShieldAlert size={12} /> Privacy Firewall: {msg.riskLevel} ({msg.category})
              </div>
            )}
            {msg.sender === 'system' && (
              <div style={{ 
                fontSize: '0.72rem', 
                fontWeight: '700', 
                marginBottom: '0.25rem', 
                display: 'flex', 
                alignItems: 'center', 
                gap: '0.35rem', 
                color: msg.type === 'error' ? '#f59e0b' : '#ef4444' 
              }}>
                {msg.type === 'error' ? <AlertTriangle size={13} /> : <ShieldAlert size={13} />}
                {msg.type === 'error' ? 'SYSTEM NOTICE' : 'SECURITY FIREWALL'}
              </div>
            )}
            <div style={{ whiteSpace: 'pre-wrap' }}>{msg.text}</div>
          </div>
        ))}

        {sending && (
          <div className="message-bubble message-assistant" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span className="pulse-dot"></span> PrivacyShield AI is analyzing security & generating response...
            <button 
              onClick={() => setSending(false)} 
              className="btn-icon" 
              style={{ padding: '0.15rem 0.4rem', fontSize: '0.72rem', marginLeft: '0.5rem' }}
            >
              <Square size={10} /> Stop
            </button>
          </div>
        )}
      </div>

      {/* Multimodal Upload Tab */}
      {activeTab !== 'text' && (
        <MultimodalUpload 
          modality={activeTab} 
          onOcrExtracted={(ocrText) => setPromptText(ocrText)} 
        />
      )}

      {/* Input Area */}
      <div className="input-container">
        {/* Credential Hard-Block Alert Banner */}
        {isCredentialBlocked && (
          <div className="warning-banner" style={{ background: 'rgba(239, 68, 68, 0.15)', borderColor: '#ef4444' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: '700', color: '#fca5a5' }}>
              <ShieldAlert size={18} color="#ef4444" /> 🔒 Authentication Credential / Secret Detected
            </div>
            <p style={{ fontSize: '0.8rem', marginTop: '0.2rem', color: '#e2e8f0' }}>
              Passphrase, API key, or authentication credential detected. High-security credentials are automatically blocked.
            </p>

            <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.6rem' }}>
              <button 
                className="btn-icon"
                onClick={handleEditPrompt}
              >
                <Edit3 size={14} /> Edit Prompt
              </button>
              <button 
                className="btn-icon"
                onClick={handleCancelPrompt}
              >
                <X size={14} /> Clear
              </button>
            </div>
          </div>
        )}

        {/* Highly Personal Information Confirmation Banner (Pipeline 2 Three-Level Guardrail) */}
        {(isHighlyPersonal || pendingConfirmation) && !isCredentialBlocked && (
          <div className="warning-banner" style={{ background: 'rgba(244, 63, 94, 0.12)', borderColor: '#f43f5e' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: '700', color: '#fda4af' }}>
              <ShieldAlert size={18} color="#f43f5e" /> 🔴 Highly Personal Information Detected
            </div>
            <p style={{ fontSize: '0.85rem', marginTop: '0.25rem', color: '#f1f5f9', fontWeight: '500' }}>
              Your message appears to contain detailed personal information.
            </p>
            <p style={{ fontSize: '0.8rem', marginTop: '0.2rem', color: '#94a3b8' }}>
              This message may contain highly personal information. Consider removing details that you do not want to share with an AI system.
            </p>

            {/* Factual Trust Indicators */}
            <div style={{ 
              background: 'rgba(0, 0, 0, 0.25)', 
              border: '1px solid rgba(244, 63, 94, 0.3)', 
              borderRadius: '6px', 
              padding: '0.5rem 0.75rem', 
              marginTop: '0.5rem', 
              fontSize: '0.78rem',
              color: '#f1f5f9'
            }}>
              <div style={{ fontWeight: '600', marginBottom: '0.25rem', display: 'flex', alignItems: 'center', gap: '0.35rem', color: '#fda4af' }}>
                <ShieldCheck size={14} /> 🛡️ Privacy Guard Active
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
                <div>✓ AI has not received this message yet.</div>
                <div>✓ You can review and edit it.</div>
                <div>✓ You decide whether to continue.</div>
              </div>
            </div>

            {/* Explicit Confirmation Action Buttons */}
            <div style={{ display: 'flex', gap: '0.6rem', marginTop: '0.7rem' }}>
              <button 
                className="btn-icon"
                style={{ background: 'rgba(255, 255, 255, 0.12)', color: '#fff', padding: '0.4rem 0.8rem', fontWeight: '600' }}
                onClick={handleEditPrompt}
              >
                <Edit3 size={14} /> Review & Edit
              </button>
              <button 
                className="btn-warning"
                style={{ background: '#f43f5e', borderColor: '#e11d48', color: '#fff', padding: '0.4rem 0.85rem', fontWeight: '600' }}
                onClick={() => handleSendMessage('CONFIRMED_CONTINUE')}
              >
                <Send size={14} /> Continue Anyway
              </button>
              <button 
                className="btn-icon"
                onClick={handleCancelPrompt}
              >
                <X size={14} /> Cancel
              </button>
            </div>
          </div>
        )}

        {/* Mild Personal Information Warning Notice */}
        {isMildPersonal && !isHighlyPersonal && !pendingConfirmation && (
          <div className="warning-banner" style={{ background: 'rgba(245, 158, 11, 0.1)', borderColor: 'rgba(245, 158, 11, 0.35)', padding: '0.5rem 0.8rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', fontSize: '0.82rem', fontWeight: '600', color: '#fde68a' }}>
              <AlertTriangle size={15} color="#f59e0b" /> 🟡 Personal information may be present
            </div>
            <p style={{ fontSize: '0.75rem', marginTop: '0.15rem', color: '#cbd5e1' }}>
              Some personal context is being shared. Safe to send, or edit if you prefer not to disclose.
            </p>
          </div>
        )}

        <div style={{ position: 'relative' }}>
          <textarea
            ref={textareaRef}
            className="prompt-textarea"
            placeholder="Type your message... (Privacy analysis triggers live as you type)"
            value={promptText}
            onChange={handleTextChange}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage('DIRECT');
              }
            }}
          />
        </div>

        <div className="action-bar">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <button className="btn-icon" title="Attach file">
              <Paperclip size={15} />
            </button>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              {isCredentialBlocked
                ? "🔴 Credential Detected (Auto-Block)"
                : isHighlyPersonal
                  ? "🔴 Highly personal information detected"
                  : isMildPersonal
                    ? "🟡 Personal information may be present"
                    : promptText.length > 0 
                      ? `🛡️ Privacy Guard Active (${promptText.length} chars)` 
                      : '🛡️ Privacy Guard Active'}
            </span>
          </div>

          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button 
              className="btn-primary"
              disabled={!promptText.trim() || sending}
              onClick={() => handleSendMessage('DIRECT')}
              title={
                isCredentialBlocked
                  ? "Submit to Privacy Firewall (Will be blocked & cleared)"
                  : isHighlyPersonal
                    ? "Review & Confirm before sending to LLM"
                    : "Send to LLM"
              }
            >
              <Send size={15} /> {
                isCredentialBlocked
                  ? "Send (Firewall Active)"
                  : isHighlyPersonal
                    ? "Review & Send"
                    : "Send to LLM"
              }
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

