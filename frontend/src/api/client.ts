import type {
  CompatibilityResult, FieldDef, PreviewResult, Session, Topic,
} from "../types";

const BASE = "";

async function request<T>(path: string, session: Session | null,
                          init: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string> | undefined),
  };
  if (session) headers.Authorization = `Bearer ${session.token}`;
  const resp = await fetch(`${BASE}${path}`, { ...init, headers });
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({}));
    const detail = body.detail;
    const message =
      typeof detail === "string" ? detail
      : detail?.message ? `${detail.message}: ${(detail.breaking_changes ?? []).join("; ")}`
      : `request failed (${resp.status})`;
    throw new Error(message);
  }
  return resp.json();
}

export const api = {
  login: (username: string, password: string) =>
    request<{ access_token: string; role: Session["role"]; username: string }>(
      "/api/auth/login", null,
      { method: "POST", body: JSON.stringify({ username, password }) }),

  listTopics: (s: Session) => request<Topic[]>("/api/topics", s),

  getTopic: (s: Session, name: string) =>
    request<Topic>(`/api/topics/${encodeURIComponent(name)}`, s),

  registerTopic: (s: Session, payload: {
    name: string; description: string; owner_team: string;
    schema_definition: { fields: FieldDef[] };
  }) => request<Topic>("/api/topics", s,
    { method: "POST", body: JSON.stringify(payload) }),

  checkSchema: (s: Session, name: string, fields: FieldDef[]) =>
    request<CompatibilityResult>(
      `/api/topics/${encodeURIComponent(name)}/schema/check`, s,
      { method: "POST", body: JSON.stringify({ schema_definition: { fields } }) }),

  evolveSchema: (s: Session, name: string, fields: FieldDef[]) =>
    request<Topic>(`/api/topics/${encodeURIComponent(name)}/schema`, s,
      { method: "POST", body: JSON.stringify({ schema_definition: { fields } }) }),

  preview: (s: Session, name: string, payloads: unknown[]) =>
    request<PreviewResult>(`/api/topics/${encodeURIComponent(name)}/preview`, s,
      { method: "POST", body: JSON.stringify({ sample_payloads: payloads }) }),
};
