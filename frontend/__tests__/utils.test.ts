import { describe, it, expect, beforeEach } from "vitest";
import { loadProfile, saveProfile, clearProfile, formatDeadline, daysUntil, randomSessionId } from "../lib/utils";

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] ?? null,
    setItem: (key: string, val: string) => { store[key] = val; },
    removeItem: (key: string) => { delete store[key]; },
    clear: () => { store = {}; },
  };
})();

Object.defineProperty(window, "localStorage", { value: localStorageMock });

describe("profile utils", () => {
  beforeEach(() => localStorageMock.clear());

  it("returns null when no profile saved", () => {
    expect(loadProfile()).toBeNull();
  });

  it("saves and loads profile", () => {
    const p = { cgpa: 8.0, branch: "CSE", backlogs: 0, grad_year: 2026 };
    saveProfile(p);
    expect(loadProfile()).toEqual(p);
  });

  it("clears profile", () => {
    saveProfile({ cgpa: 7.0, branch: "ISE", backlogs: 0, grad_year: 2026 });
    clearProfile();
    expect(loadProfile()).toBeNull();
  });
});

describe("formatDeadline", () => {
  it("returns TBD for null", () => {
    expect(formatDeadline(null)).toBe("TBD");
  });

  it("formats a valid ISO date", () => {
    const result = formatDeadline("2026-03-15T23:59:00+05:30");
    expect(result).toContain("2026");
    expect(result.length).toBeGreaterThan(4);
  });
});

describe("daysUntil", () => {
  it("returns null for null", () => {
    expect(daysUntil(null)).toBeNull();
  });

  it("returns positive days for future date", () => {
    const future = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString();
    const days = daysUntil(future);
    expect(days).toBeGreaterThan(0);
    expect(days).toBeLessThanOrEqual(8);
  });

  it("returns negative or zero for past date", () => {
    const past = new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString();
    const days = daysUntil(past);
    expect(days).toBeLessThanOrEqual(0);
  });
});

describe("randomSessionId", () => {
  it("generates a non-empty string", () => {
    expect(randomSessionId().length).toBeGreaterThan(4);
  });

  it("generates different values each time", () => {
    expect(randomSessionId()).not.toBe(randomSessionId());
  });
});
