import React from 'react';
import { 
  PlusCircle, Search, MessageSquare, Trash2, ShieldAlert, Cpu, 
  Sun, Moon, Info, BarChart3, Layers, BookOpen, Activity 
} from 'lucide-react';

export function Sidebar({ 
  chats, 
  activeChatId, 
  onSelectChat, 
  onNewChat, 
  onDeleteChat, 
  onClearAllChats, 
  searchQuery, 
  setSearchQuery,
  activeView,
  setActiveView,
  theme,
  toggleTheme,
  onOpenAbout
}) {
  const filteredChats = chats.filter(chat => 
    chat.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <aside className="sidebar-container">
      {/* Brand Header */}
      <div className="sidebar-brand">
        <img 
          src="/logo.png" 
          alt="PrivacyShield AI Logo" 
          className="brand-logo" 
          style={{ width: '40px', height: '40px', objectFit: 'contain', borderRadius: '10px', boxShadow: '0 0 16px rgba(99, 102, 241, 0.45)' }}
        />
        <div>
          <h1 className="brand-title">PrivacyShield AI</h1>
          <p className="brand-subtitle">Real-Time Privacy Guard</p>
        </div>
      </div>

      {/* Main View Navigation Links */}
      <nav className="sidebar-nav">
        <button 
          className={`nav-link ${activeView === 'chat' ? 'active' : ''}`}
          onClick={() => setActiveView('chat')}
        >
          <MessageSquare size={16} /> Chat
        </button>
        <button 
          className={`nav-link ${activeView === 'monitor' ? 'active' : ''}`}
          onClick={() => setActiveView('monitor')}
        >
          <Activity size={16} /> Privacy Monitor
        </button>
        <button 
          className={`nav-link ${activeView === 'analytics' ? 'active' : ''}`}
          onClick={() => setActiveView('analytics')}
        >
          <BarChart3 size={16} /> Analytics
        </button>
        <button 
          className={`nav-link ${activeView === 'architecture' ? 'active' : ''}`}
          onClick={() => setActiveView('architecture')}
        >
          <Layers size={16} /> Architecture
        </button>
        <button 
          className={`nav-link ${activeView === 'research' ? 'active' : ''}`}
          onClick={() => setActiveView('research')}
        >
          <BookOpen size={16} /> Research & Datasets
        </button>
      </nav>

      {/* New Chat Button */}
      <button onClick={onNewChat} className="btn-new-chat">
        <PlusCircle size={17} /> New Chat
      </button>

      {/* Search Input */}
      <div className="search-box">
        <Search size={14} className="search-icon" />
        <input 
          type="text" 
          placeholder="Search conversations..." 
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>

      {/* Chat History List */}
      <div className="chat-history-list">
        <div className="history-header">Recent Conversations</div>
        {filteredChats.length === 0 ? (
          <div className="empty-history">No conversations found.</div>
        ) : (
          filteredChats.map(chat => (
            <div 
              key={chat.id} 
              className={`chat-item ${chat.id === activeChatId && activeView === 'chat' ? 'active' : ''}`}
              onClick={() => {
                onSelectChat(chat.id);
                setActiveView('chat');
              }}
            >
              <MessageSquare size={14} style={{ flexShrink: 0 }} />
              <div className="chat-item-info">
                <div className="chat-item-title">{chat.title}</div>
                <div className="chat-item-date">{chat.date}</div>
              </div>
              <button 
                className="btn-delete-chat"
                onClick={(e) => {
                  e.stopPropagation();
                  onDeleteChat(chat.id);
                }}
                title="Delete Chat"
              >
                <Trash2 size={13} />
              </button>
            </div>
          ))
        )}
      </div>

      {/* Sidebar Footer */}
      <div className="sidebar-footer">
        <div style={{ display: 'flex', gap: '0.4rem', marginBottom: '0.5rem' }}>
          <button onClick={onOpenAbout} className="btn-icon" style={{ flex: 1, justifyContent: 'center' }}>
            <Info size={14} /> About Project
          </button>
          <button onClick={toggleTheme} className="btn-icon" style={{ padding: '0.4rem 0.6rem' }}>
            {theme === 'dark' ? <Sun size={14} /> : <Moon size={14} />}
          </button>
        </div>

        <button onClick={onClearAllChats} className="btn-clear-all">
          <Trash2 size={13} /> Clear All Conversations
        </button>

        <div className="status-pill" style={{ marginTop: '0.5rem', width: '100%', justifyContent: 'center' }}>
          <span className="pulse-dot"></span> Firewall Active
        </div>
      </div>
    </aside>
  );
}
