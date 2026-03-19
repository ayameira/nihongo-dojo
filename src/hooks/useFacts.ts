import { useState, useEffect, useCallback } from 'react';

export interface Fact {
  id: number;
  content: string;
  source: string;
  created_at: string | null;
}

interface UseFactsReturn {
  facts: Fact[];
  isLoading: boolean;
  addFact: (content: string) => Promise<Fact | null>;
  updateFact: (id: number, content: string) => Promise<boolean>;
  deleteFact: (id: number) => Promise<boolean>;
  refreshFacts: () => Promise<void>;
}

export function useFacts(): UseFactsReturn {
  const [facts, setFacts] = useState<Fact[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchFacts = useCallback(async () => {
    try {
      const response = await fetch((import.meta.env.VITE_API_URL || '') + '/api/notes/facts');
      if (response.ok) {
        const data = await response.json();
        setFacts(data.facts);
      }
    } catch (error) {
      console.error('Failed to fetch facts:', error);
    }
  }, []);

  useEffect(() => {
    const init = async () => {
      setIsLoading(true);
      await fetchFacts();
      setIsLoading(false);
    };
    init();
  }, [fetchFacts]);

  const addFact = useCallback(async (content: string): Promise<Fact | null> => {
    try {
      const response = await fetch((import.meta.env.VITE_API_URL || '') + '/api/notes/facts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content }),
      });

      if (response.ok) {
        const newFact = await response.json();
        setFacts(prev => [...prev, newFact]);
        return newFact;
      }
    } catch (error) {
      console.error('Failed to add fact:', error);
    }
    return null;
  }, []);

  const updateFact = useCallback(async (id: number, content: string): Promise<boolean> => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || ''}/api/notes/facts/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content }),
      });

      if (response.ok) {
        setFacts(prev =>
          prev.map(f => (f.id === id ? { ...f, content } : f))
        );
        return true;
      }
    } catch (error) {
      console.error('Failed to update fact:', error);
    }
    return false;
  }, []);

  const deleteFact = useCallback(async (id: number): Promise<boolean> => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || ''}/api/notes/facts/${id}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        setFacts(prev => prev.filter(f => f.id !== id));
        return true;
      }
    } catch (error) {
      console.error('Failed to delete fact:', error);
    }
    return false;
  }, []);

  const refreshFacts = useCallback(async () => {
    await fetchFacts();
  }, [fetchFacts]);

  return {
    facts,
    isLoading,
    addFact,
    updateFact,
    deleteFact,
    refreshFacts,
  };
}
