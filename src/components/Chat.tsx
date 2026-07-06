import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useChat } from '../hooks/useChat';
import type { Fact } from '../hooks/useFacts';
import { ChatComposer } from './chat/ChatComposer';
import { MessageList } from './chat/MessageList';

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
  openProfileRequest?: number;
  openChatRequest?: number;
  focusComposerRequest?: number;
}

interface ChatModel {
  id: string;
  key?: string;
  provider?: string;
  provider_name?: string;
  configured?: boolean;
  name: string;
  input_cost_per_1m: number;
  output_cost_per_1m: number;
}

const MODEL_STORAGE_KEY = 'nihongo_chat_model';

const getModelKey = (model: ChatModel) => model.key || `${model.provider || 'gemini'}:${model.id}`;
const getModelProvider = (model: ChatModel) => model.provider || getModelKey(model).split(':', 1)[0] || 'gemini';

export const Chat: React.FC<ChatProps> = ({
  facts,
  factsLoading,
  onAddFact,
  onUpdateFact,
  onDeleteFact,
  onRefreshFacts,
  sessionId,
  selectedSpeakerId,
  onRefreshSessions,
  openProfileRequest = 0,
  openChatRequest = 0,
  focusComposerRequest = 0,
}) => {
  const [availableModels, setAvailableModels] = useState<ChatModel[]>([]);
  const [selectedModel, setSelectedModel] = useState(() => localStorage.getItem(MODEL_STORAGE_KEY) || '');
  const selectedChatModel = availableModels.find(model => getModelKey(model) === selectedModel);
  const chatModel = selectedChatModel?.configured === false ? null : selectedChatModel?.id || null;
  const chatProvider = selectedChatModel?.configured === false || !selectedChatModel ? null : getModelProvider(selectedChatModel);

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
  } = useChat(sessionId, chatModel, chatProvider);

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
  const wasLoadingRef = useRef(false);

  useEffect(() => {
    let cancelled = false;

    const loadModels = async () => {
      try {
        const response = await fetch((import.meta.env.VITE_API_URL || '') + '/api/config/models');
        if (!response.ok) return;

        const data: { current_key?: string; current_model?: string; provider?: string; models?: ChatModel[] } = await response.json();
        const models = Array.isArray(data.models) ? data.models : [];
        if (cancelled) return;

        setAvailableModels(models);
        setSelectedModel(prev => {
          const fallbackKey = data.current_key
            || (data.current_model ? `${data.provider || 'gemini'}:${data.current_model}` : '');
          const firstConfiguredModel = models.find(model => model.configured !== false);
          const defaultModel = models.some(model => getModelKey(model) === fallbackKey)
            ? fallbackKey
            : firstConfiguredModel
              ? getModelKey(firstConfiguredModel)
              : models[0] ? getModelKey(models[0]) : '';
          const candidate = prev || localStorage.getItem(MODEL_STORAGE_KEY) || defaultModel;
          const nextModel = models.some(model => getModelKey(model) === candidate && model.configured !== false)
            ? candidate
            : defaultModel;

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

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  const handleJumpToBottom = useCallback(() => {
    setIsAtBottom(true);
    scrollToBottom();
  }, [scrollToBottom]);

  const handleComposerSent = useCallback(() => {
    setIsAtBottom(true);
  }, []);

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
  }, [messages, loadingState, currentAction, activeTab, isAtBottom, scrollToBottom]);

  useEffect(() => {
    if (openProfileRequest > 0) {
      setActiveTab('blackboard');
    }
  }, [openProfileRequest]);

  useEffect(() => {
    if (openChatRequest > 0) {
      setActiveTab('chat');
    }
  }, [openChatRequest]);

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

  const handleModelChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedModel(e.target.value);
    localStorage.setItem(MODEL_STORAGE_KEY, e.target.value);
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
                  <option
                    key={getModelKey(model)}
                    value={getModelKey(model)}
                    disabled={model.configured === false}
                  >
                    {model.provider_name ? `${model.provider_name}: ` : ''}{model.name}
                    {model.configured === false ? ' (key needed)' : ''}
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
              data-tutorial-target="profile-tab"
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
          <MessageList
            messages={messages}
            isLoading={isLoading}
            currentAction={currentAction}
            isAtBottom={isAtBottom}
            messagesEndRef={messagesEndRef}
            selectedSpeakerId={selectedSpeakerId}
            pendingFeedback={pendingFeedback}
            onDifficultyFeedback={sendDifficultyFeedback}
            onJumpToBottom={handleJumpToBottom}
          />
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

      <ChatComposer
        isVisible={activeTab === 'chat'}
        isLoading={isLoading}
        sendMessage={sendMessage}
        onSent={handleComposerSent}
        focusRequest={focusComposerRequest}
      />
    </div>
  );
};

export default Chat;
