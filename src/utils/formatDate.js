export function formatDate(ts) {
  const d = ts instanceof Date ? ts : new Date(ts);
  if (Number.isNaN(d.getTime())) return '';

  const now = new Date();
  const isSameDay = d.toDateString() === now.toDateString();
  const yesterday = new Date(now);
  yesterday.setDate(now.getDate() - 1);
  const isYesterday = d.toDateString() === yesterday.toDateString();

  const time = d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  if (isSameDay) return `Today ${time}`;
  if (isYesterday) return 'Yesterday';

  const month = d.toLocaleString([], { month: 'short' });
  const day = d.getDate();
  return `${month} ${day}`;
}

export default formatDate;


