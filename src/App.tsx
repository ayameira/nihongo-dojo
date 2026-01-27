import { useState, useEffect, useCallback } from 'react';
import Chat from './components/Chat';
import VocabSidebar from './components/VocabSidebar';
import CostDashboard, { CostIndicator } from './components/CostDashboard';
import { useSessions } from './hooks/useSessions';

function App() {
  const [notesContent, setNotesContent] = useState<string>("");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => {
    const saved = localStorage.getItem('nihongo_sidebar_collapsed');
    return saved ? JSON.parse(saved) : false;
  });
  const [showCostDashboard, setShowCostDashboard] = useState(false);

  // Session management
  const {
    sessions,
    currentSessionId,
    isLoading: sessionsLoading,
    createSession,
    switchSession,
    renameSession,
    deleteSession,
  } = useSessions();

  const fetchNotes = useCallback(async () => {
    try {
      const response = await fetch('/api/notes');
      if (response.ok) {
        const data = await response.json();
        setNotesContent(data.content);
      }
    } catch (error) {
      console.error('Failed to fetch notes:', error);
    }
  }, []);

  useEffect(() => {
    fetchNotes();
    // Refresh notes periodically
    const interval = setInterval(fetchNotes, 30000);
    return () => clearInterval(interval);
  }, [fetchNotes]);

  useEffect(() => {
    localStorage.setItem('nihongo_sidebar_collapsed', JSON.stringify(sidebarCollapsed));
  }, [sidebarCollapsed]);

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Vocabulary Sidebar */}
      <VocabSidebar
        isCollapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
        sessions={sessions}
        currentSessionId={currentSessionId}
        onSessionSelect={switchSession}
        onSessionRename={renameSession}
        onSessionDelete={deleteSession}
        onNewChat={createSession}
      />

      {/* Main Content */}
      <main className="flex-1 flex flex-col max-w-2xl mx-auto relative">
        {/* Cost Indicator in header area */}
        <div className="absolute top-4 right-4 z-20">
          <CostIndicator onClick={() => setShowCostDashboard(true)} />
        </div>

        {sessionsLoading ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-gray-500">Loading...</div>
          </div>
        ) : (
          <Chat
            blackboardContent={notesContent}
            onRefreshNotes={fetchNotes}
            sessionId={currentSessionId}
          />
        )}
      </main>

      {/* Cost Dashboard Modal */}
      <CostDashboard
        isOpen={showCostDashboard}
        onClose={() => setShowCostDashboard(false)}
      />
    </div>
  );
}

export default App;
