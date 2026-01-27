import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useChat, Message, AgentAction } from '../hooks/useChat';

interface ChatProps {
  blackboardContent?: string;
  onRefreshNotes?: () => void;
  sessionId: string | null;
}

const AgentActionIndicator: React.FC<{ action: AgentAction }> = ({ action }) => {
  const getActionText = () => {
    switch (action.type) {
      case 'thinking':
        return 'Thinking';
      case 'tool_call':
        return action.name ? `Using ${action.name}` : 'Processing';
      case 'tool_result':
        return action.name ? `Reading ${action.name}` : 'Reading results';
      default:
        return 'Working';
    }
  };

  return (
    <div className="agent-action">
      <div className="action-indicator">
        <span className="action-dot" />
        <span className="action-text">{getActionText()}</span>
      </div>
    </div>
  );
};

export const Chat: React.FC<ChatProps> = ({ blackboardContent, onRefreshNotes, sessionId }) => {
  const {
    messages,
    isLoading,
    loadingState,
    currentAction,
    lastUsage,
    pendingFeedback,
    sendMessage,
    sendDifficultyFeedback,
    clearPendingFeedback,
  } = useChat(sessionId);

  const [inputValue, setInputValue] = useState('');
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'chat' | 'blackboard'>('chat');
  const [isAtBottom, setIsAtBottom] = useState(true);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleScroll = () => {
    const container = containerRef.current;
    if (!container) return;
    const atBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 50;
    setIsAtBottom(atBottom);
  };

  useEffect(() => {
    if (activeTab === 'chat' && isAtBottom) {
      scrollToBottom();
    }
  }, [messages, loadingState, currentAction, activeTab, isAtBottom]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if ((!inputValue.trim() && !selectedImage) || isLoading) return;

    await sendMessage(inputValue.trim(), selectedImage || undefined);
    setInputValue('');
    setSelectedImage(null);
    setIsAtBottom(true);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) processFile(file);
  };

  const processFile = (file: File) => {
    if (!file.type.startsWith('image/')) return;
    const reader = new FileReader();
    reader.onloadend = () => setSelectedImage(reader.result as string);
    reader.readAsDataURL(file);
  };

  const handlePaste = (e: React.ClipboardEvent) => {
    const items = e.clipboardData.items;
    for (let i = 0; i < items.length; i++) {
      if (items[i].type.indexOf('image') !== -1) {
        const file = items[i].getAsFile();
        if (file) {
          processFile(file);
          e.preventDefault();
        }
      }
    }
  };

  const renderUserMessage = (msg: Message) => (
    <div key={msg.id} className="message-user">
      {msg.image && (
        <img
          src={msg.image}
          alt="Attachment"
          className="user-image"
        />
      )}
      <p className="user-text">{msg.content}</p>
    </div>
  );

  // Determine if we should show a timestamp before a message
  const shouldShowTimestamp = (msg: Message, index: number): boolean => {
    if (index === 0) return true;

    const prevMsg = messages[index - 1];
    const timeDiff = msg.timestamp.getTime() - prevMsg.timestamp.getTime();
    const fiveMinutes = 5 * 60 * 1000;

    // Show timestamp if more than 5 minutes have passed
    if (timeDiff > fiveMinutes) return true;

    // Show timestamp if it's a different day
    const prevDate = prevMsg.timestamp.toDateString();
    const currDate = msg.timestamp.toDateString();
    if (prevDate !== currDate) return true;

    return false;
  };

  const formatTimestamp = (date: Date): string => {
    const now = new Date();
    const isToday = date.toDateString() === now.toDateString();
    const yesterday = new Date(now);
    yesterday.setDate(yesterday.getDate() - 1);
    const isYesterday = date.toDateString() === yesterday.toDateString();

    const time = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    if (isToday) {
      return time;
    } else if (isYesterday) {
      return `Yesterday, ${time}`;
    } else {
      return `${date.toLocaleDateString([], { month: 'short', day: 'numeric' })}, ${time}`;
    }
  };

  const renderAssistantMessage = (msg: Message) => (
    <div key={msg.id} className="message-assistant group">
      <div className="assistant-content">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            p: ({ children }) => <p className="prose-p">{children}</p>,
            ul: ({ children }) => <ul className="prose-ul">{children}</ul>,
            ol: ({ children }) => <ol className="prose-ol">{children}</ol>,
            li: ({ children }) => <li className="prose-li">{children}</li>,
            strong: ({ children }) => <strong className="prose-strong">{children}</strong>,
            em: ({ children }) => <em className="prose-em">{children}</em>,
            code: ({ children, className }) => {
              const isInline = !className;
              return isInline ? (
                <code className="prose-code-inline">{children}</code>
              ) : (
                <code className={`prose-code-block ${className || ''}`}>
                  {children}
                </code>
              );
            },
            blockquote: ({ children }) => (
              <blockquote className="prose-blockquote">{children}</blockquote>
            ),
          }}
        >
          {msg.content || (msg.status === 'streaming' ? '' : '')}
        </ReactMarkdown>
        {msg.status === 'streaming' && !msg.content && (
          <span className="streaming-cursor" />
        )}
      </div>

      {/* Feedback buttons - appear on hover for completed messages */}
      {msg.status === 'complete' && (
        <div className="feedback-buttons">
          <button
            onClick={() => sendDifficultyFeedback('too_hard')}
            className={`feedback-btn ${pendingFeedback === 'too_hard' ? 'active-hard' : ''}`}
          >
            Too Hard
          </button>
          <button
            onClick={() => sendDifficultyFeedback('too_easy')}
            className={`feedback-btn ${pendingFeedback === 'too_easy' ? 'active-easy' : ''}`}
          >
            Too Easy
          </button>
        </div>
      )}
    </div>
  );

  const renderMessage = (msg: Message) => {
    return msg.role === 'user' ? renderUserMessage(msg) : renderAssistantMessage(msg);
  };

  return (
    <div className="chat-container">
      {/* Header */}
      <header className="chat-header">
        <div className="header-left">
          <h1 className="app-title">
            <span className="title-jp">日本語</span>
            <span className="title-en">Dojo</span>
          </h1>
          <div className="header-meta">
            <span className="status-online">
              <span className="status-dot" />
              Active
            </span>
            {lastUsage && (
              <span className="usage-info">
                {lastUsage.input_tokens + lastUsage.output_tokens} tokens
              </span>
            )}
          </div>
        </div>

        <div className="header-right">
          {pendingFeedback && (
            <span className="pending-feedback">
              {pendingFeedback === 'too_hard' ? 'Easier next time' : 'Harder next time'}
              <button onClick={clearPendingFeedback} className="clear-feedback">×</button>
            </span>
          )}

          <div className="tab-switcher">
            <button
              onClick={() => setActiveTab('chat')}
              className={`tab-btn ${activeTab === 'chat' ? 'active' : ''}`}
            >
              Chat
            </button>
            <button
              onClick={() => setActiveTab('blackboard')}
              className={`tab-btn ${activeTab === 'blackboard' ? 'active' : ''}`}
            >
              Notes
            </button>
          </div>
        </div>
      </header>

      {/* Messages Area */}
      <div
        ref={containerRef}
        onScroll={handleScroll}
        className="messages-container"
      >
        {activeTab === 'chat' ? (
          <>
            {messages.length === 0 && (
              <div className="empty-state">
                <span className="empty-jp">はじめましょう</span>
                <span className="empty-en">Let's begin your practice</span>
              </div>
            )}

            {messages.map((msg, index) => (
              <React.Fragment key={msg.id}>
                {shouldShowTimestamp(msg, index) && (
                  <div className="timestamp-cluster">
                    <span className="timestamp-label">
                      {formatTimestamp(msg.timestamp)}
                    </span>
                  </div>
                )}
                {renderMessage(msg)}
              </React.Fragment>
            ))}

            {/* Agent Action Display */}
            {isLoading && currentAction && (
              <AgentActionIndicator action={currentAction} />
            )}

            {/* Scroll to bottom button */}
            {!isAtBottom && isLoading && (
              <button
                onClick={() => {
                  setIsAtBottom(true);
                  scrollToBottom();
                }}
                className="scroll-bottom-btn"
              >
                ↓ New message
              </button>
            )}

            <div ref={messagesEndRef} />
          </>
        ) : (
          <div className="notes-view">
            <div className="notes-header">
              <h2 className="notes-title">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>
                Study Notes
              </h2>
              {onRefreshNotes && (
                <button onClick={onRefreshNotes} className="refresh-btn" title="Refresh">
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/><path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/><path d="M16 16h5v5"/></svg>
                </button>
              )}
            </div>
            {blackboardContent ? (
              <div className="notes-content">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    h1: ({ children }) => <h1 className="notes-h1">{children}</h1>,
                    h2: ({ children }) => <h2 className="notes-h2">{children}</h2>,
                    h3: ({ children }) => <h3 className="notes-h3">{children}</h3>,
                    p: ({ children }) => <p className="notes-p">{children}</p>,
                    ul: ({ children }) => <ul className="notes-ul">{children}</ul>,
                    ol: ({ children }) => <ol className="notes-ol">{children}</ol>,
                    li: ({ children }) => <li className="notes-li">{children}</li>,
                    strong: ({ children }) => <strong className="notes-strong">{children}</strong>,
                    em: ({ children }) => <em className="notes-em">{children}</em>,
                    code: ({ children, className }) => {
                      const isInline = !className;
                      return isInline ? (
                        <code className="notes-code-inline">{children}</code>
                      ) : (
                        <code className={`notes-code-block ${className || ''}`}>{children}</code>
                      );
                    },
                    blockquote: ({ children }) => (
                      <blockquote className="notes-blockquote">{children}</blockquote>
                    ),
                  }}
                >
                  {blackboardContent
                    .replace(/<!--[\s\S]*?-->/g, '')
                    .replace(/^#\s+[^\n]+\n*/m, '')
                    .trim()}
                </ReactMarkdown>
              </div>
            ) : (
              <div className="notes-empty">
                <p>No notes yet</p>
                <p className="notes-hint">Notes will appear as you learn</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Input Area */}
      {activeTab === 'chat' && (
        <div className="input-area">
          {selectedImage && (
            <div className="image-preview">
              <img src={selectedImage} alt="Preview" />
              <button onClick={() => setSelectedImage(null)} className="remove-image">
                <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
              </button>
            </div>
          )}
          <form onSubmit={handleSendMessage} className="input-form">
            <input
              type="file"
              accept="image/*"
              ref={fileInputRef}
              onChange={handleFileSelect}
              className="hidden"
            />

            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="attach-btn"
              title="Attach image"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
            </button>

            <div className="input-wrapper">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onPaste={handlePaste}
                placeholder="Write something..."
                className="message-input"
                disabled={isLoading}
              />

              <button
                type="submit"
                disabled={(!inputValue.trim() && !selectedImage) || isLoading}
                className="send-btn"
                title="Send"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};

export default Chat;
