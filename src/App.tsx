import { useState, useEffect, useCallback, useRef } from 'react';
import Chat from './components/Chat';
import VocabSidebar from './components/VocabSidebar';
import RightSidebar from './components/RightSidebar';
import CostDashboard from './components/CostDashboard';
import GrammarPage from './components/GrammarPage';
import FirstRunTutorial from './components/FirstRunTutorial';
import type { TutorialStepId } from './components/FirstRunTutorial';
import { useSessions } from './hooks/useSessions';
import { useTTS } from './hooks/useTTS';
import { useFacts } from './hooks/useFacts';
import { useTheme } from './hooks/useTheme';
import { useLanguageProfiles } from './hooks/useLanguageProfiles';

interface LimitInfo {
  spent: number;
  limit: number;
  remaining: number;
  period: string;
}

const MIN_SIDEBAR_WIDTH = 200;
const MAX_SIDEBAR_WIDTH = 500;
const DEFAULT_LEFT_WIDTH = 256;
const DEFAULT_RIGHT_WIDTH = 240;
const COLLAPSED_WIDTH = 48;
const TUTORIAL_STORAGE_KEY = 'nihongo_first_run_tutorial_complete';

function App() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => {
    const saved = localStorage.getItem('nihongo_sidebar_collapsed');
    return saved ? JSON.parse(saved) : false;
  });
  const [rightSidebarCollapsed, setRightSidebarCollapsed] = useState(() => {
    const saved = localStorage.getItem('nihongo_right_sidebar_collapsed');
    return saved ? JSON.parse(saved) : false;
  });
  const [leftSidebarWidth, setLeftSidebarWidth] = useState(() => {
    const saved = localStorage.getItem('nihongo_left_sidebar_width');
    return saved ? parseInt(saved, 10) : DEFAULT_LEFT_WIDTH;
  });
  const [rightSidebarWidth, setRightSidebarWidth] = useState(() => {
    const saved = localStorage.getItem('nihongo_right_sidebar_width');
    return saved ? parseInt(saved, 10) : DEFAULT_RIGHT_WIDTH;
  });
  const [showCostDashboard, setShowCostDashboard] = useState(false);
  const [showAnkiSetup, setShowAnkiSetup] = useState(false);
  const [showFirstRunTutorial, setShowFirstRunTutorial] = useState(() => {
    return localStorage.getItem(TUTORIAL_STORAGE_KEY) !== 'true';
  });
  const [currentView, setCurrentView] = useState<'chat' | 'grammar'>('chat');
  const [limitInfo, setLimitInfo] = useState<LimitInfo | null>(null);
  const [isResizingLeft, setIsResizingLeft] = useState(false);
  const [isResizingRight, setIsResizingRight] = useState(false);
  const [chatOpenRequest, setChatOpenRequest] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);
  const leftSidebarRef = useRef<HTMLDivElement>(null);
  const rightSidebarRef = useRef<HTMLDivElement>(null);

  // Session management
  const {
    profiles,
    activeLanguageCode,
    activeProfile,
    setActiveLanguageCode,
  } = useLanguageProfiles();

  const {
    sessions,
    currentSessionId,
    isLoading: sessionsLoading,
    createSession,
    switchSession,
    renameSession,
    deleteSession,
    refreshSessions,
  } = useSessions(activeLanguageCode);

  const currentSession = sessions.find((session) => session.id === currentSessionId) || null;
  const sessionLanguageCode = currentSession?.language_code || activeLanguageCode;
  const sessionProfile = profiles.find((profile) => profile.code === sessionLanguageCode)
    || activeProfile
    || null;

  // TTS voice selection
  const {
    speakers,
    selectedSpeakerId,
    error: ttsError,
    setSelectedSpeakerId,
  } = useTTS(sessionLanguageCode);

  // Student facts management
  const {
    facts,
    isLoading: factsLoading,
    addFact,
    updateFact,
    deleteFact,
    refreshFacts,
  } = useFacts();

  // Initialize theme (applies dark class to html element)
  useTheme();

  const fetchLimitInfo = useCallback(async () => {
    try {
      const response = await fetch((import.meta.env.VITE_API_URL || '') + '/api/telemetry/limit');
      if (response.ok) {
        const data = await response.json();
        setLimitInfo(data);
      }
    } catch (error) {
      // Silently fail
    }
  }, []);

  useEffect(() => {
    fetchLimitInfo();
    const limitInterval = setInterval(fetchLimitInfo, 30000);
    return () => {
      clearInterval(limitInterval);
    };
  }, [fetchLimitInfo]);

  useEffect(() => {
    localStorage.setItem('nihongo_sidebar_collapsed', JSON.stringify(sidebarCollapsed));
  }, [sidebarCollapsed]);

  useEffect(() => {
    localStorage.setItem('nihongo_right_sidebar_collapsed', JSON.stringify(rightSidebarCollapsed));
  }, [rightSidebarCollapsed]);

  useEffect(() => {
    localStorage.setItem('nihongo_left_sidebar_width', String(leftSidebarWidth));
  }, [leftSidebarWidth]);

  useEffect(() => {
    localStorage.setItem('nihongo_right_sidebar_width', String(rightSidebarWidth));
  }, [rightSidebarWidth]);

  // Resize handlers - use direct DOM manipulation for smooth dragging
  useEffect(() => {
    let rafId: number | null = null;

    const handleMouseMove = (e: MouseEvent) => {
      if (!containerRef.current) return;

      // Cancel any pending animation frame
      if (rafId) cancelAnimationFrame(rafId);

      rafId = requestAnimationFrame(() => {
        const containerRect = containerRef.current!.getBoundingClientRect();

        if (isResizingLeft && leftSidebarRef.current) {
          const newWidth = Math.max(MIN_SIDEBAR_WIDTH, Math.min(MAX_SIDEBAR_WIDTH, e.clientX - containerRect.left));
          leftSidebarRef.current.style.width = `${newWidth}px`;
        }

        if (isResizingRight && rightSidebarRef.current) {
          const newWidth = Math.max(MIN_SIDEBAR_WIDTH, Math.min(MAX_SIDEBAR_WIDTH, containerRect.right - e.clientX));
          rightSidebarRef.current.style.width = `${newWidth}px`;
        }
      });
    };

    const handleMouseUp = () => {
      if (rafId) cancelAnimationFrame(rafId);

      // Commit final widths to state
      if (isResizingLeft && leftSidebarRef.current) {
        setLeftSidebarWidth(parseInt(leftSidebarRef.current.style.width, 10));
      }
      if (isResizingRight && rightSidebarRef.current) {
        setRightSidebarWidth(parseInt(rightSidebarRef.current.style.width, 10));
      }

      setIsResizingLeft(false);
      setIsResizingRight(false);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };

    if (isResizingLeft || isResizingRight) {
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      if (rafId) cancelAnimationFrame(rafId);
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizingLeft, isResizingRight]);

  const totalSpent = limitInfo?.spent || 0;
  const weeklyLimit = limitInfo?.limit || 10;

  const finishTutorial = useCallback(() => {
    localStorage.setItem(TUTORIAL_STORAGE_KEY, 'true');
    setShowFirstRunTutorial(false);
  }, []);

  const prepareTutorialStep = useCallback((step: TutorialStepId) => {
    if (step === 'decks') {
      setSidebarCollapsed(false);
      setShowAnkiSetup(false);
      setCurrentView('chat');
      return;
    }

    if (step === 'chat') {
      setCurrentView('chat');
      setChatOpenRequest((request) => request + 1);
      return;
    }

    if (step === 'profile') {
      setCurrentView('chat');
      return;
    }

    setSidebarCollapsed(false);
    setCurrentView('chat');
  }, []);

  return (
    <div ref={containerRef} className="flex h-screen bg-paper">
      {/* Vocabulary Sidebar */}
      <div
        ref={leftSidebarRef}
        style={{ width: sidebarCollapsed ? COLLAPSED_WIDTH : leftSidebarWidth, flexShrink: 0 }}
      >
        <VocabSidebar
          isCollapsed={sidebarCollapsed}
          onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
          sessions={sessions}
          currentSessionId={currentSessionId}
          onSessionSelect={switchSession}
          onSessionRename={renameSession}
          onSessionDelete={deleteSession}
          onNewChat={createSession}
          currentView={currentView}
          onViewChange={setCurrentView}
          setupWizardOpen={showAnkiSetup}
          onSetupWizardOpenChange={setShowAnkiSetup}
          languageCode={sessionLanguageCode}
        />
      </div>

      {/* Left Resize Handle */}
      {!sidebarCollapsed && (
        <div
          className="w-1 hover:w-1 bg-transparent hover:bg-vermillion/50 cursor-col-resize transition-colors flex-shrink-0"
          onMouseDown={(e) => {
            e.preventDefault();
            setIsResizingLeft(true);
          }}
        />
      )}

      {/* Main Content */}
      <main className="flex-1 flex flex-col relative min-w-0">
        {currentView === 'chat' ? (
          sessionsLoading ? (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-ink-muted">Loading...</div>
            </div>
          ) : (
            <Chat
              facts={facts}
              factsLoading={factsLoading}
              onAddFact={addFact}
              onUpdateFact={updateFact}
              onDeleteFact={deleteFact}
              onRefreshFacts={refreshFacts}
              sessionId={currentSessionId}
              languageCode={sessionLanguageCode}
              speechLanguage={sessionProfile?.speech_language || 'ja-JP'}
              languageProfiles={profiles}
              activeTargetLanguageCode={activeLanguageCode}
              onActiveTargetLanguageChange={setActiveLanguageCode}
              selectedSpeakerId={selectedSpeakerId}
              onRefreshSessions={refreshSessions}
              openChatRequest={chatOpenRequest}
            />
          )
        ) : (
          <GrammarPage languageCode={sessionLanguageCode} />
        )}
      </main>

      {/* Right Resize Handle */}
      {!rightSidebarCollapsed && (
        <div
          className="w-1 hover:w-1 bg-transparent hover:bg-vermillion/50 cursor-col-resize transition-colors flex-shrink-0"
          onMouseDown={(e) => {
            e.preventDefault();
            setIsResizingRight(true);
          }}
        />
      )}

      {/* Right Sidebar */}
      <div
        ref={rightSidebarRef}
        style={{ width: rightSidebarCollapsed ? COLLAPSED_WIDTH : rightSidebarWidth, flexShrink: 0 }}
      >
        <RightSidebar
          totalSpent={totalSpent}
          weeklyLimit={weeklyLimit}
          isCollapsed={rightSidebarCollapsed}
          onToggle={() => setRightSidebarCollapsed(!rightSidebarCollapsed)}
          onBudgetClick={() => setShowCostDashboard(true)}
          speakers={speakers}
          selectedSpeakerId={selectedSpeakerId}
          onSpeakerChange={setSelectedSpeakerId}
          ttsError={ttsError}
          onTutorialClick={() => setShowFirstRunTutorial(true)}
        />
      </div>

      {/* Cost Dashboard Modal */}
      <CostDashboard
        isOpen={showCostDashboard}
        onClose={() => setShowCostDashboard(false)}
      />

      <FirstRunTutorial
        isOpen={showFirstRunTutorial}
        onFinish={finishTutorial}
        onStepChange={prepareTutorialStep}
      />
    </div>
  );
}

export default App;
