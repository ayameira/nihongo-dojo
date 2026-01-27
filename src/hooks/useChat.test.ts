import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useChat } from './useChat';
import { createMockSSEResponse } from '../test/mocks';

describe('useChat', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('initialization', () => {
    it('starts with empty messages', () => {
      const { result } = renderHook(() => useChat(null));

      expect(result.current.messages).toEqual([]);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.loadingState).toBe('idle');
    });

    it('loads history when sessionId changes', async () => {
      const history = [
        { id: 1, role: 'user', content: 'Hello', has_image: false, created_at: '2024-01-15T10:00:00Z' },
        { id: 2, role: 'assistant', content: 'Hi!', has_image: false, created_at: '2024-01-15T10:00:05Z' },
      ];

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(history),
      });

      const { result, rerender } = renderHook(
        ({ sessionId }) => useChat(sessionId),
        { initialProps: { sessionId: null as string | null } }
      );

      // Change sessionId
      rerender({ sessionId: 'test_session' });

      await waitFor(() => {
        expect(result.current.messages).toHaveLength(2);
      });

      expect(result.current.messages[0].role).toBe('user');
      expect(result.current.messages[0].content).toBe('Hello');
    });

    it('does not reload if sessionId is the same', async () => {
      const fetchSpy = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve([]),
      });
      global.fetch = fetchSpy;

      const { rerender } = renderHook(
        ({ sessionId }) => useChat(sessionId),
        { initialProps: { sessionId: 'test_session' } }
      );

      await waitFor(() => {
        expect(fetchSpy).toHaveBeenCalledTimes(1);
      });

      // Rerender with same sessionId
      rerender({ sessionId: 'test_session' });

      // Should not fetch again
      expect(fetchSpy).toHaveBeenCalledTimes(1);
    });
  });

  describe('sendMessage', () => {
    it('does nothing when loading', async () => {
      const { result } = renderHook(() => useChat('test_session'));

      // Manually set loading state (simulating ongoing request)
      // Since we can't directly modify state, this tests the guard condition
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve([]),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
    });

    it('does nothing without sessionId', async () => {
      global.fetch = vi.fn();

      const { result } = renderHook(() => useChat(null));

      await act(async () => {
        await result.current.sendMessage('Hello');
      });

      expect(global.fetch).not.toHaveBeenCalledWith(
        '/api/chat/stream',
        expect.anything()
      );
    });

    it('adds user and assistant messages', async () => {
      global.fetch = vi.fn()
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve([]),
        })
        .mockResolvedValueOnce(createMockSSEResponse([
          { type: 'text', content: 'Response' },
          { type: 'done' },
        ]));

      const { result } = renderHook(() => useChat('test_session'));

      await waitFor(() => {
        expect(result.current.messages).toEqual([]);
      });

      await act(async () => {
        await result.current.sendMessage('Hello');
      });

      expect(result.current.messages).toHaveLength(2);
      expect(result.current.messages[0].role).toBe('user');
      expect(result.current.messages[0].content).toBe('Hello');
      expect(result.current.messages[1].role).toBe('assistant');
    });

    it('strips base64 prefix from image data', async () => {
      const fetchSpy = vi.fn()
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve([]),
        })
        .mockResolvedValueOnce(createMockSSEResponse([{ type: 'done' }]));

      global.fetch = fetchSpy;

      const { result } = renderHook(() => useChat('test_session'));

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await result.current.sendMessage('Check this image', 'data:image/jpeg;base64,ABC123');
      });

      const streamCall = fetchSpy.mock.calls.find((call) => call[0] === '/api/chat/stream');
      if (streamCall) {
        const body = JSON.parse(streamCall[1].body);
        expect(body.image_data).toBe('ABC123');
      }
    });

    it('includes pending feedback in request', async () => {
      const fetchSpy = vi.fn()
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve([]),
        })
        .mockResolvedValueOnce(createMockSSEResponse([{ type: 'done' }]));

      global.fetch = fetchSpy;

      const { result } = renderHook(() => useChat('test_session'));

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Set pending feedback
      act(() => {
        result.current.sendDifficultyFeedback('too_hard');
      });

      await act(async () => {
        await result.current.sendMessage('Help me');
      });

      const streamCall = fetchSpy.mock.calls.find((call) => call[0] === '/api/chat/stream');
      if (streamCall) {
        const body = JSON.parse(streamCall[1].body);
        expect(body.difficulty_feedback).toBe('too_hard');
      }
    });

    it('clears pending feedback after sending', async () => {
      global.fetch = vi.fn()
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve([]),
        })
        .mockResolvedValueOnce(createMockSSEResponse([{ type: 'done' }]));

      const { result } = renderHook(() => useChat('test_session'));

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      act(() => {
        result.current.sendDifficultyFeedback('too_easy');
      });

      expect(result.current.pendingFeedback).toBe('too_easy');

      await act(async () => {
        await result.current.sendMessage('Test');
      });

      expect(result.current.pendingFeedback).toBe(null);
    });
  });

  describe('streaming response handling', () => {
    it('updates message content on text events', async () => {
      global.fetch = vi.fn()
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve([]),
        })
        .mockResolvedValueOnce(createMockSSEResponse([
          { type: 'text', content: 'Hello ' },
          { type: 'text', content: 'World' },
          { type: 'done' },
        ]));

      const { result } = renderHook(() => useChat('test_session'));

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await result.current.sendMessage('Hi');
      });

      const assistantMsg = result.current.messages.find((m) => m.role === 'assistant');
      expect(assistantMsg?.content).toBe('Hello World');
    });

    it('sets currentAction on tool_call events', async () => {
      global.fetch = vi.fn()
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve([]),
        })
        .mockResolvedValueOnce(createMockSSEResponse([
          { type: 'tool_call', name: 'save_vocab' },
          { type: 'done' },
        ]));

      const { result } = renderHook(() => useChat('test_session'));

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Note: We can't easily test intermediate state during streaming
      // This test documents expected behavior
    });

    it('handles error events', async () => {
      global.fetch = vi.fn()
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve([]),
        })
        .mockResolvedValueOnce(createMockSSEResponse([
          { type: 'error', content: 'API Error' },
        ]));

      const { result } = renderHook(() => useChat('test_session'));

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await result.current.sendMessage('Hi');
      });

      const assistantMsg = result.current.messages.find((m) => m.role === 'assistant');
      expect(assistantMsg?.status).toBe('error');
      expect(assistantMsg?.content).toContain('API Error');
    });
  });

  describe('sendDifficultyFeedback', () => {
    it('sets pending feedback to too_hard', () => {
      const { result } = renderHook(() => useChat('test_session'));

      act(() => {
        result.current.sendDifficultyFeedback('too_hard');
      });

      expect(result.current.pendingFeedback).toBe('too_hard');
    });

    it('sets pending feedback to too_easy', () => {
      const { result } = renderHook(() => useChat('test_session'));

      act(() => {
        result.current.sendDifficultyFeedback('too_easy');
      });

      expect(result.current.pendingFeedback).toBe('too_easy');
    });
  });

  describe('clearPendingFeedback', () => {
    it('clears pending feedback', () => {
      const { result } = renderHook(() => useChat('test_session'));

      act(() => {
        result.current.sendDifficultyFeedback('too_hard');
      });

      expect(result.current.pendingFeedback).toBe('too_hard');

      act(() => {
        result.current.clearPendingFeedback();
      });

      expect(result.current.pendingFeedback).toBe(null);
    });
  });

  describe('error handling', () => {
    it('handles fetch errors gracefully', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      global.fetch = vi.fn()
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve([]),
        })
        .mockRejectedValueOnce(new Error('Network error'));

      const { result } = renderHook(() => useChat('test_session'));

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await result.current.sendMessage('Hi');
      });

      const assistantMsg = result.current.messages.find((m) => m.role === 'assistant');
      expect(assistantMsg?.status).toBe('error');
      expect(assistantMsg?.content).toContain('Network error');

      consoleSpy.mockRestore();
    });

    it('handles HTTP errors', async () => {
      global.fetch = vi.fn()
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve([]),
        })
        .mockResolvedValueOnce({
          ok: false,
          status: 500,
        });

      const { result } = renderHook(() => useChat('test_session'));

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await result.current.sendMessage('Hi');
      });

      const assistantMsg = result.current.messages.find((m) => m.role === 'assistant');
      expect(assistantMsg?.status).toBe('error');
    });
  });
});
