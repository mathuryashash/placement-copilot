import { Suspense } from "react";
import { DriveDetailClient } from "./components/client";

// Return a non-matching ID to satisfy cache-components requirement
// Real IDs are only known at runtime from API
export async function generateStaticParams() {
  return [{ id: "build-placeholder" }];
}

export default function DriveDetailPage() {
  return (
    <Suspense fallback={<p className="text-sm text-gray-400">Loading drive...</p>}>
      <DriveDetailClient />
    </Suspense>
  );
}
