import React, { useState, useEffect } from 'react';
import { literaryQuotes } from '../data/literaryQuotes';
import { Speaker } from '../hooks/useTTS';
import { useTheme } from '../hooks/useTheme';

interface RightSidebarProps {
  totalSpent: number;
  weeklyLimit: number;
  isCollapsed: boolean;
  onToggle: () => void;
  onBudgetClick: () => void;
  speakers: Speaker[];
  selectedSpeakerId: number;
  onSpeakerChange: (id: number) => void;
  ttsError: string | null;
  onTutorialClick?: () => void;
}

const encouragements = [
  '頑張れ！',
  'よくできました！',
  '素晴らしい！',
  'その調子！',
  '負けるな！',
];

// Theme toggle button component
const ThemeToggle: React.FC = () => {
  const { theme, resolvedTheme, toggleTheme } = useTheme();

  const getIcon = () => {
    if (theme === 'system') {
      // Computer icon for system mode
      return (
        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
          <line x1="8" y1="21" x2="16" y2="21"/>
          <line x1="12" y1="17" x2="12" y2="21"/>
        </svg>
      );
    }
    if (resolvedTheme === 'dark') {
      // Moon icon for dark mode
      return (
        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
        </svg>
      );
    }
    // Sun icon for light mode
    return (
      <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="5"/>
        <line x1="12" y1="1" x2="12" y2="3"/>
        <line x1="12" y1="21" x2="12" y2="23"/>
        <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
        <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
        <line x1="1" y1="12" x2="3" y2="12"/>
        <line x1="21" y1="12" x2="23" y2="12"/>
        <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
        <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
      </svg>
    );
  };

  const getTitle = () => {
    if (theme === 'system') return 'Theme: System (click to switch)';
    if (theme === 'light') return 'Theme: Light (click to switch)';
    return 'Theme: Dark (click to switch)';
  };

  return (
    <button
      onClick={toggleTheme}
      className="sidebar-toggle"
      title={getTitle()}
    >
      {getIcon()}
    </button>
  );
};

const TanukiSamurai: React.FC<{ budgetStatus: 'good' | 'warning' | 'danger'; onClick: () => void }> = ({
  budgetStatus,
  onClick,
}) => {
  const [isClicked, setIsClicked] = useState(false);
  const [showBubble, setShowBubble] = useState(false);
  const [encouragement, setEncouragement] = useState('');

  const handleClick = () => {
    setIsClicked(true);
    setShowBubble(true);
    setEncouragement(encouragements[Math.floor(Math.random() * encouragements.length)]);
    onClick();

    setTimeout(() => setIsClicked(false), 300);
    setTimeout(() => setShowBubble(false), 2000);
  };

  return (
    <div className="tanuki-container" onClick={handleClick}>
      {showBubble && (
        <div className="speech-bubble">
          {encouragement}
        </div>
      )}
      <div className={`tanuki-samurai ${budgetStatus} ${isClicked ? 'slash' : ''}`}>
        <div className="tanuki-body">
          {/* Leaf on head */}
          <div className="tanuki-leaf" />
          {/* Helmet with kuwagata horns */}
          <div className="tanuki-helmet" />
          <div className="tanuki-horn left" />
          <div className="tanuki-horn right" />
          <div className="tanuki-horn-center" />
          {/* Face */}
          <div className="tanuki-face">
            <div className="tanuki-muzzle" />
            <div className="tanuki-eye-patch left" />
            <div className="tanuki-eye-patch right" />
            <div className="tanuki-eyebrow left" />
            <div className="tanuki-eyebrow right" />
            <div className="tanuki-eye left" />
            <div className="tanuki-eye right" />
            <div className="tanuki-nose" />
            <div className="tanuki-whiskers" />
            {budgetStatus === 'danger' && <div className="tanuki-sweat" />}
          </div>
          {/* Ears */}
          <div className="tanuki-ear left" />
          <div className="tanuki-ear right" />
          {/* Body/armor */}
          <div className="tanuki-armor" />
          {/* Shoulder guards */}
          <div className="tanuki-sode left" />
          <div className="tanuki-sode right" />
          {/* Paws */}
          <div className="tanuki-paw left" />
          <div className="tanuki-paw right" />
          {/* Katana */}
          <div className="tanuki-katana" />
          {/* Tail */}
          <div className="tanuki-tail" />
        </div>
      </div>
    </div>
  );
};

