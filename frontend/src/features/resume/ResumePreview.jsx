export default function ResumePreview({ resume }) {
  return (
    <div className="resume-preview">
      <div className="resume-preview__header">
        <h1>{resume.full_name || 'Your Name'}</h1>
        <p className="resume-preview__contact">
          {[resume.email, resume.phone, resume.location, resume.linkedin_url]
            .filter(Boolean)
            .join(' · ')}
        </p>
      </div>

      {resume.summary && (
        <section>
          <h2>Summary</h2>
          <p>{resume.summary}</p>
        </section>
      )}

      {resume.skills?.length > 0 && (
        <section>
          <h2>Skills</h2>
          <p>{resume.skills.join(' · ')}</p>
        </section>
      )}

      {resume.experiences?.length > 0 && (
        <section>
          <h2>Experience</h2>
          {resume.experiences.map((exp, i) => (
            <div key={exp.id ?? i} className="resume-preview__entry">
              <div className="resume-preview__entry-header">
                <strong>{exp.title || 'Title'}</strong>
                <span>{exp.start_date} – {exp.end_date || 'Present'}</span>
              </div>
              <p className="resume-preview__entry-subtitle">{exp.company}</p>
              <ul>
                {exp.bullets?.map((b, bi) => <li key={b.id ?? bi}>{b.text}</li>)}
              </ul>
            </div>
          ))}
        </section>
      )}

      {resume.projects?.length > 0 && (
        <section>
          <h2>Projects</h2>
          {resume.projects.map((proj, i) => (
            <div key={proj.id ?? i} className="resume-preview__entry">
              <strong>{proj.name || 'Project name'}</strong>
              <ul>
                {proj.bullets?.map((b, bi) => <li key={b.id ?? bi}>{b.text}</li>)}
              </ul>
            </div>
          ))}
        </section>
      )}

      {resume.education?.length > 0 && (
        <section>
          <h2>Education</h2>
          {resume.education.map((edu, i) => (
            <p key={i}>{edu.degree} — {edu.school}</p>
          ))}
        </section>
      )}
    </div>
  );
}