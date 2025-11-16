import HealthcareDisclaimer from '../HealthcareDisclaimer.jsx';
import MessageActions from './MessageActions.jsx';
import UserMessageActions from './UserMessageActions.jsx';
import formatDate from '../../utils/formatDate.js';

export default function MessageBubble({ role = 'assistant', children, createdAt, messageId, onEditMessage }) {
  const isUser = role === 'user';
  
  return (
    <div 
      className={`flex gap-4 w-full transition-colors duration-300 ${isUser ? 'justify-end pl-75' : 'justify-start pr-15'}`}
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
      
      {/* Message content - dynamic width for user, full width for assistant */}
      <div className={`min-w-0 ${isUser ? 'max-w-full' : 'flex-1'}`}>
        <div
          className={`transition-colors duration-300 ${
            isUser
              ? 'px-5 py-4 rounded-2xl text-left inline-block'
              : 'py-1'
          }`}
          style={isUser ? { backgroundColor: 'var(--user-msg-bg)' } : {}}
        >
          <div 
            className={`whitespace-pre-wrap break-words transition-colors duration-300 ${isUser ? 'text-left' : ''}`}
            data-message-id={messageId}
            style={{
              fontSize: isUser ? '16px' : '17px',
              lineHeight: '1.75',
              letterSpacing: '-0.011em',
              color: 'var(--text-primary)',
              fontFamily: isUser 
                ? "'Segoe UI', system-ui, -apple-system, BlinkMacSystemFont, sans-serif"
                : "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
            }}
          >
            {children}
          </div>
          {createdAt && (
            <div 
              className={`text-xs mt-3 select-none transition-colors duration-300 ${isUser ? 'text-left' : ''}`}
              style={{ 
                color: 'var(--text-tertiary)',
                fontSize: '12px',
                textAlign: isUser ? 'left' : 'left'
              }}
            >
              {formatDate(createdAt)}
            </div>
          )}
        </div>
        
        {/* Show actions for both user and assistant messages */}
        {isUser ? (
          <UserMessageActions messageId={messageId} onEdit={onEditMessage} />
        ) : (
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


