import { useState, useEffect, useCallback, useMemo } from 'react';

export interface GrammarEntry {
  id: number;
  language_code: string;
  pattern: string;
  meaning: string;
  jlpt_level: string | null;
  status: string;
  source: string;
  notes: string | null;
  times_seen: number;
  times_correct: number;
  last_assessed_at: string | null;
  last_seen_at: string | null;
  created_at: string;
}

export interface GrammarStats {
  by_status: Record<string, number>;
  by_level: Record<string, { total: number; New: number; Learning: number; Burned: number }>;
  total: number;
  custom: number;
  level_scheme?: {
    name: string;
    levels: string[];
    custom_label: string;
  };
}

interface UseGrammarReturn {
  grammar: GrammarEntry[];
  grammarByLevel: Record<string, GrammarEntry[]>;
  stats: GrammarStats | null;
  levels: string[];
  isLoading: boolean;
  statusFilter: string | null;
  searchQuery: string;
  setStatusFilter: (status: string | null) => void;
  setSearchQuery: (query: string) => void;
  updateStatus: (id: number, status: string) => Promise<boolean>;
  addGrammar: (data: { pattern: string; meaning: string; jlpt_level?: string; notes?: string }) => Promise<GrammarEntry | null>;
  deleteGrammar: (id: number) => Promise<boolean>;
  refreshGrammar: () => Promise<void>;
}

export function useGrammar(languageCode = 'ja'): UseGrammarReturn {
  const [grammar, setGrammar] = useState<GrammarEntry[]>([]);
  const [stats, setStats] = useState<GrammarStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  const fetchGrammar = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (statusFilter) params.set('status', statusFilter);
      if (searchQuery) params.set('search', searchQuery);
      params.set('language_code', languageCode);
      params.set('limit', '1000');

      const response = await fetch(`${import.meta.env.VITE_API_URL || ''}/api/grammar?${params.toString()}`);
      if (response.ok) {
        const data = await response.json();
        setGrammar(data.items);
      }
    } catch (error) {
      console.error('Failed to fetch grammar:', error);
    }
  }, [languageCode, statusFilter, searchQuery]);

  const fetchStats = useCallback(async () => {
    try {
      const params = new URLSearchParams({ language_code: languageCode });
      const response = await fetch(`${import.meta.env.VITE_API_URL || ''}/api/grammar/stats?${params.toString()}`);
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Failed to fetch grammar stats:', error);
    }
  }, [languageCode]);

  const refreshGrammar = useCallback(async () => {
    setIsLoading(true);
    await Promise.all([fetchGrammar(), fetchStats()]);
    setIsLoading(false);
  }, [fetchGrammar, fetchStats]);

  useEffect(() => {
    refreshGrammar();
  }, [statusFilter, searchQuery]);

  // Group grammar by the active profile's level scheme.
  const levels = stats?.level_scheme?.levels || ['N5', 'N4', 'N3', 'N2', 'N1'];
  const customLabel = stats?.level_scheme?.custom_label || 'Custom';

  const grammarByLevel = useMemo(() => {
    const grouped: Record<string, GrammarEntry[]> = Object.fromEntries(
      [...levels, customLabel].map((level) => [level, []])
    );

    for (const entry of grammar) {
      const level = entry.jlpt_level || customLabel;
      if (grouped[level]) {
        grouped[level].push(entry);
      } else {
        grouped[customLabel].push(entry);
      }
    }

    return grouped;
  }, [customLabel, grammar, levels]);

  const updateStatus = useCallback(async (id: number, status: string): Promise<boolean> => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || ''}/api/grammar/${id}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status }),
      });

      if (response.ok) {
        // Update local state
        setGrammar(prev =>
          prev.map(g => (g.id === id ? { ...g, status } : g))
        );
        // Refresh stats
        fetchStats();
        return true;
      }
      return false;
    } catch (error) {
      console.error('Failed to update grammar status:', error);
      return false;
    }
  }, [fetchStats]);

  const addGrammar = useCallback(async (data: {
    pattern: string;
    meaning: string;
    jlpt_level?: string;
    notes?: string;
  }): Promise<GrammarEntry | null> => {
    try {
      const response = await fetch((import.meta.env.VITE_API_URL || '') + '/api/grammar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...data, language_code: languageCode }),
      });

      if (response.ok) {
        const newEntry = await response.json();
        setGrammar(prev => [newEntry, ...prev]);
        fetchStats();
        return newEntry;
      }
      return null;
    } catch (error) {
      console.error('Failed to add grammar:', error);
      return null;
    }
  }, [fetchStats, languageCode]);

  const deleteGrammar = useCallback(async (id: number): Promise<boolean> => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || ''}/api/grammar/${id}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        setGrammar(prev => prev.filter(g => g.id !== id));
        fetchStats();
        return true;
      }
      return false;
    } catch (error) {
      console.error('Failed to delete grammar:', error);
      return false;
    }
  }, [fetchStats]);

  return {
    grammar,
    grammarByLevel,
    stats,
    levels: [...levels, customLabel],
    isLoading,
    statusFilter,
    searchQuery,
    setStatusFilter,
    setSearchQuery,
    updateStatus,
    addGrammar,
    deleteGrammar,
    refreshGrammar,
  };
}
