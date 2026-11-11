// Typed API client for the Placement Copilot backend
// All endpoints communicate with NEXT_PUBLIC_API_URL

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:18400";

export interface EligibilityRule {
  min_cgpa: number | null;
  allowed_branches: string[] | null;
  max_backlogs: number;
  grad_years: number[] | null;
  extra_notes: string;
}

export interface Round {
  name: string;
  description: string;
  date_hint: string;
}

export interface Drive {
  id: string;
  company: string;
  role: string;
  ctc_lpa: number | null;
  stipend_pm: number | null;
  locations: string[];
  eligibility: EligibilityRule;
  registration_deadline: string | null;
  test_date: string | null;
  rounds: Round[];
  links: string[];
  notice_ids: string[];
}

export interface StudentProfile {
  cgpa: number;
  branch: string;
  backlogs: number;
  grad_year: number;
}

export interface EligibilityResult {
  eligible: boolean;
  reasons: string[];
}

export interface Citation {
  notice_id: string;
  chunk_text: string;
  score: number;
}

export interface ChatResponse {
  answer: string;
  citations: Citation[];
  is_refusal: boolean;
}

export interface DeadlineItem {
  drive_id: string;
  company: string;
  role: string;
  deadline: string;
  days_left: number;
}

export interface IngestResponse {
  notice_id: string;
  drive_id: string | null;
  message: string;
}

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new ApiError(res.status, text || res.statusText);
  }
  return res.json() as Promise<T>;
}

// --- Drives ------------------------------------------------------------------

export async function listDrives(params?: {
  company?: string;
  closing_in_days?: number;
}): Promise<Drive[]> {
  const qs = new URLSearchParams();
  if (params?.company) qs.set("company", params.company);
  if (params?.closing_in_days != null)
    qs.set("closing_in_days", String(params.closing_in_days));
  const query = qs.toString() ? `?${qs.toString()}` : "";
  return apiFetch<Drive[]>(`/api/v1/drives${query}`);
}

export async function getDrive(id: string): Promise<Drive> {
  return apiFetch<Drive>(`/api/v1/drives/${id}`);
}

export async function checkEligibility(
  driveId: string,
  profile: StudentProfile,
): Promise<EligibilityResult> {
  return apiFetch<EligibilityResult>(
    `/api/v1/drives/${driveId}/eligibility`,
    {
      method: "POST",
      body: JSON.stringify({ profile }),
    },
  );
}

// --- Chat --------------------------------------------------------------------

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export async function sendChatMessage(
  messages: ChatMessage[],
  profile: StudentProfile | null,
  sessionId: string,
): Promise<ChatResponse> {
  return apiFetch<ChatResponse>("/api/v1/chat", {
    method: "POST",
    body: JSON.stringify({ messages, profile, session_id: sessionId }),
  });
}

export async function submitFeedback(
  sessionId: string,
  messageIndex: number,
  feedback: "up" | "down",
): Promise<void> {
  await apiFetch("/api/v1/feedback", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, message_index: messageIndex, feedback }),
  });
}

// --- Ingest ------------------------------------------------------------------

export async function ingestText(
  text: string,
  sourceName = "pasted",
): Promise<IngestResponse> {
  return apiFetch<IngestResponse>("/api/v1/ingest/text", {
    method: "POST",
    body: JSON.stringify({ text, source_name: sourceName }),
  });
}

// --- Deadlines ---------------------------------------------------------------

export async function getDeadlines(daysAhead = 30): Promise<DeadlineItem[]> {
  return apiFetch<DeadlineItem[]>(`/api/v1/deadlines?days_ahead=${daysAhead}`);
}

export { ApiError };
