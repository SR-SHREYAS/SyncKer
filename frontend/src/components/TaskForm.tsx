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
  const [validationError, setValidationError] = useState<string | null>(null);

  useEffect(() => {
    setFormValues(buildFormValues(initialTask));
    setValidationError(null);
  }, [initialTask]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setValidationError(null);

    const trimmedTitle = formValues.title.trim();

    if (trimmedTitle.length < 2) {
      setValidationError("Title must be at least 2 characters.");
      return;
    }

    if (formValues.estimated_minutes === "") {
      setValidationError("Estimated minutes is required.");
      return;
    }

    if (!Number.isFinite(formValues.estimated_minutes)) {
      setValidationError("Estimated minutes must be a valid number.");
      return;
    }

    if (
      formValues.estimated_minutes < 15 ||
      formValues.estimated_minutes > 1440
    ) {
      setValidationError(
        "Estimated minutes must be between 15 and 1440.",
      );
      return;
    }

    const normalizedDeadlineAt = toIsoOrNull(formValues.deadline_at);
    const normalizedPlannedStartAt = toIsoOrNull(formValues.planned_start_at);
    const normalizedPlannedEndAt = toIsoOrNull(formValues.planned_end_at);

    if (formValues.deadline_at.trim() && normalizedDeadlineAt === null) {
      setValidationError("Deadline must be a valid date and time.");
      return;
    }

    if (formValues.planned_start_at.trim() && normalizedPlannedStartAt === null) {
      setValidationError("Planned start must be a valid date and time.");
      return;
    }

    if (formValues.planned_end_at.trim() && normalizedPlannedEndAt === null) {
      setValidationError("Planned end must be a valid date and time.");
      return;
    }

    if (normalizedPlannedStartAt && normalizedPlannedEndAt) {
      const plannedStartDate = new Date(normalizedPlannedStartAt);
      const plannedEndDate = new Date(normalizedPlannedEndAt);

      if (plannedEndDate.getTime() < plannedStartDate.getTime()) {
        setValidationError("Planned end must be after planned start.");
        return;
      }
    }

    await onSubmit({
      title: trimmedTitle,
      description: formValues.description.trim() || null,
      priority: formValues.priority,
      status: formValues.status,
      estimated_minutes: formValues.estimated_minutes,
      deadline_at: normalizedDeadlineAt,
      planned_start_at: normalizedPlannedStartAt,
      planned_end_at: normalizedPlannedEndAt,
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
              estimated_minutes:
                event.target.value === ""
                  ? ""
                  : Number(event.target.value),
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

      {validationError ? <p className="form-error">{validationError}</p> : null}
      {!validationError && submitError ? <p className="form-error">{submitError}</p> : null}

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
