export interface SSEEvent {
  type: 'text' | 'tool_call' | 'tool_result' | 'usage' | 'done' | 'error';
  content?: string;
  name?: string;
  args?: Record<string, unknown>;
  result?: string;
  usage?: {
    input_tokens: number;
    output_tokens: number;
    cost_usd: number;
  };
}

export async function* readSSEStream(response: Response): AsyncGenerator<SSEEvent> {
  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            yield data as SSEEvent;
          } catch (e) {
            console.error('Failed to parse SSE event:', e);
          }
        }
      }
    }

    // Process any remaining buffer
    if (buffer.startsWith('data: ')) {
      try {
        const data = JSON.parse(buffer.slice(6));
        yield data as SSEEvent;
      } catch (e) {
        // Ignore incomplete final chunk
      }
    }
  } finally {
    reader.releaseLock();
  }
}
