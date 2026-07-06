import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { FirstRunTutorial } from './FirstRunTutorial';

describe('FirstRunTutorial', () => {
  const defaultProps = {
    isOpen: true,
    onFinish: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    document.body.innerHTML = '';
  });

  it('does not render when closed', () => {
    render(<FirstRunTutorial {...defaultProps} isOpen={false} />);

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('starts with deck setup guidance', () => {
    render(<FirstRunTutorial {...defaultProps} />);

    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('Connect Your Decks')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Back' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Next' })).toBeInTheDocument();
  });

  it('keeps only Back and Next in the footer controls', () => {
    const { container } = render(<FirstRunTutorial {...defaultProps} />);

    const actions = container.querySelector('.tutorial-actions');
    expect(actions).toBeInTheDocument();
    expect(within(actions as HTMLElement).getAllByRole('button')).toHaveLength(2);
    expect(within(actions as HTMLElement).getByRole('button', { name: 'Back' })).toBeInTheDocument();
    expect(within(actions as HTMLElement).getByRole('button', { name: 'Next' })).toBeInTheDocument();
    expect(screen.queryByText('Skip guide')).not.toBeInTheDocument();
    expect(screen.queryByText('Open deck setup')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '1' })).not.toBeInTheDocument();
  });

  it('asks the app to prepare the visible tutorial step', () => {
    const onStepChange = vi.fn();

    render(<FirstRunTutorial {...defaultProps} onStepChange={onStepChange} />);

    expect(onStepChange).toHaveBeenCalledWith('decks');
  });

  it('draws a spotlight around the current target when it exists', async () => {
    const target = document.createElement('button');
    target.dataset.tutorialTarget = 'deck-settings';
    target.textContent = 'Configure decks';
    target.getBoundingClientRect = vi.fn(() => ({
      x: 24,
      y: 42,
      top: 42,
      left: 24,
      right: 56,
      bottom: 74,
      width: 32,
      height: 32,
      toJSON: () => ({}),
    }));
    document.body.appendChild(target);

    render(<FirstRunTutorial {...defaultProps} />);

    await waitFor(() => {
      expect(document.querySelector('.tutorial-spotlight')).toBeInTheDocument();
    });
    expect(screen.getByText('Vocabulary settings')).toBeInTheDocument();
  });

  it('moves through tutorial steps', async () => {
    const user = userEvent.setup();
    render(<FirstRunTutorial {...defaultProps} />);

    await user.click(screen.getByRole('button', { name: 'Next' }));
    expect(screen.getByText('Chat With The Tutor')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Next' }));
    expect(screen.getByText('Review Your Profile')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Next' }));
    expect(screen.getByText('Track Grammar Points')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Next' }));
    expect(defaultProps.onFinish).toHaveBeenCalledTimes(1);
  });

  it('goes back to the previous step', async () => {
    const user = userEvent.setup();
    render(<FirstRunTutorial {...defaultProps} />);

    await user.click(screen.getByRole('button', { name: 'Next' }));
    expect(screen.getByText('Chat With The Tutor')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Back' }));

    expect(screen.getByText('Connect Your Decks')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Back' })).toBeDisabled();
  });

  it('stays in the tutorial when the highlighted target is clicked', async () => {
    const user = userEvent.setup();
    const target = document.createElement('button');
    target.dataset.tutorialTarget = 'deck-settings';
    target.textContent = 'Configure decks';
    target.getBoundingClientRect = vi.fn(() => ({
      x: 24,
      y: 42,
      top: 42,
      left: 24,
      right: 56,
      bottom: 74,
      width: 32,
      height: 32,
      toJSON: () => ({}),
    }));
    document.body.appendChild(target);

    render(<FirstRunTutorial {...defaultProps} />);

    await user.click(target);

    await waitFor(() => {
      expect(screen.getByText('Keep using the app here. The guide will wait while you finish this step.')).toBeInTheDocument();
    });
    expect(defaultProps.onFinish).not.toHaveBeenCalled();
  });

  it('finishes when closed or dismissed with Escape', async () => {
    const user = userEvent.setup();
    render(<FirstRunTutorial {...defaultProps} />);

    await user.click(screen.getByTitle('Close tutorial'));
    expect(defaultProps.onFinish).toHaveBeenCalledTimes(1);

    await user.keyboard('{Escape}');
    expect(defaultProps.onFinish).toHaveBeenCalledTimes(2);
  });
});
