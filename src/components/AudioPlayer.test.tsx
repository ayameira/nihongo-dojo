import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AudioPlayer } from './AudioPlayer';

describe('AudioPlayer', () => {
  const speak = vi.fn();
  const cancel = vi.fn();

  beforeEach(() => {
    speak.mockClear();
    cancel.mockClear();

    class MockSpeechSynthesisUtterance {
      text: string;
      lang = '';
      voice: SpeechSynthesisVoice | null = null;
      onstart: (() => void) | null = null;
      onend: (() => void) | null = null;
      onerror: (() => void) | null = null;

      constructor(text: string) {
        this.text = text;
      }
    }

    vi.stubGlobal('SpeechSynthesisUtterance', MockSpeechSynthesisUtterance);
    vi.stubGlobal('speechSynthesis', {
      speak,
      cancel,
      getVoices: () => [
        { lang: 'ja-JP', name: 'Japanese' },
        { lang: 'es-ES', name: 'Spanish' },
      ],
    });
  });

  it('uses the active profile speech language for browser fallback', async () => {
    const user = userEvent.setup();
    render(
      <AudioPlayer
        text="hola"
        speakerId="browser"
        speechLanguage="es-ES"
        languageCode="es"
      />
    );

    await user.click(screen.getByRole('button', { name: 'Play audio' }));

    expect(cancel).toHaveBeenCalled();
    expect(speak).toHaveBeenCalledTimes(1);
    expect(speak.mock.calls[0][0].lang).toBe('es-ES');
  });

  it('strips markdown before speaking', async () => {
    const user = userEvent.setup();
    render(
      <AudioPlayer
        text="La palabra **comer** significa *to eat*"
        speakerId="browser"
        speechLanguage="es-ES"
        languageCode="es"
      />
    );

    await user.click(screen.getByRole('button', { name: 'Play audio' }));

    expect(speak.mock.calls[0][0].text).toBe('La palabra comer significa to eat');
  });

  it('sends cleaned text to the server TTS endpoint', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      blob: async () => new Blob(['audio'], { type: 'audio/wav' }),
    });
    vi.stubGlobal('fetch', fetchMock);
    vi.stubGlobal('URL', {
      ...URL,
      createObjectURL: vi.fn(() => 'blob:mock'),
      revokeObjectURL: vi.fn(),
    });
    vi.stubGlobal(
      'Audio',
      class {
        onplay: (() => void) | null = null;
        onended: (() => void) | null = null;
        onerror: (() => void) | null = null;
        async play() {}
      }
    );

    const user = userEvent.setup();
    render(
      <AudioPlayer
        text="「**食べる**」は `to eat` です"
        speakerId="2"
        speechLanguage="ja-JP"
        languageCode="ja"
      />
    );

    await user.click(screen.getByRole('button', { name: 'Play audio' }));

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const body = JSON.parse(fetchMock.mock.calls[0][1].body);
    expect(body.text).toBe('「食べる」は to eat です');
  });
});
