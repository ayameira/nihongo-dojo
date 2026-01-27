import { vi } from 'vitest';
import type { Session } from '../hooks/useSessions';
import type { Message } from '../hooks/useChat';

export const mockSessions: Session[] = [
  {
    id: 'session_1',
    name: 'Test Session 1',
    preview: 'Hello world',
    message_count: 5,
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-15T12:00:00Z',
  },
  {
    id: 'session_2',
    name: null,
    preview: 'Another conversation',
    message_count: 3,
    created_at: '2024-01-14T08:00:00Z',
    updated_at: '2024-01-14T10:00:00Z',
  },
  {
    id: 'session_3',
    name: null,
    preview: null,
    message_count: 0,
    created_at: '2024-01-13T06:00:00Z',
    updated_at: '2024-01-13T06:00:00Z',
  },
];

export const mockMessages: Message[] = [
  {
    id: 'msg_1',
    role: 'user',
    content: 'こんにちは',
    timestamp: new Date('2024-01-15T10:00:00Z'),
    status: 'complete',
  },
  {
    id: 'msg_2',
    role: 'assistant',
    content: 'こんにちは！元気ですか？',
    timestamp: new Date('2024-01-15T10:00:05Z'),
    status: 'complete',
  },
];

export function createMockFetch(responses: Record<string, unknown>) {
  return vi.fn().mockImplementation((url: string, options?: RequestInit) => {
    const method = options?.method || 'GET';
    const key = `${method} ${url}`;

    // Find matching response
    for (const [pattern, response] of Object.entries(responses)) {
      if (key.includes(pattern) || url.includes(pattern)) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(response),
          text: () => Promise.resolve(JSON.stringify(response)),
        });
      }
    }

    // Default 404 response
    return Promise.resolve({
      ok: false,
      status: 404,
      json: () => Promise.resolve({ error: 'Not found' }),
    });
  });
}

export function createMockSSEResponse(events: Array<{ type: string; content?: string; name?: string }>) {
  const encoder = new TextEncoder();
  const eventStrings = events.map((e) => `data: ${JSON.stringify(e)}\n\n`);

  let index = 0;
  const stream = new ReadableStream({
    pull(controller) {
      if (index < eventStrings.length) {
        controller.enqueue(encoder.encode(eventStrings[index]));
        index++;
      } else {
        controller.close();
      }
    },
  });

  return {
    ok: true,
    body: stream,
  };
}
