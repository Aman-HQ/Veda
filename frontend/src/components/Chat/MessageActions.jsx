import { useState } from 'react';

export default function MessageActions({ messageId }) {
  const [feedback, setFeedback] = useState(null); // 'up' | 'down' | null
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

  const handleFeedback = (type) => {
    setFeedback(feedback === type ? null : type);
    // TODO: Send feedback to backend
    console.log(`Feedback ${type} for message ${messageId}`);
  };

  const handleRegenerate = () => {
    // TODO: Implement regenerate functionality
    console.log('Regenerate message', messageId);
  };

  return (
    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
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

      {/* Thumbs Up */}
      <button
        onClick={() => handleFeedback('up')}
        className={`inline-flex items-center justify-center h-8 w-8 rounded-md outline-none focus-visible:ring-2 focus-visible:ring-blue-500 transition-all ${
          feedback === 'up' ? 'bg-green-100 dark:bg-green-900/30' : ''
        }`}
        style={{ 
          color: feedback === 'up' ? '#10b981' : 'var(--text-secondary)'
        }}
        onMouseEnter={(e) => {
          if (feedback !== 'up') {
            e.currentTarget.style.backgroundColor = 'var(--user-msg-bg)';
            e.currentTarget.style.color = 'var(--text-primary)';
          }
        }}
        onMouseLeave={(e) => {
          if (feedback !== 'up') {
            e.currentTarget.style.backgroundColor = 'transparent';
            e.currentTarget.style.color = 'var(--text-secondary)';
          }
        }}
        title="Good response"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill={feedback === 'up' ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M7 10v12"></path>
          <path d="M15 5.88 14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2h0a3.13 3.13 0 0 1 3 3.88Z"></path>
        </svg>
      </button>

      {/* Thumbs Down */}
      <button
        onClick={() => handleFeedback('down')}
        className={`inline-flex items-center justify-center h-8 w-8 rounded-md outline-none focus-visible:ring-2 focus-visible:ring-blue-500 transition-all ${
          feedback === 'down' ? 'bg-red-100 dark:bg-red-900/30' : ''
        }`}
        style={{ 
          color: feedback === 'down' ? '#ef4444' : 'var(--text-secondary)'
        }}
        onMouseEnter={(e) => {
          if (feedback !== 'down') {
            e.currentTarget.style.backgroundColor = 'var(--user-msg-bg)';
            e.currentTarget.style.color = 'var(--text-primary)';
          }
        }}
        onMouseLeave={(e) => {
          if (feedback !== 'down') {
            e.currentTarget.style.backgroundColor = 'transparent';
            e.currentTarget.style.color = 'var(--text-secondary)';
          }
        }}
        title="Bad response"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill={feedback === 'down' ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M17 14V2"></path>
          <path d="M9 18.12 10 14H4.17a2 2 0 0 1-1.92-2.56l2.33-8A2 2 0 0 1 6.5 2H20a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-2.76a2 2 0 0 0-1.79 1.11L12 22h0a3.13 3.13 0 0 1-3-3.88Z"></path>
        </svg>
      </button>

      {/* Regenerate button */}
      <button
        onClick={handleRegenerate}
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
        title="Regenerate response"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 2v6h-6"></path>
          <path d="M3 12a9 9 0 0 1 15-6.7L21 8"></path>
          <path d="M3 22v-6h6"></path>
          <path d="M21 12a9 9 0 0 1-15 6.7L3 16"></path>
        </svg>
      </button>
    </div>
  );
}
