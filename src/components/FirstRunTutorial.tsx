import React, { useCallback, useEffect, useState } from 'react';

export type TutorialStepId = 'decks' | 'chat' | 'profile' | 'grammar';
type TutorialMode = 'spotlight' | 'docked';

interface TutorialStep {
  id: TutorialStepId;
  eyebrow: string;
  title: string;
  lead: string;
  points: string[];
  targetLabel: string;
  targetSelector: string;
}

interface FirstRunTutorialProps {
  isOpen: boolean;
  onFinish: () => void;
  onStepChange?: (step: TutorialStepId) => void;
}

interface TargetBox {
  top: number;
  left: number;
  width: number;
  height: number;
}

const SPOTLIGHT_PADDING = 8;

const steps: TutorialStep[] = [
  {
    id: 'decks',
    eyebrow: 'Step 1',
    title: 'Connect Your Decks',
    lead: 'Nihongo Dojo learns from the vocabulary you already review in Anki.',
    points: [
      'Click the highlighted settings button in the vocabulary sidebar.',
      'Choose the Anki collection file, select decks, then map reading and meaning fields.',
      'After sync, words appear as New, Learning, or Mature so the tutor can aim practice at the right level.',
    ],
    targetLabel: 'Vocabulary settings',
    targetSelector: '[data-tutorial-target="deck-settings"]',
  },
  {
    id: 'chat',
    eyebrow: 'Step 2',
    title: 'Chat With The Tutor',
    lead: 'Use the chat like a practice room: ask questions, answer prompts, paste Japanese, or attach an image.',
    points: [
      'Click into the highlighted message box to start a practice turn.',
      'The tutor uses your synced vocabulary and profile to choose useful examples.',
      'After a reply, use the difficulty feedback buttons when you want the next turn easier or harder.',
    ],
    targetLabel: 'Message box',
    targetSelector: '[data-tutorial-target="message-composer"]',
  },
  {
    id: 'profile',
    eyebrow: 'Step 3',
    title: 'Review Your Profile',
    lead: 'The Profile tab is the tutor memory you can inspect and edit.',
    points: [
      'Click the highlighted Profile tab in the chat header.',
      'Add facts like goals, interests, weak spots, preferred correction style, or upcoming trips.',
      'The tutor may add useful facts during conversation, and you can edit or delete anything.',
    ],
    targetLabel: 'Profile tab',
    targetSelector: '[data-tutorial-target="profile-tab"]',
  },
  {
    id: 'grammar',
    eyebrow: 'Step 4',
    title: 'Track Grammar Points',
    lead: 'Grammar points are reusable sentence patterns, not just isolated words.',
    points: [
      'Click the highlighted Grammar button in the left sidebar.',
      'The Grammar Tree groups points by JLPT level and status: New, Learning, or Burned.',
    ],
    targetLabel: 'Grammar tree button',
    targetSelector: '[data-tutorial-target="grammar-tree"]',
  },
];

const clamp = (value: number, min: number, max: number) => Math.min(Math.max(value, min), max);

