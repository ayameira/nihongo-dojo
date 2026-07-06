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
        speakerId={0}
        speechLanguage="es-ES"
        languageCode="es"
      />
    );

    await user.click(screen.getByRole('button', { name: 'Play audio' }));

    expect(cancel).toHaveBeenCalled();
    expect(speak).toHaveBeenCalledTimes(1);
    expect(speak.mock.calls[0][0].lang).toBe('es-ES');
  });
});
