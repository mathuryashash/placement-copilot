"use client";
import { useEffect, useState, useCallback } from "react";
import type { Drive } from "@/lib/api";
import { listDrives, checkEligibility } from "@/lib/api";
import { loadProfile, formatDeadline, daysUntil } from "@/lib/utils";
import Link from "next/link";

export default function DrivesPage() {
  const [drives, setDrives] = useState<Drive[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [closingFilter, setClosingFilter] = useState(false);
  const [eligibleFilter, setEligibleFilter] = useState(false);
  const [eligibilityMap, setEligibilityMap] = useState<Record<string, boolean>>({});

  const fetchDrives = useCallback((closing: boolean) => {
    setLoading(true);
    listDrives({ closing_in_days: closing ? 14 : undefined })
      .then(setDrives)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetchDrives(closingFilter);
  }, [closingFilter, fetchDrives]);

  useEffect(() => {
    if (!eligibleFilter) return;
    const profile = loadProfile();
    if (!profile) return;
    drives.forEach((d) => {
      if (d.id in eligibilityMap) return;
      checkEligibility(d.id, profile)
        .then((r) => setEligibilityMap((m) => ({ ...m, [d.id]: r.eligible })))
        .catch(() => {});
    });
  }, [eligibleFilter, drives]); // eslint-disable-line react-hooks/exhaustive-deps

  const displayDrives = eligibleFilter
    ? drives.filter((d) => eligibilityMap[d.id] === true)
    : drives;

  return (
    <div>
      <h1 className="mb-3 text-xl font-bold">Placement Drives</h1>
      <div className="mb-4 flex flex-wrap gap-3">
        <label className="flex items-center gap-1 text-sm">
          <input
            type="checkbox"
            checked={closingFilter}
            onChange={(e) => setClosingFilter(e.target.checked)}
          />
          Closing in 14 days
        </label>
        <label className="flex items-center gap-1 text-sm">
          <input
            type="checkbox"
            checked={eligibleFilter}
            onChange={(e) => setEligibleFilter(e.target.checked)}
          />
          Eligible for me (uses saved profile)
        </label>
      </div>

      {loading && <p className="text-sm text-gray-400">Loading...</p>}
      {error && <p className="text-sm text-red-600">Error: {error}</p>}
      {!loading && displayDrives.length === 0 && (
        <p className="text-sm text-gray-500">
          No drives found. Try ingesting some synthetic notices first.
        </p>
      )}

      <div className="grid gap-3 sm:grid-cols-2">
        {displayDrives.map((d) => {
          const days = daysUntil(d.registration_deadline);
          return (
            <Link
              key={d.id}
              href={`/drives/${d.id}`}
              className="block rounded-lg border border-gray-200 bg-white p-4 shadow-sm hover:shadow-md"
            >
              <div className="mb-1 flex items-start justify-between">
                <span className="font-semibold text-gray-900">{d.company}</span>
                {d.ctc_lpa && (
                  <span className="text-sm font-medium text-green-700">
                    {d.ctc_lpa} LPA
                  </span>
                )}
              </div>
              <p className="text-sm text-gray-600">{d.role}</p>
              {d.registration_deadline && (
                <p className="mt-1 text-xs text-gray-500">
                  Deadline: {formatDeadline(d.registration_deadline)}
                  {days !== null && days >= 0 && days <= 7 && (
                    <span className="ml-1 rounded bg-red-100 px-1 text-red-700">
                      {days}d left
                    </span>
                  )}
                </p>
              )}
              {d.eligibility.min_cgpa && (
                <p className="mt-1 text-xs text-gray-500">
                  CGPA: {d.eligibility.min_cgpa}+
                  {d.eligibility.allowed_branches && (
                    <span className="ml-1">
                      | {d.eligibility.allowed_branches.slice(0, 3).join(", ")}
                    </span>
                  )}
                </p>
              )}
            </Link>
          );
        })}
      </div>
    </div>
  );
}
