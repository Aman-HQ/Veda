import { useState, useEffect } from 'react';

export default function SettingsPanel({ isOpen, onClose }) {
  const [theme, setTheme] = useState('system');
  const [notifications, setNotifications] = useState(true);
  const [soundEnabled, setSoundEnabled] = useState(true);

  useEffect(() => {
    // Load settings from localStorage
    const savedTheme = localStorage.getItem('theme') || 'system';
    const savedNotifications = localStorage.getItem('notifications') !== 'false';
    const savedSound = localStorage.getItem('soundEnabled') !== 'false';
    
    setTheme(savedTheme);
    setNotifications(savedNotifications);
    setSoundEnabled(savedSound);
  }, [isOpen]);

  const handleThemeChange = (newTheme) => {
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
    // TODO: Implement actual theme switching logic
  };

  const handleNotificationsToggle = () => {
    const newValue = !notifications;
    setNotifications(newValue);
    localStorage.setItem('notifications', newValue.toString());
  };

  const handleSoundToggle = () => {
    const newValue = !soundEnabled;
    setSoundEnabled(newValue);
    localStorage.setItem('soundEnabled', newValue.toString());
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/50 z-50 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Panel */}
      <div 
        className="fixed inset-y-0 right-0 w-full sm:w-96 z-50 flex flex-col shadow-2xl"
        style={{
          backgroundColor: 'var(--sidebar-bg)',
          borderLeft: '1px solid var(--sidebar-border)'
        }}
      >
        {/* Header */}
        <div 
          className="flex items-center justify-between p-4 border-b"
          style={{ borderColor: 'var(--sidebar-border)' }}
        >
          <h2 
            className="text-lg font-semibold"
            style={{ 
              color: 'var(--sidebar-text)',
              fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
            }}
          >
            Settings
          </h2>
          <button
            onClick={onClose}
            className="inline-flex items-center justify-center h-8 w-8 rounded-md outline-none focus-visible:ring-2 focus-visible:ring-blue-500 transition-all"
            style={{ color: 'var(--sidebar-text)' }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = 'var(--sidebar-hover)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'transparent';
            }}
            aria-label="Close settings"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          {/* Theme Section */}
          <div>
            <h3 
              className="text-sm font-semibold mb-3"
              style={{ 
                color: 'var(--sidebar-text)',
                fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
              }}
            >
              Appearance
            </h3>
            <div className="space-y-2">
              {['light', 'dark', 'system'].map((themeOption) => (
                <button
                  key={themeOption}
                  onClick={() => handleThemeChange(themeOption)}
                  className={`w-full text-left px-3 py-2 rounded-lg text-sm outline-none focus-visible:ring-2 focus-visible:ring-blue-500 transition-all ${
                    theme === themeOption ? 'ring-2 ring-blue-500' : ''
                  }`}
                  style={{
                    backgroundColor: theme === themeOption ? 'var(--sidebar-hover)' : 'rgba(255, 255, 255, 0.05)',
                    color: 'var(--sidebar-text)'
                  }}
                  onMouseEnter={(e) => {
                    if (theme !== themeOption) {
                      e.currentTarget.style.backgroundColor = 'var(--sidebar-hover)';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (theme !== themeOption) {
                      e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.05)';
                    }
                  }}
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${
                      theme === themeOption ? 'border-blue-500' : 'border-gray-400'
                    }`}>
                      {theme === themeOption && (
                        <div className="w-2 h-2 rounded-full bg-blue-500" />
                      )}
                    </div>
                    <span className="capitalize">{themeOption}</span>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Notifications Section */}
          <div>
            <h3 
              className="text-sm font-semibold mb-3"
              style={{ 
                color: 'var(--sidebar-text)',
                fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
              }}
            >
              Notifications
            </h3>
            <div className="space-y-3">
              {/* Notifications Toggle */}
              <div 
                className="flex items-center justify-between p-3 rounded-lg"
                style={{ backgroundColor: 'rgba(255, 255, 255, 0.05)' }}
              >
                <span 
                  className="text-sm"
                  style={{ color: 'var(--sidebar-text)' }}
                >
                  Enable notifications
                </span>
                <button
                  onClick={handleNotificationsToggle}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    notifications ? 'bg-blue-500' : 'bg-gray-400'
                  }`}
                  aria-label="Toggle notifications"
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      notifications ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>

              {/* Sound Toggle */}
              <div 
                className="flex items-center justify-between p-3 rounded-lg"
                style={{ backgroundColor: 'rgba(255, 255, 255, 0.05)' }}
              >
                <span 
                  className="text-sm"
                  style={{ color: 'var(--sidebar-text)' }}
                >
                  Sound effects
                </span>
                <button
                  onClick={handleSoundToggle}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    soundEnabled ? 'bg-blue-500' : 'bg-gray-400'
                  }`}
                  aria-label="Toggle sound"
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      soundEnabled ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>
            </div>
          </div>

          {/* About Section */}
          <div>
            <h3 
              className="text-sm font-semibold mb-3"
              style={{ 
                color: 'var(--sidebar-text)',
                fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
              }}
            >
              About
            </h3>
            <div 
              className="p-3 rounded-lg space-y-2"
              style={{ backgroundColor: 'rgba(255, 255, 255, 0.05)' }}
            >
              <div className="flex justify-between text-sm">
                <span style={{ color: 'var(--sidebar-text-secondary)' }}>Version</span>
                <span style={{ color: 'var(--sidebar-text)' }}>1.0.0</span>
              </div>
              <div className="flex justify-between text-sm">
                <span style={{ color: 'var(--sidebar-text-secondary)' }}>App Name</span>
                <span style={{ color: 'var(--sidebar-text)' }}>Veda</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
