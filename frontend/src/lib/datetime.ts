// Frontend convention:
// backend timestamps are treated as ISO datetime strings and rendered in the
// user's local timezone for both form editing and display labels.
function parseDateValue(value: string): Date | null {
  const parsedDate = new Date(value);

  if (Number.isNaN(parsedDate.getTime())) {
    return null;
  }

  return parsedDate;
}

export function toDatetimeLocalValue(value: string | null): string {
  if (!value) {
    return "";
  }

  const date = parseDateValue(value);

  if (!date) {
    return "";
  }

  const timezoneOffsetMinutes = date.getTimezoneOffset();
  const localDate = new Date(date.getTime() - timezoneOffsetMinutes * 60_000);
  return localDate.toISOString().slice(0, 16);
}

export function toIsoOrNull(value: string): string | null {
  if (!value.trim()) {
    return null;
  }

  return parseDateValue(value)?.toISOString() ?? null;
}

export function formatDateTimeLabel(value: string | null): string {
  if (!value) {
    return "Not set";
  }

  const date = parseDateValue(value);

  if (!date) {
    return "Invalid date";
  }

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}
