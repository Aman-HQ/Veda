import { useState } from 'react';

export default function UserMessageActions({ messageId, onEdit }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    // Copy message content to clipboard
    const messageElement = document.querySelector(`[data-message-id="${messageId}"]`);
    if (messageElement) {
      try {
        await navigator.clipboard.writeText(messageElement.textContent);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      } catch (err) {
        console.error('Failed to copy:', err);
      }
    }
  };

  const handleEdit = () => {
    // Get the message content and pass it to the edit function
    const messageElement = document.querySelector(`[data-message-id="${messageId}"]`);
    if (messageElement && onEdit) {
      const messageContent = messageElement.textContent;
      onEdit(messageContent);
    }
  };

  return (
    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200 justify-end mt-2">
      {/* Copy button */}
      <button
        onClick={handleCopy}
        className="inline-flex items-center justify-center h-8 w-8 rounded-md outline-none focus-visible:ring-2 focus-visible:ring-blue-500 transition-all"
        style={{ color: 'var(--text-secondary)' }}
        onMouseEnter={(e) => {
          e.currentTarget.style.backgroundColor = 'var(--user-msg-bg)';
          e.currentTarget.style.color = 'var(--text-primary)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.backgroundColor = 'transparent';
          e.currentTarget.style.color = 'var(--text-secondary)';
        }}
        title={copied ? 'Copied!' : 'Copy message'}
      >
        {copied ? (
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="20 6 9 17 4 12"></polyline>
          </svg>
        ) : (
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
          </svg>
        )}
      </button>

      {/* Edit button */}
      <button
        onClick={handleEdit}
        className="inline-flex items-center justify-center h-8 w-8 rounded-md outline-none focus-visible:ring-2 focus-visible:ring-blue-500 transition-all"
        style={{ color: 'var(--text-secondary)' }}
        onMouseEnter={(e) => {
          e.currentTarget.style.backgroundColor = 'var(--user-msg-bg)';
          e.currentTarget.style.color = 'var(--text-primary)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.backgroundColor = 'transparent';
          e.currentTarget.style.color = 'var(--text-secondary)';
        }}
        title="Edit message"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
          <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
        </svg>
      </button>
    </div>
  );
}