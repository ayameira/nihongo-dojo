import { useState, useEffect, useCallback } from 'react';

export interface Speaker {
  id: number;
  name: string;
  style: string;
  display_name: string;
}

interface SpeakersResponse {
  speakers: Speaker[];
  default_speaker_id: number;
}

interface UseTTSReturn {
  speakers: Speaker[];
  selectedSpeakerId: number;
  isLoading: boolean;
  error: string | null;
  setSelectedSpeakerId: (id: number) => void;
}

const storageKey = (languageCode: string) => `nihongo-dojo-tts-speaker:${languageCode}`;

export function useTTS(languageCode = 'ja'): UseTTSReturn {
  const [speakers, setSpeakers] = useState<Speaker[]>([]);
  const [selectedSpeakerId, setSelectedSpeakerIdState] = useState<number>(() => {
    const stored = localStorage.getItem(storageKey(languageCode));
    return stored ? parseInt(stored, 10) : 2; // Default to Shikoku Metan
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch available speakers on mount
  useEffect(() => {
    const fetchSpeakers = async () => {
      try {
        const response = await fetch((import.meta.env.VITE_API_URL || '') + '/api/media/speakers');

        if (!response.ok) {
          throw new Error('Failed to load voices');
        }

        const data: SpeakersResponse = await response.json();
        setSpeakers(data.speakers);

        // If stored speaker doesn't exist in available speakers, use default
        const stored = localStorage.getItem(storageKey(languageCode));
        if (!stored || !data.speakers.some((s) => s.id === parseInt(stored, 10))) {
          setSelectedSpeakerIdState(data.default_speaker_id);
        }

        setError(null);
      } catch (err) {
        // Fallback to Web Speech API
        setSpeakers([
          { id: 0, name: 'Browser TTS', style: 'Default', display_name: 'Web Speech API (Fallback)' },
        ]);
        setSelectedSpeakerIdState(0);
        setError(null);
      } finally {
        setIsLoading(false);
      }
    };

    fetchSpeakers();
  }, [languageCode]);

  const setSelectedSpeakerId = useCallback((id: number) => {
    setSelectedSpeakerIdState(id);
    localStorage.setItem(storageKey(languageCode), id.toString());
  }, [languageCode]);

  return {
    speakers,
    selectedSpeakerId,
    isLoading,
    error,
    setSelectedSpeakerId,
  };
}
