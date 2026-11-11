"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import type { Drive, EligibilityResult } from "@/lib/api";
import { getDrive, checkEligibility } from "@/lib/api";
import { loadProfile, formatDeadline } from "@/lib/utils";
import Link from "next/link";

// Mark as dynamic; params only available at runtime
export const dynamicParams = true;

export default function DriveDetailPage() {
  const params = useParams<{ id: string }>();
  const [drive, setDrive] = useState<Drive | null>(null);
  const [eligibility, setEligibility] = useState<EligibilityResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!params?.id) return;
    getDrive(params.id)
      .then((d) => {
        setDrive(d);
        const profile = loadProfile();
        if (profile) {
          return checkEligibility(d.id, profile).then(setEligibility);
        }
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [params?.id]);

  if (loading) return <p className="text-sm text-gray-400">Loading...</p>;
  if (error) return <p className="text-sm text-red-600">Error: {error}</p>;
  if (!drive) return <p className="text-sm text-gray-500">Drive not found.</p>;

  const el = drive.eligibility;

  return (
    <div className="max-w-2xl">
      <Link href="/drives" className="text-sm text-blue-600 hover:underline">
        ← Back to Drives
      </Link>
      <h1 className="mt-3 text-2xl font-bold">{drive.company}</h1>
      <p className="text-lg text-gray-700">{drive.role}</p>

      {eligibility && (
        <div
          className={`mt-4 rounded-md border px-4 py-3 text-sm ${
            eligibility.eligible
              ? "border-green-200 bg-green-50 text-green-800"
              : "border-red-200 bg-red-50 text-red-800"
          }`}
        >
          <strong>{eligibility.eligible ? "You are eligible" : "You are not eligible"}</strong>
          <ul className="mt-1 list-disc pl-4 space-y-1">
            {eligibility.reasons.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-6 grid gap-4 sm:grid-cols-2">
        {drive.ctc_lpa && (
          <div>
            <span className="text-xs font-medium uppercase text-gray-500">CTC</span>
            <p className="font-semibold text-green-700">{drive.ctc_lpa} LPA</p>
          </div>
        )}
        {drive.locations.length > 0 && (
          <div>
            <span className="text-xs font-medium uppercase text-gray-500">Locations</span>
            <p>{drive.locations.join(", ")}</p>
          </div>
        )}
        {drive.registration_deadline && (
          <div>
            <span className="text-xs font-medium uppercase text-gray-500">Registration Deadline</span>
            <p>{formatDeadline(drive.registration_deadline)}</p>
          </div>
        )}
      </div>

      <div className="mt-6">
        <h2 className="mb-2 font-semibold">Eligibility</h2>
        <ul className="space-y-1 text-sm text-gray-700">
          {el.min_cgpa && <li>Minimum CGPA: {el.min_cgpa}</li>}
          {el.allowed_branches && <li>Branches: {el.allowed_branches.join(", ")}</li>}
          <li>Max Backlogs: {el.max_backlogs}</li>
          {el.grad_years && <li>Graduation Years: {el.grad_years.join(", ")}</li>}
          {el.extra_notes && <li>Note: {el.extra_notes}</li>}
        </ul>
      </div>

      {drive.rounds.length > 0 && (
        <div className="mt-6">
          <h2 className="mb-2 font-semibold">Selection Process</h2>
          <ol className="space-y-2 text-sm">
            {drive.rounds.map((r, i) => (
              <li key={i} className="flex gap-2">
                <span className="font-medium text-blue-700">{i + 1}.</span>
                <div>
                  <span className="font-medium">{r.name}</span>
                  {r.description && (
                    <span className="ml-1 text-gray-600">— {r.description}</span>
                  )}
                  {r.date_hint && (
                    <span className="ml-1 text-gray-500">({r.date_hint})</span>
                  )}
                </div>
              </li>
            ))}
          </ol>
        </div>
      )}

      {drive.links.length > 0 && (
        <div className="mt-6">
          <h2 className="mb-2 font-semibold">Links</h2>
          <ul className="space-y-1">
            {drive.links.map((l, i) => (
              <li key={i}>
                <a
                  href={l}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-blue-600 hover:underline"
                >
                  {l}
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
