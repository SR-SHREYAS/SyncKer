import { useEffect, useState, type FormEvent } from "react";

import { toDatetimeLocalValue, toIsoOrNull } from "../lib/datetime";
import type { Task, TaskFormValues, TaskPayload, TaskPriority, TaskStatus } from "../types/task";

type TaskFormProps = {
  initialTask?: Task | null;
  isSubmitting: boolean;
  submitError: string | null;
  onSubmit: (payload: TaskPayload) => Promise<void>;
  onCancelEdit?: () => void;
};

const defaultTaskFormValues: TaskFormValues = {
  title: "",
  description: "",
  priority: "medium",
  status: "pending",
  estimated_minutes: 60,
  deadline_at: "",
  planned_start_at: "",
  planned_end_at: "",
};

const priorityOptions: TaskPriority[] = ["low", "medium", "high"];
const statusOptions: TaskStatus[] = ["pending", "in_progress", "completed"];

function buildFormValues(task?: Task | null): TaskFormValues {
  if (!task) {
    return defaultTaskFormValues;
  }

  return {
    title: task.title,
    description: task.description ?? "",
    priority: task.priority,
    status: task.status,
    estimated_minutes: task.estimated_minutes,
    deadline_at: toDatetimeLocalValue(task.deadline_at),
    planned_start_at: toDatetimeLocalValue(task.planned_start_at),
    planned_end_at: toDatetimeLocalValue(task.planned_end_at),
  };
}

export function TaskForm({
  initialTask,
  isSubmitting,
  submitError,
  onSubmit,
  onCancelEdit,
}: TaskFormProps) {
  const [formValues, setFormValues] = useState<TaskFormValues>(
    buildFormValues(initialTask),
  );

  useEffect(() => {
    setFormValues(buildFormValues(initialTask));
  }, [initialTask]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    await onSubmit({
      title: formValues.title.trim(),
      description: formValues.description.trim() || null,
      priority: formValues.priority,
      status: formValues.status,
      estimated_minutes: Number(formValues.estimated_minutes),
      deadline_at: toIsoOrNull(formValues.deadline_at),
      planned_start_at: toIsoOrNull(formValues.planned_start_at),
      planned_end_at: toIsoOrNull(formValues.planned_end_at),
      skill_id: null,
    });

    if (!initialTask) {
      setFormValues(defaultTaskFormValues);
    }
  }

  return (
    <form className="stack-form" onSubmit={handleSubmit}>
      <div className="section-heading">
        <div>
          <p className="eyebrow">Personal Timetable</p>
          <h2>{initialTask ? "Edit task" : "Add task"}</h2>
        </div>
        {initialTask && onCancelEdit ? (
          <button
            className="secondary-button"
            disabled={isSubmitting}
            onClick={onCancelEdit}
            type="button"
          >
            Cancel
          </button>
        ) : null}
      </div>

      <label className="field">
        <span>Title</span>
        <input
          type="text"
          value={formValues.title}
          onChange={(event) =>
            setFormValues((currentValues) => ({
              ...currentValues,
              title: event.target.value,
            }))
          }
          disabled={isSubmitting}
          minLength={2}
          maxLength={160}
          placeholder="Deep work block, client review, study session..."
          required
        />
      </label>

      <label className="field">
        <span>Description</span>
        <textarea
          value={formValues.description}
          onChange={(event) =>
            setFormValues((currentValues) => ({
              ...currentValues,
              description: event.target.value,
            }))
          }
          disabled={isSubmitting}
          maxLength={2000}
          placeholder="Optional context for this task"
          rows={4}
        />
      </label>

      <div className="field-grid">
        <label className="field">
          <span>Priority</span>
          <select
            value={formValues.priority}
            onChange={(event) =>
              setFormValues((currentValues) => ({
                ...currentValues,
                priority: event.target.value as TaskPriority,
              }))
            }
            disabled={isSubmitting}
          >
            {priorityOptions.map((priorityOption) => (
              <option key={priorityOption} value={priorityOption}>
                {priorityOption}
              </option>
            ))}
          </select>
        </label>

        <label className="field">
          <span>Status</span>
          <select
            value={formValues.status}
            onChange={(event) =>
              setFormValues((currentValues) => ({
                ...currentValues,
                status: event.target.value as TaskStatus,
              }))
            }
            disabled={isSubmitting}
          >
            {statusOptions.map((statusOption) => (
              <option key={statusOption} value={statusOption}>
                {statusOption}
              </option>
            ))}
          </select>
        </label>
      </div>

      <label className="field">
        <span>Estimated minutes</span>
        <input
          type="number"
          value={formValues.estimated_minutes}
          onChange={(event) =>
            setFormValues((currentValues) => ({
              ...currentValues,
              estimated_minutes: Number(event.target.value),
            }))
          }
          disabled={isSubmitting}
          min={15}
          max={1440}
          step={15}
          required
        />
      </label>

      <div className="field-grid">
        <label className="field">
          <span>Deadline</span>
          <input
            type="datetime-local"
            value={formValues.deadline_at}
            onChange={(event) =>
              setFormValues((currentValues) => ({
                ...currentValues,
                deadline_at: event.target.value,
              }))
            }
            disabled={isSubmitting}
          />
        </label>

        <label className="field">
          <span>Planned start</span>
          <input
            type="datetime-local"
            value={formValues.planned_start_at}
            onChange={(event) =>
              setFormValues((currentValues) => ({
                ...currentValues,
                planned_start_at: event.target.value,
              }))
            }
            disabled={isSubmitting}
          />
        </label>
      </div>

      <label className="field">
        <span>Planned end</span>
        <input
          type="datetime-local"
          value={formValues.planned_end_at}
          onChange={(event) =>
            setFormValues((currentValues) => ({
              ...currentValues,
              planned_end_at: event.target.value,
            }))
          }
          disabled={isSubmitting}
        />
      </label>

      {submitError ? <p className="form-error">{submitError}</p> : null}

      <button className="primary-button wide-button" disabled={isSubmitting} type="submit">
        {isSubmitting
          ? initialTask
            ? "Saving task..."
            : "Creating task..."
          : initialTask
            ? "Save task"
            : "Create task"}
      </button>
    </form>
  );
}
