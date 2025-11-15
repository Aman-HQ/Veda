export default function VoiceInput({ onStart, onStop }) {
  return (
    <div className="inline-flex items-center gap-1">
      <button
        type="button"
        aria-label="Voice input"
        title="Voice input"
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
        onClick={onStart}
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"></path>
          <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
          <line x1="12" x2="12" y1="19" y2="22"></line>
        </svg>
      </button>
      <button
        type="button"
        aria-label="Stop voice input"
        className="hidden"
        onClick={onStop}
      />
    </div>
  );
}

