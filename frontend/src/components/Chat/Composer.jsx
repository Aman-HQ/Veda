import { useCallback, useEffect, useRef, useState } from 'react';
import ImageUploader from './ImageUploader.jsx';
import VoiceInput from './VoiceInput.jsx';

export default function Composer({ onSend, onAttachImage, onStartVoice, onStopVoice, initialValue }) {
  const [value, setValue] = useState('');
  const [pastedImages, setPastedImages] = useState([]);
  const [previewImage, setPreviewImage] = useState(null);
  const textareaRef = useRef(null);

  // Update value when initialValue changes
  useEffect(() => {
    if (initialValue) {
      setValue(initialValue);
      textareaRef.current?.focus();
    }
  }, [initialValue]);

  // Auto-resize textarea based on content
  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    // Reset height to auto to get the correct scrollHeight
    textarea.style.height = 'auto';
    
    const lineHeight = 16 * 1.6; // 16px fontSize * 1.6 lineHeight = 25.6px per line
    const maxLines = 6;
    const maxHeight = lineHeight * maxLines + 24; // 20px for padding (8px top + 8px bottom + margin)
    const minHeight = 40; // minimum height for single line
    
    // Calculate new height based on content
    const newHeight = Math.min(textarea.scrollHeight, maxHeight);
    
    // Apply new height (use max to ensure minimum height)
    textarea.style.height = `${Math.max(newHeight, minHeight)}px`;
    
    // Enable/disable scrolling based on whether we've reached max height
    if (textarea.scrollHeight > maxHeight) {
      textarea.style.overflowY = 'auto';
      textarea.style.paddingBottom = '18px'; // More bottom padding when scrolling
      textarea.style.marginBottom = '8px'; // Add margin between textarea and buttons
    } else {
      textarea.style.overflowY = 'hidden';
      textarea.style.paddingBottom = '8px'; // Normal bottom padding
      textarea.style.marginBottom = '0px'; // No margin for single/few lines
    }
    // Expand container width on multiline
    // const container = textarea.closest('.max-w-3xl, [style*="maxWidth"]');
    // if (container && (value.includes('\n') || value.length > 80)) {
    //   container.style.maxWidth = '100%';
    // } else if (container) {
    //   container.style.maxWidth = '768px';
    // }
  }, [value]);

  const handleKeyDown = useCallback(
    (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        submit();
      }
    },
    [value]
  );

  const handlePaste = useCallback((e) => {
    const clipboardData = e.clipboardData || window.clipboardData;
    const items = clipboardData.items;
    
    for (let i = 0; i < items.length; i++) {
      const item = items[i];
      
      // Check if the item is an image
      if (item.type.indexOf('image') !== -1) {
        e.preventDefault(); // Prevent default paste behavior
        
        const file = item.getAsFile();
        if (file) {
          // Create a preview URL
          const imageUrl = URL.createObjectURL(file);
          const imageData = {
            id: Date.now(),
            file: file,
            url: imageUrl,
            name: file.name || 'Pasted Image'
          };
          
          setPastedImages(prev => [...prev, imageData]);
          
          // Also call the onAttachImage callback if provided
          if (onAttachImage) {
            onAttachImage(file);
          }
        }
        break;
      }
    }
  }, [onAttachImage]);

  const removeImage = useCallback((imageId) => {
    setPastedImages(prev => {
      const updated = prev.filter(img => img.id !== imageId);
      // Clean up object URLs to prevent memory leaks
      const removed = prev.find(img => img.id === imageId);
      if (removed) {
        URL.revokeObjectURL(removed.url);
      }
      return updated;
    });
  }, []);

  const showImagePreview = useCallback((image) => {
    setPreviewImage(image);
  }, []);

  const closeImagePreview = useCallback(() => {
    setPreviewImage(null);
  }, []);

  const submit = () => {
    const trimmed = value.trim();
    if (!trimmed && pastedImages.length === 0) return;
    onSend?.(trimmed);
    setValue('');
    // Clear pasted images after sending
    pastedImages.forEach(img => URL.revokeObjectURL(img.url));
    setPastedImages([]);
    // Reset height after sending
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
    textareaRef.current?.focus();
  };

  return (
    <div className="sticky bottom-0 inset-x-0 px-4 sm:px-6 py-3">
      <div className="max-w-3xl mx-auto w-full">
        <form
          className="relative rounded-3xl border backdrop-blur-xl shadow-lg transition-all duration-200"
          style={{
            background: 'linear-gradient(135deg, var(--composer-bg-start) 0%, var(--composer-bg-end) 100%)',
            backdropFilter: 'blur(20px)',
            WebkitBackdropFilter: 'blur(20px)',
            borderColor: 'var(--composer-border)',
            boxShadow: '0 4px 6px var(--glass-shadow), 0 0 0 1px rgba(255, 255, 255, 0.5) inset',
            padding: '8px 12px'
          }}
          onSubmit={(e) => {
            e.preventDefault();
            submit();
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.boxShadow = '0 8px 16px var(--glass-shadow), 0 0 0 1px rgba(255, 255, 255, 0.5) inset';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.boxShadow = '0 4px 6px var(--glass-shadow), 0 0 0 1px rgba(255, 255, 255, 0.5) inset';
          }}
          role="form"
          aria-label="Message composer"
        >
          {/* <div className="flex items-end gap-2"> */}
          <div className="flex flex-col gap-1">
            {/* Image previews */}
            {pastedImages.length > 0 && (
              <div className="flex flex-wrap gap-2 p-2">
                {pastedImages.map((image) => (
                  <div key={image.id} className="relative group">
                    <div 
                      className="relative w-15 h-15 rounded-xl overflow-hidden border border-gray-300 dark:border-gray-600 cursor-pointer hover:border-blue-400 dark:hover:border-blue-500 transition-colors"
                      onClick={() => showImagePreview(image)}
                      title="Click to preview image"
                    >
                      <img 
                        src={image.url} 
                        alt={image.name}
                        className="w-full h-full object-cover hover:scale-105 transition-transform duration-200"
                      />
                    </div>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        removeImage(image.id);
                      }}
                      className="absolute -top-2 -right-2 w-6 h-6 bg-white hover:bg-gray-100 text-gray-800 hover:text-black rounded-full flex items-center justify-center text-lg font-bold shadow-lg border border-gray-200 opacity-0 group-hover:opacity-100 transition-all duration-200 transform hover:scale-110"
                      title="Remove image"
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            )}
            
            {/* Textarea */}
              <textarea
                ref={textareaRef}
                value={value}
                onChange={(e) => setValue(e.target.value)}
                onKeyDown={handleKeyDown}
                onPaste={handlePaste}
                placeholder="How can I help you today?"
                rows={1}
                className="resize-none bg-transparent outline-none px-3 transition-all duration-150"
                style={{ 
                  minHeight: '40px', 
                  maxHeight: 'none',
                  height: '40px',
                  color: 'var(--text-primary)',
                  fontSize: '16px',
                  lineHeight: '1.6',
                  fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
                  overflowY: 'hidden',
                  paddingTop: '8px',
                  paddingBottom: '8px',
                  width: 'calc(100% - 5px)', // Account for scrollbar space
                  marginRight: '0.5px', // Space for scrollbar
                }}
              />

            {/* Buttons row - always at bottom */}
            <div className="flex items-center justify-between gap-2">
              {/* Action buttons on the left */}
              <div className="flex items-center gap-2">
                <ImageUploader onSelect={onAttachImage} />
                <VoiceInput onStart={onStartVoice} onStop={onStopVoice} />
                {/* Camera button */}
                <button
                  type="button"
                  aria-label="Camera"
                  className="inline-flex items-center justify-center h-9 w-9 rounded-full outline-none focus-visible:ring-2 focus-visible:ring-blue-500 transition-all"
                  style={{ color: 'var(--text-secondary)' }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = 'var(--user-msg-bg)';
                    e.currentTarget.style.color = 'var(--text-primary)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'transparent';
                    e.currentTarget.style.color = 'var(--text-secondary)';
                  }}
                  title="Camera"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path>
                    <circle cx="12" cy="13" r="4"></circle>
                  </svg>
                </button>
              </div>
              
              {/* Send button integrated on the right */}
              <button
                type="submit"
                disabled={!value.trim() && pastedImages.length === 0}
                className="flex-shrink-0 inline-flex items-center justify-center h-9 w-9 rounded-full text-white shadow-md outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 transition-all duration-200 mb-2 disabled:cursor-not-allowed"
                style={{
                  background: (value.trim() || pastedImages.length > 0)
                    ? 'linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-primary-hover) 100%)'
                    : 'linear-gradient(135deg, #cbd5e1 15%, #94a3b8 85%)',
                  boxShadow: (value.trim() || pastedImages.length > 0) ? '0 4px 12px rgba(59, 130, 246, 0.4)' : 'none',
                  transform: (value.trim() || pastedImages.length > 0) ? 'scale(1)' : 'scale(1)',
                  opacity: (value.trim() || pastedImages.length > 0) ? '1' : '0.8'
                }}
                onMouseEnter={(e) => {
                  if (value.trim() || pastedImages.length > 0) {
                    e.currentTarget.style.transform = 'scale(1.05)';
                    e.currentTarget.style.boxShadow = '0 6px 16px rgba(59, 130, 246, 0.5)';
                  }
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'scale(1)';
                  e.currentTarget.style.boxShadow = (value.trim() || pastedImages.length > 0) ? '0 4px 12px rgba(59, 130, 246, 0.4)' : 'none';
                }}
                aria-label="Send message"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={(value.trim() || pastedImages.length > 0) ? "currentColor" : "rgba(255,255,255,0.8)"} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="22" y1="2" x2="11" y2="13"></line>
                  <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                </svg>
              </button>
            </div>
          </div>
        </form>
          <p 
            className="text-center mt-3 transition-colors duration-300"
            style={{ 
              color: 'var(--text-secondary)',
              fontSize: '13px',
              lineHeight: '1.5'
            }}
          >
            Veda can make mistakes. Consider checking important information.
          </p>
        </div>
      

      {/* Image Preview Modal */}
      {previewImage && (
        <div 
          className="fixed inset-0 flex items-center justify-center z-50"
          style={{
            backgroundColor: 'rgba(1, 4, 13, 0.7)',
            backdropFilter: 'blur(50px)',
            WebkitBackdropFilter: 'blur(50px)'
          }}
          onClick={closeImagePreview}
        >
          <div className="relative max-w-5xl max-h-4xl p-4">
            <img 
              src={previewImage.url} 
              alt={previewImage.name}
              className="w-[75vw] h-[80vh] object-contain rounded-lg shadow-2xl"
              onClick={(e) => e.stopPropagation()}
            />
            <button
              onClick={closeImagePreview}
              className="absolute -top-4 -right-4 w-10 h-10 bg-white hover:bg-gray-100 text-gray-800 hover:text-black rounded-full flex items-center justify-center text-xl font-bold shadow-lg border border-gray-200 transition-all duration-200 transform hover:scale-110"
              title="Close preview"
            >
              ×
            </button>
            <div className="absolute bottom-2 left-2 right-2 bg-black bg-opacity-50 text-white p-2 rounded text-sm">
              {previewImage.name}
            </div>
          </div>  
        </div>
      )}
    </div>
  );
}