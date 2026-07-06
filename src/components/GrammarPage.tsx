import React, { useState, useCallback } from 'react';
import { useGrammar, GrammarEntry } from '../hooks/useGrammar';

const STATUS_CYCLE = ['New', 'Learning', 'Burned'] as const;

const STATUS_COLORS: Record<string, string> = {
  New: 'bg-blue-500 dark:bg-blue-400',
  Learning: 'bg-yellow-500 dark:bg-yellow-400',
  Burned: 'bg-jade',
};

interface AddGrammarModalProps {
  isOpen: boolean;
  onClose: () => void;
  levels: string[];
  levelSchemeName: string;
  onAdd: (data: { pattern: string; meaning: string; jlpt_level?: string; notes?: string }) => Promise<GrammarEntry | null>;
}

function AddGrammarModal({ isOpen, onClose, levels, levelSchemeName, onAdd }: AddGrammarModalProps) {
  const [pattern, setPattern] = useState('');
  const [meaning, setMeaning] = useState('');
  const [jlptLevel, setJlptLevel] = useState('');
  const [notes, setNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!pattern.trim() || !meaning.trim()) return;

    setIsSubmitting(true);
    const result = await onAdd({
      pattern: pattern.trim(),
      meaning: meaning.trim(),
      jlpt_level: jlptLevel || undefined,
      notes: notes.trim() || undefined,
    });
    setIsSubmitting(false);

    if (result) {
      setPattern('');
      setMeaning('');
      setJlptLevel('');
      setNotes('');
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 dark:bg-black/75 flex items-center justify-center z-50">
      <div className="bg-paper rounded-lg shadow-xl w-full max-w-md mx-4 border border-paper-dark">
        <div className="p-4 border-b border-paper-dark">
          <h2 className="text-lg font-semibold text-ink">Add Grammar Point</h2>
        </div>

        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          <div>
            <label className="block text-sm font-medium text-ink-muted mb-1">
              Pattern <span className="text-vermillion">*</span>
            </label>
            <input
              type="text"
              value={pattern}
              onChange={(e) => setPattern(e.target.value)}
              className="w-full px-3 py-2 bg-paper-warm border border-paper-dark rounded-lg text-ink focus:outline-none focus:border-vermillion"
              placeholder="e.g. ている"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-ink-muted mb-1">
              Meaning <span className="text-vermillion">*</span>
            </label>
            <input
              type="text"
              value={meaning}
              onChange={(e) => setMeaning(e.target.value)}
              className="w-full px-3 py-2 bg-paper-warm border border-paper-dark rounded-lg text-ink focus:outline-none focus:border-vermillion"
              placeholder="e.g. is/are/am doing"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-ink-muted mb-1">
              {levelSchemeName} Level
            </label>
            <select
              value={jlptLevel}
              onChange={(e) => setJlptLevel(e.target.value)}
              className="w-full px-3 py-2 bg-paper-warm border border-paper-dark rounded-lg text-ink focus:outline-none focus:border-vermillion"
            >
              <option value="">Custom (no level)</option>
              {levels.map(level => (
                <option key={level} value={level}>{level}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-ink-muted mb-1">
              Notes
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="w-full px-3 py-2 bg-paper-warm border border-paper-dark rounded-lg text-ink focus:outline-none focus:border-vermillion resize-none"
              placeholder="Optional notes about usage..."
              rows={3}
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-ink-muted hover:text-ink transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting || !pattern.trim() || !meaning.trim()}
              className="px-4 py-2 bg-vermillion text-white rounded-lg hover:bg-vermillion-soft disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isSubmitting ? 'Adding...' : 'Add Grammar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

interface GrammarItemProps {
  entry: GrammarEntry;
  onStatusChange: (id: number, status: string) => void;
}

function GrammarItem({ entry, onStatusChange }: GrammarItemProps) {
  const cycleStatus = () => {
    const currentIndex = STATUS_CYCLE.indexOf(entry.status as typeof STATUS_CYCLE[number]);
    const nextIndex = (currentIndex + 1) % STATUS_CYCLE.length;
    onStatusChange(entry.id, STATUS_CYCLE[nextIndex]);
  };

  return (
    <div className="flex items-center gap-3 px-3 py-2 hover:bg-paper-warm rounded-lg transition-colors group">
      <button
        onClick={cycleStatus}
        className={`w-3 h-3 rounded-full ${STATUS_COLORS[entry.status] || STATUS_COLORS.New} flex-shrink-0 cursor-pointer hover:ring-2 hover:ring-offset-2 hover:ring-vermillion/50 transition-all`}
        title={`Status: ${entry.status}. Click to cycle.`}
      />
      <div className="flex-1 min-w-0">
        <span className="font-medium text-ink" style={{ fontFamily: 'var(--font-jp)' }}>
          {entry.pattern}
        </span>
        <span className="text-ink-muted ml-2 text-sm">
          {entry.meaning}
        </span>
      </div>
      {entry.notes && (
        <span className="text-ink-muted text-xs hidden group-hover:inline" title={entry.notes}>
          [notes]
        </span>
      )}
    </div>
  );
}

interface LevelSectionProps {
  level: string;
  entries: GrammarEntry[];
  isExpanded: boolean;
  onToggle: () => void;
  onStatusChange: (id: number, status: string) => void;
  stats?: { total: number; New: number; Learning: number; Burned: number };
}

function LevelSection({ level, entries, isExpanded, onToggle, onStatusChange, stats }: LevelSectionProps) {
  if (entries.length === 0) return null;

  return (
    <div className="border border-paper-dark rounded-lg overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between px-4 py-3 bg-paper-warm hover:bg-paper-dark/50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <span className="text-lg font-semibold text-ink">{level}</span>
          <span className="text-sm text-ink-muted">({entries.length})</span>
        </div>
        <div className="flex items-center gap-4">
          {stats && (
            <div className="flex items-center gap-2 text-xs">
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-blue-500" />
                {stats.New}
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-yellow-500" />
                {stats.Learning}
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-jade" />
                {stats.Burned}
              </span>
            </div>
          )}
          <svg
            className={`w-5 h-5 text-ink-muted transition-transform ${isExpanded ? 'rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      {isExpanded && (
        <div className="divide-y divide-paper-dark/50">
          {entries.map(entry => (
            <GrammarItem
              key={entry.id}
              entry={entry}
              onStatusChange={onStatusChange}
            />
          ))}
        </div>
      )}
    </div>
  );
}

interface GrammarPageProps {
  languageCode?: string;
}

export default function GrammarPage({ languageCode = 'ja' }: GrammarPageProps) {
  const {
    grammarByLevel,
    stats,
    levels,
    isLoading,
    statusFilter,
    searchQuery,
    setStatusFilter,
    setSearchQuery,
    updateStatus,
    addGrammar,
  } = useGrammar(languageCode);

  const [expandedLevels, setExpandedLevels] = useState<Set<string>>(new Set([levels[0] || 'N5']));
  const [showAddModal, setShowAddModal] = useState(false);
  const customLabel = stats?.level_scheme?.custom_label || 'Custom';
  const grammarLevels = levels.filter(level => level !== customLabel);

  const toggleLevel = useCallback((level: string) => {
    setExpandedLevels(prev => {
      const next = new Set(prev);
      if (next.has(level)) {
        next.delete(level);
      } else {
        next.add(level);
      }
      return next;
    });
  }, []);

  const handleStatusChange = useCallback((id: number, status: string) => {
    updateStatus(id, status);
  }, [updateStatus]);

  const statusFilters = [
    { label: 'All', value: null },
    { label: 'New', value: 'New', color: 'bg-blue-500' },
    { label: 'Learning', value: 'Learning', color: 'bg-yellow-500' },
    { label: 'Burned', value: 'Burned', color: 'bg-jade' },
  ];

  return (
    <div className="flex flex-col h-full bg-paper">
      {/* Header */}
      <div className="flex-shrink-0 px-4 py-3 border-b border-paper-dark">
        <div className="flex items-center justify-between mb-3">
          <h1 className="text-xl font-semibold text-ink" style={{ fontFamily: 'var(--font-jp)' }}>
            Grammar Tree
          </h1>
          <button
            onClick={() => setShowAddModal(true)}
            className="px-3 py-1.5 text-sm bg-vermillion text-white rounded-lg hover:bg-vermillion-soft transition-colors"
          >
            + Add Grammar
          </button>
        </div>

        {/* Stats strip */}
        {stats && (
          <div className="flex items-center gap-4 mb-3 text-sm">
            <span className="text-ink-muted">
              Total: <span className="text-ink font-medium">{stats.total}</span>
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-blue-500" />
              <span className="text-ink">{stats.by_status.New}</span>
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-yellow-500" />
              <span className="text-ink">{stats.by_status.Learning}</span>
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-jade" />
              <span className="text-ink">{stats.by_status.Burned}</span>
            </span>
            {stats.custom > 0 && (
              <span className="text-ink-muted">
                Custom: <span className="text-ink">{stats.custom}</span>
              </span>
            )}
          </div>
        )}

        {/* Filters */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1">
            {statusFilters.map(filter => (
              <button
                key={filter.label}
                onClick={() => setStatusFilter(filter.value)}
                className={`px-3 py-1 text-sm rounded-full transition-colors ${
                  statusFilter === filter.value
                    ? 'bg-vermillion text-white'
                    : 'text-ink-muted hover:text-ink hover:bg-paper-warm'
                }`}
              >
                {filter.color && (
                  <span className={`inline-block w-2 h-2 rounded-full ${filter.color} mr-1.5`} />
                )}
                {filter.label}
              </button>
            ))}
          </div>

          <div className="flex-1 max-w-xs">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search grammar..."
              className="w-full px-3 py-1.5 text-sm bg-paper-warm border border-paper-dark rounded-lg text-ink placeholder:text-ink-muted focus:outline-none focus:border-vermillion"
            />
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {isLoading ? (
          <div className="flex items-center justify-center h-32">
            <span className="text-ink-muted">Loading grammar...</span>
          </div>
        ) : (
          levels.map(level => (
            <LevelSection
              key={level}
              level={level}
              entries={grammarByLevel[level] || []}
              isExpanded={expandedLevels.has(level)}
              onToggle={() => toggleLevel(level)}
              onStatusChange={handleStatusChange}
              stats={level !== customLabel ? stats?.by_level[level] : undefined}
            />
          ))
        )}
      </div>

      {/* Add Modal */}
      <AddGrammarModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        levels={grammarLevels}
        levelSchemeName={stats?.level_scheme?.name || 'JLPT'}
        onAdd={addGrammar}
      />
    </div>
  );
}
