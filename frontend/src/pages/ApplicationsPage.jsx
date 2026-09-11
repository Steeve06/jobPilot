import { useState } from 'react';
import { DndContext, PointerSensor, useSensor, useSensors } from '@dnd-kit/core';
import KanbanColumn from '../features/applications/KanbanColumn';
import ApplicationDrawer from '../features/applications/ApplicationDrawer';
import { COLUMNS, COLUMN_DEFAULT_STATUS, columnForStatus } from '../features/applications/statusMapping';
import { useApplications, useUpdateApplication } from '../features/applications/useApplications';
import './ApplicationsPage.css';

export default function ApplicationsPage() {
  const { data: applications, isLoading } = useApplications();
  const updateApplication = useUpdateApplication();
  const [openApp, setOpenApp] = useState(null);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } }),
  );

  function handleDragEnd(event) {
    const { active, over } = event;
    if (!over) return;
    const application = applications.find((a) => a.id === active.id);
    const targetColumnId = over.id;
    if (columnForStatus(application.status) === targetColumnId) return;

    if (targetColumnId === 'offer_rejected') {
      const outcome = window.confirm(
        'Click OK for Offer, or Cancel for Rejected.',
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

  const isEmpty = applications.length === 0;

  return (
    <>
      {isEmpty ? (
        <div className="feed-page__state">
          <p>No applications yet.</p>
          <p className="drawer__muted">
            Applications appear here once you choose to pursue a posting from the Feed.
          </p>
        </div>
      ) : (
        <DndContext sensors={sensors} onDragEnd={handleDragEnd}>
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
      )}

      {openApp && (
        <ApplicationDrawer
          application={applications.find((a) => a.id === openApp.id) ?? openApp}
          onClose={() => setOpenApp(null)}
        />
      )}
    </>
  );
}