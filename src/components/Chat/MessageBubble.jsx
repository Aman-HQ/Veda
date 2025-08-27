import HealthcareDisclaimer from '../HealthcareDisclaimer.jsx';
import formatDate from '../../utils/formatDate.js';

export default function MessageBubble({ role = 'assistant', children, createdAt }) {
  const isUser = role === 'user';
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`} role="article" aria-label={isUser ? 'User message' : 'Assistant message'}>
      <div
        className={`max-w-[85%] sm:max-w-[70%] rounded-2xl px-4 py-3 shadow transition-all duration-200 ${
          isUser
            ? 'bg-indigo-600 text-white rounded-br-none'
            : 'bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-100 rounded-bl-none'
        }`}
      >
        <div className="whitespace-pre-wrap break-words">{children}</div>
        {createdAt && (
          <div className="text-xs text-slate-400 dark:text-slate-500 mt-1 text-right select-none">
            {formatDate(createdAt)}
          </div>
        )}
        {!isUser ? <HealthcareDisclaimer /> : null}
      </div>
    </div>
  );
}

