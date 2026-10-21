import { notFound, redirect } from "next/navigation";

export default function LabRoute({ params }: { params: { courseId: string } }) {
  if (!["cache-lab", "ldpc-5g", "optical-flow"].includes(params.courseId)) notFound();
  redirect("/?course=" + params.courseId);
}
