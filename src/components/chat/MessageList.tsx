import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { AgentAction, Message } from '../../hooks/useChat';
import { AudioPlayer } from '../AudioPlayer';

type DifficultyFeedback = 'too_hard' | 'too_easy';

interface MessageListProps {
  messages: Message[];
  isLoading: boolean;
  currentAction: AgentAction | null;
  isAtBottom: boolean;
  messagesEndRef: React.RefObject<HTMLDivElement>;
  selectedSpeakerId?: string;
  speechLanguage?: string;
  languageCode?: string;
  pendingFeedback: DifficultyFeedback | null;
  onDifficultyFeedback: (direction: DifficultyFeedback) => void;
  onJumpToBottom: () => void;
}

const MARKDOWN_COMPONENTS = {
  p: ({ children }: { children?: React.ReactNode }) => <p className="prose-p">{children}</p>,
  ul: ({ children }: { children?: React.ReactNode }) => <ul className="prose-ul">{children}</ul>,
  ol: ({ children }: { children?: React.ReactNode }) => <ol className="prose-ol">{children}</ol>,
  li: ({ children }: { children?: React.ReactNode }) => <li className="prose-li">{children}</li>,
  strong: ({ children }: { children?: React.ReactNode }) => <strong className="prose-strong">{children}</strong>,
  em: ({ children }: { children?: React.ReactNode }) => <em className="prose-em">{children}</em>,
  code: ({ children, className }: { children?: React.ReactNode; className?: string }) => {
    const isInline = !className;
    return isInline ? (
      <code className="prose-code-inline">{children}</code>
    ) : (
      <code className={`prose-code-block ${className || ''}`}>
        {children}
      </code>
    );
  },
  blockquote: ({ children }: { children?: React.ReactNode }) => (
    <blockquote className="prose-blockquote">{children}</blockquote>
  ),
};

const REMARK_PLUGINS = [remarkGfm];

const AgentActionIndicator: React.FC<{ action: AgentAction }> = ({ action }) => {
  const getActionText = () => {
    switch (action.type) {
      case 'thinking':
        return 'Thinking';
      case 'tool_call':
        return action.name ? `Using ${action.name}` : 'Processing';
      case 'tool_result':
        return action.name ? `Reading ${action.name}` : 'Reading results';
      default:
        return 'Working';
    }
  };

  return (
    <div className="agent-action">
      <div className="action-indicator">
        <span className="action-dot" />
        <span className="action-text">{getActionText()}</span>
      </div>
    </div>
  );
};

const shouldShowTimestamp = (message: Message, previousMessage?: Message): boolean => {
  if (!previousMessage) return true;

  const timeDiff = message.timestamp.getTime() - previousMessage.timestamp.getTime();
  const fiveMinutes = 5 * 60 * 1000;

  if (timeDiff > fiveMinutes) return true;

  const prevDate = previousMessage.timestamp.toDateString();
  const currDate = message.timestamp.toDateString();
  return prevDate !== currDate;
};

const formatTimestamp = (date: Date): string => {
  const now = new Date();
  const isToday = date.toDateString() === now.toDateString();
  const yesterday = new Date(now);
  yesterday.setDate(yesterday.getDate() - 1);
  const isYesterday = date.toDateString() === yesterday.toDateString();

  const time = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  if (isToday) {
    return time;
  } else if (isYesterday) {
    return `Yesterday, ${time}`;
  } else {
    return `${date.toLocaleDateString([], { month: 'short', day: 'numeric' })}, ${time}`;
  }
};

const UserMessage: React.FC<{ message: Message }> = React.memo(({ message }) => (
  <div className="message-user">
    {message.image && (
      <img
        src={message.image}
        alt="Attachment"
        className="user-image"
      />
    )}
    <p className="user-text">{message.content}</p>
  </div>
));

