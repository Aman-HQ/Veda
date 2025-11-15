import { useCallback, useEffect, useRef, useState } from 'react';
import ImageUploader from './ImageUploader.jsx';
import VoiceInput from './VoiceInput.jsx';

export default function Composer({ onSend, onAttachImage, onStartVoice, onStopVoice, initialValue }) {
  const [value, setValue] = useState('');
  const textareaRef = useRef(null);

  // Update value when initialValue changes
  useEffect(() => {
    if (initialValue) {
      setValue(initialValue);
      textareaRef.current?.focus();
    }
  }, [initialValue]);

  // Auto-resize textarea based on content
  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    // Reset height to auto to get the correct scrollHeight
    textarea.style.height = 'auto';
    
    const lineHeight = 16 * 1.6; // 16px fontSize * 1.6 lineHeight = 25.6px per line
    const maxLines = 6;
    const maxHeight = lineHeight * maxLines + 24; // 24px for padding (py-3 = 12px top + 12px bottom)
    const minHeight = 44; // minimum height for single line
    
    // Calculate new height based on content
    const newHeight = Math.min(textarea.scrollHeight, maxHeight);
    
    // Apply new height (use max to ensure minimum height)
    textarea.style.height = `${Math.max(newHeight, minHeight)}px`;
    
    // Enable/disable scrolling based on whether we've reached max height
    if (textarea.scrollHeight > maxHeight) {
      textarea.style.overflowY = 'auto';
    } else {
      textarea.style.overflowY = 'hidden';
    }
  }, [value]);

  const handleKeyDown = useCallback(
    (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        submit();
      }
    },
    [value]
  );

  const submit = () => {
    const trimmed = value.trim();
    if (!trimmed) return;
    onSend?.(trimmed);
    setValue('');
    // Reset height after sending
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
    textareaRef.current?.focus();
  };

  return (
    <div className="sticky bottom-0 inset-x-0 px-4 sm:px-6 py-3">
      <div className="max-w-3xl mx-auto w-full">
        <form
          className="relative rounded-3xl border backdrop-blur-xl shadow-lg transition-all duration-200"
          style={{
            background: 'linear-gradient(135deg, var(--composer-bg-start) 0%, var(--composer-bg-end) 100%)',
            backdropFilter: 'blur(20px)',
            WebkitBackdropFilter: 'blur(20px)',
            borderColor: 'var(--composer-border)',
            boxShadow: '0 4px 6px var(--glass-shadow), 0 0 0 1px rgba(255, 255, 255, 0.5) inset',
            padding: '12px'
          }}
          onSubmit={(e) => {
            e.preventDefault();
            submit();
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.boxShadow = '0 8px 16px var(--glass-shadow), 0 0 0 1px rgba(255, 255, 255, 0.5) inset';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.boxShadow = '0 4px 6px var(--glass-shadow), 0 0 0 1px rgba(255, 255, 255, 0.5) inset';
          }}
          role="form"
          aria-label="Message composer"
        >
            <div className="flex items-end gap-2">
              {/* Action buttons on the left */}
              <div className="flex items-center gap-1 pb-2">
                <ImageUploader onSelect={onAttachImage} />
                <VoiceInput onStart={onStartVoice} onStop={onStopVoice} />
                {/* Camera button */}
                <button
                  type="button"
                  aria-label="Camera"
                  className="inline-flex items-center justify-center h-9 w-9 rounded-full outline-none focus-visible:ring-2 focus-visible:ring-blue-500 transition-all"
                  style={{ color: 'var(--text-secondary)' }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = 'var(--user-msg-bg)';
                    e.currentTarget.style.color = 'var(--text-primary)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'transparent';
                    e.currentTarget.style.color = 'var(--text-secondary)';
                  }}
                  title="Camera"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path>
                    <circle cx="12" cy="13" r="4"></circle>
                  </svg>
                </button>
              </div>
              
              {/* Textarea */}
              <textarea
                ref={textareaRef}
                value={value}
                onChange={(e) => setValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="How can I help you today?"
                rows={1}
                className="flex-1 resize-none bg-transparent outline-none px-3 py-3 leading-relaxed transition-all duration-150"
                style={{ 
                  minHeight: '44px', 
                  maxHeight: 'none',
                  height: '44px',
                  color: 'var(--text-primary)',
                  fontSize: '16px',
                  lineHeight: '1.6',
                  fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
                  overflowY: 'hidden'
                }}
              />
              
              {/* Send button integrated on the right */}
              <button
                type="submit"
                disabled={!value.trim()}
                className="flex-shrink-0 inline-flex items-center justify-center h-9 w-9 rounded-full text-white shadow-md outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 transition-all duration-200 mb-2 disabled:cursor-not-allowed"
                style={{
                  background: value.trim() 
                    ? 'linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-primary-hover) 100%)'
                    : 'linear-gradient(135deg, #cbd5e1 0%, #94a3b8 100%)',
                  boxShadow: value.trim() ? '0 4px 12px rgba(59, 130, 246, 0.4)' : 'none',
                  transform: value.trim() ? 'scale(1)' : 'scale(1)',
                  opacity: value.trim() ? '1' : '0.6'
                }}
                onMouseEnter={(e) => {
                  if (value.trim()) {
                    e.currentTarget.style.transform = 'scale(1.05)';
                    e.currentTarget.style.boxShadow = '0 6px 16px rgba(59, 130, 246, 0.5)';
                  }
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'scale(1)';
                  e.currentTarget.style.boxShadow = value.trim() ? '0 4px 12px rgba(59, 130, 246, 0.4)' : 'none';
                }}
                aria-label="Send message"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="22" y1="2" x2="11" y2="13"></line>
                  <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                </svg>
              </button>
            </div>
          </form>
          <p 
            className="text-center mt-3 transition-colors duration-300"
            style={{ 
              color: 'var(--text-secondary)',
              fontSize: '13px',
              lineHeight: '1.5'
            }}
          >
            Veda can make mistakes. Consider checking important information.
          </p>
        </div>
      </div>
  );
}


