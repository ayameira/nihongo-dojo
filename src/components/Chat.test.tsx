import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Chat } from './Chat';

// Mock useChat hook
const mockUseChat = vi.fn();
vi.mock('../hooks/useChat', () => ({
  useChat: () => mockUseChat(),
}));

// Mock react-markdown
vi.mock('react-markdown', () => ({
  default: ({ children }: { children: string }) => <div data-testid="markdown">{children}</div>,
}));

vi.mock('remark-gfm', () => ({
  default: () => {},
}));

describe('Chat', () => {
  const mockMessages = [
    {
      id: 'msg_1',
      role: 'user' as const,
      content: 'こんにちは',
      timestamp: new Date('2024-01-15T10:00:00Z'),
      status: 'complete' as const,
    },
    {
      id: 'msg_2',
      role: 'assistant' as const,
      content: 'こんにちは！元気ですか？',
      timestamp: new Date('2024-01-15T10:00:30Z'),
      status: 'complete' as const,
    },
  ];

  const defaultHookReturn = {
    messages: mockMessages,
    isLoading: false,
    loadingState: 'idle' as const,
    currentAction: null,
    lastUsage: null,
    pendingFeedback: null,
    sendMessage: vi.fn(),
    sendDifficultyFeedback: vi.fn(),
    clearPendingFeedback: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockUseChat.mockReturnValue(defaultHookReturn);
  });

  describe('rendering', () => {
    it('renders chat and notes tabs', () => {
      render(<Chat sessionId="test_session" />);

      expect(screen.getByRole('button', { name: 'Chat' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Notes' })).toBeInTheDocument();
    });

    it('renders messages', () => {
      render(<Chat sessionId="test_session" />);

      expect(screen.getByText('こんにちは')).toBeInTheDocument();
    });

    it('renders app title', () => {
      render(<Chat sessionId="test_session" />);

      expect(screen.getByText('日本語')).toBeInTheDocument();
      expect(screen.getByText('Dojo')).toBeInTheDocument();
    });

    it('renders message input', () => {
      render(<Chat sessionId="test_session" />);

      expect(screen.getByPlaceholderText('Write something...')).toBeInTheDocument();
    });

    it('shows empty state when no messages', () => {
      mockUseChat.mockReturnValue({ ...defaultHookReturn, messages: [] });
      render(<Chat sessionId="test_session" />);

      expect(screen.getByText('はじめましょう')).toBeInTheDocument();
      expect(screen.getByText("Let's begin your practice")).toBeInTheDocument();
    });

    it('shows active status', () => {
      render(<Chat sessionId="test_session" />);

      expect(screen.getByText('Active')).toBeInTheDocument();
    });
  });

  describe('tabs', () => {
    it('shows chat tab by default', () => {
      render(<Chat sessionId="test_session" />);

      expect(screen.getByText('こんにちは')).toBeInTheDocument();
    });

    it('switches to notes tab when clicked', async () => {
      const user = userEvent.setup();
      render(<Chat sessionId="test_session" blackboardContent="# Notes" />);

      await user.click(screen.getByRole('button', { name: 'Notes' }));

      expect(screen.getByText('Study Notes')).toBeInTheDocument();
    });

    it('shows notes content in notes tab', async () => {
      const user = userEvent.setup();
      render(<Chat sessionId="test_session" blackboardContent="## Current Focus\nLearn verbs" />);

      await user.click(screen.getByRole('button', { name: 'Notes' }));

      expect(screen.getByTestId('markdown')).toBeInTheDocument();
    });

    it('shows empty notes message when no content', async () => {
      const user = userEvent.setup();
      render(<Chat sessionId="test_session" />);

      await user.click(screen.getByRole('button', { name: 'Notes' }));

      expect(screen.getByText('No notes yet')).toBeInTheDocument();
    });

    it('switches back to chat tab', async () => {
      const user = userEvent.setup();
      render(<Chat sessionId="test_session" blackboardContent="# Notes" />);

      await user.click(screen.getByRole('button', { name: 'Notes' }));
      await user.click(screen.getByRole('button', { name: 'Chat' }));

      expect(screen.getByText('こんにちは')).toBeInTheDocument();
    });
  });

  describe('message input', () => {
    it('allows typing in input', async () => {
      const user = userEvent.setup();
      render(<Chat sessionId="test_session" />);

      const input = screen.getByPlaceholderText('Write something...');
      await user.type(input, 'Hello');

      expect(input).toHaveValue('Hello');
    });

    it('calls sendMessage when form submitted', async () => {
      const sendMessage = vi.fn();
      mockUseChat.mockReturnValue({ ...defaultHookReturn, sendMessage });

      const user = userEvent.setup();
      render(<Chat sessionId="test_session" />);

      const input = screen.getByPlaceholderText('Write something...');
      await user.type(input, 'Test message');
      await user.click(screen.getByTitle('Send'));

      expect(sendMessage).toHaveBeenCalledWith('Test message', undefined);
    });

    it('clears input after sending', async () => {
      const user = userEvent.setup();
      render(<Chat sessionId="test_session" />);

      const input = screen.getByPlaceholderText('Write something...');
      await user.type(input, 'Test message');
      await user.click(screen.getByTitle('Send'));

      expect(input).toHaveValue('');
    });

    it('does not send empty message', async () => {
      const sendMessage = vi.fn();
      mockUseChat.mockReturnValue({ ...defaultHookReturn, sendMessage });

      const user = userEvent.setup();
      render(<Chat sessionId="test_session" />);

      await user.click(screen.getByTitle('Send'));

      expect(sendMessage).not.toHaveBeenCalled();
    });

    it('disables input when loading', () => {
      mockUseChat.mockReturnValue({ ...defaultHookReturn, isLoading: true });
      render(<Chat sessionId="test_session" />);

      const input = screen.getByPlaceholderText('Write something...');
      expect(input).toBeDisabled();
    });

    it('shows attach image button', () => {
      render(<Chat sessionId="test_session" />);

      expect(screen.getByTitle('Attach image')).toBeInTheDocument();
    });
  });

  describe('difficulty feedback', () => {
    it('renders difficulty feedback buttons on assistant messages', () => {
      render(<Chat sessionId="test_session" />);

      expect(screen.getByText('Too Hard')).toBeInTheDocument();
      expect(screen.getByText('Too Easy')).toBeInTheDocument();
    });

    it('calls sendDifficultyFeedback when too hard clicked', async () => {
      const sendDifficultyFeedback = vi.fn();
      mockUseChat.mockReturnValue({ ...defaultHookReturn, sendDifficultyFeedback });

      const user = userEvent.setup();
      render(<Chat sessionId="test_session" />);

      await user.click(screen.getByText('Too Hard'));

      expect(sendDifficultyFeedback).toHaveBeenCalledWith('too_hard');
    });

    it('calls sendDifficultyFeedback when too easy clicked', async () => {
      const sendDifficultyFeedback = vi.fn();
      mockUseChat.mockReturnValue({ ...defaultHookReturn, sendDifficultyFeedback });

      const user = userEvent.setup();
      render(<Chat sessionId="test_session" />);

      await user.click(screen.getByText('Too Easy'));

      expect(sendDifficultyFeedback).toHaveBeenCalledWith('too_easy');
    });

    it('shows pending feedback indicator', () => {
      mockUseChat.mockReturnValue({ ...defaultHookReturn, pendingFeedback: 'too_hard' });
      render(<Chat sessionId="test_session" />);

      expect(screen.getByText('Easier next time')).toBeInTheDocument();
    });

    it('shows clear feedback button when feedback is pending', () => {
      mockUseChat.mockReturnValue({ ...defaultHookReturn, pendingFeedback: 'too_easy' });
      render(<Chat sessionId="test_session" />);

      expect(screen.getByText('×')).toBeInTheDocument();
    });

    it('calls clearPendingFeedback when clear clicked', async () => {
      const clearPendingFeedback = vi.fn();
      mockUseChat.mockReturnValue({
        ...defaultHookReturn,
        pendingFeedback: 'too_hard',
        clearPendingFeedback,
      });

      const user = userEvent.setup();
      render(<Chat sessionId="test_session" />);

      await user.click(screen.getByText('×'));

      expect(clearPendingFeedback).toHaveBeenCalled();
    });
  });

  describe('loading states', () => {
    it('shows agent action indicator when loading with action', () => {
      mockUseChat.mockReturnValue({
        ...defaultHookReturn,
        isLoading: true,
        currentAction: { type: 'thinking', timestamp: new Date() },
      });

      render(<Chat sessionId="test_session" />);

      expect(screen.getByText('Thinking')).toBeInTheDocument();
    });

    it('shows tool name when tool call action', () => {
      mockUseChat.mockReturnValue({
        ...defaultHookReturn,
        isLoading: true,
        currentAction: { type: 'tool_call', name: 'save_vocab', timestamp: new Date() },
      });

      render(<Chat sessionId="test_session" />);

      expect(screen.getByText('Using save_vocab')).toBeInTheDocument();
    });

    it('shows tool result action', () => {
      mockUseChat.mockReturnValue({
        ...defaultHookReturn,
        isLoading: true,
        currentAction: { type: 'tool_result', name: 'save_vocab', timestamp: new Date() },
      });

      render(<Chat sessionId="test_session" />);

      expect(screen.getByText('Reading save_vocab')).toBeInTheDocument();
    });
  });

  describe('usage display', () => {
    it('shows token usage when available', () => {
      mockUseChat.mockReturnValue({
        ...defaultHookReturn,
        lastUsage: { input_tokens: 100, output_tokens: 50, cost_usd: 0.001 },
      });

      render(<Chat sessionId="test_session" />);

      expect(screen.getByText('150 tokens')).toBeInTheDocument();
    });
  });

  describe('message rendering', () => {
    it('renders user messages with correct class', () => {
      render(<Chat sessionId="test_session" />);

      const userMessage = document.querySelector('.message-user');
      expect(userMessage).toBeInTheDocument();
    });

    it('renders assistant messages with correct class', () => {
      render(<Chat sessionId="test_session" />);

      const assistantMessage = document.querySelector('.message-assistant');
      expect(assistantMessage).toBeInTheDocument();
    });

    it('renders markdown in assistant messages', () => {
      render(<Chat sessionId="test_session" />);

      expect(screen.getAllByTestId('markdown').length).toBeGreaterThan(0);
    });

    it('shows streaming cursor for streaming messages', () => {
      mockUseChat.mockReturnValue({
        ...defaultHookReturn,
        messages: [
          {
            id: 'msg_1',
            role: 'assistant' as const,
            content: '',
            timestamp: new Date(),
            status: 'streaming' as const,
          },
        ],
      });

      render(<Chat sessionId="test_session" />);

      const cursor = document.querySelector('.streaming-cursor');
      expect(cursor).toBeInTheDocument();
    });
  });

  describe('image handling', () => {
    it('shows image preview when message has image', () => {
      mockUseChat.mockReturnValue({
        ...defaultHookReturn,
        messages: [
          {
            id: 'msg_1',
            role: 'user' as const,
            content: 'Check this',
            image: 'data:image/jpeg;base64,ABC123',
            timestamp: new Date(),
            status: 'complete' as const,
          },
        ],
      });

      render(<Chat sessionId="test_session" />);

      const image = document.querySelector('.user-image');
      expect(image).toBeInTheDocument();
    });
  });

  describe('notes tab features', () => {
    it('shows refresh button when onRefreshNotes provided', async () => {
      const onRefreshNotes = vi.fn();
      const user = userEvent.setup();
      render(<Chat sessionId="test_session" blackboardContent="# Notes" onRefreshNotes={onRefreshNotes} />);

      await user.click(screen.getByRole('button', { name: 'Notes' }));

      expect(screen.getByTitle('Refresh')).toBeInTheDocument();
    });

    it('calls onRefreshNotes when refresh clicked', async () => {
      const onRefreshNotes = vi.fn();
      const user = userEvent.setup();
      render(<Chat sessionId="test_session" blackboardContent="# Notes" onRefreshNotes={onRefreshNotes} />);

      await user.click(screen.getByRole('button', { name: 'Notes' }));
      await user.click(screen.getByTitle('Refresh'));

      expect(onRefreshNotes).toHaveBeenCalled();
    });
  });

  describe('timestamp display', () => {
    it('shows timestamp for first message', () => {
      render(<Chat sessionId="test_session" />);

      const timestamp = document.querySelector('.timestamp-cluster');
      expect(timestamp).toBeInTheDocument();
    });

    it('groups messages within 5 minutes', () => {
      const closeMessages = [
        {
          id: 'msg_1',
          role: 'user' as const,
          content: 'First',
          timestamp: new Date('2024-01-15T10:00:00Z'),
          status: 'complete' as const,
        },
        {
          id: 'msg_2',
          role: 'assistant' as const,
          content: 'Second',
          timestamp: new Date('2024-01-15T10:00:30Z'),
          status: 'complete' as const,
        },
      ];

      mockUseChat.mockReturnValue({ ...defaultHookReturn, messages: closeMessages });
      render(<Chat sessionId="test_session" />);

      // Should only have one timestamp cluster
      const timestamps = document.querySelectorAll('.timestamp-cluster');
      expect(timestamps.length).toBe(1);
    });
  });
});
