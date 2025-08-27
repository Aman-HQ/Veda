import { useCallback, useRef, useState } from 'react';
import ImageUploader from './ImageUploader.jsx';
import VoiceInput from './VoiceInput.jsx';

export default function Composer({ onSend, onAttachImage, onStartVoice, onStopVoice }) {
  const [value, setValue] = useState('');
  const textareaRef = useRef(null);

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
    textareaRef.current?.focus();
  };

  return (
    <div className="sticky bottom-0 inset-x-0">
      <div className="px-4 sm:px-6">
        <div className="max-w-2xl mx-auto w-full pb-4 sm:pb-6">
          <form
            className="rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 shadow-sm p-2"
            onSubmit={(e) => {
              e.preventDefault();
              submit();
            }}
            role="form"
            aria-label="Message composer"
          >
            <textarea
              ref={textareaRef}
              value={value}
              onChange={(e) => setValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Message Veda..."
              rows={1}
              className="w-full resize-none bg-transparent outline-none text-slate-800 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 px-3 py-2 focus-visible:ring-2 focus-visible:ring-indigo-500 rounded-xl"
            />
            <div className="flex items-center justify-between px-2">
              <div className="flex items-center gap-2">
                <ImageUploader onSelect={onAttachImage} />
                <VoiceInput onStart={onStartVoice} onStop={onStopVoice} />
              </div>
              <button
                type="submit"
                className="inline-flex items-center gap-2 rounded-md bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium px-3 py-1.5 outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2 dark:focus-visible:ring-offset-slate-900"
                aria-label="Send message"
              >
                Send
              </button>
            </div>
          </form>
          <p className="text-center text-xs text-slate-500 dark:text-slate-400 mt-2">
            Veda can make mistakes. Consider checking important information.
          </p>
        </div>
      </div>
    </div>
  );
}


