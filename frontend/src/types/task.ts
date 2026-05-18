export type TaskPriority = "low" | "medium" | "high";
export type TaskStatus = "pending" | "in_progress" | "completed";

export type Task = {
  id: number;
  user_id: number;
  title: string;
  description: string | null;
  priority: TaskPriority;
  status: TaskStatus;
  estimated_minutes: number;
  deadline_at: string | null;
  planned_start_at: string | null;
  planned_end_at: string | null;
  skill_id: number | null;
  created_at: string;
  updated_at: string;
};

export type TaskPayload = {
  title: string;
  description: string | null;
  priority: TaskPriority;
  status: TaskStatus;
  estimated_minutes: number;
  deadline_at: string | null;
  planned_start_at: string | null;
  planned_end_at: string | null;
  skill_id: number | null;
};

export type TaskFormValues = {
  title: string;
  description: string;
  priority: TaskPriority;
  status: TaskStatus;
  estimated_minutes: number | "";
  deadline_at: string;
  planned_start_at: string;
  planned_end_at: string;
};
