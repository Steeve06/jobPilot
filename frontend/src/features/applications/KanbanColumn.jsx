import { useDroppable } from '@dnd-kit/core';
import ApplicationCard from './ApplicationCard';

export default function KanbanColumn({ column, applications, onOpenCard }) {
  const { setNodeRef, isOver } = useDroppable({ id: column.id });

  return (
    <div
      ref={setNodeRef}
      className={`kanban-column${isOver ? ' kanban-column--over' : ''}`}
    >
      <div className="kanban-column__header">
        <span>{column.label}</span>
        <span className="kanban-column__count">{applications.length}</span>
      </div>
      <div className="kanban-column__cards">
        {applications.map((app) => (
          <ApplicationCard key={app.id} application={app} onOpen={onOpenCard} />
        ))}
      </div>
    </div>
  );
}