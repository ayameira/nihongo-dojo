import { useState, useEffect, useCallback } from 'react';

// Reserved id for the browser's Web Speech API; other ids are server
// voices (VOICEVOX style ids like "2", Kokoro voice names like "af_heart").
export const BROWSER_SPEAKER_ID = 'browser';

export interface Speaker {
  id: string;
  name: string;
  style: string;
  display_name: string;
}

interface SpeakersResponse {
  speakers: Speaker[];
  default_speaker_id: string;
}

interface UseTTSReturn {
  speakers: Speaker[];
  selectedSpeakerId: string;
  isLoading: boolean;
  error: string | null;
  setSelectedSpeakerId: (id: string) => void;
}

const storageKey = (languageCode: string) => `nihongo-dojo-tts-speaker:${languageCode}`;

export function useTTS(languageCode = 'ja'): UseTTSReturn {
  const [speakers, setSpeakers] = useState<Speaker[]>([]);
  const [selectedSpeakerId, setSelectedSpeakerIdState] = useState<string>(
    () => localStorage.getItem(storageKey(languageCode)) || BROWSER_SPEAKER_ID
  );
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch available speakers on mount
  useEffect(() => {
    const fetchSpeakers = async () => {
      try {
        const response = await fetch(
          `${import.meta.env.VITE_API_URL || ''}/api/media/speakers?language_code=${encodeURIComponent(languageCode)}`
        );

        if (!response.ok) {
          throw new Error('Failed to load voices');
        }

        const data: SpeakersResponse = await response.json();
        setSpeakers(data.speakers);

        // Apply this language's stored speaker; fall back to the default
        // when nothing is stored or the stored speaker no longer exists
        const stored = localStorage.getItem(storageKey(languageCode));
        if (stored && data.speakers.some((s) => s.id === stored)) {
          setSelectedSpeakerIdState(stored);
        } else {
          setSelectedSpeakerIdState(data.default_speaker_id);
        }

        setError(null);
      } catch (err) {
        // Fallback to Web Speech API
        setSpeakers([
          { id: BROWSER_SPEAKER_ID, name: 'Browser TTS', style: 'Default', display_name: 'Web Speech API (Fallback)' },
        ]);
        setSelectedSpeakerIdState(BROWSER_SPEAKER_ID);
        setError(null);
      } finally {
        setIsLoading(false);
      }
    };

    fetchSpeakers();
  }, [languageCode]);

  const setSelectedSpeakerId = useCallback((id: string) => {
    setSelectedSpeakerIdState(id);
    localStorage.setItem(storageKey(languageCode), id);
  }, [languageCode]);

  return {
    speakers,
    selectedSpeakerId,
    isLoading,
    error,
    setSelectedSpeakerId,
  };
}
