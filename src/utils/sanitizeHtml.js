// Basic sanitizer: strips <script> tags and on* attributes
// NOTE: We currently render plain text in MessageBubble.
// This utility is prepared for future rich text rendering.
export function sanitizeHtml(input) {
  if (!input || typeof input !== 'string') return '';
  // Remove script tags entirely
  let out = input.replace(/<script[\s\S]*?>[\s\S]*?<\/script>/gi, '');
  // Remove on* attributes like onclick=, onload=, etc.
  out = out.replace(/\son[a-z]+\s*=\s*(["']).*?\1/gi, '');
  return out;
}

export default sanitizeHtml;


