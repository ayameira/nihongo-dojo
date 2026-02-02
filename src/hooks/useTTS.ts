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

const STORAGE_KEY = 'nihongo-dojo-tts-speaker';

export function useTTS(): UseTTSReturn {
  const [speakers, setSpeakers] = useState<Speaker[]>([]);
  const [selectedSpeakerId, setSelectedSpeakerIdState] = useState<number>(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? parseInt(stored, 10) : 2; // Default to Shikoku Metan
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch available speakers on mount
  useEffect(() => {
    const fetchSpeakers = async () => {
      try {
        const response = await fetch('/api/media/speakers');

        if (!response.ok) {
          if (response.status === 503) {
            setError('VOICEVOX not running');
          } else {
            setError('Failed to load voices');
          }
          return;
        }

        const data: SpeakersResponse = await response.json();
        setSpeakers(data.speakers);

        // If stored speaker doesn't exist in available speakers, use default
        const stored = localStorage.getItem(STORAGE_KEY);
        if (!stored || !data.speakers.some(s => s.id === parseInt(stored, 10))) {
          setSelectedSpeakerIdState(data.default_speaker_id);
        }

        setError(null);
      } catch (err) {
        setError('Failed to connect');
      } finally {
        setIsLoading(false);
      }
    };

    fetchSpeakers();
  }, []);

  const setSelectedSpeakerId = useCallback((id: number) => {
    setSelectedSpeakerIdState(id);
    localStorage.setItem(STORAGE_KEY, id.toString());
  }, []);

  return {
    speakers,
    selectedSpeakerId,
    isLoading,
    error,
    setSelectedSpeakerId,
  };
}
