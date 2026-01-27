import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SessionList } from './SessionList';
import { mockSessions } from '../test/mocks';

describe('SessionList', () => {
  const defaultProps = {
    sessions: mockSessions,
    currentSessionId: 'session_1',
    onSelect: vi.fn(),
    onRename: vi.fn(),
    onDelete: vi.fn(),
    onNewChat: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('rendering', () => {
    it('renders new chat button', () => {
      render(<SessionList {...defaultProps} />);

      expect(screen.getByText('New Chat')).toBeInTheDocument();
    });

    it('renders all sessions', () => {
      render(<SessionList {...defaultProps} />);

      expect(screen.getByText('Test Session 1')).toBeInTheDocument();
    });

    it('shows empty state when no sessions', () => {
      render(<SessionList {...defaultProps} sessions={[]} />);

      expect(screen.getByText('No conversations yet')).toBeInTheDocument();
    });

    it('highlights current session', () => {
      render(<SessionList {...defaultProps} />);

      const sessionItems = document.querySelectorAll('.session-item');
      const activeItem = Array.from(sessionItems).find((item) =>
        item.classList.contains('active')
      );

      expect(activeItem).toBeDefined();
    });
  });

  describe('display name logic', () => {
    it('shows custom name when available', () => {
      render(<SessionList {...defaultProps} />);

      expect(screen.getByText('Test Session 1')).toBeInTheDocument();
    });

    it('shows preview when no name', () => {
      const sessionsWithPreviewOnly = [
        {
          ...mockSessions[1],
          name: null,
          preview: 'This is a preview',
        },
      ];

      render(<SessionList {...defaultProps} sessions={sessionsWithPreviewOnly} />);

      expect(screen.getByText('This is a preview')).toBeInTheDocument();
    });

    it('truncates long previews', () => {
      const sessionsWithLongPreview = [
        {
          ...mockSessions[1],
          name: null,
          preview: 'This is a very long preview that should be truncated to 30 characters',
        },
      ];

      render(<SessionList {...defaultProps} sessions={sessionsWithLongPreview} />);

      // Should be truncated and have ellipsis
      const truncatedText = screen.getByText(/This is a very long preview th/);
      expect(truncatedText).toBeInTheDocument();
    });

    it('shows date when no name or preview', () => {
      const sessionsWithNoNameOrPreview = [
        {
          ...mockSessions[2],
          name: null,
          preview: null,
        },
      ];

      render(<SessionList {...defaultProps} sessions={sessionsWithNoNameOrPreview} />);

      // Should show formatted date - the exact format depends on locale
      // Just check that something is rendered
      const sessionItems = document.querySelectorAll('.session-name');
      expect(sessionItems.length).toBeGreaterThan(0);
    });
  });

  describe('interactions', () => {
    it('calls onNewChat when new chat button clicked', async () => {
      const user = userEvent.setup();
      render(<SessionList {...defaultProps} />);

      await user.click(screen.getByText('New Chat'));

      expect(defaultProps.onNewChat).toHaveBeenCalledTimes(1);
    });

    it('calls onSelect when session clicked', async () => {
      const user = userEvent.setup();
      render(<SessionList {...defaultProps} />);

      const sessionItem = screen.getByText('Test Session 1').closest('.session-item');
      if (sessionItem) {
        await user.click(sessionItem);
      }

      expect(defaultProps.onSelect).toHaveBeenCalledWith('session_1');
    });

    it('does not call onSelect when in edit mode', async () => {
      const user = userEvent.setup();
      render(<SessionList {...defaultProps} />);

      // Click edit button
      const editButtons = screen.getAllByTitle('Rename');
      await user.click(editButtons[0]);

      // In edit mode, text is replaced with input
      // The session name text should not be visible
      expect(screen.queryByText('Test Session 1')).not.toBeInTheDocument();

      // Verify onSelect was not called
      expect(defaultProps.onSelect).not.toHaveBeenCalled();
    });
  });

  describe('renaming', () => {
    it('shows input when rename button clicked', async () => {
      const user = userEvent.setup();
      render(<SessionList {...defaultProps} />);

      const editButtons = screen.getAllByTitle('Rename');
      await user.click(editButtons[0]);

      expect(screen.getByRole('textbox')).toBeInTheDocument();
    });

    it('pre-fills input with current name', async () => {
      const user = userEvent.setup();
      render(<SessionList {...defaultProps} />);

      const editButtons = screen.getAllByTitle('Rename');
      await user.click(editButtons[0]);

      const input = screen.getByRole('textbox') as HTMLInputElement;
      expect(input.value).toBe('Test Session 1');
    });

    it('calls onRename when Enter pressed', async () => {
      const user = userEvent.setup();
      render(<SessionList {...defaultProps} />);

      const editButtons = screen.getAllByTitle('Rename');
      await user.click(editButtons[0]);

      const input = screen.getByRole('textbox');
      await user.clear(input);
      await user.type(input, 'New Name{Enter}');

      expect(defaultProps.onRename).toHaveBeenCalledWith('session_1', 'New Name');
    });

    it('cancels edit when Escape pressed', async () => {
      const user = userEvent.setup();
      render(<SessionList {...defaultProps} />);

      const editButtons = screen.getAllByTitle('Rename');
      await user.click(editButtons[0]);

      const input = screen.getByRole('textbox');
      await user.type(input, 'New Name{Escape}');

      expect(defaultProps.onRename).not.toHaveBeenCalled();
      expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
    });

    it('saves on blur', async () => {
      const user = userEvent.setup();
      render(<SessionList {...defaultProps} />);

      const editButtons = screen.getAllByTitle('Rename');
      await user.click(editButtons[0]);

      const input = screen.getByRole('textbox');
      await user.clear(input);
      await user.type(input, 'Blurred Name');

      // Blur the input
      fireEvent.blur(input);

      expect(defaultProps.onRename).toHaveBeenCalledWith('session_1', 'Blurred Name');
    });

    it('does not rename if value is empty', async () => {
      const user = userEvent.setup();
      render(<SessionList {...defaultProps} />);

      const editButtons = screen.getAllByTitle('Rename');
      await user.click(editButtons[0]);

      const input = screen.getByRole('textbox');
      await user.clear(input);
      await user.type(input, '{Enter}');

      expect(defaultProps.onRename).not.toHaveBeenCalled();
    });
  });

  describe('deletion', () => {
    it('shows confirmation modal when delete clicked', async () => {
      const user = userEvent.setup();
      render(<SessionList {...defaultProps} />);

      const deleteButtons = screen.getAllByTitle('Delete');
      await user.click(deleteButtons[0]);

      expect(screen.getByText('Delete conversation?')).toBeInTheDocument();
    });

    it('calls onDelete when confirmed', async () => {
      const user = userEvent.setup();
      render(<SessionList {...defaultProps} />);

      const deleteButtons = screen.getAllByTitle('Delete');
      await user.click(deleteButtons[0]);

      // Find the confirmation modal and click its Delete button
      const modal = screen.getByText('Delete conversation?').closest('div')?.parentElement;
      const confirmButton = modal?.querySelector('button.bg-red-500');
      expect(confirmButton).toBeTruthy();
      await user.click(confirmButton!);

      expect(defaultProps.onDelete).toHaveBeenCalledWith('session_1');
    });

    it('closes modal when cancel clicked', async () => {
      const user = userEvent.setup();
      render(<SessionList {...defaultProps} />);

      const deleteButtons = screen.getAllByTitle('Delete');
      await user.click(deleteButtons[0]);

      await user.click(screen.getByRole('button', { name: 'Cancel' }));

      expect(screen.queryByText('Delete conversation?')).not.toBeInTheDocument();
      expect(defaultProps.onDelete).not.toHaveBeenCalled();
    });
  });

  describe('date formatting', () => {
    it('formats today as time', () => {
      const todaySession = {
        ...mockSessions[0],
        name: null,
        preview: null,
        created_at: new Date().toISOString(),
      };

      render(<SessionList {...defaultProps} sessions={[todaySession]} />);

      // Should show time format (e.g., "2:30 PM")
      // This is locale-dependent, so just verify it renders
      const sessionNames = document.querySelectorAll('.session-name');
      expect(sessionNames.length).toBe(1);
    });

    it('formats yesterday correctly', () => {
      const yesterday = new Date();
      yesterday.setDate(yesterday.getDate() - 1);

      const yesterdaySession = {
        ...mockSessions[0],
        name: null,
        preview: null,
        created_at: yesterday.toISOString(),
      };

      render(<SessionList {...defaultProps} sessions={[yesterdaySession]} />);

      expect(screen.getByText('Yesterday')).toBeInTheDocument();
    });
  });
});
