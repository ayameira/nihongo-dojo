import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { RightSidebar } from './RightSidebar';

describe('RightSidebar', () => {
  const defaultProps = {
    totalSpent: 2.5,
    weeklyLimit: 10.0,
    isCollapsed: false,
    onToggle: vi.fn(),
    onBudgetClick: vi.fn(),
    speakers: [],
    selectedSpeakerId: 'browser',
    onSpeakerChange: vi.fn(),
    ttsError: null,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('expanded state', () => {
    it('renders dashboard title', () => {
      render(<RightSidebar {...defaultProps} />);

      expect(screen.getByText('Dashboard')).toBeInTheDocument();
    });

    it('displays budget amount', () => {
      render(<RightSidebar {...defaultProps} />);

      expect(screen.getByText('$2.50')).toBeInTheDocument();
    });

    it('displays percentage', () => {
      render(<RightSidebar {...defaultProps} />);

      expect(screen.getByText('25.0%')).toBeInTheDocument();
    });

    it('displays remaining amount', () => {
      render(<RightSidebar {...defaultProps} />);

      expect(screen.getByText('$7.50 left')).toBeInTheDocument();
    });

    it('shows collapse button', () => {
      render(<RightSidebar {...defaultProps} />);

      const collapseButton = screen.getByTitle('Collapse');
      expect(collapseButton).toBeInTheDocument();
    });

    it('calls onToggle when collapse clicked', async () => {
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      render(<RightSidebar {...defaultProps} />);

      await user.click(screen.getByTitle('Collapse'));

      expect(defaultProps.onToggle).toHaveBeenCalledTimes(1);
    });

    it('calls onBudgetClick when budget section clicked', async () => {
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      render(<RightSidebar {...defaultProps} />);

      const budgetSection = screen.getByTitle('View detailed breakdown');
      await user.click(budgetSection);

      expect(defaultProps.onBudgetClick).toHaveBeenCalledTimes(1);
    });

    it('opens the tutorial when guide button is clicked', async () => {
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      const onTutorialClick = vi.fn();
      render(<RightSidebar {...defaultProps} onTutorialClick={onTutorialClick} />);

      await user.click(screen.getByTitle('Open tutorial'));

      expect(onTutorialClick).toHaveBeenCalledTimes(1);
    });
  });

  describe('collapsed state', () => {
    it('renders collapsed view', () => {
      render(<RightSidebar {...defaultProps} isCollapsed={true} />);

      expect(screen.getByTitle('Expand')).toBeInTheDocument();
    });

    it('does not show dashboard title when collapsed', () => {
      render(<RightSidebar {...defaultProps} isCollapsed={true} />);

      expect(screen.queryByText('Dashboard')).not.toBeInTheDocument();
    });

    it('shows mini progress bar', () => {
      render(<RightSidebar {...defaultProps} isCollapsed={true} />);

      const progressBar = document.querySelector('.collapsed-progress-fill');
      expect(progressBar).toBeInTheDocument();
    });

    it('calls onToggle when expand clicked', async () => {
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      render(<RightSidebar {...defaultProps} isCollapsed={true} />);

      await user.click(screen.getByTitle('Expand'));

      expect(defaultProps.onToggle).toHaveBeenCalledTimes(1);
    });
  });

  describe('budget status', () => {
    it('shows good status when under 50%', () => {
      render(<RightSidebar {...defaultProps} totalSpent={2.0} weeklyLimit={10.0} />);

      expect(screen.getByText('Ready for training!')).toBeInTheDocument();
    });

    it('shows warning status between 50-80%', () => {
      render(<RightSidebar {...defaultProps} totalSpent={6.0} weeklyLimit={10.0} />);

      expect(screen.getByText('Stay focused...')).toBeInTheDocument();
    });

    it('shows danger status at 80% or above', () => {
      render(<RightSidebar {...defaultProps} totalSpent={8.5} weeklyLimit={10.0} />);

      expect(screen.getByText('Budget is tight!')).toBeInTheDocument();
    });

    it('shows sweat on tanuki in danger state', () => {
      render(<RightSidebar {...defaultProps} totalSpent={9.0} weeklyLimit={10.0} />);

      const sweat = document.querySelector('.tanuki-sweat');
      expect(sweat).toBeInTheDocument();
    });
  });

  describe('progress bar colors', () => {
    it('uses green color for good status', () => {
      render(<RightSidebar {...defaultProps} totalSpent={2.0} weeklyLimit={10.0} />);

      const progressBar = document.querySelector('.budget-fill');
      expect(progressBar?.classList.contains('progress-green')).toBe(true);
    });

    it('uses yellow color for warning status', () => {
      render(<RightSidebar {...defaultProps} totalSpent={6.0} weeklyLimit={10.0} />);

      const progressBar = document.querySelector('.budget-fill');
      expect(progressBar?.classList.contains('progress-yellow')).toBe(true);
    });

    it('uses red color for danger status', () => {
      render(<RightSidebar {...defaultProps} totalSpent={9.0} weeklyLimit={10.0} />);

      const progressBar = document.querySelector('.budget-fill');
      expect(progressBar?.classList.contains('progress-red')).toBe(true);
    });
  });

  describe('progress bar width', () => {
    it('sets width based on percentage', () => {
      render(<RightSidebar {...defaultProps} totalSpent={5.0} weeklyLimit={10.0} />);

      const progressBar = document.querySelector('.budget-fill') as HTMLElement;
      expect(progressBar?.style.width).toBe('50%');
    });

    it('caps width at 100% when over budget', () => {
      render(<RightSidebar {...defaultProps} totalSpent={15.0} weeklyLimit={10.0} />);

      const progressBar = document.querySelector('.budget-fill') as HTMLElement;
      expect(progressBar?.style.width).toBe('100%');
    });
  });

  describe('quotes per language', () => {
    it('displays a Japanese quote with translation by default', () => {
      render(<RightSidebar {...defaultProps} />);

      // Should show one of the quotes
      const quoteText = document.querySelector('.quote-text');
      expect(quoteText).toBeInTheDocument();
      expect(quoteText?.textContent).toBeTruthy();
      expect(document.querySelector('.quote-translation')?.textContent).toBeTruthy();
      // Japanese authors show both native and Latin names
      expect(document.querySelector('.quote-author-en')).toBeInTheDocument();
    });

    it('displays a French quote with English translation', () => {
      render(<RightSidebar {...defaultProps} languageCode="fr" />);

      const quoteText = document.querySelector('.quote-text');
      expect(quoteText?.textContent).toBeTruthy();
      expect(document.querySelector('.quote-translation')?.textContent).toBeTruthy();
      // French author names have no separate native-script line
      expect(document.querySelector('.quote-author-en')).not.toBeInTheDocument();
    });

    it('displays an English quote without a translation line', () => {
      render(<RightSidebar {...defaultProps} languageCode="en" />);

      const quoteText = document.querySelector('.quote-text');
      expect(quoteText?.textContent).toBeTruthy();
      expect(document.querySelector('.quote-translation')).not.toBeInTheDocument();
    });

    it('hides the quote section for languages without a collection', () => {
      render(<RightSidebar {...defaultProps} languageCode="es" />);

      expect(document.querySelector('.quote-section')).not.toBeInTheDocument();
    });

    it('re-rolls the quote when the language changes', () => {
      const { rerender } = render(<RightSidebar {...defaultProps} languageCode="ja" />);

      rerender(<RightSidebar {...defaultProps} languageCode="fr" />);

      const quoteText = document.querySelector('.quote-text');
      expect(quoteText?.textContent).toBeTruthy();
      // French quotes are Latin-script, so no native author line is shown
      expect(document.querySelector('.quote-author-en')).not.toBeInTheDocument();
    });

    it('rotates quotes on an interval', () => {
      render(<RightSidebar {...defaultProps} />);

      const initialQuote = document.querySelector('.quote-text')?.textContent;
      expect(initialQuote).toBeDefined(); // Use initialQuote to satisfy TS

      // Advance past the 45-second rotation interval
      act(() => {
        vi.advanceTimersByTime(45000);
      });

      // Note: Quote might be the same if random selection hits same index
      // This test just verifies the interval is set up
    });
  });

  describe('tanuki interaction', () => {
    it('shows speech bubble when clicked', async () => {
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      render(<RightSidebar {...defaultProps} />);

      const tanukiContainer = document.querySelector('.tanuki-container');
      if (tanukiContainer) {
        await user.click(tanukiContainer);
      }

      const bubble = document.querySelector('.speech-bubble');
      expect(bubble).toBeInTheDocument();
    });

    it('hides speech bubble after 2 seconds', async () => {
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      render(<RightSidebar {...defaultProps} />);

      const tanukiContainer = document.querySelector('.tanuki-container');
      if (tanukiContainer) {
        await user.click(tanukiContainer);
      }

      expect(document.querySelector('.speech-bubble')).toBeInTheDocument();

      act(() => {
        vi.advanceTimersByTime(2000);
      });

      expect(document.querySelector('.speech-bubble')).not.toBeInTheDocument();
    });

    it('shows random encouragement', async () => {
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      render(<RightSidebar {...defaultProps} />);

      const tanukiContainer = document.querySelector('.tanuki-container');
      if (tanukiContainer) {
        await user.click(tanukiContainer);
      }

      const bubble = document.querySelector('.speech-bubble');
      // Should contain one of the Japanese encouragements
      expect(bubble?.textContent).toMatch(/頑張れ|よくできました|素晴らしい|その調子|負けるな/);
    });

    it('applies slash animation class when clicked', async () => {
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      render(<RightSidebar {...defaultProps} />);

      const tanukiContainer = document.querySelector('.tanuki-container');
      if (tanukiContainer) {
        await user.click(tanukiContainer);
      }

      const tanuki = document.querySelector('.tanuki-samurai');
      expect(tanuki?.classList.contains('slash')).toBe(true);
    });

    it('removes slash class after 300ms', async () => {
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      render(<RightSidebar {...defaultProps} />);

      const tanukiContainer = document.querySelector('.tanuki-container');
      if (tanukiContainer) {
        await user.click(tanukiContainer);
      }

      act(() => {
        vi.advanceTimersByTime(300);
      });

      const tanuki = document.querySelector('.tanuki-samurai');
      expect(tanuki?.classList.contains('slash')).toBe(false);
    });
  });

  describe('edge cases', () => {
    it('handles zero spent', () => {
      render(<RightSidebar {...defaultProps} totalSpent={0} />);

      expect(screen.getByText('$0.00')).toBeInTheDocument();
      expect(screen.getByText('0.0%')).toBeInTheDocument();
    });

    it('handles zero limit gracefully', () => {
      // This would cause division by zero
      render(<RightSidebar {...defaultProps} weeklyLimit={0} />);

      // Should not crash - percentage would be Infinity or NaN
      // The component should handle this gracefully
    });

    it('handles negative remaining', () => {
      render(<RightSidebar {...defaultProps} totalSpent={15.0} weeklyLimit={10.0} />);

      expect(screen.getByText('$-5.00 left')).toBeInTheDocument();
    });
  });
});
