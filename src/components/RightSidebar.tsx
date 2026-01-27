import React, { useState, useEffect } from 'react';
import { literaryQuotes } from '../data/literaryQuotes';

interface RightSidebarProps {
  totalSpent: number;
  weeklyLimit: number;
  isCollapsed: boolean;
  onToggle: () => void;
  onBudgetClick: () => void;
}

const encouragements = [
  '頑張れ！',
  'よくできました！',
  '素晴らしい！',
  'その調子！',
  '負けるな！',
];

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
          {/* Helmet */}
          <div className="tanuki-helmet" />
          {/* Face */}
          <div className="tanuki-face">
            <div className="tanuki-eye left" />
            <div className="tanuki-eye right" />
            <div className="tanuki-nose" />
            {budgetStatus === 'danger' && <div className="tanuki-sweat" />}
          </div>
          {/* Ears */}
          <div className="tanuki-ear left" />
          <div className="tanuki-ear right" />
          {/* Body/armor */}
          <div className="tanuki-armor" />
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
        <button onClick={onToggle} className="sidebar-toggle" title="Collapse">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="9 18 15 12 9 6" />
          </svg>
        </button>
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
