import { useState } from 'react';
import Accordion from '../components/Accordion';
import SkillsInput from '../features/resume/SkillsInput';
import ExperienceEditor from '../features/resume/ExperienceEditor';
import ProjectEditor from '../features/resume/ProjectEditor';
import ResumePreview from '../features/resume/ResumePreview';
import { useResume, useSaveResume, importResume } from '../features/resume/useResume';
import '../features/resume/ResumePreview.css';
import './ResumePage.css';

export default function ResumePage() {
  const { data: savedResume, isLoading } = useResume();
  const saveResume = useSaveResume();

  const [formData, setFormData] = useState(null);
  const [initializedFromId, setInitializedFromId] = useState(null);
  const [importError, setImportError] = useState('');
  const [importing, setImporting] = useState(false);

  // Seed local editable state from the query result once per distinct
  // resume id — done here in the render body (a React-supported pattern
  // for deriving state) rather than in a useEffect, so it doesn't trigger
  // an extra render/commit cycle. Guarding on `id` (not just "do we have
  // formData yet") also protects in-progress edits from being clobbered
  // if React Query silently refetches savedResume in the background later.
  if (savedResume && initializedFromId !== savedResume.id) {
    setFormData(savedResume);
    setInitializedFromId(savedResume.id);
  }

  function updateField(field, value) {
    setFormData((prev) => ({ ...prev, [field]: value }));
  }

  async function handleExport() {
    const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;
    const response = await fetch(`${API_BASE_URL}/api/resume/export/`, {
      credentials: 'include',
    });
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${formData.full_name || 'resume'}_resume.docx`;
    a.click();
    window.URL.revokeObjectURL(url);
  }

  async function handleImport(e) {
    const file = e.target.files[0];
    if (!file) return;
    setImportError('');
    setImporting(true);
    try {
      const draft = await importResume(file);
      // Merge into current formData, preserving any existing ids the
      // draft doesn't know about — an import always replaces content
      // wholesale, per ADR-007 this is still just a draft until Save.
      setFormData((prev) => ({ ...prev, ...draft }));
    } catch (err) {
      setImportError(err.message);
    } finally {
      setImporting(false);
      e.target.value = ''; // allow re-selecting the same file if retrying
    }
  }

  function handleSave() {
    saveResume.mutate(formData);
  }

  if (isLoading || !formData) return <p className="feed-page__state">Loading resume…</p>;

  return (
    <div className="resume-page">
      <div className="resume-page__editor">
        <div className="resume-page__toolbar">
          <label className="import-button">
            {importing ? 'Importing…' : 'Import Resume'}
            <input type="file" accept=".docx,.pdf" onChange={handleImport} disabled={importing} hidden />
          </label>
          <button onClick={handleSave} disabled={saveResume.isPending} className="save-button">
            {saveResume.isPending ? 'Saving…' : 'Save'}
          </button>
          <button onClick={handleExport} className="export-button">
            Export
          </button>
        </div>
        {importError && <p className="resume-page__error">{importError}</p>}
        {saveResume.isSuccess && <p className="resume-page__success">Saved.</p>}

        <Accordion title="Contact Info" defaultOpen>
          <input placeholder="Full name" value={formData.full_name}
            onChange={(e) => updateField('full_name', e.target.value)} />
          <input placeholder="Email" value={formData.email}
            onChange={(e) => updateField('email', e.target.value)} />
          <input placeholder="Phone" value={formData.phone}
            onChange={(e) => updateField('phone', e.target.value)} />
          <input placeholder="Location" value={formData.location}
            onChange={(e) => updateField('location', e.target.value)} />
          <input placeholder="LinkedIn URL" value={formData.linkedin_url}
            onChange={(e) => updateField('linkedin_url', e.target.value)} />
          <input placeholder="GitHub URL" value={formData.github_url}
            onChange={(e) => updateField('github_url', e.target.value)} />
        </Accordion>

        <Accordion title="Summary">
          <textarea rows={4} value={formData.summary}
            onChange={(e) => updateField('summary', e.target.value)} />
        </Accordion>

        <Accordion title="Skills">
          <SkillsInput skills={formData.skills} onChange={(skills) => updateField('skills', skills)} />
        </Accordion>

        <Accordion title="Experience">
          <ExperienceEditor
            experiences={formData.experiences}
            onChange={(experiences) => updateField('experiences', experiences)}
          />
        </Accordion>

        <Accordion title="Projects">
          <ProjectEditor
            projects={formData.projects}
            onChange={(projects) => updateField('projects', projects)}
          />
        </Accordion>
      </div>

      <div className="resume-page__preview">
        <ResumePreview resume={formData} />
      </div>
    </div>
  );
}