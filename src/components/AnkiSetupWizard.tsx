import React, { useState, useEffect, useCallback } from 'react';
import { useLanguageProfiles } from '../hooks/useLanguageProfiles';

const API = import.meta.env.VITE_API_URL || '';

interface DeckInfo {
  deck_name: string;
  note_count: number;
}

interface NoteType {
  model_name: string;
  note_count: number;
  fields: string[];
  samples: Record<string, string>[];
}

interface DeckFields {
  language_code: string;
  deck_name: string;
  note_count: number;
  note_types: NoteType[];
  suggested: {
    kanji_field: string | null;
    kana_field: string | null;
    meaning_field: string | null;
    pos_field: string | null;
  };
}

interface DeckConfig {
  id: number;
  language_code: string;
  name: string;
  collection_path: string;
  deck_name: string;
  enabled: boolean;
  kanji_field: string | null;
  kana_field: string;
  meaning_field: string;
  pos_field: string | null;
  filter_field: string | null;
  filter_value: string | null;
  last_synced_at: string | null;
  vocab_count: number;
}

interface Mapping {
  name: string;
  kanji_field: string;
  kana_field: string;
  meaning_field: string;
  pos_field: string;
  filter_field: string;
  filter_value: string;
}

interface AnkiSetupWizardProps {
  languageCode?: string;
  onClose: () => void;
  onSynced?: () => void;
}

type Step = 'manage' | 'path' | 'mapping' | 'result';

const NONE = '';

