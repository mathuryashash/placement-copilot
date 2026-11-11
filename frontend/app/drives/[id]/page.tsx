import { DriveDetailClient } from "./components/client";

export async function generateStaticParams() {
  return [];
}

export default function DriveDetailPage() {
  return <DriveDetailClient />;
}
