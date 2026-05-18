import { useEffect, useMemo, useState } from "react";

import { ApiError } from "../lib/api";
import { formatDateTimeLabel } from "../lib/datetime";
import {
  createPlanningTask,
  deletePlanningTask,
  listPlanningTasks,
  updatePlanningTask,
} from "../services/planningService";
import type { Task, TaskPayload } from "../types/task";
import { TaskForm } from "./TaskForm";

function getTaskErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Something went wrong while updating tasks.";
}

function sortTasks(tasks: Task[]): Task[] {
  return [...tasks].sort((leftTask, rightTask) => {
    const leftReference =
      leftTask.planned_start_at ||
      leftTask.deadline_at ||
      leftTask.created_at;
    const rightReference =
      rightTask.planned_start_at ||
      rightTask.deadline_at ||
      rightTask.created_at;

    return new Date(leftReference).getTime() - new Date(rightReference).getTime();
  });
}

type TaskSummaryRowProps = {
  task: Task;
  isDeleting: boolean;
  onEdit: (task: Task) => void;
  onDelete: (taskId: number) => Promise<void>;
};

function TaskSummaryRow({
  task,
  isDeleting,
  onEdit,
  onDelete,
}: TaskSummaryRowProps) {
  return (
    <article className="task-card">
      <div className="task-card-top">
        <div>
          <h3>{task.title}</h3>
          <p className="muted">
            {task.priority} priority · {task.status.replace("_", " ")} ·{" "}
            {task.estimated_minutes} min
          </p>
        </div>

        <div className="task-card-actions">
          <button className="secondary-button" onClick={() => onEdit(task)} type="button">
            Edit
          </button>
          <button
            className="secondary-button destructive-button"
            disabled={isDeleting}
            onClick={() => void onDelete(task.id)}
            type="button"
          >
            {isDeleting ? "Deleting..." : "Delete"}
          </button>
        </div>
      </div>

      <div className="task-meta-grid">
        <div>
          <span>Deadline</span>
          <strong>{formatDateTimeLabel(task.deadline_at)}</strong>
        </div>
        <div>
          <span>Planned start</span>
          <strong>{formatDateTimeLabel(task.planned_start_at)}</strong>
        </div>
        <div>
          <span>Planned end</span>
          <strong>{formatDateTimeLabel(task.planned_end_at)}</strong>
        </div>
      </div>

      {task.description ? <p className="task-description">{task.description}</p> : null}
    </article>
  );
}

export function PersonalTimetablePanel() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [deletingTaskId, setDeletingTaskId] = useState<number | null>(null);

  useEffect(() => {
    void loadTasks();
  }, []);

  const sortedTasks = useMemo(() => sortTasks(tasks), [tasks]);

  async function loadTasks(): Promise<void> {
    setLoadError(null);

    try {
      const loadedTasks = await listPlanningTasks();
      setTasks(loadedTasks);
    } catch (error) {
      setLoadError(getTaskErrorMessage(error));
    } finally {
      setIsLoading(false);
    }
  }

  async function handleSubmit(payload: TaskPayload): Promise<void> {
    setSubmitError(null);
    setDeleteError(null);
    setIsSubmitting(true);

    try {
      if (editingTask) {
        const updatedTask = await updatePlanningTask(editingTask.id, payload);
        setTasks((currentTasks) =>
          currentTasks.map((task) =>
            task.id === updatedTask.id ? updatedTask : task,
          ),
        );
        setEditingTask(null);
      } else {
        const createdTask = await createPlanningTask(payload);
        setTasks((currentTasks) => [createdTask, ...currentTasks]);
      }
    } catch (error) {
      setSubmitError(getTaskErrorMessage(error));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleDelete(taskId: number): Promise<void> {
    setDeleteError(null);
    setDeletingTaskId(taskId);

    try {
      await deletePlanningTask(taskId);
      setTasks((currentTasks) =>
        currentTasks.filter((task) => task.id !== taskId),
      );

      if (editingTask?.id === taskId) {
        setEditingTask(null);
      }
    } catch (error) {
      setDeleteError(getTaskErrorMessage(error));
    } finally {
      setDeletingTaskId(null);
    }
  }

  return (
    <section className="personal-timetable-grid">
      <article className="panel personal-form-panel">
        <TaskForm
          initialTask={editingTask}
          isSubmitting={isSubmitting}
          submitError={submitError}
          onSubmit={handleSubmit}
          onCancelEdit={() => {
            setEditingTask(null);
            setSubmitError(null);
          }}
        />
      </article>

      <article className="panel personal-list-panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Current Tasks</p>
            <h2>Your timetable</h2>
          </div>
          <p className="muted">{sortedTasks.length} task(s)</p>
        </div>

        {loadError ? <p className="form-error">{loadError}</p> : null}
        {deleteError ? <p className="form-error">{deleteError}</p> : null}

        {isLoading ? (
          <div className="empty-state">
            <h3>Loading tasks</h3>
            <p className="muted">
              We are fetching your current timetable from the backend.
            </p>
          </div>
        ) : null}

        {!isLoading && !sortedTasks.length ? (
          <div className="empty-state">
            <h3>No tasks yet</h3>
            <p className="muted">
              Add your first task to start shaping your timetable.
            </p>
          </div>
        ) : null}

        {!isLoading && sortedTasks.length ? (
          <div className="task-list">
            {sortedTasks.map((task) => (
              <TaskSummaryRow
                key={task.id}
                task={task}
                isDeleting={deletingTaskId === task.id}
                onEdit={setEditingTask}
                onDelete={handleDelete}
              />
            ))}
          </div>
        ) : null}
      </article>
    </section>
  );
}
