"use client";
import { useEffect, useState, useCallback } from "react";
import type { DeadlineItem } from "@/lib/api";
import { getDeadlines } from "@/lib/api";
import { formatDeadline } from "@/lib/utils";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:18400";

export default function DeadlinesPage() {
  const [deadlines, setDeadlines] = useState<DeadlineItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [days, setDays] = useState(30);

  const fetchDeadlines = useCallback((daysAhead: number) => {
    setLoading(true);
    getDeadlines(daysAhead)
      .then(setDeadlines)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetchDeadlines(days);
  }, [days, fetchDeadlines]);

  return (
    <div className="max-w-2xl">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-bold">Upcoming Deadlines</h1>
        <a
          href={`${API_BASE}/api/v1/deadlines/calendar.ics?days_ahead=${days}`}
          download="placement-deadlines.ics"
          className="rounded border border-gray-300 px-3 py-1 text-sm text-gray-600 hover:bg-gray-50"
        >
          Download .ics
        </a>
      </div>

      <div className="mb-4 flex items-center gap-2 text-sm">
        <span>Show deadlines in next</span>
        <select
          value={days}
          onChange={(e) => setDays(parseInt(e.target.value))}
          className="rounded border border-gray-300 px-2 py-1 text-sm"
        >
          <option value={7}>7 days</option>
          <option value={14}>14 days</option>
          <option value={30}>30 days</option>
          <option value={90}>90 days</option>
        </select>
      </div>

      {loading && <p className="text-sm text-gray-400">Loading...</p>}
      {error && <p className="text-sm text-red-600">Error: {error}</p>}
      {!loading && deadlines.length === 0 && (
        <p className="text-sm text-gray-500">
          No upcoming deadlines in the next {days} days.
        </p>
      )}

      <div className="space-y-2">
        {deadlines.map((d) => (
          <div
            key={d.drive_id}
            className="flex items-center justify-between rounded-lg border border-gray-200 bg-white px-4 py-3"
          >
            <div>
              <p className="font-medium text-gray-900">{d.company}</p>
              <p className="text-sm text-gray-600">{d.role}</p>
            </div>
            <div className="text-right">
              <p className="text-sm font-medium text-gray-700">
                {formatDeadline(d.deadline)}
              </p>
              <p
                className={`text-xs ${
                  d.days_left <= 3
                    ? "text-red-600"
                    : d.days_left <= 7
                    ? "text-orange-600"
                    : "text-gray-500"
                }`}
              >
                {d.days_left === 0
                  ? "Today!"
                  : d.days_left === 1
                  ? "Tomorrow"
                  : `${d.days_left} days left`}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
