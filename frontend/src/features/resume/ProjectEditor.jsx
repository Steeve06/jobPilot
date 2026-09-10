import BulletList from './BulletList';

export default function ProjectEditor({ projects, onChange }) {
  function updateProject(index, patch) {
    const next = [...projects];
    next[index] = { ...next[index], ...patch };
    onChange(next);
  }
  function removeProject(index) {
    onChange(projects.filter((_, i) => i !== index));
  }
  function addProject() {
    onChange([...projects, { name: '', bullets: [] }]);
  }

  return (
    <div>
      {projects.map((proj, i) => (
        <div key={proj.id ?? `new-${i}`} className="repeater-entry">
          <input placeholder="Project name" value={proj.name}
            onChange={(e) => updateProject(i, { name: e.target.value })} />
          <BulletList
            bullets={proj.bullets}
            onChange={(bullets) => updateProject(i, { bullets })}
          />
          <button type="button" onClick={() => removeProject(i)} className="remove-button">
            Remove project
          </button>
        </div>
      ))}
      <button type="button" onClick={addProject} className="add-button">+ Add project</button>
    </div>
  );
}