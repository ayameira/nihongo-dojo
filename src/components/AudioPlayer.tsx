import React, { useState, useRef, useCallback } from 'react';

interface AudioPlayerProps {
  text: string;
  speakerId?: number;
  speechLanguage?: string;
  languageCode?: string;
}

export const AudioPlayer: React.FC<AudioPlayerProps> = ({
  text,
  speakerId,
  speechLanguage = 'ja-JP',
  languageCode = 'ja',
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const handleClick = useCallback(async () => {
    if (isLoading) return;

    // If already playing, stop it
    if (isPlaying && audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      setIsPlaying(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    // Use Web Speech API fallback
    if (speakerId === 0) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = speechLanguage;
      // Fallback voice selection (find a matching target-language voice if available)
      const voices = window.speechSynthesis.getVoices();
      const languagePrefix = speechLanguage.split('-', 1)[0];
      const matchingVoice = voices.find((v) => v.lang === speechLanguage)
        || voices.find((v) => v.lang.startsWith(languagePrefix));
      if (matchingVoice) {
        utterance.voice = matchingVoice;
      }
      utterance.onstart = () => {
        setIsPlaying(true);
        setIsLoading(false);
      };
      utterance.onend = () => {
        setIsPlaying(false);
      };
      utterance.onerror = () => {
        setError('TTS playback failed');
        setIsPlaying(false);
        setIsLoading(false);
      };

      // We must cancel any ongoing native speech before speaking
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(utterance);
      return;
    }

    try {
      const response = await fetch((import.meta.env.VITE_API_URL || '') + '/api/media/tts', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text,
          speaker_id: speakerId,
          language_code: languageCode,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      const blob = await response.blob();
      const audioUrl = URL.createObjectURL(blob);

      // Clean up previous audio if exists
      if (audioRef.current) {
        URL.revokeObjectURL(audioRef.current.src);
      }

      const audio = new Audio(audioUrl);
      audioRef.current = audio;

      audio.onplay = () => {
        setIsPlaying(true);
        setIsLoading(false);
      };

      audio.onended = () => {
        setIsPlaying(false);
        URL.revokeObjectURL(audioUrl);
      };

      audio.onerror = () => {
        setError('Playback failed');
        setIsPlaying(false);
        setIsLoading(false);
        URL.revokeObjectURL(audioUrl);
      };

      await audio.play();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to generate audio';
      setError(message);
      setIsLoading(false);
    }
  }, [text, speakerId, speechLanguage, languageCode, isLoading, isPlaying]);

  return (
    <button
      onClick={handleClick}
      disabled={isLoading}
      className="audio-player-btn"
      title={error || (isPlaying ? 'Stop' : 'Play audio')}
      aria-label={isPlaying ? 'Stop audio' : 'Play audio'}
    >
      {isLoading ? (
        <span className="audio-spinner" />
      ) : isPlaying ? (
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="currentColor"
          stroke="none"
        >
          <rect x="6" y="4" width="4" height="16" rx="1" />
          <rect x="14" y="4" width="4" height="16" rx="1" />
        </svg>
      ) : error ? (
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="audio-error"
        >
          <circle cx="12" cy="12" r="10" />
          <line x1="15" y1="9" x2="9" y2="15" />
          <line x1="9" y1="9" x2="15" y2="15" />
        </svg>
      ) : (
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
          <path d="M15.54 8.46a5 5 0 0 1 0 7.07" />
          <path d="M19.07 4.93a10 10 0 0 1 0 14.14" />
        </svg>
      )}
    </button>
  );
};

export default AudioPlayer;
