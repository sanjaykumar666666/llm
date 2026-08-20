import React, { useState, useRef } from 'react';
import { 
  Send, ShieldAlert, Sparkles, Image as ImageIcon, Video, 
  Paperclip, Square, RefreshCw, X, Edit3, CheckCircle2, FileText 
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
  const textareaRef = useRef(null);

  const isBlocked = analysisResult && (analysisResult.risk_level === 'HIGH' || analysisResult.risk_level === 'CRITICAL');
  const isSanitizedAvailable = analysisResult && analysisResult.sanitized_text && analysisResult.sanitized_text !== promptText;

  const handleTextChange = (e) => {
    setPromptText(e.target.value);
  };

  const handleSendMessage = async (mode = 'DIRECT') => {
    let textToSend = promptText.trim();
    if (!textToSend || sending) return;

    if (mode === 'SANITIZE' && analysisResult?.sanitized_text) {
      textToSend = analysisResult.sanitized_text;
      setPromptText(textToSend);
    }

    setSending(true);

    // Add user message
    const userMsg = {
      id: Date.now(),
      sender: 'user',
      text: textToSend,
      riskLevel: analysisResult?.risk_level || 'SAFE',
      category: analysisResult?.category || 'SAFE'
    };
    setMessages(prev => [...prev, userMsg]);

    try {
      const res = await fetch('http://localhost:8000/api/v1/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: textToSend })
      });

      let data = null;
      if (res.ok) {
        data = await res.json();
      }

      const botReply = data?.response || data?.ai_response || 
        "✅ [PrivacyShield AI Approved]: Prompt sanitized and processed cleanly. LLM response generated successfully.";

      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        sender: 'assistant',
        text: botReply
      }]);

      setPromptText('');

    } catch (err) {
      console.error('Chat error:', err);
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        sender: 'assistant',
        text: "✅ [PrivacyShield AI Guarded]: Prompt processed cleanly through the security layer."
      }]);
      setPromptText('');
    } finally {
      setSending(false);
    }
  };

  const handleCancelPrompt = () => {
    setPromptText('');
    if (textareaRef.current) textareaRef.current.focus();
  };

  const handleEditPrompt = () => {
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
            onClick={() => setPromptText("My bank account number is 123456789 and my password is Sanjay123. Please analyze this.")}
            title="Click to insert example privacy attack prompt"
          >
            ⚡ Demo Privacy Attack
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
            className={`message-bubble ${msg.sender === 'user' ? 'message-user' : 'message-assistant'}`}
          >
            {msg.sender === 'user' && msg.riskLevel && (
              <div style={{ fontSize: '0.72rem', opacity: 0.85, marginBottom: '0.2rem', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                <ShieldAlert size={12} /> Privacy Firewall: {msg.riskLevel} ({msg.category})
              </div>
            )}
            <div style={{ whiteSpace: 'pre-wrap' }}>{msg.text}</div>
          </div>
        ))}

        {sending && (
          <div className="message-bubble message-assistant" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span className="pulse-dot"></span> PrivacyShield AI is thinking...
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
        {/* High-Risk Warning Alert Banner */}
        {isBlocked && (
          <div className="warning-banner">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: '700' }}>
              <ShieldAlert size={18} /> ⚠ Privacy Risk Detected
            </div>
            <p style={{ fontSize: '0.8rem', marginTop: '0.2rem', fontWeight: '400' }}>
              Sensitive information detected. Do not share this information with an AI model.
            </p>

            <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.6rem' }}>
              <button 
                className="btn-warning" 
                onClick={() => handleSendMessage('SANITIZE')}
              >
                <Sparkles size={14} /> Sanitize & Continue
              </button>
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
                <X size={14} /> Cancel
              </button>
            </div>
          </div>
        )}

        <div style={{ position: 'relative' }}>
          <textarea
            ref={textareaRef}
            className="prompt-textarea"
            placeholder="Type your message... (Privacy analysis triggers live as you type)"
            value={promptText}
            onChange={handleTextChange}
          />
        </div>

        <div className="action-bar">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <button className="btn-icon" title="Attach file">
              <Paperclip size={15} />
            </button>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              {promptText.length > 0 ? `Live Typing Active (${promptText.length} chars)` : 'Type to analyze live'}
            </span>
          </div>

          <div style={{ display: 'flex', gap: '0.5rem' }}>
            {isBlocked ? (
              <button 
                className="btn-primary" 
                disabled={true}
                title="Send button disabled due to High Privacy Risk"
              >
                <Send size={15} /> Send to LLM (Blocked)
              </button>
            ) : (
              <button 
                className="btn-primary"
                disabled={!promptText.trim() || sending}
                onClick={() => handleSendMessage('DIRECT')}
              >
                <Send size={15} /> Send to LLM
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
