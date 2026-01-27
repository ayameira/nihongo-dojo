import React, { useState, useEffect, useCallback } from 'react';

interface VocabEntry {
  id: number;
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
}

export const VocabSidebar: React.FC<VocabSidebarProps> = ({
  isCollapsed = false,
  onToggle,
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
  const [showConfig, setShowConfig] = useState(false);
  const [ankiPath, setAnkiPath] = useState('');
  const [ankiPathExists, setAnkiPathExists] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncMessage, setSyncMessage] = useState('');

  const fetchStats = useCallback(async () => {
    try {
      const response = await fetch('/api/vocab/stats');
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Failed to fetch vocab stats:', error);
    }
  }, []);

  const fetchLearningVocab = useCallback(async () => {
    try {
      const response = await fetch('/api/vocab/learning?limit=50');
      if (response.ok) {
        const data = await response.json();
        setLearningVocab(data);
      }
    } catch (error) {
      console.error('Failed to fetch learning vocab:', error);
    }
  }, []);

  const fetchMatureVocab = useCallback(async () => {
    try {
      const response = await fetch('/api/vocab?status=Mature&limit=50');
      if (response.ok) {
        const data = await response.json();
        setMatureVocab(data.items || []);
      }
    } catch (error) {
      console.error('Failed to fetch mature vocab:', error);
    }
  }, []);

  const fetchNewVocab = useCallback(async () => {
    try {
      const response = await fetch('/api/vocab?status=New&limit=50');
      if (response.ok) {
        const data = await response.json();
        setNewVocab(data.items || []);
      }
    } catch (error) {
      console.error('Failed to fetch new vocab:', error);
    }
  }, []);

  const fetchAnkiPath = useCallback(async () => {
    try {
      const response = await fetch('/api/config/anki-path');
      if (response.ok) {
        const data = await response.json();
        setAnkiPath(data.path);
        setAnkiPathExists(data.exists);
      }
    } catch (error) {
      console.error('Failed to fetch Anki path:', error);
    }
  }, []);

  const saveAnkiPath = async (path: string) => {
    try {
      const response = await fetch('/api/config/anki-path', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path }),
      });
      if (response.ok) {
        const data = await response.json();
        setAnkiPath(data.path);
        setAnkiPathExists(data.exists);
        return data;
      }
    } catch (error) {
      console.error('Failed to save Anki path:', error);
    }
    return null;
  };

  const syncAnki = async () => {
    setIsSyncing(true);
    setSyncMessage('Syncing...');
    try {
      const response = await fetch('/api/config/sync-anki', { method: 'POST' });
      if (response.ok) {
        const data = await response.json();
        setSyncMessage(`Synced: ${data.imported} new, ${data.updated} updated`);
        // Refresh vocab data
        fetchStats();
        fetchLearningVocab();
        fetchMatureVocab();
        fetchNewVocab();
      } else {
        const error = await response.json();
        setSyncMessage(`Error: ${error.detail}`);
      }
    } catch (error) {
      setSyncMessage('Sync failed');
    } finally {
      setIsSyncing(false);
      setTimeout(() => setSyncMessage(''), 3000);
    }
  };

  useEffect(() => {
    fetchStats();
    fetchLearningVocab();
    fetchMatureVocab();
    fetchNewVocab();
    fetchAnkiPath();

    // Refresh periodically
    const interval = setInterval(() => {
      fetchStats();
      fetchLearningVocab();
      fetchMatureVocab();
      fetchNewVocab();
    }, 30000);

    return () => clearInterval(interval);
  }, [fetchStats, fetchLearningVocab, fetchMatureVocab, fetchNewVocab, fetchAnkiPath]);

  const handleSearch = useCallback(async (query: string) => {
    setSearchQuery(query);
    if (!query.trim()) {
      setSearchResults([]);
      setIsSearching(false);
      return;
    }

    setIsSearching(true);
    try {
      const response = await fetch(`/api/vocab?search=${encodeURIComponent(query)}&limit=20`);
      if (response.ok) {
        const data = await response.json();
        setSearchResults(data.items || []);
      }
    } catch (error) {
      console.error('Search failed:', error);
    }
  }, []);

  const formatVocabDisplay = (vocab: VocabEntry) => {
    if (vocab.kanji) {
      return (
        <span>
          <span className="font-medium">{vocab.kanji}</span>
          <span className="text-gray-500 text-xs ml-1">({vocab.kana})</span>
        </span>
      );
    }
    return <span className="font-medium">{vocab.kana}</span>;
  };

  if (isCollapsed) {
    return (
      <div className="w-12 bg-white border-r border-gray-200 flex flex-col items-center py-4">
        <button
          onClick={onToggle}
          className="p-2 hover:bg-gray-100 rounded-lg"
          title="Expand vocabulary"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/>
          </svg>
        </button>
        <div className="mt-4 text-xs text-center">
          <div className="text-yellow-600 font-bold">{stats.learning}</div>
          <div className="text-gray-400">学習</div>
        </div>
      </div>
    );
  }

  return (
    <div className="w-64 bg-white border-r border-gray-200 flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 flex items-center justify-between">
        <h2 className="font-bold text-gray-800">Vocabulary</h2>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setShowConfig(true)}
            className="p-1 hover:bg-gray-100 rounded"
            title="Settings"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/>
              <circle cx="12" cy="12" r="3"/>
            </svg>
          </button>
          <button
            onClick={onToggle}
            className="p-1 hover:bg-gray-100 rounded"
            title="Collapse"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="m11 17-5-5 5-5"/>
              <path d="m18 17-5-5 5-5"/>
            </svg>
          </button>
        </div>
      </div>

      {/* Search */}
      <div className="p-2 border-b border-gray-100">
        <input
          type="text"
          placeholder="Search..."
          value={searchQuery}
          onChange={(e) => handleSearch(e.target.value)}
          className="w-full px-3 py-1.5 text-sm bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {isSearching ? (
          // Search Results
          <div className="p-2">
            <div className="text-xs text-gray-500 mb-2">
              {searchResults.length} results
            </div>
            {searchResults.map((vocab) => (
              <button
                key={vocab.id}
                onClick={() => setSelectedVocab(vocab)}
                className="w-full text-left p-2 hover:bg-gray-50 rounded-lg text-sm"
              >
                {formatVocabDisplay(vocab)}
                <div className="text-xs text-gray-500 truncate">{vocab.meaning}</div>
              </button>
            ))}
          </div>
        ) : (
          // Category View
          <>
            {/* Learning Section */}
            <div className="border-b border-gray-100">
              <button
                onClick={() => setExpandedSection(expandedSection === 'learning' ? '' : 'learning')}
                className="w-full p-3 flex items-center justify-between hover:bg-gray-50"
              >
                <span className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-yellow-500"></span>
                  <span className="font-medium text-sm">Learning</span>
                </span>
                <span className="text-sm text-gray-500">{stats.learning}</span>
              </button>
              {expandedSection === 'learning' && (
                <div className="px-2 pb-2 max-h-60 overflow-y-auto">
                  {learningVocab.length === 0 ? (
                    <div className="text-xs text-gray-400 p-2 text-center">
                      No vocabulary yet
                    </div>
                  ) : (
                    learningVocab.map((vocab) => (
                      <button
                        key={vocab.id}
                        onClick={() => setSelectedVocab(vocab)}
                        className="w-full text-left p-2 hover:bg-gray-50 rounded text-sm"
                      >
                        {formatVocabDisplay(vocab)}
                        <div className="text-xs text-gray-500 truncate">{vocab.meaning}</div>
                      </button>
                    ))
                  )}
                </div>
              )}
            </div>

            {/* Mature Section */}
            <div className="border-b border-gray-100">
              <button
                onClick={() => setExpandedSection(expandedSection === 'mature' ? '' : 'mature')}
                className="w-full p-3 flex items-center justify-between hover:bg-gray-50"
              >
                <span className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-green-500"></span>
                  <span className="font-medium text-sm">Mature</span>
                </span>
                <span className="text-sm text-gray-500">{stats.mature}</span>
              </button>
              {expandedSection === 'mature' && (
                <div className="px-2 pb-2 max-h-60 overflow-y-auto">
                  {matureVocab.length === 0 ? (
                    <div className="text-xs text-gray-400 p-2 text-center">
                      No mature vocabulary yet
                    </div>
                  ) : (
                    matureVocab.map((vocab) => (
                      <button
                        key={vocab.id}
                        onClick={() => setSelectedVocab(vocab)}
                        className="w-full text-left p-2 hover:bg-gray-50 rounded text-sm"
                      >
                        {formatVocabDisplay(vocab)}
                        <div className="text-xs text-gray-500 truncate">{vocab.meaning}</div>
                      </button>
                    ))
                  )}
                </div>
              )}
            </div>

            {/* New Section */}
            <div className="border-b border-gray-100">
              <button
                onClick={() => setExpandedSection(expandedSection === 'new' ? '' : 'new')}
                className="w-full p-3 flex items-center justify-between hover:bg-gray-50"
              >
                <span className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                  <span className="font-medium text-sm">New</span>
                </span>
                <span className="text-sm text-gray-500">{stats.new}</span>
              </button>
              {expandedSection === 'new' && (
                <div className="px-2 pb-2 max-h-60 overflow-y-auto">
                  {newVocab.length === 0 ? (
                    <div className="text-xs text-gray-400 p-2 text-center">
                      No new vocabulary yet
                    </div>
                  ) : (
                    newVocab.map((vocab) => (
                      <button
                        key={vocab.id}
                        onClick={() => setSelectedVocab(vocab)}
                        className="w-full text-left p-2 hover:bg-gray-50 rounded text-sm"
                      >
                        {formatVocabDisplay(vocab)}
                        <div className="text-xs text-gray-500 truncate">{vocab.meaning}</div>
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
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-sm w-full mx-4 p-4">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="text-xl font-bold">
                  {selectedVocab.kanji || selectedVocab.kana}
                </h3>
                {selectedVocab.kanji && (
                  <p className="text-gray-500">{selectedVocab.kana}</p>
                )}
              </div>
              <button
                onClick={() => setSelectedVocab(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>
            <p className="text-gray-700 mb-4">{selectedVocab.meaning}</p>
            <div className="text-sm text-gray-500">
              <span className="font-medium">Status:</span> {selectedVocab.status}
            </div>
          </div>
        </div>
      )}

      {/* Config Modal */}
      {showConfig && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-4">
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-lg font-bold">Anki Settings</h3>
              <button
                onClick={() => setShowConfig(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Anki Collection Path
              </label>
              <input
                type="text"
                value={ankiPath}
                onChange={(e) => setAnkiPath(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="~/Library/Application Support/Anki2/User 1/collection.anki2"
              />
              <div className="mt-1 text-xs">
                {ankiPathExists ? (
                  <span className="text-green-600">File found</span>
                ) : (
                  <span className="text-red-500">File not found</span>
                )}
              </div>
            </div>

            <div className="flex gap-2">
              <button
                onClick={async () => {
                  const result = await saveAnkiPath(ankiPath);
                  if (result) {
                    setSyncMessage('Path saved');
                    setTimeout(() => setSyncMessage(''), 2000);
                  }
                }}
                className="flex-1 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm font-medium"
              >
                Save Path
              </button>
              <button
                onClick={syncAnki}
                disabled={isSyncing}
                className="flex-1 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg text-sm font-medium disabled:opacity-50"
              >
                {isSyncing ? 'Syncing...' : 'Sync Now'}
              </button>
            </div>

            {syncMessage && (
              <div className="mt-3 text-sm text-center text-gray-600">
                {syncMessage}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Footer Stats */}
      <div className="p-3 border-t border-gray-200 bg-gray-50 text-xs text-gray-500">
        Total: {stats.total} words
      </div>
    </div>
  );
};

export default VocabSidebar;
