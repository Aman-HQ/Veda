export default function EmptyState({ username, onPromptClick }) {
  const prompts = [
    {
      icon: '🩺',
      title: 'Health Advice',
      prompt: 'What are common symptoms of the flu?'
    },
    {
      icon: '💊',
      title: 'Medications',
      prompt: 'Tell me about medication interactions'
    },
    {
      icon: '🏃',
      title: 'Wellness Tips',
      prompt: 'How can I improve my sleep quality?'
    },
    {
      icon: '🍎',
      title: 'Nutrition',
      prompt: "What's a balanced diet for adults?"
    }
  ];

  return (
    <div className="flex flex-col items-center justify-center px-6 py-12 min-h-full">
      {/* Welcome Section */}
      <div className="text-center mb-12">
        <div className="text-6xl mb-6 animate-float">✨</div>
        <h1 
          className="text-5xl font-bold mb-3"
          style={{ 
            color: 'var(--text-primary)',
            letterSpacing: '-0.02em',
            fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
          }}
        >
          Hello, {username || 'there'}
        </h1>
        <p 
          className="text-xl"
          style={{ 
            color: 'var(--text-secondary)',
            fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
          }}
        >
          How can I help you today?
        </p>
      </div>

      {/* Suggested Prompts */}
      <div className="w-full max-w-4xl mb-8">
        <h3 
          className="text-base font-semibold text-center mb-4"
          style={{ 
            color: 'var(--text-secondary)',
            fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
          }}
        >
          Try asking about:
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {prompts.map((item, index) => (
            <button
              key={index}
              onClick={() => onPromptClick?.(item.prompt)}
              className="prompt-card group"
              style={{
                padding: '20px',
                borderRadius: '12px',
                border: '1px solid var(--composer-border)',
                background: 'var(--composer-bg)',
                backdropFilter: 'blur(10px)',
                WebkitBackdropFilter: 'blur(10px)',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                textAlign: 'left'
              }}
            >
              <div className="text-3xl mb-3">{item.icon}</div>
              <div 
                className="font-semibold mb-2"
                style={{ 
                  fontSize: '14px',
                  color: 'var(--text-primary)',
                  fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
                }}
              >
                {item.title}
              </div>
              <div 
                style={{ 
                  fontSize: '13px',
                  color: 'var(--text-secondary)',
                  lineHeight: '1.5',
                  fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
                }}
              >
                {item.prompt}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Start Typing Hint */}
      <div 
        className="flex items-center gap-2 animate-bounce-subtle"
        style={{ 
          color: 'var(--text-secondary)',
          fontSize: '14px',
          fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
        }}
      >
        <svg 
          width="16" 
          height="16" 
          viewBox="0 0 16 16" 
          fill="none" 
          xmlns="http://www.w3.org/2000/svg"
          className="opacity-70"
        >
          <path 
            d="M8 3V13M8 13L12 9M8 13L4 9" 
            stroke="currentColor" 
            strokeWidth="2" 
            strokeLinecap="round" 
            strokeLinejoin="round"
          />
        </svg>
        Start typing below to begin a new conversation
      </div>
    </div>
  );
}
