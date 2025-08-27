export default function VoiceInput({ onStart, onStop }) {
  return (
    <div className="inline-flex items-center gap-1">
      <button
        type="button"
        aria-label="Start voice input"
        className="inline-flex items-center justify-center h-8 w-8 rounded-md text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2 dark:focus-visible:ring-offset-slate-900"
        onClick={onStart}
      >
        🎤
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

