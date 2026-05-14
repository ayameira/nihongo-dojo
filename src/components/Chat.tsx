import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useChat, Message, AgentAction } from '../hooks/useChat';
import { AudioPlayer } from './AudioPlayer';
import { Fact } from '../hooks/useFacts';

interface ChatProps {
  facts?: Fact[];
  factsLoading?: boolean;
  onAddFact?: (content: string) => Promise<Fact | null>;
  onUpdateFact?: (id: number, content: string) => Promise<boolean>;
  onDeleteFact?: (id: number) => Promise<boolean>;
  onRefreshFacts?: () => Promise<void>;
  sessionId: string | null;
  selectedSpeakerId?: number;
  onRefreshSessions?: () => Promise<void>;
}

interface ChatModel {
  id: string;
  name: string;
  input_cost_per_1m: number;
  output_cost_per_1m: number;
}

const MODEL_STORAGE_KEY = 'nihongo_chat_model';

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

export const Chat: React.FC<ChatProps> = ({ facts, factsLoading, onAddFact, onUpdateFact, onDeleteFact, onRefreshFacts, sessionId, selectedSpeakerId, onRefreshSessions }) => {
  const [availableModels, setAvailableModels] = useState<ChatModel[]>([]);
  const [selectedModel, setSelectedModel] = useState(() => localStorage.getItem(MODEL_STORAGE_KEY) || '');
  const chatModel = availableModels.some(model => model.id === selectedModel) ? selectedModel : null;

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
  } = useChat(sessionId, chatModel);

  const [inputValue, setInputValue] = useState('');
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'chat' | 'blackboard'>('chat');
  const [isAtBottom, setIsAtBottom] = useState(true);

  // Facts editing state
  const [editingFactId, setEditingFactId] = useState<number | null>(null);
  const [editFactValue, setEditFactValue] = useState('');
  const [deleteConfirmFactId, setDeleteConfirmFactId] = useState<number | null>(null);
  const [newFactValue, setNewFactValue] = useState('');
  const [isAddingFact, setIsAddingFact] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const wasLoadingRef = useRef(false);

  useEffect(() => {
    let cancelled = false;

    const loadModels = async () => {
      try {
        const response = await fetch((import.meta.env.VITE_API_URL || '') + '/api/config/models');
        if (!response.ok) return;

        const data: { current_model?: string; models?: ChatModel[] } = await response.json();
        const models = Array.isArray(data.models) ? data.models : [];
        if (cancelled) return;

        setAvailableModels(models);
        setSelectedModel(prev => {
          const defaultModel = models.some(model => model.id === data.current_model)
            ? data.current_model || ''
            : models[0]?.id || '';
          const candidate = prev || localStorage.getItem(MODEL_STORAGE_KEY) || defaultModel;
          const nextModel = models.some(model => model.id === candidate) ? candidate : defaultModel;

          if (nextModel) {
            localStorage.setItem(MODEL_STORAGE_KEY, nextModel);
          }

          return nextModel;
        });
      } catch {
        // The backend default still applies if the model list is unavailable.
      }
    };

    loadModels();

    return () => {
      cancelled = true;
    };
  }, []);

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

  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${textarea.scrollHeight}px`;
    }
  }, [inputValue]);

  // Refresh data when chat response completes
  useEffect(() => {
    let timer: ReturnType<typeof setTimeout> | null = null;

    if (wasLoadingRef.current && !isLoading) {
      // Refresh facts (AI may have updated them)
      if (onRefreshFacts) {
        onRefreshFacts();
      }
      // Refresh sessions to get preview and auto-generated title
      if (onRefreshSessions) {
        onRefreshSessions();
        // Delayed refresh to catch the LLM-generated title (runs in background)
        timer = setTimeout(() => {
          onRefreshSessions();
        }, 3000);
      }
    }
    wasLoadingRef.current = isLoading;

    return () => {
      if (timer) clearTimeout(timer);
    };
  }, [isLoading, onRefreshFacts, onRefreshSessions]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if ((!inputValue.trim() && !selectedImage) || isLoading) return;

    await sendMessage(inputValue.trim(), selectedImage || undefined);
    setInputValue('');
    setSelectedImage(null);
    setIsAtBottom(true);
  };

  const handleModelChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedModel(e.target.value);
    localStorage.setItem(MODEL_STORAGE_KEY, e.target.value);
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

  // Facts editing handlers
  const handleStartFactEdit = (fact: Fact) => {
    setEditingFactId(fact.id);
    setEditFactValue(fact.content);
  };

  const handleSaveFactEdit = async () => {
    if (editingFactId && editFactValue.trim() && onUpdateFact) {
      await onUpdateFact(editingFactId, editFactValue.trim());
    }
    setEditingFactId(null);
    setEditFactValue('');
  };

  const handleFactKeyDown = (e: React.KeyboardEvent) => {
    // Ignore Enter during IME composition (Japanese/Chinese/Korean input)
    const isComposing = e.nativeEvent.isComposing || e.keyCode === 229;
    if (e.key === 'Enter' && !isComposing) {
      handleSaveFactEdit();
    } else if (e.key === 'Escape') {
      setEditingFactId(null);
      setEditFactValue('');
    }
  };

  const handleAddFact = async () => {
    if (newFactValue.trim() && onAddFact) {
      await onAddFact(newFactValue.trim());
      setNewFactValue('');
      setIsAddingFact(false);
    }
  };

  const handleNewFactKeyDown = (e: React.KeyboardEvent) => {
    // Ignore Enter during IME composition (Japanese/Chinese/Korean input)
    const isComposing = e.nativeEvent.isComposing || e.keyCode === 229;
    if (e.key === 'Enter' && !isComposing) {
      handleAddFact();
    } else if (e.key === 'Escape') {
      setIsAddingFact(false);
      setNewFactValue('');
    }
  };

  const handleConfirmFactDelete = async () => {
    if (deleteConfirmFactId && onDeleteFact) {
      await onDeleteFact(deleteConfirmFactId);
      setDeleteConfirmFactId(null);
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

  const renderAssistantMessage = (msg: Message) => {
    // Split content by paragraphs for per-chunk audio playback
    const chunks = msg.content
      ? msg.content.split(/\n\n+/).filter(chunk => chunk.trim())
      : [];

    const markdownComponents = {
      p: ({ children }: { children?: React.ReactNode }) => <p className="prose-p">{children}</p>,
      ul: ({ children }: { children?: React.ReactNode }) => <ul className="prose-ul">{children}</ul>,
      ol: ({ children }: { children?: React.ReactNode }) => <ol className="prose-ol">{children}</ol>,
      li: ({ children }: { children?: React.ReactNode }) => <li className="prose-li">{children}</li>,
      strong: ({ children }: { children?: React.ReactNode }) => <strong className="prose-strong">{children}</strong>,
      em: ({ children }: { children?: React.ReactNode }) => <em className="prose-em">{children}</em>,
      code: ({ children, className }: { children?: React.ReactNode; className?: string }) => {
        const isInline = !className;
        return isInline ? (
          <code className="prose-code-inline">{children}</code>
        ) : (
          <code className={`prose-code-block ${className || ''}`}>
            {children}
          </code>
        );
      },
      blockquote: ({ children }: { children?: React.ReactNode }) => (
        <blockquote className="prose-blockquote">{children}</blockquote>
      ),
    };

    return (
      <div key={msg.id} className="message-assistant group">
        <div className="assistant-content">
          {chunks.length > 0 ? (
            chunks.map((chunk, index) => (
              <div key={index} className="message-chunk">
                <div className="chunk-content">
                  <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
                    {chunk}
                  </ReactMarkdown>
                </div>
                {msg.status === 'complete' && (
                  <AudioPlayer text={chunk} speakerId={selectedSpeakerId} />
                )}
              </div>
            ))
          ) : (
            msg.status === 'streaming' && !msg.content && (
              <span className="streaming-cursor" />
            )
          )}
        </div>

        {/* Feedback buttons - whole message scope */}
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
  };

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
          {availableModels.length > 0 && (
            <label className="model-selector" title="Chat model">
              <span className="model-selector-label">Model</span>
              <select
                aria-label="Chat model"
                value={selectedModel}
                onChange={handleModelChange}
                className="model-select"
                disabled={isLoading}
              >
                {availableModels.map(model => (
                  <option key={model.id} value={model.id}>
                    {model.name}
                  </option>
                ))}
              </select>
            </label>
          )}

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
              Profile
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
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                Student Profile
              </h2>
              <button onClick={() => setIsAddingFact(true)} className="add-fact-btn" title="Add fact">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
              </button>
            </div>

            {/* Add new fact form */}
            {isAddingFact && (
              <div className="fact-add-form">
                <input
                  type="text"
                  value={newFactValue}
                  onChange={(e) => setNewFactValue(e.target.value)}
                  onKeyDown={handleNewFactKeyDown}
                  placeholder="Add a new fact about yourself..."
                  className="fact-edit-input"
                  autoFocus
                />
                <div className="fact-add-actions">
                  <button onClick={handleAddFact}>Save</button>
                  <button onClick={() => { setIsAddingFact(false); setNewFactValue(''); }}>Cancel</button>
                </div>
              </div>
            )}

            {/* Facts list */}
            {factsLoading ? (
              <div className="notes-empty">
                <p>Loading...</p>
              </div>
            ) : facts && facts.length > 0 ? (
              <div className="facts-list">
                {facts.map((fact) => (
                  <div key={fact.id} className="fact-item">
                    {editingFactId === fact.id ? (
                      <input
                        type="text"
                        className="fact-edit-input"
                        value={editFactValue}
                        onChange={(e) => setEditFactValue(e.target.value)}
                        onBlur={handleSaveFactEdit}
                        onKeyDown={handleFactKeyDown}
                        autoFocus
                      />
                    ) : (
                      <>
                        <span className="fact-content">{fact.content}</span>
                        <div className="fact-actions">
                          <button
                            className="fact-action-btn"
                            onClick={() => handleStartFactEdit(fact)}
                            title="Edit"
                          >
                            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                          </button>
                          <button
                            className="fact-action-btn delete"
                            onClick={() => setDeleteConfirmFactId(fact.id)}
                            title="Delete"
                          >
                            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                          </button>
                        </div>
                      </>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="notes-empty">
                <p>No profile yet</p>
                <p className="notes-hint">Add facts about yourself or let your tutor learn about you</p>
              </div>
            )}

            {/* Delete confirmation modal */}
            {deleteConfirmFactId && (
              <div className="fact-delete-modal-overlay">
                <div className="fact-delete-modal">
                  <h3>Delete this fact?</h3>
                  <p>This cannot be undone.</p>
                  <div className="fact-delete-actions">
                    <button onClick={() => setDeleteConfirmFactId(null)}>Cancel</button>
                    <button className="delete" onClick={handleConfirmFactDelete}>Delete</button>
                  </div>
                </div>
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
              <textarea
                ref={textareaRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onPaste={handlePaste}
                onKeyDown={(e) => {
                  // Ignore Enter during IME composition (Japanese/Chinese/Korean input)
                  const isComposing = e.nativeEvent.isComposing || e.keyCode === 229;
                  if (e.key === 'Enter' && !e.shiftKey && !isComposing) {
                    e.preventDefault();
                    if ((inputValue.trim() || selectedImage) && !isLoading) {
                      handleSendMessage(e);
                    }
                  }
                }}
                placeholder="Write something..."
                className="message-input"
                disabled={isLoading}
                rows={1}
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
