import React, { useEffect, useLayoutEffect, useRef, useState } from 'react';

interface ChatComposerProps {
  isVisible: boolean;
  isLoading: boolean;
  sendMessage: (content: string, image?: string) => Promise<void>;
  onSent: () => void;
  focusRequest?: number;
}

const MESSAGE_INPUT_MIN_HEIGHT = 44;
const MESSAGE_INPUT_DEFAULT_MAX_HEIGHT = 220;

const getMessageInputMaxHeight = () => {
  if (typeof window === 'undefined') {
    return MESSAGE_INPUT_DEFAULT_MAX_HEIGHT;
  }

  return Math.min(
    260,
    Math.max(140, Math.round(window.innerHeight * 0.32)),
  );
};

const resizeMessageInput = (textarea: HTMLTextAreaElement) => {
  textarea.style.height = 'auto';

  const maxHeight = getMessageInputMaxHeight();
  const scrollHeight = textarea.scrollHeight;
  const contentHeight = textarea.value ? scrollHeight : MESSAGE_INPUT_MIN_HEIGHT;
  const nextHeight = Math.min(
    Math.max(contentHeight, MESSAGE_INPUT_MIN_HEIGHT),
    maxHeight,
  );

  textarea.style.height = `${nextHeight}px`;
  textarea.style.overflowY = textarea.value && scrollHeight > maxHeight ? 'auto' : 'hidden';
};

export const ChatComposer: React.FC<ChatComposerProps> = React.memo(({ isVisible, isLoading, sendMessage, onSent, focusRequest = 0 }) => {
  const [inputValue, setInputValue] = useState('');
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useLayoutEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      resizeMessageInput(textarea);
    }
  }, [inputValue, isVisible]);

  useEffect(() => {
    const handleResize = () => {
      const textarea = textareaRef.current;
      if (textarea) {
        resizeMessageInput(textarea);
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  useEffect(() => {
    if (isVisible && focusRequest > 0) {
      textareaRef.current?.focus();
    }
  }, [focusRequest, isVisible]);

  const processFile = (file: File) => {
    if (!file.type.startsWith('image/')) return;
    const reader = new FileReader();
    reader.onloadend = () => setSelectedImage(reader.result as string);
    reader.readAsDataURL(file);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) processFile(file);
  };

  const handlePaste = (e: React.ClipboardEvent) => {
    const items = e.clipboardData.items;
    for (let i = 0; i < items.length; i++) {
      if (items[i].type.indexOf('image') !== -1) {
        const file = items[i].getAsFile();
        if (file) {
          processFile(file);
          e.preventDefault();
        }
      }
    }
  };

  const handleSubmit = async (e?: React.SyntheticEvent) => {
    e?.preventDefault();
    if ((!inputValue.trim() && !selectedImage) || isLoading) return;

    await sendMessage(inputValue.trim(), selectedImage || undefined);
    setInputValue('');
    setSelectedImage(null);
    onSent();
  };

  return (
    <div className="input-area" hidden={!isVisible}>
      {selectedImage && (
        <div className="image-preview">
          <img src={selectedImage} alt="Preview" />
          <button onClick={() => setSelectedImage(null)} className="remove-image">
            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg>
          </button>
        </div>
      )}
      <form onSubmit={(e) => { void handleSubmit(e); }} className="input-form">
        <input
          type="file"
          accept="image/*"
          ref={fileInputRef}
          onChange={handleFileSelect}
          className="hidden"
        />

        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          className="attach-btn"
          title="Attach image"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2" /><circle cx="8.5" cy="8.5" r="1.5" /><polyline points="21 15 16 10 5 21" /></svg>
        </button>

        <div className="input-wrapper">
          <textarea
            ref={textareaRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onPaste={handlePaste}
            onKeyDown={(e) => {
              const isComposing = e.nativeEvent.isComposing || e.keyCode === 229;
              if (e.key === 'Enter' && !e.shiftKey && !isComposing) {
                e.preventDefault();
                if ((inputValue.trim() || selectedImage) && !isLoading) {
                  void handleSubmit(e);
                }
              }
            }}
            placeholder="Write something..."
            aria-label="Message"
            data-tutorial-target="message-composer"
            className="message-input"
            disabled={isLoading}
            rows={1}
          />

          <button
            type="submit"
            disabled={(!inputValue.trim() && !selectedImage) || isLoading}
            className="send-btn"
            title="Send"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="5" y1="12" x2="19" y2="12" /><polyline points="12 5 19 12 12 19" /></svg>
          </button>
        </div>
      </form>
    </div>
  );
});

export default ChatComposer;
