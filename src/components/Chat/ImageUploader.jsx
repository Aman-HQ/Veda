export default function ImageUploader({ onSelect }) {
  const onChange = (e) => {
    const file = e.target.files?.[0];
    if (file) onSelect?.(file);
  };

  return (
    <label className="inline-flex items-center justify-center h-8 w-8 rounded-md text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer outline-none focus-within:ring-2 focus-within:ring-indigo-500 focus-within:ring-offset-2 dark:focus-within:ring-offset-slate-900"
      aria-label="Attach image"
    >
      <input type="file" accept="image/*" className="hidden" onChange={onChange} />
      <span aria-hidden>📎</span>
      <span className="sr-only">Attach image</span>
    </label>
  );
}

