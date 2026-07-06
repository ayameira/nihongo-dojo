import React, { useState, useEffect, useCallback } from 'react';
import { SessionList } from './SessionList';
import { AnkiSetupWizard } from './AnkiSetupWizard';
import type { Session } from '../hooks/useSessions';

interface VocabEntry {
  id: number;
  language_code: string;
  kanji: string | null;
  kana: string;
  meaning: string;
  pos: string | null;
  status: string;
  times_seen: number;
  times_correct: number;
}

interface VocabStats {
  new: number;
  learning: number;
  mature: number;
  total: number;
}

interface VocabSidebarProps {
  isCollapsed?: boolean;
  onToggle?: () => void;
  sessions?: Session[];
  currentSessionId?: string | null;
  onSessionSelect?: (sessionId: string) => void;
  onSessionRename?: (sessionId: string, name: string) => void;
  onSessionDelete?: (sessionId: string) => void;
  onNewChat?: () => void;
  currentView?: 'chat' | 'grammar';
  onViewChange?: (view: 'chat' | 'grammar') => void;
  setupWizardOpen?: boolean;
  onSetupWizardOpenChange?: (open: boolean) => void;
  languageCode?: string;
}

export const VocabSidebar: React.FC<VocabSidebarProps> = ({
  isCollapsed = false,
  onToggle,
  sessions = [],
  currentSessionId = null,
  onSessionSelect,
  onSessionRename,
  onSessionDelete,
  onNewChat,
  currentView = 'chat',
  onViewChange,
  setupWizardOpen,
  onSetupWizardOpenChange,
  languageCode = 'ja',
}) => {
  const [stats, setStats] = useState<VocabStats>({ new: 0, learning: 0, mature: 0, total: 0 });
  const [learningVocab, setLearningVocab] = useState<VocabEntry[]>([]);
  const [matureVocab, setMatureVocab] = useState<VocabEntry[]>([]);
  const [newVocab, setNewVocab] = useState<VocabEntry[]>([]);
  const [expandedSection, setExpandedSection] = useState<string>('learning');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<VocabEntry[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [selectedVocab, setSelectedVocab] = useState<VocabEntry | null>(null);
  const [internalShowConfig, setInternalShowConfig] = useState(false);
  const showConfig = setupWizardOpen ?? internalShowConfig;
  const setShowConfig = onSetupWizardOpenChange ?? setInternalShowConfig;
  const languageParam = `language_code=${encodeURIComponent(languageCode)}`;

  const fetchStats = useCallback(async () => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || ''}/api/vocab/stats?${languageParam}`);
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Failed to fetch vocab stats:', error);
    }
  }, [languageParam]);

  const fetchLearningVocab = useCallback(async () => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || ''}/api/vocab/learning?limit=50&${languageParam}`);
      if (response.ok) {
        const data = await response.json();
        setLearningVocab(data);
      }
    } catch (error) {
      console.error('Failed to fetch learning vocab:', error);
    }
  }, [languageParam]);

  const fetchMatureVocab = useCallback(async () => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || ''}/api/vocab?status=Mature&limit=50&${languageParam}`);
      if (response.ok) {
        const data = await response.json();
        setMatureVocab(data.items || []);
      }
    } catch (error) {
      console.error('Failed to fetch mature vocab:', error);
    }
  }, [languageParam]);

  const fetchNewVocab = useCallback(async () => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || ''}/api/vocab?status=New&limit=50&${languageParam}`);
      if (response.ok) {
        const data = await response.json();
        setNewVocab(data.items || []);
      }
    } catch (error) {
      console.error('Failed to fetch new vocab:', error);
    }
  }, [languageParam]);

  const refreshVocab = useCallback(() => {
    fetchStats();
    fetchLearningVocab();
    fetchMatureVocab();
    fetchNewVocab();
  }, [fetchStats, fetchLearningVocab, fetchMatureVocab, fetchNewVocab]);

  useEffect(() => {
    refreshVocab();

    // Refresh periodically
    const interval = setInterval(refreshVocab, 30000);

    return () => clearInterval(interval);
  }, [refreshVocab]);

  const handleSearch = useCallback(async (query: string) => {
    setSearchQuery(query);
    if (!query.trim()) {
      setSearchResults([]);
      setIsSearching(false);
      return;
    }

    setIsSearching(true);
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || ''}/api/vocab?search=${encodeURIComponent(query)}&limit=20&${languageParam}`);
      if (response.ok) {
        const data = await response.json();
        setSearchResults(data.items || []);
      }
    } catch (error) {
      console.error('Search failed:', error);
    }
  }, [languageParam]);

  const formatVocabDisplay = (vocab: VocabEntry) => {
    if (vocab.kanji) {
      return (
        <span>
          <span className="font-medium">{vocab.kanji}</span>
          <span className="text-ink-muted text-xs ml-1">({vocab.kana})</span>
        </span>
      );
    }
    return <span className="font-medium">{vocab.kana}</span>;
  };

  if (isCollapsed) {
    return (
      <div className="w-full h-full bg-paper border-r border-paper-dark flex flex-col items-center py-4">
        <button
          onClick={onToggle}
          className="p-2 hover:bg-paper-dark rounded-lg text-ink-muted hover:text-ink"
          title="Expand vocabulary"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/>
          </svg>
        </button>
        <div className="mt-4 text-xs text-center">
          <div className="text-yellow-600 dark:text-yellow-400 font-bold">{stats.learning}</div>
          <div className="text-ink-muted">学習</div>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full bg-paper border-r border-paper-dark flex flex-col h-full">
      {/* View Switcher */}
      {onViewChange && (
        <div className="p-2 border-b border-paper-dark flex gap-1">
          <button
            onClick={() => onViewChange('chat')}
            data-tutorial-target="chat-view"
            className={`flex-1 px-3 py-1.5 text-sm rounded-lg font-medium transition-colors ${
              currentView === 'chat'
                ? 'bg-vermillion text-white'
                : 'text-ink-muted hover:bg-paper-warm hover:text-ink'
            }`}
          >
            Chat
          </button>
          <button
            onClick={() => onViewChange('grammar')}
            data-tutorial-target="grammar-tree"
            className={`flex-1 px-3 py-1.5 text-sm rounded-lg font-medium transition-colors ${
              currentView === 'grammar'
                ? 'bg-vermillion text-white'
                : 'text-ink-muted hover:bg-paper-warm hover:text-ink'
            }`}
          >
            Grammar
          </button>
        </div>
      )}

      {/* Header */}
      <div className="p-4 border-b border-paper-dark flex items-center justify-between">
        <h2 className="font-bold text-ink">Vocabulary</h2>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setShowConfig(true)}
            data-tutorial-target="deck-settings"
            className="p-1 hover:bg-paper-dark rounded text-ink-muted hover:text-ink"
            aria-label="Configure decks"
            title="Configure decks"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/>
              <circle cx="12" cy="12" r="3"/>
            </svg>
          </button>
          <button
            onClick={onToggle}
            className="p-1 hover:bg-paper-dark rounded text-ink-muted hover:text-ink"
            title="Collapse"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="m11 17-5-5 5-5"/>
              <path d="m18 17-5-5 5-5"/>
            </svg>
          </button>
        </div>
      </div>

      {/* Sessions */}
      {onSessionSelect && onSessionRename && onSessionDelete && onNewChat && (
        <div className="border-b border-paper-dark">
          <SessionList
            sessions={sessions}
            currentSessionId={currentSessionId}
            onSelect={onSessionSelect}
            onRename={onSessionRename}
            onDelete={onSessionDelete}
            onNewChat={onNewChat}
          />
        </div>
      )}

      {/* Search */}
      <div className="p-2 border-b border-paper-dark">
        <input
          type="text"
          placeholder="Search vocab..."
          value={searchQuery}
          onChange={(e) => handleSearch(e.target.value)}
          className="w-full px-3 py-1.5 text-sm bg-paper-warm border border-paper-dark rounded-lg focus:outline-none focus:ring-1 focus:ring-vermillion text-ink placeholder:text-ink-muted"
        />
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {isSearching ? (
          // Search Results
          <div className="p-2">
            <div className="text-xs text-ink-muted mb-2">
              {searchResults.length} results
            </div>
            {searchResults.map((vocab) => (
              <button
                key={vocab.id}
                onClick={() => setSelectedVocab(vocab)}
                className="w-full text-left p-2 hover:bg-paper-warm rounded-lg text-sm text-ink"
              >
                {formatVocabDisplay(vocab)}
                <div className="text-xs text-ink-muted truncate">{vocab.meaning}</div>
              </button>
            ))}
          </div>
        ) : (
          // Category View
          <>
            {/* Learning Section */}
            <div className="border-b border-paper-dark">
              <button
                onClick={() => setExpandedSection(expandedSection === 'learning' ? '' : 'learning')}
                className="w-full p-3 flex items-center justify-between hover:bg-paper-warm text-ink"
              >
                <span className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-yellow-500 dark:bg-yellow-400"></span>
                  <span className="font-medium text-sm">Learning</span>
                </span>
                <span className="text-sm text-ink-muted">{stats.learning}</span>
              </button>
              {expandedSection === 'learning' && (
                <div className="px-2 pb-2 max-h-60 overflow-y-auto">
                  {learningVocab.length === 0 ? (
                    <div className="text-xs text-ink-muted p-2 text-center">
                      No vocabulary yet
                    </div>
                  ) : (
                    learningVocab.map((vocab) => (
                      <button
                        key={vocab.id}
                        onClick={() => setSelectedVocab(vocab)}
                        className="w-full text-left p-2 hover:bg-paper-warm rounded text-sm text-ink"
                      >
                        {formatVocabDisplay(vocab)}
                        <div className="text-xs text-ink-muted truncate">{vocab.meaning}</div>
                      </button>
                    ))
                  )}
                </div>
              )}
            </div>

            {/* Mature Section */}
            <div className="border-b border-paper-dark">
              <button
                onClick={() => setExpandedSection(expandedSection === 'mature' ? '' : 'mature')}
                className="w-full p-3 flex items-center justify-between hover:bg-paper-warm text-ink"
              >
                <span className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-jade"></span>
                  <span className="font-medium text-sm">Mature</span>
                </span>
                <span className="text-sm text-ink-muted">{stats.mature}</span>
              </button>
              {expandedSection === 'mature' && (
                <div className="px-2 pb-2 max-h-60 overflow-y-auto">
                  {matureVocab.length === 0 ? (
                    <div className="text-xs text-ink-muted p-2 text-center">
                      No mature vocabulary yet
                    </div>
                  ) : (
                    matureVocab.map((vocab) => (
                      <button
                        key={vocab.id}
                        onClick={() => setSelectedVocab(vocab)}
                        className="w-full text-left p-2 hover:bg-paper-warm rounded text-sm text-ink"
                      >
                        {formatVocabDisplay(vocab)}
                        <div className="text-xs text-ink-muted truncate">{vocab.meaning}</div>
                      </button>
                    ))
                  )}
                </div>
              )}
            </div>

            {/* New Section */}
            <div className="border-b border-paper-dark">
              <button
                onClick={() => setExpandedSection(expandedSection === 'new' ? '' : 'new')}
                className="w-full p-3 flex items-center justify-between hover:bg-paper-warm text-ink"
              >
                <span className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-blue-500 dark:bg-blue-400"></span>
                  <span className="font-medium text-sm">New</span>
                </span>
                <span className="text-sm text-ink-muted">{stats.new}</span>
              </button>
              {expandedSection === 'new' && (
                <div className="px-2 pb-2 max-h-60 overflow-y-auto">
                  {newVocab.length === 0 ? (
                    <div className="text-xs text-ink-muted p-2 text-center">
                      No new vocabulary yet
                    </div>
                  ) : (
                    newVocab.map((vocab) => (
                      <button
                        key={vocab.id}
                        onClick={() => setSelectedVocab(vocab)}
                        className="w-full text-left p-2 hover:bg-paper-warm rounded text-sm text-ink"
                      >
                        {formatVocabDisplay(vocab)}
                        <div className="text-xs text-ink-muted truncate">{vocab.meaning}</div>
                      </button>
                    ))
                  )}
                </div>
              )}
            </div>
          </>
        )}
      </div>

      {/* Vocab Detail Modal */}
      {selectedVocab && (
        <div className="fixed inset-0 bg-black/50 dark:bg-black/75 flex items-center justify-center z-50">
          <div className="bg-paper rounded-lg shadow-xl max-w-sm w-full mx-4 p-4 dark:border dark:border-paper-dark">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="text-xl font-bold text-ink">
                  {selectedVocab.kanji || selectedVocab.kana}
                </h3>
                {selectedVocab.kanji && (
                  <p className="text-ink-muted">{selectedVocab.kana}</p>
                )}
              </div>
              <button
                onClick={() => setSelectedVocab(null)}
                className="text-ink-muted hover:text-ink"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>
            <p className="text-ink-light mb-4">{selectedVocab.meaning}</p>
            <div className="text-sm text-ink-muted">
              <span className="font-medium">Status:</span> {selectedVocab.status}
            </div>
          </div>
        </div>
      )}

      {/* Anki Setup Wizard */}
      {showConfig && (
        <AnkiSetupWizard
          languageCode={languageCode}
          onClose={() => setShowConfig(false)}
          onSynced={refreshVocab}
        />
      )}

      {/* Footer Stats */}
      <div className="p-3 border-t border-paper-dark bg-paper-warm text-xs text-ink-muted">
        Total: {stats.total} words
      </div>
    </div>
  );
};

export default VocabSidebar;
