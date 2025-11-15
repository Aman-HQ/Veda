export default function HealthcareDisclaimer() {
  return (
    <div 
      className="mt-4 pt-4 border-t transition-colors duration-300"
      style={{ 
        borderColor: 'var(--composer-border)',
        fontSize: '13px',
        lineHeight: '1.6'
      }}
    >
      <div className="flex gap-2">
        <span className="flex-shrink-0 text-amber-600 dark:text-amber-500">⚕️</span>
        <p 
          className="transition-colors duration-300"
          style={{ 
            color: 'var(--text-secondary)',
            margin: 0
          }}
        >
          <strong style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Healthcare Information Notice:</strong> This information is for educational purposes only and should not replace professional medical advice. Always consult with a qualified healthcare provider for medical concerns.
        </p>
      </div>
    </div>
  );
}


