export type ApiFieldErrors = Record<string, string[]>;

type UnknownRecord = Record<string, unknown>;

function isRecord(value: unknown): value is UnknownRecord {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function toMessages(value: unknown): string[] {
  if (typeof value === "string") return [value];
  if (Array.isArray(value)) {
    return value.flatMap((item) => toMessages(item));
  }
  if (isRecord(value)) {
    return Object.values(value).flatMap((item) => toMessages(item));
  }
  return [];
}

function getResponseData(error: unknown): UnknownRecord | null {
  if (!isRecord(error)) return null;
  const response = error.response;
  if (!isRecord(response)) return null;
  const data = response.data;
  return isRecord(data) ? data : null;
}

export function extractApiFieldErrors(error: unknown): ApiFieldErrors {
  const data = getResponseData(error);
  if (!data) return {};

  const fieldErrors: ApiFieldErrors = {};
  for (const [key, value] of Object.entries(data)) {
    if (["detail", "message", "error", "non_field_errors"].includes(key)) continue;
    const messages = toMessages(value);
    if (messages.length) {
      fieldErrors[key] = messages;
    }
  }
  return fieldErrors;
}

export function extractApiErrorMessage(error: unknown, fallback = "Unable to complete the request."): string {
  const data = getResponseData(error);
  if (!data) return fallback;

  const detail = data.detail ?? data.message ?? data.error;
  const detailMessages = toMessages(detail);
  if (detailMessages.length) {
    return detailMessages[0];
  }

  const nonFieldMessages = toMessages(data.non_field_errors);
  if (nonFieldMessages.length) {
    return nonFieldMessages[0];
  }

  const fieldErrors = extractApiFieldErrors(error);
  const firstFieldMessage = Object.values(fieldErrors).flat()[0];
  return firstFieldMessage || fallback;
}

export function firstFieldError(errorMessages?: string[] | null): string {
  return errorMessages?.[0] || "";
}
