export default function ImageUploader({ onSelect }) {
  const onChange = (e) => {
    const file = e.target.files?.[0];
    if (file) onSelect?.(file);
  };

  return (
    <label 
      className="inline-flex items-center justify-center h-9 w-9 rounded-full cursor-pointer outline-none focus-within:ring-2 focus-within:ring-blue-500 transition-all"
      style={{ color: 'var(--text-secondary)' }}
      onMouseEnter={(e) => {
        e.currentTarget.style.backgroundColor = 'var(--user-msg-bg)';
        e.currentTarget.style.color = 'var(--text-primary)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.backgroundColor = 'transparent';
        e.currentTarget.style.color = 'var(--text-secondary)';
      }}
      aria-label="Attach file"
      title="Attach file"
    >
      <input type="file" accept="image/*" className="hidden" onChange={onChange} />
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"></path>
      </svg>
      <span className="sr-only">Attach file</span>
    </label>
  );
}