export const FirstRunTutorial: React.FC<FirstRunTutorialProps> = ({
  isOpen,
  onFinish,
  onStepChange,
}) => {
  const [stepIndex, setStepIndex] = useState(0);
  const [targetBox, setTargetBox] = useState<TargetBox | null>(null);
  const [mode, setMode] = useState<TutorialMode>('spotlight');

  const currentStep = steps[stepIndex];
  const isFirstStep = stepIndex === 0;
  const isLastStep = stepIndex === steps.length - 1;
  const activeTargetBox = mode === 'spotlight' ? targetBox : null;

  const goToStep = useCallback((index: number) => {
    setStepIndex(clamp(index, 0, steps.length - 1));
    setMode('spotlight');
  }, []);

  const goToNextStep = useCallback(() => {
    if (isLastStep) {
      onFinish();
      return;
    }

    goToStep(stepIndex + 1);
  }, [goToStep, isLastStep, onFinish, stepIndex]);

  const goToPreviousStep = useCallback(() => {
    goToStep(stepIndex - 1);
  }, [goToStep, stepIndex]);

  const updateTargetBox = useCallback(() => {
    const target = document.querySelector<HTMLElement>(currentStep.targetSelector);

    if (!target) {
      setTargetBox(null);
      return;
    }

    const rect = target.getBoundingClientRect();
    setTargetBox({
      top: rect.top,
      left: rect.left,
      width: rect.width,
      height: rect.height,
    });
  }, [currentStep.targetSelector]);

  useEffect(() => {
    if (isOpen) {
      setStepIndex(0);
      setMode('spotlight');
    }
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onFinish();
      }
      if (event.key === 'ArrowRight') {
        goToNextStep();
      }
      if (event.key === 'ArrowLeft') {
        goToPreviousStep();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [goToNextStep, goToPreviousStep, isOpen, onFinish]);

  useEffect(() => {
    if (!isOpen) return;

    onStepChange?.(currentStep.id);

    const frameId = typeof requestAnimationFrame === 'function'
      ? requestAnimationFrame(updateTargetBox)
      : 0;
    const timeoutId = window.setTimeout(updateTargetBox, 80);

    const handleUpdate = () => updateTargetBox();
    window.addEventListener('resize', handleUpdate);
    window.addEventListener('scroll', handleUpdate, true);

    return () => {
      if (frameId && typeof cancelAnimationFrame === 'function') {
        cancelAnimationFrame(frameId);
      }
      window.clearTimeout(timeoutId);
      window.removeEventListener('resize', handleUpdate);
      window.removeEventListener('scroll', handleUpdate, true);
    };
  }, [currentStep.id, isOpen, onStepChange, updateTargetBox]);

  useEffect(() => {
    if (!isOpen || mode !== 'spotlight') return;

    const handleTargetClick = (event: MouseEvent) => {
      const target = event.target instanceof Element
        ? event.target.closest(currentStep.targetSelector)
        : null;

      if (!target) return;

      window.setTimeout(() => {
        setMode('docked');
      }, 120);
    };

    document.addEventListener('click', handleTargetClick);
    return () => document.removeEventListener('click', handleTargetClick);
  }, [currentStep.targetSelector, isOpen, mode]);

  if (!isOpen) return null;

  return (
    <div className="tutorial-overlay">
      {activeTargetBox && (
        <>
          <div
            className="tutorial-spotlight"
            style={{
              top: activeTargetBox.top - SPOTLIGHT_PADDING,
              left: activeTargetBox.left - SPOTLIGHT_PADDING,
              width: activeTargetBox.width + SPOTLIGHT_PADDING * 2,
              height: activeTargetBox.height + SPOTLIGHT_PADDING * 2,
            }}
            aria-hidden="true"
          />
          <div
            className="tutorial-target-label"
            style={{
              top: Math.max(10, activeTargetBox.top - 34),
              left: Math.max(10, activeTargetBox.left - SPOTLIGHT_PADDING),
            }}
            aria-hidden="true"
          >
            {currentStep.targetLabel}
          </div>
        </>
      )}

      <div
        className={`tutorial-panel ${mode}`}
        role="dialog"
        aria-labelledby="tutorial-title"
      >
        <div className="tutorial-topline">
          <span>{currentStep.eyebrow}</span>
          <button type="button" onClick={onFinish} className="tutorial-close" title="Close tutorial">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        <h2 id="tutorial-title" className="tutorial-title">{currentStep.title}</h2>
        <p className="tutorial-lead">{currentStep.lead}</p>
        {mode === 'docked' && (
          <p className="tutorial-docked-note">
            Keep using the app here. The guide will wait while you finish this step.
          </p>
        )}

        <ul className="tutorial-points">
          {currentStep.points.map((point) => (
            <li key={point}>
              <span className="tutorial-point-mark" aria-hidden="true" />
              <span>{point}</span>
            </li>
          ))}
        </ul>

        <div className="tutorial-actions">
          <div className="tutorial-nav-actions">
            <button
              type="button"
              className="tutorial-secondary"
              onClick={goToPreviousStep}
              disabled={isFirstStep}
            >
              Back
            </button>
            <button
              type="button"
              className="tutorial-secondary"
              onClick={goToNextStep}
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FirstRunTutorial;
