import { useState, useEffect } from 'react';

export default function EmptyState({ username, onPromptClick }) {
  // All 20 healthcare-related prompts
  const allPrompts = [
    // Set 1 (Original)
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
    },
    // Set 2
    {
      icon: '❤️',
      title: 'Heart Health',
      prompt: 'How can I maintain a healthy heart?'
    },
    {
      icon: '🧠',
      title: 'Mental Wellness',
      prompt: 'What are effective stress management techniques?'
    },
    {
      icon: '🦴',
      title: 'Bone Health',
      prompt: 'How can I prevent osteoporosis?'
    },
    {
      icon: '👁️',
      title: 'Eye Care',
      prompt: 'What are signs of eye strain from screens?'
    },
    // Set 3
    {
      icon: '🫁',
      title: 'Respiratory Health',
      prompt: 'How can I improve lung capacity?'
    },
    {
      icon: '💉',
      title: 'Vaccinations',
      prompt: 'What vaccines do adults need?'
    },
    {
      icon: '🧘',
      title: 'Mindfulness',
      prompt: 'How does meditation benefit health?'
    },
    {
      icon: '🥗',
      title: 'Healthy Eating',
      prompt: 'What foods boost immune system?'
    },
    // Set 4
    {
      icon: '🏋️',
      title: 'Fitness',
      prompt: 'What exercises are best for beginners?'
    },
    {
      icon: '😴',
      title: 'Sleep Health',
      prompt: 'How many hours of sleep do I need?'
    },
    {
      icon: '🩸',
      title: 'Blood Pressure',
      prompt: 'How can I naturally lower blood pressure?'
    },
    {
      icon: '🦷',
      title: 'Dental Health',
      prompt: 'What are best practices for oral hygiene?'
    },
    // Set 5
    {
      icon: '🌡️',
      title: 'Fever',
      prompt: 'When should I be concerned about a fever?'
    },
    {
      icon: '🧴',
      title: 'Skin Care',
      prompt: 'How can I protect my skin from sun damage?'
    },
    {
      icon: '💪',
      title: 'Muscle Health',
      prompt: 'How can I prevent muscle cramps?'
    },
    {
      icon: '🍵',
      title: 'Hydration',
      prompt: 'How much water should I drink daily?'
    }
  ];

  // Cycling logic with localStorage persistence
  // Initialize with the next set in sequence (no repeats until full cycle)
  const [currentSetIndex, setCurrentSetIndex] = useState(() => {
    try {
      const stored = localStorage.getItem('vedaCardSetIndex');
      const storedTime = localStorage.getItem('vedaCardLastChange');
      
      if (stored !== null) {
        const index = parseInt(stored, 10);
        const lastChange = storedTime ? parseInt(storedTime, 10) : Date.now();
        const timeSinceLastChange = Date.now() - lastChange;
        
        // If more than 15 minutes passed, advance to next set
        if (timeSinceLastChange >= 900000) { // 15 minutes
          const nextIndex = (index + 1) % 5; // Cycle through 0-4
          localStorage.setItem('vedaCardSetIndex', nextIndex.toString());
          localStorage.setItem('vedaCardLastChange', Date.now().toString());
          return nextIndex;
        }
        return index;
      }
      
      // First time: start at 0
      localStorage.setItem('vedaCardSetIndex', '0');
      localStorage.setItem('vedaCardLastChange', Date.now().toString());
      return 0;
    } catch (error) {
      console.error('Error accessing localStorage:', error);
      return 0;
    }
  });
  
  const [isFlipping, setIsFlipping] = useState(false);

  // Handle page refresh - advance to next set
  useEffect(() => {
    const handleBeforeUnload = () => {
      try {
        const currentIndex = parseInt(localStorage.getItem('vedaCardSetIndex') || '0', 10);
        const nextIndex = (currentIndex + 1) % 5; // Move to next set on refresh
        localStorage.setItem('vedaCardSetIndex', nextIndex.toString());
        localStorage.setItem('vedaCardLastChange', Date.now().toString());
      } catch (error) {
        console.error('Error updating localStorage on refresh:', error);
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, []);

  // Calculate which 4 cards to show
  const startIndex = currentSetIndex * 4;
  const currentPrompts = allPrompts.slice(startIndex, startIndex + 4);

  useEffect(() => {
    // Rotate cards every 15 minutes (900000 ms)
    const rotationInterval = setInterval(() => {
      setIsFlipping(true);
      
      // After flip animation starts, change the cards
      setTimeout(() => {
        setCurrentSetIndex((prevIndex) => {
          const nextIndex = (prevIndex + 1) % 5; // Cycle through 0-4, no repeats
          
          // Persist to localStorage
          try {
            localStorage.setItem('vedaCardSetIndex', nextIndex.toString());
            localStorage.setItem('vedaCardLastChange', Date.now().toString());
          } catch (error) {
            console.error('Error saving to localStorage:', error);
          }
          
          return nextIndex;
        });
        
        // End flip animation
        setTimeout(() => {
          setIsFlipping(false);
        }, 300);
      }, 300);
    }, 900000); // 15 minutes

    return () => clearInterval(rotationInterval);
  }, []);

  return (
    <div className="flex flex-col items-center justify-center px-6 pt-7 min-h-full">
      {/* Welcome Section */}
      <div className="text-center mb-10">
        <h1 
          className="text-5xl font-bold -ml-9"
          style={{ 
            color: 'var(--text-primary)',
            letterSpacing: '-0.02em',
            fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
          }}
        ><span className="text-6xl mb-6 animate-float">✨ </span>
          Hello, {username || 'there'}
        </h1>
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
          Let’s  take  a  step  toward's  Your  better  Health!
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {currentPrompts.map((item, index) => (
            <button
              key={`${currentSetIndex}-${index}`}
              onClick={() => onPromptClick?.(item.prompt)}
              className={`prompt-card group ${isFlipping ? 'flip-out' : 'flip-in'}`}
              style={{
                padding: '20px',
                borderRadius: '12px',
                border: '1px solid var(--composer-border)',
                background: 'var(--composer-bg)',
                backdropFilter: 'blur(10px)',
                WebkitBackdropFilter: 'blur(10px)',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                textAlign: 'left',
                animation: isFlipping 
                  ? 'flipOut 0.6s ease-in-out' 
                  : 'flipIn 0.6s ease-in-out'
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
    </div>
  );
}
