import BulletList from './BulletList';

export default function ExperienceEditor({ experiences, onChange }) {
  function updateExperience(index, patch) {
    const next = [...experiences];
    next[index] = { ...next[index], ...patch };
    onChange(next);
  }
  function removeExperience(index) {
    onChange(experiences.filter((_, i) => i !== index));
  }
  function addExperience() {
    onChange([...experiences, {
      company: '', title: '', start_date: '', end_date: null, bullets: [],
    }]);
  }

  return (
    <div>
      {experiences.map((exp, i) => (
        <div key={exp.id ?? `new-${i}`} className="repeater-entry">
          <div className="repeater-entry__row">
            <input placeholder="Company" value={exp.company}
              onChange={(e) => updateExperience(i, { company: e.target.value })} />
            <input placeholder="Title" value={exp.title}
              onChange={(e) => updateExperience(i, { title: e.target.value })} />
          </div>
          <div className="repeater-entry__row">
            <input type="date" value={exp.start_date ?? ''}
              onChange={(e) => updateExperience(i, { start_date: e.target.value })} />
            <input type="date" value={exp.end_date ?? ''} placeholder="Present"
              onChange={(e) => updateExperience(i, { end_date: e.target.value || null })} />
          </div>
          <BulletList
            bullets={exp.bullets}
            onChange={(bullets) => updateExperience(i, { bullets })}
          />
          <button type="button" onClick={() => removeExperience(i)} className="remove-button">
            Remove experience
          </button>
        </div>
      ))}
      <button type="button" onClick={addExperience} className="add-button">+ Add experience</button>
    </div>
  );
}