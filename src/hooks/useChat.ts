import { useState, useCallback, useEffect, useRef } from 'react';
import { readSSEStream } from '../utils/streamReader';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  image?: string;
  timestamp: Date;
  status: 'sending' | 'streaming' | 'complete' | 'error';
}

export interface UsageData {
  input_tokens: number;
  output_tokens: number;
  cost_usd: number;
}

export interface AgentAction {
  type: 'thinking' | 'tool_call' | 'tool_result';
  name?: string;
  timestamp: Date;
}

interface UseChatReturn {
  messages: Message[];
  isLoading: boolean;
  loadingState: 'idle' | 'connecting' | 'streaming';
  currentAction: AgentAction | null;
  lastUsage: UsageData | null;
  pendingFeedback: 'too_hard' | 'too_easy' | null;
  sendMessage: (content: string, image?: string) => Promise<void>;
  sendDifficultyFeedback: (direction: 'too_hard' | 'too_easy') => void;
  clearPendingFeedback: () => void;
  clearHistory: () => void;
}

export function useChat(): UseChatReturn {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingState, setLoadingState] = useState<'idle' | 'connecting' | 'streaming'>('idle');
  const [currentAction, setCurrentAction] = useState<AgentAction | null>(null);
  const [lastUsage, setLastUsage] = useState<UsageData | null>(null);
  const [pendingFeedback, setPendingFeedback] = useState<'too_hard' | 'too_easy' | null>(null);
  const sessionIdRef = useRef<string>('');

  // Generate or retrieve session ID and load history
  useEffect(() => {
    let sessionId = localStorage.getItem('nihongo_session_id');
    if (!sessionId) {
      sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      localStorage.setItem('nihongo_session_id', sessionId);
    }
    sessionIdRef.current = sessionId;

    // Load chat history from backend
    const loadHistory = async () => {
      try {
        const response = await fetch(`/api/chat/history/${sessionId}`);
        if (response.ok) {
          const history = await response.json();
          if (history.length > 0) {
            const loadedMessages: Message[] = history.map((msg: { id: number; role: 'user' | 'assistant'; content: string; has_image: boolean; created_at: string }) => ({
              id: `msg_${msg.id}`,
              role: msg.role,
              content: msg.content,
              timestamp: new Date(msg.created_at),
              status: 'complete' as const,
            }));
            setMessages(loadedMessages);
          }
        }
      } catch (error) {
        console.error('Failed to load chat history:', error);
      }
    };

    loadHistory();
  }, []);

  const sendMessage = useCallback(async (content: string, image?: string) => {
    if (isLoading) return;

    const userMessage: Message = {
      id: `msg_${Date.now()}`,
      role: 'user',
      content,
      image,
      timestamp: new Date(),
      status: 'complete',
    };

    const assistantMessage: Message = {
      id: `msg_${Date.now() + 1}`,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      status: 'streaming',
    };

    setMessages(prev => [...prev, userMessage, assistantMessage]);
    setIsLoading(true);
    setLoadingState('connecting');
    setCurrentAction({ type: 'thinking', timestamp: new Date() });

    try {
      // Strip data URI prefix from image if present
      let imageData = image;
      if (imageData && imageData.includes('base64,')) {
        imageData = imageData.split('base64,')[1];
      }

      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: content,
          image_data: imageData,
          session_id: sessionIdRef.current,
          difficulty_feedback: pendingFeedback,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Clear pending feedback after sending
      setPendingFeedback(null);
      setLoadingState('streaming');

      let fullContent = '';

      for await (const event of readSSEStream(response)) {
        switch (event.type) {
          case 'text':
            fullContent += event.content || '';
            setCurrentAction(null); // Clear action when text starts streaming
            setMessages(prev => {
              const updated = [...prev];
              const lastMsg = updated[updated.length - 1];
              if (lastMsg.role === 'assistant') {
                lastMsg.content = fullContent;
              }
              return updated;
            });
            break;

          case 'tool_call':
            setCurrentAction({
              type: 'tool_call',
              name: event.name,
              timestamp: new Date()
            });
            break;

          case 'tool_result':
            setCurrentAction({
              type: 'tool_result',
              name: event.name,
              timestamp: new Date()
            });
            break;

          case 'usage':
            if (event.usage) {
              setLastUsage(event.usage);
            }
            break;

          case 'done':
            setCurrentAction(null);
            setMessages(prev => {
              const updated = [...prev];
              const lastMsg = updated[updated.length - 1];
              if (lastMsg.role === 'assistant') {
                lastMsg.status = 'complete';
              }
              return updated;
            });
            break;

          case 'error':
            setCurrentAction(null);
            setMessages(prev => {
              const updated = [...prev];
              const lastMsg = updated[updated.length - 1];
              if (lastMsg.role === 'assistant') {
                lastMsg.content = event.content || 'An error occurred';
                lastMsg.status = 'error';
              }
              return updated;
            });
            break;
        }
      }

    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => {
        const updated = [...prev];
        const lastMsg = updated[updated.length - 1];
        if (lastMsg.role === 'assistant') {
          lastMsg.content = `Error: ${error instanceof Error ? error.message : 'Failed to connect'}`;
          lastMsg.status = 'error';
        }
        return updated;
      });
    } finally {
      setIsLoading(false);
      setLoadingState('idle');
      setCurrentAction(null);
    }
  }, [isLoading, pendingFeedback]);

  const sendDifficultyFeedback = useCallback((direction: 'too_hard' | 'too_easy') => {
    setPendingFeedback(direction);
  }, []);

  const clearPendingFeedback = useCallback(() => {
    setPendingFeedback(null);
  }, []);

  const clearHistory = useCallback(() => {
    setMessages([]);
    // Generate new session ID
    const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    localStorage.setItem('nihongo_session_id', newSessionId);
    sessionIdRef.current = newSessionId;
  }, []);

  return {
    messages,
    isLoading,
    loadingState,
    currentAction,
    lastUsage,
    pendingFeedback,
    sendMessage,
    sendDifficultyFeedback,
    clearPendingFeedback,
    clearHistory,
  };
}
