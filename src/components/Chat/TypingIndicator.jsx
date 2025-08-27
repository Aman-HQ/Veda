export default function TypingIndicator() {
  return (
    <div className="flex justify-start">
      <div className="inline-flex items-center gap-1 rounded-full bg-slate-200 dark:bg-slate-700 px-3 py-1">
        <span className="sr-only">Assistant is typing</span>
        <span className="w-2 h-2 rounded-full bg-slate-500 animate-bounce [animation-delay:-0.2s]" />
        <span className="w-2 h-2 rounded-full bg-slate-500 animate-bounce" />
        <span className="w-2 h-2 rounded-full bg-slate-500 animate-bounce [animation-delay:0.2s]" />
      </div>
    </div>
  );
}

