import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Chat } from './Chat';
import { Fact } from '../hooks/useFacts';

// Mock useChat hook
const mockUseChat = vi.fn();
vi.mock('../hooks/useChat', () => ({
  useChat: (...args: unknown[]) => mockUseChat(...args),
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
    global.fetch = vi.fn().mockResolvedValue({ ok: false });
    mockUseChat.mockReturnValue(defaultHookReturn);
  });

  describe('rendering', () => {
    it('renders chat and profile tabs', () => {
      render(<Chat sessionId="test_session" />);

      expect(screen.getByRole('button', { name: 'Chat' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Profile' })).toBeInTheDocument();
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

    it('renders the configured chat model selector', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          current_model: 'gemini-3-flash-preview',
          models: [
            {
              id: 'gemini-3-flash-preview',
              name: 'Gemini 3 Flash Preview',
              input_cost_per_1m: 0.5,
              output_cost_per_1m: 3,
            },
            {
              id: 'gemini-3-pro-preview',
              name: 'Gemini 3 Pro Preview',
              input_cost_per_1m: 2,
              output_cost_per_1m: 12,
            },
          ],
        }),
      });

      render(<Chat sessionId="test_session" />);

      const selector = await screen.findByLabelText('Chat model');
      expect(selector).toHaveValue('gemini:gemini-3-flash-preview');
      expect(screen.getByText('Gemini 3 Pro Preview')).toBeInTheDocument();

      await waitFor(() => {
        expect(mockUseChat).toHaveBeenLastCalledWith('test_session', 'gemini-3-flash-preview', 'gemini');
      });
    });

    it('updates the selected chat model', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          current_model: 'gemini-3-flash-preview',
          models: [
            {
              id: 'gemini-3-flash-preview',
              name: 'Gemini 3 Flash Preview',
              input_cost_per_1m: 0.5,
              output_cost_per_1m: 3,
            },
            {
              id: 'gemini-3-pro-preview',
              name: 'Gemini 3 Pro Preview',
              input_cost_per_1m: 2,
              output_cost_per_1m: 12,
            },
          ],
        }),
      });
      const user = userEvent.setup();

      render(<Chat sessionId="test_session" />);

      const selector = await screen.findByLabelText('Chat model');
      await user.selectOptions(selector, 'gemini:gemini-3-pro-preview');

      expect(selector).toHaveValue('gemini:gemini-3-pro-preview');
      expect(localStorage.setItem).toHaveBeenCalledWith('nihongo_chat_model', 'gemini:gemini-3-pro-preview');

      await waitFor(() => {
        expect(mockUseChat).toHaveBeenLastCalledWith('test_session', 'gemini-3-pro-preview', 'gemini');
      });
    });
  });

  describe('tabs', () => {
    const mockFacts: Fact[] = [
      { id: 1, content: 'Likes anime', source: 'tutor', created_at: '2024-01-15T10:00:00Z' },
      { id: 2, content: 'Learning for travel', source: 'manual', created_at: '2024-01-15T11:00:00Z' },
    ];

    it('shows chat tab by default', () => {
      render(<Chat sessionId="test_session" />);

      expect(screen.getByText('こんにちは')).toBeInTheDocument();
    });

    it('switches to profile tab when clicked', async () => {
      const user = userEvent.setup();
      render(<Chat sessionId="test_session" facts={mockFacts} />);

      await user.click(screen.getByRole('button', { name: 'Profile' }));

      expect(screen.getByText('Student Profile')).toBeInTheDocument();
    });

    it('shows facts in profile tab', async () => {
      const user = userEvent.setup();
      render(<Chat sessionId="test_session" facts={mockFacts} />);

      await user.click(screen.getByRole('button', { name: 'Profile' }));

      expect(screen.getByText('Likes anime')).toBeInTheDocument();
      expect(screen.getByText('Learning for travel')).toBeInTheDocument();
    });

    it('shows empty profile message when no facts', async () => {
      const user = userEvent.setup();
      render(<Chat sessionId="test_session" facts={[]} />);

      await user.click(screen.getByRole('button', { name: 'Profile' }));

      expect(screen.getByText('No profile yet')).toBeInTheDocument();
    });

    it('switches back to chat tab', async () => {
      const user = userEvent.setup();
      render(<Chat sessionId="test_session" facts={mockFacts} />);

      await user.click(screen.getByRole('button', { name: 'Profile' }));
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

  describe('profile tab features', () => {
    const mockFacts: Fact[] = [
      { id: 1, content: 'Likes anime', source: 'tutor', created_at: '2024-01-15T10:00:00Z' },
    ];

    it('shows add fact button', async () => {
      const user = userEvent.setup();
      render(<Chat sessionId="test_session" facts={mockFacts} />);

      await user.click(screen.getByRole('button', { name: 'Profile' }));

      expect(screen.getByTitle('Add fact')).toBeInTheDocument();
    });

    it('shows add fact form when add button clicked', async () => {
      const user = userEvent.setup();
      render(<Chat sessionId="test_session" facts={mockFacts} onAddFact={vi.fn()} />);

      await user.click(screen.getByRole('button', { name: 'Profile' }));
      await user.click(screen.getByTitle('Add fact'));

      expect(screen.getByPlaceholderText('Add a new fact about yourself...')).toBeInTheDocument();
    });

    it('calls onAddFact when saving new fact', async () => {
      const onAddFact = vi.fn().mockResolvedValue({ id: 2, content: 'New fact', source: 'manual' });
      const user = userEvent.setup();
      render(<Chat sessionId="test_session" facts={mockFacts} onAddFact={onAddFact} />);

      await user.click(screen.getByRole('button', { name: 'Profile' }));
      await user.click(screen.getByTitle('Add fact'));
      await user.type(screen.getByPlaceholderText('Add a new fact about yourself...'), 'New fact');
      await user.click(screen.getByText('Save'));

      expect(onAddFact).toHaveBeenCalledWith('New fact');
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
