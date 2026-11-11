"use client";
import { useEffect, useState } from "react";
import type { StudentProfile } from "@/lib/api";
import { loadProfile, saveProfile, clearProfile } from "@/lib/utils";

export default function ProfilePage() {
  const [profile, setProfile] = useState<StudentProfile>({
    cgpa: 7.5,
    branch: "CSE",
    backlogs: 0,
    grad_year: 2026,
  });
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const p = loadProfile();
    if (p) setProfile(p);
  }, []);

  function handleSave(e: React.FormEvent) {
    e.preventDefault();
    saveProfile(profile);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  return (
    <div className="max-w-md">
      <h1 className="mb-2 text-xl font-bold">My Profile</h1>
      <p className="mb-4 text-sm text-gray-500">
        Your profile is stored only in your browser (localStorage) and is sent
        to the server per-request for eligibility checks only. The server does
        not store it.
      </p>
      <form onSubmit={handleSave} className="space-y-4">
        <div>
          <label className="mb-1 block text-sm font-medium">CGPA (0–10)</label>
          <input
            type="number"
            step="0.01"
            min="0"
            max="10"
            value={profile.cgpa}
            onChange={(e) => setProfile({ ...profile, cgpa: parseFloat(e.target.value) })}
            className="w-full rounded border border-gray-300 px-3 py-2 text-sm"
            required
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium">Branch</label>
          <select
            value={profile.branch}
            onChange={(e) => setProfile({ ...profile, branch: e.target.value })}
            className="w-full rounded border border-gray-300 px-3 py-2 text-sm"
          >
            {["CSE", "ISE", "ECE", "EEE", "ME", "CV"].map((b) => (
              <option key={b} value={b}>{b}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium">Active Backlogs</label>
          <input
            type="number"
            min="0"
            value={profile.backlogs}
            onChange={(e) => setProfile({ ...profile, backlogs: parseInt(e.target.value) })}
            className="w-full rounded border border-gray-300 px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium">Graduation Year</label>
          <input
            type="number"
            min="2024"
            max="2030"
            value={profile.grad_year}
            onChange={(e) => setProfile({ ...profile, grad_year: parseInt(e.target.value) })}
            className="w-full rounded border border-gray-300 px-3 py-2 text-sm"
          />
        </div>
        <div className="flex gap-3">
          <button
            type="submit"
            className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            {saved ? "Saved!" : "Save Profile"}
          </button>
          <button
            type="button"
            onClick={() => { clearProfile(); setProfile({ cgpa: 0, branch: "CSE", backlogs: 0, grad_year: 2026 }); }}
            className="rounded border border-gray-300 px-4 py-2 text-sm text-gray-600 hover:bg-gray-100"
          >
            Clear
          </button>
        </div>
      </form>
    </div>
  );
}
