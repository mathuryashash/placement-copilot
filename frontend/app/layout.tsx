import type { Metadata } from "next";
import "./globals.css";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Placement Copilot",
  description:
    "RAG-powered Q&A over synthetic placement notices — demo/portfolio project",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-50 text-gray-900">
        <nav className="border-b border-gray-200 bg-white px-4 py-3">
          <div className="mx-auto flex max-w-5xl items-center gap-6">
            <Link
              href="/"
              className="font-semibold text-blue-700 hover:text-blue-900"
            >
              Placement Copilot
            </Link>
            <Link
              href="/chat"
              className="text-sm text-gray-600 hover:text-gray-900"
            >
              Chat
            </Link>
            <Link
              href="/drives"
              className="text-sm text-gray-600 hover:text-gray-900"
            >
              Drives
            </Link>
            <Link
              href="/deadlines"
              className="text-sm text-gray-600 hover:text-gray-900"
            >
              Deadlines
            </Link>
            <Link
              href="/profile"
              className="ml-auto text-sm text-gray-600 hover:text-gray-900"
            >
              My Profile
            </Link>
          </div>
        </nav>
        <main className="mx-auto max-w-5xl px-4 py-6">{children}</main>
        <footer className="mt-10 border-t border-gray-200 py-4 text-center text-xs text-gray-400">
          Synthetic data only — no real company or student information.
          Portfolio project by Yashash Mathur.
        </footer>
      </body>
    </html>
  );
}
