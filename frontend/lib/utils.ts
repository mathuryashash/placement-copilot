// Profile utilities: load/save from localStorage
// The student profile is ONLY stored client-side and sent per-request.
// The server never stores it.

import type { StudentProfile } from "./api";

const PROFILE_KEY = "placement_copilot_profile";

export function loadProfile(): StudentProfile | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(PROFILE_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as StudentProfile;
  } catch {
    return null;
  }
}

export function saveProfile(profile: StudentProfile): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(PROFILE_KEY, JSON.stringify(profile));
}

export function clearProfile(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(PROFILE_KEY);
}

export function formatDeadline(isoString: string | null): string {
  if (!isoString) return "TBD";
  try {
    const d = new Date(isoString);
    return d.toLocaleDateString("en-IN", {
      day: "numeric",
      month: "short",
      year: "numeric",
      timeZone: "Asia/Kolkata",
    });
  } catch {
    return isoString;
  }
}

export function daysUntil(isoString: string | null): number | null {
  if (!isoString) return null;
  try {
    const d = new Date(isoString);
    const now = new Date();
    const diff = d.getTime() - now.getTime();
    return Math.ceil(diff / (1000 * 60 * 60 * 24));
  } catch {
    return null;
  }
}

export function randomSessionId(): string {
  return Math.random().toString(36).slice(2) + Date.now().toString(36);
}
