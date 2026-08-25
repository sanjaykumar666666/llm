import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { ChatGPTPrompt } from './components/ChatGPTPrompt';
import { PrivacyDashboard } from './components/PrivacyDashboard';
import { ArchitectureView } from './components/ArchitectureView';
import { AnalyticsView } from './components/AnalyticsView';
import { ResearchDatasetsView } from './components/ResearchDatasetsView';
import { PrivacyMonitorView } from './components/PrivacyMonitorView';
import { AboutProjectModal } from './components/AboutProjectModal';
import './index.css';

export function App() {
  const [theme, setTheme] = useState('dark');
  const [activeView, setActiveView] = useState('chat'); // 'chat' | 'monitor' | 'analytics' | 'architecture' | 'research'
  const [promptText, setPromptText] = useState('');
  const [analysisResult, setAnalysisResult] = useState(null);
  const [isAboutOpen, setIsAboutOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // Conversation Sessions State
  const [chats, setChats] = useState([
    {
      id: 'chat-1',
      title: 'General AI Privacy Query',
      date: 'Today',
      messages: [
        {
          id: 1,
          sender: 'assistant',
          text: "Hello! I am PrivacyShield AI. Ask me any question while the Live Keystroke Privacy Firewall guards your inputs."
        }
      ]
    },
    {
      id: 'chat-2',
      title: 'Bank Statement Analysis',
      date: 'Yesterday',
      messages: [
        {
          id: 101,
          sender: 'assistant',
          text: "Welcome! Drop or type your document text below for real-time PII & financial scanning."
        }
      ]
    }
  ]);

  const [activeChatId, setActiveChatId] = useState('chat-1');

  // Active chat session helper
  const activeChat = chats.find(c => c.id === activeChatId) || chats[0];

  const handleSelectChat = (id) => {
    setActiveChatId(id);
    setPromptText('');
  };

  const handleNewChat = () => {
    const newId = `chat-${Date.now()}`;
    const newSession = {
      id: newId,
      title: `Conversation ${chats.length + 1}`,
      date: 'Just Now',
      messages: [
        {
          id: Date.now(),
          sender: 'assistant',
          text: "Hello! I am PrivacyShield AI. Type any message to see real-time privacy analysis active."
        }
      ]
    };
    setChats(prev => [newSession, ...prev]);
    setActiveChatId(newId);
    setActiveView('chat');
    setPromptText('');
  };

  const handleDeleteChat = (id) => {
    if (chats.length <= 1) return;
    const updated = chats.filter(c => c.id !== id);
    setChats(updated);
    if (activeChatId === id) {
      setActiveChatId(updated[0].id);
    }
  };

  const handleClearAllChats = () => {
    const freshId = `chat-${Date.now()}`;
    setChats([
      {
        id: freshId,
        title: 'New Conversation',
        date: 'Just Now',
        messages: [
          {
            id: Date.now(),
            sender: 'assistant',
            text: "All chat conversations cleared. PrivacyShield AI is ready."
          }
        ]
      }
    ]);
    setActiveChatId(freshId);
    setPromptText('');
  };

  const setMessagesForActiveChat = (updateFn) => {
    setChats(prev => prev.map(chat => {
      if (chat.id === activeChatId) {
        const nextMsgs = typeof updateFn === 'function' ? updateFn(chat.messages) : updateFn;
        let title = chat.title;
        if (chat.title.startsWith('Conversation') || chat.title === 'New Conversation') {
          const firstUserMsg = nextMsgs.find(m => m.sender === 'user');
          if (firstUserMsg) {
            title = firstUserMsg.text.slice(0, 28) + (firstUserMsg.text.length > 28 ? '...' : '');
          }
        }
        return { ...chat, title, messages: nextMsgs };
      }
      return chat;
    }));
  };

  // Toggle Dark / Light Theme
  const toggleTheme = () => {
    const nextTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(nextTheme);
    if (nextTheme === 'light') {
      document.body.classList.add('theme-light');
    } else {
      document.body.classList.remove('theme-light');
    }
  };

  // Real-Time Keystroke Privacy Analysis effect (<200ms debounced)
  useEffect(() => {
    if (!promptText.trim()) {
      setAnalysisResult({
        text: "",
        risk_score: 0,
        risk_level: "SAFE",
        category: "SAFE",
        detected_categories: [],
        detected_entities: [],
        sanitized_text: "",
        decision: "ALLOW",
        action: "ALLOW",
        confidence: 0.98,
        explanation: "No sensitive information detected in prompt."
      });
      return;
    }

    const timer = setTimeout(async () => {
      try {
        const response = await fetch('http://localhost:8000/api/v1/privacy/analyze', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: promptText })
        });

        if (response.ok) {
          const data = await response.json();
          setAnalysisResult(data);
        } else {
          setAnalysisResult({
            text: promptText,
            risk_score: null,
            risk_level: "ERROR",
            category: "SERVICE_ERROR",
            detected_categories: [],
            detected_entities: [],
            sanitized_text: null,
            decision: "ERROR",
            action: "ERROR",
            confidence: 0,
            can_send_to_llm: false,
            warning_message: "Backend privacy analysis service returned an error.",
            explanation: `Privacy analysis unavailable: Backend returned status ${response.status}.`,
            shap: { token_attributions: [], feature_contributions: [] },
            sbert: { highest_similarity_percentage: 0, top_matched_category: "UNAVAILABLE" }
          });
        }
      } catch (err) {
        setAnalysisResult({
          text: promptText,
          risk_score: null,
          risk_level: "ERROR",
          category: "CONNECTION_ERROR",
          detected_categories: [],
          detected_entities: [],
          sanitized_text: null,
          decision: "ERROR",
          action: "ERROR",
          confidence: 0,
          can_send_to_llm: false,
          warning_message: "Cannot connect to backend privacy service.",
          explanation: "Backend service is unreachable at http://localhost:8000/api/v1/privacy/analyze. Please ensure the backend server is running.",
          shap: { token_attributions: [], feature_contributions: [] },
          sbert: { highest_similarity_percentage: 0, top_matched_category: "UNAVAILABLE" }
        });
      }
    }, 200);

    return () => clearTimeout(timer);
  }, [promptText]);

  return (
    <div className="app-layout">
      {activeView === 'chat' ? (
        <main className="three-column-grid">
          {/* Column 1: Left Navigation & History Sidebar */}
          <Sidebar 
            chats={chats}
            activeChatId={activeChatId}
            onSelectChat={handleSelectChat}
            onNewChat={handleNewChat}
            onDeleteChat={handleDeleteChat}
            onClearAllChats={handleClearAllChats}
            searchQuery={searchQuery}
            setSearchQuery={setSearchQuery}
            activeView={activeView}
            setActiveView={setActiveView}
            theme={theme}
            toggleTheme={toggleTheme}
            onOpenAbout={() => setIsAboutOpen(true)}
          />

          {/* Column 2: Center ChatGPT Conversation Area */}
          <ChatGPTPrompt 
            promptText={promptText}
            setPromptText={setPromptText}
            analysisResult={analysisResult}
            messages={activeChat ? activeChat.messages : []}
            setMessages={setMessagesForActiveChat}
            activeChatTitle={activeChat ? activeChat.title : ''}
          />

          {/* Column 3: Right LIVE PRIVACY ANALYSIS Panel */}
          <PrivacyDashboard 
            analysisResult={analysisResult}
          />
        </main>
      ) : (
        <main className="view-grid">
          <Sidebar 
            chats={chats}
            activeChatId={activeChatId}
            onSelectChat={handleSelectChat}
            onNewChat={handleNewChat}
            onDeleteChat={handleDeleteChat}
            onClearAllChats={handleClearAllChats}
            searchQuery={searchQuery}
            setSearchQuery={setSearchQuery}
            activeView={activeView}
            setActiveView={setActiveView}
            theme={theme}
            toggleTheme={toggleTheme}
            onOpenAbout={() => setIsAboutOpen(true)}
          />

          {activeView === 'monitor' && <PrivacyMonitorView analysisResult={analysisResult} />}
          {activeView === 'analytics' && <AnalyticsView />}
          {activeView === 'architecture' && <ArchitectureView />}
          {activeView === 'research' && <ResearchDatasetsView />}
        </main>
      )}

      <AboutProjectModal 
        isOpen={isAboutOpen}
        onClose={() => setIsAboutOpen(false)}
      />
    </div>
  );
}

export default App;
