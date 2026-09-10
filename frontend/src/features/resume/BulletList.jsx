export default function BulletList({ bullets, onChange }) {
  function updateBullet(index, text) {
    const next = [...bullets];
    next[index] = { ...next[index], text };
    onChange(next);
  }
  function removeBullet(index) {
    onChange(bullets.filter((_, i) => i !== index));
  }
  function addBullet() {
    onChange([...bullets, { text: '', skill_tags: [] }]);
  }

  return (
    <div className="bullet-list">
      {bullets.map((bullet, i) => (
        <div key={bullet.id ?? `new-${i}`} className="bullet-row">
          <textarea
            value={bullet.text}
            onChange={(e) => updateBullet(i, e.target.value)}
            rows={2}
          />
          <button type="button" onClick={() => removeBullet(i)} aria-label="Remove bullet">×</button>
        </div>
      ))}
      <button type="button" onClick={addBullet} className="add-button">+ Add bullet</button>
    </div>
  );
}