export const RightSidebar: React.FC<RightSidebarProps> = ({
  totalSpent,
  weeklyLimit,
  isCollapsed,
  onToggle,
  onBudgetClick,
  speakers,
  selectedSpeakerId,
  onSpeakerChange,
  ttsError,
  onTutorialClick,
}) => {
  const [currentQuote, setCurrentQuote] = useState(() =>
    Math.floor(Math.random() * literaryQuotes.length)
  );

  // Rotate quotes every 45 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentQuote(Math.floor(Math.random() * literaryQuotes.length));
    }, 45000);
    return () => clearInterval(interval);
  }, []);

  const spentPercentage = (totalSpent / weeklyLimit) * 100;
  const remaining = weeklyLimit - totalSpent;

  const getBudgetStatus = (): 'good' | 'warning' | 'danger' => {
    if (spentPercentage >= 80) return 'danger';
    if (spentPercentage >= 50) return 'warning';
    return 'good';
  };

  const getProgressColor = () => {
    const status = getBudgetStatus();
    if (status === 'danger') return 'progress-red';
    if (status === 'warning') return 'progress-yellow';
    return 'progress-green';
  };

  if (isCollapsed) {
    return (
      <div className="right-sidebar collapsed" style={{ width: '100%' }}>
        <button onClick={onToggle} className="sidebar-toggle" title="Expand">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="15 18 9 12 15 6" />
          </svg>
        </button>
        <div className="collapsed-tanuki">
          <div className="mini-tanuki" />
        </div>
        <div className="collapsed-progress">
          <div
            className={`collapsed-progress-fill ${getProgressColor()}`}
            style={{ height: `${Math.min(spentPercentage, 100)}%` }}
          />
        </div>
      </div>
    );
  }

  const quote = literaryQuotes[currentQuote];

  return (
    <div className="right-sidebar expanded" style={{ width: '100%' }}>
      {/* Header */}
      <div className="sidebar-header">
        <span className="sidebar-title">Dashboard</span>
        <div className="flex items-center gap-1">
          {onTutorialClick && (
            <button onClick={onTutorialClick} className="sidebar-toggle" title="Open tutorial">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10" />
                <path d="M9.09 9a3 3 0 1 1 5.82 1c0 2-3 2-3 4" />
                <line x1="12" y1="17" x2="12.01" y2="17" />
              </svg>
            </button>
          )}
          <ThemeToggle />
          <button onClick={onToggle} className="sidebar-toggle" title="Collapse">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="9 18 15 12 9 6" />
            </svg>
          </button>
        </div>
      </div>

      {/* Budget Section */}
      <div className="budget-section" onClick={onBudgetClick} title="View detailed breakdown">
        <div className="budget-header">
          <span className="budget-label">Weekly Budget</span>
          <span className="budget-amount">${totalSpent.toFixed(2)}</span>
        </div>
        <div className="budget-bar">
          <div
            className={`budget-fill ${getProgressColor()}`}
            style={{ width: `${Math.min(spentPercentage, 100)}%` }}
          />
        </div>
        <div className="budget-footer">
          <span className="budget-percent">{spentPercentage.toFixed(1)}%</span>
          <span className="budget-remaining">${remaining.toFixed(2)} left</span>
        </div>
      </div>

      {/* Voice Selector Section */}
      <div className="voice-section">
        <div className="voice-header">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
            <path d="M15.54 8.46a5 5 0 0 1 0 7.07" />
          </svg>
          <span className="voice-label">Voice</span>
        </div>
        {ttsError ? (
          <div className="voice-error">{ttsError}</div>
        ) : speakers.length > 0 ? (
          <select
            value={selectedSpeakerId}
            onChange={(e) => onSpeakerChange(parseInt(e.target.value, 10))}
            className="voice-select"
          >
            {speakers.map((speaker) => (
              <option key={speaker.id} value={speaker.id}>
                {speaker.display_name}
              </option>
            ))}
          </select>
        ) : (
          <div className="voice-loading">Loading voices...</div>
        )}
      </div>

      {/* Quote Section */}
      <div className="quote-section">
        <div className="quote-jp">{quote.jp}</div>
        <div className="quote-en">{quote.en}</div>
        <div className="quote-attribution">
          <span className="quote-author">{quote.authorJp}</span>
          <span className="quote-author-en">{quote.author}</span>
          {quote.workJp && <span className="quote-work">『{quote.workJp}』</span>}
        </div>
      </div>

      {/* Tanuki Section */}
      <div className="tanuki-section">
        <TanukiSamurai budgetStatus={getBudgetStatus()} onClick={() => {}} />
        <div className="tanuki-caption">
          {getBudgetStatus() === 'good' && 'Ready for training!'}
          {getBudgetStatus() === 'warning' && 'Stay focused...'}
          {getBudgetStatus() === 'danger' && 'Budget is tight!'}
        </div>
      </div>
    </div>
  );
};

export default RightSidebar;
