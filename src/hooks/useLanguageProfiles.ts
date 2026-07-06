import { useCallback, useEffect, useState } from 'react';

export interface LanguageProfile {
  code: string;
  display_name: string;
  native_name: string;
  speech_language: string;
  grammar_level_scheme: {
    name: string;
    levels: string[];
    custom_label: string;
    source_name: string;
  };
  vocabulary_semantics: {
    term_label: string;
    reading_label: string;
    meaning_label: string;
    part_of_speech_label: string;
  };
}

interface UseLanguageProfilesReturn {
  profiles: LanguageProfile[];
  activeLanguageCode: string;
  activeProfile: LanguageProfile | null;
  setActiveLanguageCode: (code: string) => void;
}

const STORAGE_KEY = 'nihongo_active_language_code';
const DEFAULT_LANGUAGE = 'ja';

export function useLanguageProfiles(): UseLanguageProfilesReturn {
  const [profiles, setProfiles] = useState<LanguageProfile[]>([]);
  const [activeLanguageCode, setActiveLanguageCodeState] = useState(() => (
    localStorage.getItem(STORAGE_KEY) || DEFAULT_LANGUAGE
  ));

  useEffect(() => {
    let cancelled = false;

    const loadProfiles = async () => {
      try {
        const response = await fetch((import.meta.env.VITE_API_URL || '') + '/api/config/languages');
        if (!response.ok) return;

        const data: { active_language_code?: string; profiles?: LanguageProfile[] } = await response.json();
        if (cancelled) return;

        const loadedProfiles = Array.isArray(data.profiles) ? data.profiles : [];
        setProfiles(loadedProfiles);

        setActiveLanguageCodeState((current) => {
          const stored = localStorage.getItem(STORAGE_KEY);
          const candidate = stored || current || data.active_language_code || DEFAULT_LANGUAGE;
          const next = loadedProfiles.some((profile) => profile.code === candidate)
            ? candidate
            : data.active_language_code || DEFAULT_LANGUAGE;
          localStorage.setItem(STORAGE_KEY, next);
          return next;
        });
      } catch {
        // Japanese remains the local fallback if profile metadata is unavailable.
      }
    };

    loadProfiles();

    return () => {
      cancelled = true;
    };
  }, []);

  const setActiveLanguageCode = useCallback((code: string) => {
    setActiveLanguageCodeState(code);
    localStorage.setItem(STORAGE_KEY, code);
  }, []);

  const activeProfile = profiles.find((profile) => profile.code === activeLanguageCode) || null;

  return {
    profiles,
    activeLanguageCode,
    activeProfile,
    setActiveLanguageCode,
  };
}
