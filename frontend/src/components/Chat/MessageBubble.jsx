import HealthcareDisclaimer from '../HealthcareDisclaimer.jsx';
import MessageActions from './MessageActions.jsx';
import formatDate from '../../utils/formatDate.js';

export default function MessageBubble({ role = 'assistant', children, createdAt, messageId }) {
  const isUser = role === 'user';
  
  return (
    <div 
      className={`flex gap-4 w-full transition-colors duration-300 ${isUser ? 'pl-16' : 'pr-16'}`}
      role="article" 
      aria-label={isUser ? 'User message' : 'Assistant message'}
    >
      {/* Avatar for assistant (left side) */}
      {!isUser && (
        <div 
          className="flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center text-white font-semibold text-base shadow-md transition-all duration-300"
          style={{
            background: 'linear-gradient(135deg, #a855f7 0%, #6366f1 100%)'
          }}
        >
          V
        </div>
      )}
      
      {/* Message content */}
      <div className="flex-1 min-w-0">
        <div
          className={`transition-colors duration-300 ${
            isUser
              ? 'px-5 py-4 rounded-2xl'
              : 'py-1'
          }`}
          style={isUser ? { backgroundColor: 'var(--user-msg-bg)' } : {}}
        >
          <div 
            className="whitespace-pre-wrap break-words transition-colors duration-300"
            data-message-id={messageId}
            style={{
              fontSize: '17px',
              lineHeight: '1.75',
              letterSpacing: '-0.011em',
              color: 'var(--text-primary)',
              fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
            }}
          >
            {children}
          </div>
          {createdAt && (
            <div 
              className="text-xs mt-3 select-none transition-colors duration-300"
              style={{ 
                color: 'var(--text-tertiary)',
                fontSize: '12px'
              }}
            >
              {formatDate(createdAt)}
            </div>
          )}
        </div>
        
        {/* Show actions and disclaimer only for assistant messages */}
        {!isUser && (
          <div className="mt-3">
            <MessageActions messageId={messageId} />
            <HealthcareDisclaimer />
          </div>
        )}
      </div>
      
      {/* Avatar for user (right side) */}
      {isUser && (
        <div 
          className="flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center text-white font-semibold text-base shadow-md transition-all duration-300"
          style={{
            background: 'linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-primary-hover) 100%)'
          }}
        >
          U
        </div>
      )}
    </div>
  );
}


