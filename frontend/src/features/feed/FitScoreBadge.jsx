function getBand(score) {
  if (score >= 80) return { label: 'high', bg: 'var(--color-success-bg)', fg: 'var(--color-success)' };
  if (score >= 50) return { label: 'medium', bg: 'var(--color-warning-bg)', fg: 'var(--color-warning)' };
  return { label: 'low', bg: 'var(--color-danger-bg)', fg: 'var(--color-danger)' };
}

export default function FitScoreBadge({ score }) {
  if (score == null) return null;
  const band = getBand(score);
  return (
    <div
      role="img"
      aria-label={`Fit score ${score} out of 100, ${band.label} match`}
      style={{
        background: band.bg,
        color: band.fg,
        borderRadius: '50%',
        width: 48,
        height: 48,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        fontWeight: 600,
        fontSize: 'var(--text-base)',
        lineHeight: 1,
        flexShrink: 0,
      }}
    >
      {score}
      <span style={{ fontSize: 9, fontWeight: 500 }}>FIT</span>
    </div>
  );
}