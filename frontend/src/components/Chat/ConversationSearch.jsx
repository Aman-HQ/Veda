import { useState } from 'react';

export default function ConversationSearch({ onSearch }) {
  const [searchQuery, setSearchQuery] = useState('');

  const handleChange = (e) => {
    const value = e.target.value;
    setSearchQuery(value);
    onSearch?.(value);
  };

  const handleClear = () => {
    setSearchQuery('');
    onSearch?.('');
  };

  return (
    <div 
      className="relative p-3 border-b transition-colors duration-300"
      style={{ borderColor: 'var(--sidebar-border)' }}
    >
      {/* Search Icon */}
      <div className="absolute left-6 top-1/2 transform -translate-y-1/2 pointer-events-none">
        <svg 
          xmlns="http://www.w3.org/2000/svg" 
          width="16" 
          height="16" 
          viewBox="0 0 24 24" 
          fill="none" 
          stroke="currentColor" 
          strokeWidth="2" 
          strokeLinecap="round" 
          strokeLinejoin="round"
          style={{ color: 'var(--sidebar-text-secondary)' }}
        >
          <circle cx="11" cy="11" r="8"></circle>
          <path d="m21 21-4.35-4.35"></path>
        </svg>
      </div>

      {/* Search Input */}
      <input
        type="text"
        placeholder="Search conversations..."
        value={searchQuery}
        onChange={handleChange}
        className="w-full pl-9 pr-9 py-2 rounded-lg text-sm outline-none focus-visible:ring-2 focus-visible:ring-blue-500 transition-all"
        style={{
          backgroundColor: 'rgba(255, 255, 255, 0.1)',
          border: '1px solid var(--sidebar-border)',
          color: 'var(--sidebar-text)',
          fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
        }}
        onFocus={(e) => {
          e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.15)';
          e.currentTarget.style.borderColor = 'var(--accent-primary)';
        }}
        onBlur={(e) => {
          e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
          e.currentTarget.style.borderColor = 'var(--sidebar-border)';
        }}
      />

      {/* Clear Button */}
      {searchQuery && (
        <button
          onClick={handleClear}
          className="absolute right-6 top-1/2 transform -translate-y-1/2 inline-flex items-center justify-center h-6 w-6 rounded-full outline-none focus-visible:ring-2 focus-visible:ring-blue-500 transition-all"
          style={{ color: 'var(--sidebar-text-secondary)' }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = 'var(--sidebar-hover)';
            e.currentTarget.style.color = 'var(--sidebar-text)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = 'transparent';
            e.currentTarget.style.color = 'var(--sidebar-text-secondary)';
          }}
          aria-label="Clear search"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      )}
    </div>
  );
}
