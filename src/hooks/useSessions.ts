import { useState, useEffect, useCallback } from 'react';

export interface Session {
  id: string;
  name: string | null;
  preview: string | null;
  message_count: number;
  created_at: string;
  updated_at: string;
}

interface UseSessionsReturn {
  sessions: Session[];
  currentSessionId: string | null;
  isLoading: boolean;
  createSession: () => Promise<string>;
  switchSession: (sessionId: string) => void;
  renameSession: (sessionId: string, name: string) => Promise<void>;
  deleteSession: (sessionId: string) => Promise<void>;
  refreshSessions: () => Promise<void>;
}

function generateSessionId(): string {
  return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

export function useSessions(): UseSessionsReturn {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchSessions = useCallback(async () => {
    try {
      const response = await fetch('/api/sessions');
      if (response.ok) {
        const data = await response.json();
        setSessions(data);
        return data;
      }
    } catch (error) {
      console.error('Failed to fetch sessions:', error);
    }
    return [];
  }, []);

  // Initialize: load sessions and set current
  useEffect(() => {
    const init = async () => {
      setIsLoading(true);
      const loadedSessions = await fetchSessions();

      // Get stored session ID
      let storedId = localStorage.getItem('nihongo_session_id');

      if (storedId && loadedSessions.some((s: Session) => s.id === storedId)) {
        // Use stored session if it exists
        setCurrentSessionId(storedId);
      } else if (loadedSessions.length > 0) {
        // Use most recent session
        const mostRecent = loadedSessions[0].id;
        setCurrentSessionId(mostRecent);
        localStorage.setItem('nihongo_session_id', mostRecent);
      } else {
        // No sessions exist, create a new one
        const newId = generateSessionId();
        setCurrentSessionId(newId);
        localStorage.setItem('nihongo_session_id', newId);
      }

      setIsLoading(false);
    };

    init();
  }, [fetchSessions]);

  const createSession = useCallback(async (): Promise<string> => {
    const newId = generateSessionId();

    try {
      const response = await fetch('/api/sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: newId }),
      });

      if (response.ok) {
        const newSession = await response.json();
        setSessions(prev => [newSession, ...prev]);
      }
    } catch (error) {
      console.error('Failed to create session:', error);
    }

    // Switch to new session
    setCurrentSessionId(newId);
    localStorage.setItem('nihongo_session_id', newId);

    return newId;
  }, []);

  const switchSession = useCallback((sessionId: string) => {
    setCurrentSessionId(sessionId);
    localStorage.setItem('nihongo_session_id', sessionId);
  }, []);

  const renameSession = useCallback(async (sessionId: string, name: string) => {
    try {
      const response = await fetch(`/api/sessions/${sessionId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name }),
      });

      if (response.ok) {
        const updated = await response.json();
        setSessions(prev =>
          prev.map(s => (s.id === sessionId ? updated : s))
        );
      }
    } catch (error) {
      console.error('Failed to rename session:', error);
    }
  }, []);

  const deleteSession = useCallback(async (sessionId: string) => {
    try {
      const response = await fetch(`/api/sessions/${sessionId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        setSessions(prev => {
          const remaining = prev.filter(s => s.id !== sessionId);

          // If deleted current session, switch to another
          if (sessionId === currentSessionId) {
            if (remaining.length > 0) {
              const nextId = remaining[0].id;
              setCurrentSessionId(nextId);
              localStorage.setItem('nihongo_session_id', nextId);
            } else {
              // No sessions left, create a new one
              const newId = generateSessionId();
              setCurrentSessionId(newId);
              localStorage.setItem('nihongo_session_id', newId);
            }
          }

          return remaining;
        });
      }
    } catch (error) {
      console.error('Failed to delete session:', error);
    }
  }, [currentSessionId]);

  const refreshSessions = useCallback(async () => {
    await fetchSessions();
  }, [fetchSessions]);

  return {
    sessions,
    currentSessionId,
    isLoading,
    createSession,
    switchSession,
    renameSession,
    deleteSession,
    refreshSessions,
  };
}