export const AnkiSetupWizard: React.FC<AnkiSetupWizardProps> = ({
  languageCode = 'ja',
  onClose,
  onSynced,
}) => {
  const [step, setStep] = useState<Step>('manage');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  // Field labels follow the active language profile; Japanese keeps its
  // original wording, and languages without a secondary script hide the
  // term column entirely (the word is stored in the reading slot).
  const { profiles } = useLanguageProfiles();
  const languageProfile = profiles.find((p) => p.code === languageCode) || null;
  const showTermField = languageProfile?.has_secondary_script ?? true;
  const capitalize = (text: string) => text.charAt(0).toUpperCase() + text.slice(1);
  const termFieldLabel = languageProfile && languageProfile.code !== 'ja'
    ? `${capitalize(languageProfile.vocabulary_semantics.term_label)} field`
    : 'Word / Kanji field';
  const readingFieldLabel = languageProfile && languageProfile.code !== 'ja'
    ? `${capitalize(languageProfile.vocabulary_semantics.reading_label)} field`
    : 'Reading / Kana field';

  // Manage view
  const [configs, setConfigs] = useState<DeckConfig[]>([]);

  // Path / deck selection
  const [path, setPath] = useState('');
  const [uploadedFileName, setUploadedFileName] = useState('');
  const [decks, setDecks] = useState<DeckInfo[]>([]);
  const [selectedDecks, setSelectedDecks] = useState<Set<string>>(new Set());

  // Field mapping
  const [deckFields, setDeckFields] = useState<Record<string, DeckFields>>({});
  const [mappings, setMappings] = useState<Record<string, Mapping>>({});
  const [editingId, setEditingId] = useState<number | null>(null);

  // Result
  const [result, setResult] = useState<{ imported: number; updated: number; skipped: number } | null>(null);
  const languageParam = `language_code=${encodeURIComponent(languageCode)}`;

  const loadConfigs = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/anki/configs?${languageParam}`);
      if (res.ok) setConfigs(await res.json());
    } catch {
      /* ignore */
    }
  }, [languageParam]);

  useEffect(() => {
    loadConfigs();
  }, [loadConfigs]);

  // --- Path step -----------------------------------------------------------

  const startWizard = async () => {
    setError('');
    setEditingId(null);
    setUploadedFileName('');
    setSelectedDecks(new Set());
    setDecks([]);
    setDeckFields({});
    setMappings({});
    setStep('path');
    try {
      const res = await fetch(`${API}/api/anki/default-path`);
      if (res.ok) {
        const data = await res.json();
        setPath(data.path);
      }
    } catch {
      /* ignore */
    }
  };

  const uploadCollection = async (file: File | null) => {
    if (!file) return;
    setBusy(true);
    setError('');
    setDecks([]);
    setSelectedDecks(new Set());
    try {
      const formData = new FormData();
      formData.append('file', file);

      const res = await fetch(`${API}/api/anki/upload`, {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail || 'Could not read that Anki collection.');
        return;
      }

      setUploadedFileName(data.filename || file.name);
      setPath(data.path);
      setDecks(data.decks || []);
      if ((data.decks || []).length === 0) {
        setError('No decks with cards found in this collection.');
      }
    } catch {
      setError('Could not reach the server.');
    } finally {
      setBusy(false);
    }
  };

  const findDecks = async () => {
    if (!path.trim()) return;
    setBusy(true);
    setError('');
    try {
      const res = await fetch(`${API}/api/anki/decks?path=${encodeURIComponent(path.trim())}`);
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail || 'Could not read collection');
        setDecks([]);
        return;
      }
      setDecks(data.decks);
      if (data.decks.length === 0) setError('No decks with cards found in this collection.');
    } catch {
      setError('Could not reach the server.');
    } finally {
      setBusy(false);
    }
  };

  const toggleDeck = (name: string) => {
    setSelectedDecks((prev) => {
      const next = new Set(prev);
      next.has(name) ? next.delete(name) : next.add(name);
      return next;
    });
  };

  const goToMapping = async () => {
    if (selectedDecks.size === 0) return;
    setBusy(true);
    setError('');
    try {
      const fields: Record<string, DeckFields> = {};
      const maps: Record<string, Mapping> = {};
      for (const deck of selectedDecks) {
        const res = await fetch(
          `${API}/api/anki/deck-fields?path=${encodeURIComponent(path.trim())}&deck=${encodeURIComponent(deck)}&${languageParam}`
        );
        const data: DeckFields = await res.json();
        if (!res.ok) {
          setError((data as unknown as { detail: string }).detail || `Could not inspect ${deck}`);
          return;
        }
        fields[deck] = data;
        maps[deck] = {
          name: deck.split('::').pop() || deck,
          kanji_field: data.suggested.kanji_field || NONE,
          kana_field: data.suggested.kana_field || NONE,
          meaning_field: data.suggested.meaning_field || NONE,
          pos_field: data.suggested.pos_field || NONE,
          filter_field: NONE,
          filter_value: '',
        };
      }
      setDeckFields(fields);
      setMappings(maps);
      setStep('mapping');
    } catch {
      setError('Could not reach the server.');
    } finally {
      setBusy(false);
    }
  };

  // --- Mapping step --------------------------------------------------------

  const updateMapping = (deck: string, patch: Partial<Mapping>) => {
    setMappings((prev) => ({ ...prev, [deck]: { ...prev[deck], ...patch } }));
  };

  const allFields = (deck: string): string[] => {
    const df = deckFields[deck];
    if (!df) return [];
    const set = new Set<string>();
    df.note_types.forEach((nt) => nt.fields.forEach((f) => set.add(f)));
    return [...set];
  };

  const mappingValid = (m: Mapping): boolean =>
    !!m.name.trim() && !!m.kana_field && !!m.meaning_field &&
    (!m.filter_field || !!m.filter_value.trim());

  const allMappingsValid = (): boolean =>
    Object.values(mappings).length > 0 && Object.values(mappings).every(mappingValid);

  const saveAndSync = async () => {
    setBusy(true);
    setError('');
    try {
      const ids: number[] = [];
      for (const deck of Object.keys(mappings)) {
        const m = mappings[deck];
        const body = {
          name: m.name.trim(),
          language_code: languageCode,
          collection_path: path.trim(),
          deck_name: deck,
          enabled: true,
          kanji_field: m.kanji_field || null,
          kana_field: m.kana_field,
          meaning_field: m.meaning_field,
          pos_field: m.pos_field || null,
          filter_field: m.filter_field || null,
          filter_value: m.filter_field ? m.filter_value.trim() : null,
        };
        let res: Response;
        if (editingId != null) {
          res = await fetch(`${API}/api/anki/configs/${editingId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
          });
        } else {
          res = await fetch(`${API}/api/anki/configs`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
          });
        }
        const data = await res.json();
        if (!res.ok) {
          setError(data.detail || 'Failed to save deck source');
          return;
        }
        ids.push(editingId ?? data.id);
      }

      // Sync the just-saved sources.
      const totals = { imported: 0, updated: 0, skipped: 0 };
      for (const id of ids) {
        const res = await fetch(`${API}/api/anki/configs/${id}/sync`, { method: 'POST' });
        const data = await res.json();
        if (res.ok) {
          totals.imported += data.imported;
          totals.updated += data.updated;
          totals.skipped += data.skipped;
        }
      }
      setResult(totals);
      setStep('result');
      await loadConfigs();
      onSynced?.();
    } catch {
      setError('Could not reach the server.');
    } finally {
      setBusy(false);
    }
  };

  // --- Manage actions ------------------------------------------------------

  const editConfig = (config: DeckConfig) => {
    setEditingId(config.id);
    setPath(config.collection_path);
    setUploadedFileName('');
    setSelectedDecks(new Set([config.deck_name]));
    setBusy(true);
    setError('');
    fetch(
      `${API}/api/anki/deck-fields?path=${encodeURIComponent(config.collection_path)}&deck=${encodeURIComponent(config.deck_name)}`
      + `&${languageParam}`
    )
      .then(async (res) => {
        const data: DeckFields = await res.json();
        if (!res.ok) {
          setError((data as unknown as { detail: string }).detail || 'Could not inspect deck');
          setStep('manage');
          return;
        }
        setDeckFields({ [config.deck_name]: data });
        setMappings({
          [config.deck_name]: {
            name: config.name,
            kanji_field: config.kanji_field || NONE,
            kana_field: config.kana_field,
            meaning_field: config.meaning_field,
            pos_field: config.pos_field || NONE,
            filter_field: config.filter_field || NONE,
            filter_value: config.filter_value || '',
          },
        });
        setStep('mapping');
      })
      .catch(() => {
        setError('Could not reach the server.');
        setStep('manage');
      })
      .finally(() => setBusy(false));
  };

  const toggleEnabled = async (config: DeckConfig) => {
    await fetch(`${API}/api/anki/configs/${config.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enabled: !config.enabled }),
    });
    loadConfigs();
  };

  const syncConfig = async (config: DeckConfig) => {
    setBusy(true);
    try {
      await fetch(`${API}/api/anki/configs/${config.id}/sync`, { method: 'POST' });
      await loadConfigs();
      onSynced?.();
    } finally {
      setBusy(false);
    }
  };

  const deleteConfig = async (config: DeckConfig) => {
    if (!confirm(`Remove "${config.name}" and the ${config.vocab_count} words it imported?`)) return;
    await fetch(`${API}/api/anki/configs/${config.id}`, { method: 'DELETE' });
    loadConfigs();
    onSynced?.();
  };

  const syncAll = async () => {
    setBusy(true);
    try {
      await fetch(`${API}/api/anki/sync?${languageParam}`, { method: 'POST' });
      await loadConfigs();
      onSynced?.();
    } finally {
      setBusy(false);
    }
  };

  // --- Render --------------------------------------------------------------

  const fieldSelect = (
    deck: string,
    value: string,
    onChange: (v: string) => void,
    allowNone: boolean
  ) => (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="w-full px-2 py-1.5 text-sm border border-paper-dark rounded-lg bg-paper text-ink focus:outline-none focus:ring-1 focus:ring-vermillion"
    >
      {allowNone && <option value={NONE}>— none —</option>}
      {!allowNone && value === NONE && <option value={NONE}>— select —</option>}
      {allFields(deck).map((f) => (
        <option key={f} value={f}>
          {f}
        </option>
      ))}
    </select>
  );

  return (
    <div className="fixed inset-0 bg-black/50 dark:bg-black/75 flex items-center justify-center z-50 p-4">
      <div className="bg-paper rounded-lg shadow-xl max-w-2xl w-full max-h-[85vh] flex flex-col dark:border dark:border-paper-dark">
        {/* Header */}
        <div className="flex justify-between items-center p-4 border-b border-paper-dark">
          <h3 className="text-lg font-bold text-ink">
            {step === 'manage' && 'Anki Vocabulary'}
            {step === 'path' && (editingId ? 'Edit Anki Deck' : 'Connect Anki Deck')}
            {step === 'mapping' && (editingId ? 'Edit Field Matching' : 'Review Field Matching')}
            {step === 'result' && 'Import Complete'}
          </h3>
          <button onClick={onClose} className="text-ink-muted hover:text-ink" title="Close">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          {error && (
            <div className="mb-3 px-3 py-2 text-sm rounded-lg bg-vermillion/10 text-vermillion border border-vermillion/30">
              {error}
            </div>
          )}

          {/* ---- Manage ---- */}
          {step === 'manage' && (
            <div>
              {configs.length === 0 ? (
                <div className="text-center py-8">
                  <div className="text-ink font-medium">No Anki decks connected yet.</div>
                  <div className="text-ink-muted text-sm mt-1">
                    Choose your Anki collection file and Nihongo Dojo will pull in the decks you select.
                  </div>
                </div>
              ) : (
                <div className="space-y-2">
                  {configs.map((c) => (
                    <div key={c.id} className="border border-paper-dark rounded-lg p-3">
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0">
                          <div className="font-medium text-ink truncate">{c.name}</div>
                          <div className="text-xs text-ink-muted truncate">{c.deck_name}</div>
                          <div className="text-xs text-ink-muted mt-1">
                            {c.vocab_count} words
                            {c.last_synced_at
                              ? ` · synced ${new Date(c.last_synced_at).toLocaleDateString()}`
                              : ' · never synced'}
                          </div>
                        </div>
                        <div className="flex items-center gap-1 shrink-0">
                          <label className="flex items-center gap-1 text-xs text-ink-muted cursor-pointer mr-1">
                            <input
                              type="checkbox"
                              checked={c.enabled}
                              onChange={() => toggleEnabled(c)}
                            />
                            on
                          </label>
                          <button
                            onClick={() => syncConfig(c)}
                            disabled={busy}
                            className="px-2 py-1 text-xs rounded bg-paper-dark hover:bg-paper-warm text-ink disabled:opacity-50"
                          >
                            Sync
                          </button>
                          <button
                            onClick={() => editConfig(c)}
                            disabled={busy}
                            className="px-2 py-1 text-xs rounded bg-paper-dark hover:bg-paper-warm text-ink disabled:opacity-50"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => deleteConfig(c)}
                            className="px-2 py-1 text-xs rounded text-vermillion hover:bg-vermillion/10"
                          >
                            Delete
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* ---- Path / deck selection ---- */}
          {step === 'path' && (
            <div className="space-y-5">
              {!editingId && (
                <div className="rounded-lg border border-paper-dark bg-paper-warm p-4">
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <div className="text-sm font-medium text-ink">Choose your Anki collection</div>
                      <div className="text-xs text-ink-muted mt-1">
                        Usually named <span className="font-mono">collection.anki2</span>.
                      </div>
                    </div>
                    <label className="inline-flex cursor-pointer items-center justify-center rounded-lg bg-vermillion px-4 py-2 text-sm font-medium text-white hover:bg-vermillion-soft">
                      {busy ? 'Reading...' : 'Choose File'}
                      <input
                        type="file"
                        accept=".anki2"
                        className="sr-only"
                        disabled={busy}
                        onChange={(e) => {
                          uploadCollection(e.currentTarget.files?.[0] || null);
                          e.currentTarget.value = '';
                        }}
                      />
                    </label>
                  </div>
                  {uploadedFileName && (
                    <div className="mt-3 text-xs text-ink-muted">
                      Ready: <span className="text-ink">{uploadedFileName}</span>
                    </div>
                  )}
                </div>
              )}

              <div>
                <div className="flex items-center gap-2 mb-1">
                  <label className="block text-sm font-medium text-ink-light">
                    {editingId ? 'Anki Collection Path' : 'Advanced: use a local path'}
                  </label>
                  {!editingId && (
                    <span className="text-[11px] uppercase tracking-wide text-ink-muted">optional</span>
                  )}
                </div>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={path}
                    onChange={(e) => {
                      setPath(e.target.value);
                      setUploadedFileName('');
                    }}
                    placeholder="~/Library/Application Support/Anki2/User 1/collection.anki2"
                    className="flex-1 px-3 py-2 text-sm border border-paper-dark rounded-lg bg-paper text-ink focus:outline-none focus:ring-1 focus:ring-vermillion"
                  />
                  <button
                    onClick={findDecks}
                    disabled={busy || !path.trim()}
                    className="px-4 py-2 text-sm rounded-lg bg-paper-dark hover:bg-paper-warm text-ink disabled:opacity-50"
                  >
                    {busy ? '...' : 'Find Decks'}
                  </button>
                </div>
                <p className="mt-1 text-xs text-ink-muted">
                  This works best when Nihongo Dojo is running on the same computer as Anki.
                </p>
              </div>

              {decks.length > 0 && (
                <div>
                  <div className="text-sm font-medium text-ink-light mb-2">
                    Select decks to import ({selectedDecks.size} selected)
                  </div>
                  <div className="space-y-1 max-h-64 overflow-y-auto">
                    {decks.map((d) => (
                      <label
                        key={d.deck_name}
                        className="flex items-center gap-2 p-2 rounded-lg hover:bg-paper-warm cursor-pointer"
                      >
                        <input
                          type="checkbox"
                          checked={selectedDecks.has(d.deck_name)}
                          onChange={() => toggleDeck(d.deck_name)}
                        />
                        <span className="text-sm text-ink flex-1 truncate">{d.deck_name}</span>
                        <span className="text-xs text-ink-muted">{d.note_count} notes</span>
                      </label>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ---- Field mapping ---- */}
          {step === 'mapping' && (
            <div className="space-y-5">
              <p className="text-xs text-ink-muted">
                We've guessed the mappings below — adjust anything that looks wrong.
                <span className="text-vermillion"> Reading</span> and
                <span className="text-vermillion"> Meaning</span> are required.
              </p>
              {Object.keys(mappings).map((deck) => {
                const m = mappings[deck];
                const df = deckFields[deck];
                const sampleType = df?.note_types[0];
                return (
                  <div key={deck} className="border border-paper-dark rounded-lg p-3">
                    <div className="text-sm font-medium text-ink mb-1">{deck}</div>
                    <div className="text-xs text-ink-muted mb-3">
                      {df?.note_count} notes ·{' '}
                      {df?.note_types.map((nt) => nt.model_name).join(', ')}
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-xs text-ink-muted mb-1">Name in Nihongo Dojo</label>
                        <input
                          type="text"
                          value={m.name}
                          onChange={(e) => updateMapping(deck, { name: e.target.value })}
                          className="w-full px-2 py-1.5 text-sm border border-paper-dark rounded-lg bg-paper text-ink focus:outline-none focus:ring-1 focus:ring-vermillion"
                        />
                      </div>
                      {showTermField && (
                        <div>
                          <label className="block text-xs text-ink-muted mb-1">{termFieldLabel}</label>
                          {fieldSelect(deck, m.kanji_field, (v) => updateMapping(deck, { kanji_field: v }), true)}
                        </div>
                      )}
                      <div>
                        <label className="block text-xs text-ink-muted mb-1">
                          {readingFieldLabel} <span className="text-vermillion">*</span>
                        </label>
                        {fieldSelect(deck, m.kana_field, (v) => updateMapping(deck, { kana_field: v }), false)}
                      </div>
                      <div>
                        <label className="block text-xs text-ink-muted mb-1">
                          Meaning field <span className="text-vermillion">*</span>
                        </label>
                        {fieldSelect(deck, m.meaning_field, (v) => updateMapping(deck, { meaning_field: v }), false)}
                      </div>
                      <div>
                        <label className="block text-xs text-ink-muted mb-1">Part of speech field</label>
                        {fieldSelect(deck, m.pos_field, (v) => updateMapping(deck, { pos_field: v }), true)}
                      </div>
                    </div>

                    {/* Optional filter */}
                    <div className="mt-3 pt-3 border-t border-paper-dark">
                      <label className="block text-xs text-ink-muted mb-1">
                        Optional filter — only import notes where a field equals a value
                      </label>
                      <div className="flex items-center gap-2">
                        {fieldSelect(deck, m.filter_field, (v) => updateMapping(deck, { filter_field: v }), true)}
                        <span className="text-ink-muted text-sm">=</span>
                        <input
                          type="text"
                          value={m.filter_value}
                          disabled={!m.filter_field}
                          onChange={(e) => updateMapping(deck, { filter_value: e.target.value })}
                          placeholder="e.g. Vocabulary"
                          className="flex-1 px-2 py-1.5 text-sm border border-paper-dark rounded-lg bg-paper text-ink focus:outline-none focus:ring-1 focus:ring-vermillion disabled:opacity-50"
                        />
                      </div>
                    </div>

                    {/* Sample preview */}
                    {sampleType && sampleType.samples.length > 0 && (
                      <details className="mt-3 text-xs">
                        <summary className="cursor-pointer text-ink-muted">
                          Preview sample notes
                        </summary>
                        <div className="mt-2 overflow-x-auto">
                          <table className="text-xs border border-paper-dark">
                            <thead>
                              <tr>
                                {sampleType.fields.map((f) => (
                                  <th key={f} className="px-2 py-1 border border-paper-dark bg-paper-warm text-ink-light text-left">
                                    {f}
                                  </th>
                                ))}
                              </tr>
                            </thead>
                            <tbody>
                              {sampleType.samples.slice(0, 4).map((row, i) => (
                                <tr key={i}>
                                  {sampleType.fields.map((f) => (
                                    <td key={f} className="px-2 py-1 border border-paper-dark text-ink max-w-[12rem] truncate">
                                      {row[f]}
                                    </td>
                                  ))}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </details>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {/* ---- Result ---- */}
          {step === 'result' && result && (
            <div className="text-center py-6">
              <div className="text-ink text-sm mb-2">Your vocabulary is up to date.</div>
              <div className="text-2xl font-bold text-ink">
                {result.imported} new · {result.updated} updated
              </div>
              {result.skipped > 0 && (
                <div className="text-xs text-ink-muted mt-1">{result.skipped} notes skipped</div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-between items-center gap-2 p-4 border-t border-paper-dark">
          {step === 'manage' && (
            <>
              <button
                onClick={syncAll}
                disabled={busy || configs.length === 0}
                className="px-4 py-2 text-sm rounded-lg bg-paper-dark hover:bg-paper-warm text-ink disabled:opacity-50"
              >
                {busy ? 'Syncing...' : 'Sync All'}
              </button>
              <button
                onClick={startWizard}
                className="px-4 py-2 text-sm rounded-lg bg-vermillion hover:bg-vermillion-soft text-white font-medium"
              >
                {configs.length === 0 ? 'Connect Anki Deck' : '+ Add Another Deck'}
              </button>
            </>
          )}

          {step === 'path' && (
            <>
              <button
                onClick={() => setStep('manage')}
                className="px-4 py-2 text-sm rounded-lg bg-paper-dark hover:bg-paper-warm text-ink"
              >
                Back
              </button>
              <button
                onClick={goToMapping}
                disabled={busy || selectedDecks.size === 0}
                className="px-4 py-2 text-sm rounded-lg bg-vermillion hover:bg-vermillion-soft text-white font-medium disabled:opacity-50"
              >
                {busy ? 'Loading...' : 'Next: Review Fields'}
              </button>
            </>
          )}

          {step === 'mapping' && (
            <>
              <button
                onClick={() => setStep(editingId ? 'manage' : 'path')}
                className="px-4 py-2 text-sm rounded-lg bg-paper-dark hover:bg-paper-warm text-ink"
              >
                Back
              </button>
              <button
                onClick={saveAndSync}
                disabled={busy || !allMappingsValid()}
                className="px-4 py-2 text-sm rounded-lg bg-vermillion hover:bg-vermillion-soft text-white font-medium disabled:opacity-50"
              >
                {busy ? 'Saving...' : editingId ? 'Save & Sync' : 'Import Vocabulary'}
              </button>
            </>
          )}

          {step === 'result' && (
            <button
              onClick={() => {
                setStep('manage');
                setResult(null);
              }}
              className="px-4 py-2 text-sm rounded-lg bg-vermillion hover:bg-vermillion-soft text-white font-medium ml-auto"
            >
              Done
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default AnkiSetupWizard;