const AssistantMessage: React.FC<{
  message: Message;
  selectedSpeakerId?: string;
  speechLanguage?: string;
  languageCode?: string;
  pendingFeedback: DifficultyFeedback | null;
  onDifficultyFeedback: (direction: DifficultyFeedback) => void;
}> = React.memo(({ message, selectedSpeakerId, speechLanguage, languageCode, pendingFeedback, onDifficultyFeedback }) => {
  const chunks = message.content
    ? message.content.split(/\n\n+/).filter(chunk => chunk.trim())
    : [];

  return (
    <div className="message-assistant group">
      <div className="assistant-content">
        {chunks.length > 0 ? (
          chunks.map((chunk, index) => (
            <div key={index} className="message-chunk">
              <div className="chunk-content">
                <ReactMarkdown remarkPlugins={REMARK_PLUGINS} components={MARKDOWN_COMPONENTS}>
                  {chunk}
                </ReactMarkdown>
              </div>
              {message.status === 'complete' && (
                <AudioPlayer
                  text={chunk}
                  speakerId={selectedSpeakerId}
                  speechLanguage={speechLanguage}
                  languageCode={languageCode}
                />
              )}
            </div>
          ))
        ) : (
          message.status === 'streaming' && !message.content && (
            <span className="streaming-cursor" />
          )
        )}
      </div>

      {message.status === 'complete' && (
        <div className="feedback-buttons">
          <button
            onClick={() => onDifficultyFeedback('too_hard')}
            className={`feedback-btn ${pendingFeedback === 'too_hard' ? 'active-hard' : ''}`}
          >
            Too Hard
          </button>
          <button
            onClick={() => onDifficultyFeedback('too_easy')}
            className={`feedback-btn ${pendingFeedback === 'too_easy' ? 'active-easy' : ''}`}
          >
            Too Easy
          </button>
        </div>
      )}
    </div>
  );
});

const MessageRow: React.FC<{
  message: Message;
  previousMessage?: Message;
  selectedSpeakerId?: string;
  speechLanguage?: string;
  languageCode?: string;
  pendingFeedback: DifficultyFeedback | null;
  onDifficultyFeedback: (direction: DifficultyFeedback) => void;
}> = React.memo(({ message, previousMessage, selectedSpeakerId, speechLanguage, languageCode, pendingFeedback, onDifficultyFeedback }) => (
  <>
    {shouldShowTimestamp(message, previousMessage) && (
      <div className="timestamp-cluster">
        <span className="timestamp-label">
          {formatTimestamp(message.timestamp)}
        </span>
      </div>
    )}
    {message.role === 'user' ? (
      <UserMessage message={message} />
    ) : (
      <AssistantMessage
        message={message}
        selectedSpeakerId={selectedSpeakerId}
        speechLanguage={speechLanguage}
        languageCode={languageCode}
        pendingFeedback={pendingFeedback}
        onDifficultyFeedback={onDifficultyFeedback}
      />
    )}
  </>
));

export const MessageList: React.FC<MessageListProps> = React.memo(({
  messages,
  isLoading,
  currentAction,
  isAtBottom,
  messagesEndRef,
  selectedSpeakerId,
  speechLanguage,
  languageCode,
  pendingFeedback,
  onDifficultyFeedback,
  onJumpToBottom,
}) => (
  <>
    {messages.length === 0 && (
      <div className="empty-state">
        <span className="empty-jp">はじめましょう</span>
        <span className="empty-en">Let's begin your practice</span>
      </div>
    )}

    {messages.map((message, index) => (
      <MessageRow
        key={message.id}
        message={message}
        previousMessage={index > 0 ? messages[index - 1] : undefined}
        selectedSpeakerId={selectedSpeakerId}
        speechLanguage={speechLanguage}
        languageCode={languageCode}
        pendingFeedback={pendingFeedback}
        onDifficultyFeedback={onDifficultyFeedback}
      />
    ))}

    {isLoading && currentAction && (
      <AgentActionIndicator action={currentAction} />
    )}

    {!isAtBottom && isLoading && (
      <button
        onClick={onJumpToBottom}
        className="scroll-bottom-btn"
      >
        ↓ New message
      </button>
    )}

    <div ref={messagesEndRef} />
  </>
));

export default MessageList;
