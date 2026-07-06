import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from './App';

vi.mock('./hooks/useSessions', () => ({
  useSessions: () => ({
    sessions: [],
    currentSessionId: 'test_session',
    isLoading: false,
    createSession: vi.fn(),
    switchSession: vi.fn(),
    renameSession: vi.fn(),
    deleteSession: vi.fn(),
    refreshSessions: vi.fn(),
  }),
}));

vi.mock('./hooks/useTTS', () => ({
  useTTS: () => ({
    speakers: [],
    selectedSpeakerId: 0,
    error: null,
    setSelectedSpeakerId: vi.fn(),
  }),
}));

vi.mock('./hooks/useFacts', () => ({
  useFacts: () => ({
    facts: [],
    isLoading: false,
    addFact: vi.fn(),
    updateFact: vi.fn(),
    deleteFact: vi.fn(),
    refreshFacts: vi.fn(),
  }),
}));

vi.mock('./hooks/useTheme', () => ({
  useTheme: () => ({
    theme: 'light',
    resolvedTheme: 'light',
    toggleTheme: vi.fn(),
  }),
}));

vi.mock('./hooks/useLanguageProfiles', () => ({
  useLanguageProfiles: () => ({
    profiles: [
      {
        code: 'ja',
        display_name: 'Japanese',
        native_name: '日本語',
        speech_language: 'ja-JP',
        grammar_level_scheme: { name: 'JLPT', levels: ['N5', 'N4', 'N3', 'N2', 'N1'], custom_label: 'Custom', source_name: 'jlpt' },
        vocabulary_semantics: {
          term_label: 'term',
          reading_label: 'reading',
          meaning_label: 'meaning',
          part_of_speech_label: 'part of speech',
        },
      },
    ],
    activeLanguageCode: 'ja',
    activeProfile: {
      code: 'ja',
      display_name: 'Japanese',
      native_name: '日本語',
      speech_language: 'ja-JP',
      grammar_level_scheme: { name: 'JLPT', levels: ['N5', 'N4', 'N3', 'N2', 'N1'], custom_label: 'Custom', source_name: 'jlpt' },
      vocabulary_semantics: {
        term_label: 'term',
        reading_label: 'reading',
        meaning_label: 'meaning',
        part_of_speech_label: 'part of speech',
      },
    },
    setActiveLanguageCode: vi.fn(),
  }),
}));

vi.mock('./components/VocabSidebar', () => ({
  default: ({
    setupWizardOpen,
    onSetupWizardOpenChange,
  }: {
    setupWizardOpen?: boolean;
    onSetupWizardOpenChange?: (open: boolean) => void;
  }) => (
    <aside data-testid="vocab-sidebar">
      <button
        type="button"
        data-tutorial-target="deck-settings"
        onClick={() => onSetupWizardOpenChange?.(true)}
      >
        Configure decks
      </button>
      {setupWizardOpen ? 'Deck setup open' : 'Deck setup closed'}
    </aside>
  ),
}));

vi.mock('./components/RightSidebar', () => ({
  default: ({ onTutorialClick }: { onTutorialClick?: () => void }) => (
    <aside>
      <button type="button" onClick={onTutorialClick}>Guide</button>
    </aside>
  ),
}));

vi.mock('./components/Chat', () => ({
  default: () => <main>Chat surface</main>,
}));

vi.mock('./components/CostDashboard', () => ({
  default: () => null,
}));

vi.mock('./components/GrammarPage', () => ({
  default: () => <main>Grammar surface</main>,
}));

describe('App first-run tutorial', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(localStorage.getItem).mockReturnValue(null);
  });

  it('shows the tutorial on first launch and persists dismissal', async () => {
    const user = userEvent.setup();
    render(<App />);

    expect(screen.getByRole('dialog')).toBeInTheDocument();

    await user.click(screen.getByTitle('Close tutorial'));

    expect(localStorage.setItem).toHaveBeenCalledWith('nihongo_first_run_tutorial_complete', 'true');
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('does not show the tutorial after it has been completed', () => {
    vi.mocked(localStorage.getItem).mockImplementation((key) => {
      return key === 'nihongo_first_run_tutorial_complete' ? 'true' : null;
    });

    render(<App />);

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('can reopen the tutorial from the dashboard guide button', async () => {
    const user = userEvent.setup();
    vi.mocked(localStorage.getItem).mockImplementation((key) => {
      return key === 'nihongo_first_run_tutorial_complete' ? 'true' : null;
    });

    render(<App />);

    await user.click(screen.getByRole('button', { name: 'Guide' }));

    expect(screen.getByRole('dialog')).toBeInTheDocument();
  });

  it('keeps the tutorial open while the highlighted deck control is clicked', async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.click(screen.getByRole('button', { name: 'Configure decks' }));

    expect(screen.getByTestId('vocab-sidebar')).toHaveTextContent('Deck setup open');
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText('Keep using the app here. The guide will wait while you finish this step.')).toBeInTheDocument();
    });
    expect(localStorage.setItem).not.toHaveBeenCalledWith('nihongo_first_run_tutorial_complete', 'true');
  });
});
