import { useState } from 'react';

export default function Accordion({ title, defaultOpen = false, children }) {
  const [open, setOpen] = useState(defaultOpen);
  const contentId = `accordion-${title.replace(/\s+/g, '-').toLowerCase()}`;

  return (
    <div className="accordion-section">
      <button
        type="button"
        className="accordion-header"
        aria-expanded={open}
        aria-controls={contentId}
        onClick={() => setOpen((o) => !o)}
      >
        {title}
        <span aria-hidden="true">{open ? '−' : '+'}</span>
      </button>
      {open && <div id={contentId} className="accordion-content">{children}</div>}
    </div>
  );
}