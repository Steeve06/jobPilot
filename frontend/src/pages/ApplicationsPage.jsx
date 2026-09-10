import { useState } from 'react';
import { DndContext } from '@dnd-kit/core';
import KanbanColumn from '../features/applications/KanbanColumn';
import ApplicationDrawer from '../features/applications/ApplicationDrawer';
import { COLUMNS, COLUMN_DEFAULT_STATUS, columnForStatus } from '../features/applications/statusMapping';
import { useApplications, useUpdateApplication } from '../features/applications/useApplications';
import './ApplicationsPage.css';

export default function ApplicationsPage() {
  const { data: applications, isLoading } = useApplications();
  const updateApplication = useUpdateApplication();
  const [openApp, setOpenApp] = useState(null);

  function handleDragEnd(event) {
    const { active, over } = event;
    if (!over) return;
    const application = applications.find((a) => a.id === active.id);
    const targetColumnId = over.id;
    if (columnForStatus(application.status) === targetColumnId) return;

    if (targetColumnId === 'offer_rejected') {
      const outcome = window.confirm(
        'Click OK for Offer, or Rejected for Rejected.',
      ) ? 'offer' : 'rejected';
      updateApplication.mutate({ id: application.id, status: outcome });
      return;
    }

    updateApplication.mutate({
      id: application.id,
      status: COLUMN_DEFAULT_STATUS[targetColumnId],
    });
  }

  if (isLoading) return <p className="feed-page__state">Loading applications…</p>;

  return (
    <>
      <DndContext onDragEnd={handleDragEnd}>
        <div className="kanban-board">
          {COLUMNS.map((column) => (
            <KanbanColumn
              key={column.id}
              column={column}
              applications={applications.filter(
                (a) => columnForStatus(a.status) === column.id,
              )}
              onOpenCard={setOpenApp}
            />
          ))}
        </div>
      </DndContext>

      {openApp && (
        <ApplicationDrawer
          application={applications.find((a) => a.id === openApp.id) ?? openApp}
          onClose={() => setOpenApp(null)}
        />
      )}
    </>
  );
}