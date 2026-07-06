import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useSessions } from './useSessions';
import { mockSessions, createMockFetch } from '../test/mocks';

describe('useSessions', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.getItem = vi.fn().mockReturnValue(null);
    localStorage.setItem = vi.fn();
  });

  describe('initialization', () => {
    it('fetches sessions on mount', async () => {
      global.fetch = createMockFetch({
        '/api/sessions': mockSessions,
      });

      const { result } = renderHook(() => useSessions());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.sessions).toEqual(mockSessions);
    });

    it('uses stored session ID if valid', async () => {
      localStorage.getItem = vi.fn().mockReturnValue('session_1');

      global.fetch = createMockFetch({
        '/api/sessions': mockSessions,
      });

      const { result } = renderHook(() => useSessions());

      await waitFor(() => {
        expect(result.current.currentSessionId).toBe('session_1');
      });
    });

    it('uses most recent session if stored ID is invalid', async () => {
      localStorage.getItem = vi.fn().mockReturnValue('invalid_id');

      global.fetch = createMockFetch({
        '/api/sessions': mockSessions,
      });

      const { result } = renderHook(() => useSessions());

      await waitFor(() => {
        expect(result.current.currentSessionId).toBe('session_1');
      });
    });

    it('generates new session ID when no sessions exist', async () => {
      global.fetch = createMockFetch({
        '/api/sessions': [],
      });

      const { result } = renderHook(() => useSessions());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.currentSessionId).toMatch(/^session_\d+_/);
    });
  });

  describe('createSession', () => {
    it('creates new session and switches to it', async () => {
      const newSession = {
        id: 'new_session',
        language_code: 'ja',
        name: null,
        preview: null,
        message_count: 0,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };

      global.fetch = vi.fn()
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockSessions),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(newSession),
        });

      const { result } = renderHook(() => useSessions());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      let newId: string = '';
      await act(async () => {
        newId = await result.current.createSession();
      });

      expect(newId).toMatch(/^session_\d+_/);
      expect(result.current.currentSessionId).toBe(newId);
      expect(localStorage.setItem).toHaveBeenCalledWith('nihongo_session_id', newId);
    });

    it('sends the active target language when creating a session', async () => {
      const fetchSpy = vi.fn()
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve([]),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({
            id: 'new_session',
            language_code: 'ja',
            name: null,
            preview: null,
            message_count: 0,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          }),
        });
      global.fetch = fetchSpy;

      const { result } = renderHook(() => useSessions('ja'));

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await result.current.createSession();
      });

      expect(fetchSpy).toHaveBeenLastCalledWith(
        expect.stringContaining('/api/sessions'),
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('"language_code":"ja"'),
        }),
      );
    });
  });

  describe('switchSession', () => {
    it('switches to specified session', async () => {
      global.fetch = createMockFetch({
        '/api/sessions': mockSessions,
      });

      const { result } = renderHook(() => useSessions());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      act(() => {
        result.current.switchSession('session_2');
      });

      expect(result.current.currentSessionId).toBe('session_2');
      expect(localStorage.setItem).toHaveBeenCalledWith('nihongo_session_id', 'session_2');
    });
  });

  describe('renameSession', () => {
    it('renames session and updates state', async () => {
      const updatedSession = { ...mockSessions[0], name: 'New Name' };

      global.fetch = vi.fn()
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockSessions),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(updatedSession),
        });

      const { result } = renderHook(() => useSessions());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await result.current.renameSession('session_1', 'New Name');
      });

      const renamed = result.current.sessions.find((s) => s.id === 'session_1');
      expect(renamed?.name).toBe('New Name');
    });
  });

  describe('deleteSession', () => {
    it('deletes session and switches to another', async () => {
      global.fetch = vi.fn()
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockSessions),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ success: true }),
        });

      const { result } = renderHook(() => useSessions());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Set current session to the one we'll delete
      act(() => {
        result.current.switchSession('session_1');
      });

      await act(async () => {
        await result.current.deleteSession('session_1');
      });

      // Should switch to next available session
      expect(result.current.currentSessionId).not.toBe('session_1');
      expect(result.current.sessions.find((s) => s.id === 'session_1')).toBeUndefined();
    });

    it('creates new session when deleting last session', async () => {
      const singleSession = [mockSessions[0]];

      global.fetch = vi.fn()
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(singleSession),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ success: true }),
        });

      const { result } = renderHook(() => useSessions());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      act(() => {
        result.current.switchSession('session_1');
      });

      await act(async () => {
        await result.current.deleteSession('session_1');
      });

      // Should generate a new session ID
      expect(result.current.currentSessionId).toMatch(/^session_\d+_/);
    });
  });

  describe('refreshSessions', () => {
    it('refetches sessions', async () => {
      const fetchSpy = vi.fn()
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockSessions),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve([...mockSessions, { ...mockSessions[0], id: 'session_4' }]),
        });

      global.fetch = fetchSpy;

      const { result } = renderHook(() => useSessions());

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await result.current.refreshSessions();
      });

      expect(fetchSpy).toHaveBeenCalledTimes(2);
    });
  });

  describe('generateSessionId', () => {
    it('generates unique IDs', async () => {
      global.fetch = createMockFetch({
        '/api/sessions': [],
      });

      const { result: result1 } = renderHook(() => useSessions());
      const { result: result2 } = renderHook(() => useSessions());

      await waitFor(() => {
        expect(result1.current.isLoading).toBe(false);
        expect(result2.current.isLoading).toBe(false);
      });

      // IDs should be different
      expect(result1.current.currentSessionId).not.toBe(result2.current.currentSessionId);
    });
  });
});
