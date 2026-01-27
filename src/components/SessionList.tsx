import React, { useState } from 'react';
import type { Session } from '../hooks/useSessions';

interface SessionListProps {
  sessions: Session[];
  currentSessionId: string | null;
  onSelect: (sessionId: string) => void;
  onRename: (sessionId: string, name: string) => void;
  onDelete: (sessionId: string) => void;
  onNewChat: () => void;
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));

  if (diffDays === 0) {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } else if (diffDays === 1) {
    return 'Yesterday';
  } else if (diffDays < 7) {
    return date.toLocaleDateString([], { weekday: 'short' });
  } else {
    return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
  }
}

function getDisplayName(session: Session): string {
  if (session.name) return session.name;
  if (session.preview) return session.preview.slice(0, 30) + (session.preview.length > 30 ? '...' : '');
  return formatDate(session.created_at);
}

export const SessionList: React.FC<SessionListProps> = ({
  sessions,
  currentSessionId,
  onSelect,
  onRename,
  onDelete,
  onNewChat,
}) => {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState('');
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);

  const handleStartEdit = (session: Session) => {
    setEditingId(session.id);
    setEditValue(session.name || session.preview || '');
  };

  const handleSaveEdit = () => {
    if (editingId && editValue.trim()) {
      onRename(editingId, editValue.trim());
    }
    setEditingId(null);
    setEditValue('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSaveEdit();
    } else if (e.key === 'Escape') {
      setEditingId(null);
      setEditValue('');
    }
  };

  const handleDeleteClick = (sessionId: string) => {
    setDeleteConfirmId(sessionId);
  };

  const handleConfirmDelete = () => {
    if (deleteConfirmId) {
      onDelete(deleteConfirmId);
      setDeleteConfirmId(null);
    }
  };

  return (
    <div className="session-list-container">
      {/* New Chat Button */}
      <button onClick={onNewChat} className="new-chat-btn">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 5v14M5 12h14"/>
        </svg>
        <span>New Chat</span>
      </button>

      {/* Sessions List */}
      <div className="session-list">
        {sessions.map((session) => (
          <div
            key={session.id}
            className={`session-item ${session.id === currentSessionId ? 'active' : ''}`}
            onClick={() => !editingId && onSelect(session.id)}
          >
            {editingId === session.id ? (
              <input
                type="text"
                className="session-edit-input"
                value={editValue}
                onChange={(e) => setEditValue(e.target.value)}
                onBlur={handleSaveEdit}
                onKeyDown={handleKeyDown}
                autoFocus
                onClick={(e) => e.stopPropagation()}
              />
            ) : (
              <>
                <span className="session-name">{getDisplayName(session)}</span>
                <div className="session-actions">
                  <button
                    className="session-action-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleStartEdit(session);
                    }}
                    title="Rename"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>
                    </svg>
                  </button>
                  <button
                    className="session-action-btn delete"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteClick(session.id);
                    }}
                    title="Delete"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M3 6h18M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
                    </svg>
                  </button>
                </div>
              </>
            )}
          </div>
        ))}

        {sessions.length === 0 && (
          <div className="session-empty">No conversations yet</div>
        )}
      </div>

      {/* Delete Confirmation Modal */}
      {deleteConfirmId && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-sm w-full mx-4 p-4">
            <h3 className="text-lg font-bold mb-2">Delete conversation?</h3>
            <p className="text-gray-600 text-sm mb-4">
              This will permanently delete this conversation and all its messages.
            </p>
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => setDeleteConfirmId(null)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmDelete}
                className="px-4 py-2 text-sm font-medium text-white bg-red-500 hover:bg-red-600 rounded-lg"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SessionList;
