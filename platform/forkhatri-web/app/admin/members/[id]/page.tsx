import MemberDetail from "@/components/admin/MemberDetail";

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <MemberDetail memberId={id} />;
}
