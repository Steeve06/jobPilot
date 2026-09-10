export const COLUMNS = [
  { id: 'discovered', label: 'Discovered', statuses: ['discovered'] },
  { id: 'tailoring', label: 'Tailoring', statuses: ['tailoring'] },
  { id: 'ready', label: 'Ready', statuses: ['ready'] },
  { id: 'applied', label: 'Applied', statuses: ['applied', 'ghosted'] },
  { id: 'interview', label: 'Interview', statuses: ['oa_interview'] },
  { id: 'offer_rejected', label: 'Offer / Rejected', statuses: ['offer', 'rejected'] },
];

// The status a drag-drop into this column actually sets.
// Ghosted/rejected/offer distinctions are set manually via the drawer, not by dragging.
export const COLUMN_DEFAULT_STATUS = {
  discovered: 'discovered',
  tailoring: 'tailoring',
  ready: 'ready',
  applied: 'applied',
  interview: 'oa_interview',
};

export function columnForStatus(status) {
  return COLUMNS.find((col) => col.statuses.includes(status))?.id ?? 'discovered';
}