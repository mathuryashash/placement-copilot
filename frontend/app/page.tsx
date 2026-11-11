import Link from "next/link";

export default function HomePage() {
  return (
    <div className="max-w-2xl">
      <h1 className="mb-3 text-2xl font-bold text-gray-900">
        Placement Copilot
      </h1>
      <p className="mb-6 text-gray-600">
        Ask questions about placement drives from your college placement cell
        notices. Get cited answers, check eligibility, and track deadlines.
      </p>
      <div className="mb-4 rounded-md border border-yellow-200 bg-yellow-50 px-4 py-3 text-sm text-yellow-800">
        <strong>Demo notice:</strong> This is a portfolio project using
        synthetic (fictional) company data only. No real placement data is stored or used.
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <Link href="/chat" className="block rounded-lg border border-gray-200 bg-white p-4 shadow-sm hover:shadow-md">
          <h2 className="mb-1 font-semibold text-blue-700">Chat</h2>
          <p className="text-sm text-gray-600">Ask questions and get answers with citations to source notices.</p>
        </Link>
        <Link href="/drives" className="block rounded-lg border border-gray-200 bg-white p-4 shadow-sm hover:shadow-md">
          <h2 className="mb-1 font-semibold text-blue-700">Drives</h2>
          <p className="text-sm text-gray-600">Browse all placement drives with filters for eligibility and deadline.</p>
        </Link>
        <Link href="/deadlines" className="block rounded-lg border border-gray-200 bg-white p-4 shadow-sm hover:shadow-md">
          <h2 className="mb-1 font-semibold text-blue-700">Deadlines</h2>
          <p className="text-sm text-gray-600">See upcoming registration deadlines and download a calendar file.</p>
        </Link>
        <Link href="/profile" className="block rounded-lg border border-gray-200 bg-white p-4 shadow-sm hover:shadow-md">
          <h2 className="mb-1 font-semibold text-blue-700">My Profile</h2>
          <p className="text-sm text-gray-600">Set your CGPA, branch, and grad year. Stored only in your browser.</p>
        </Link>
      </div>
    </div>
  );
}
