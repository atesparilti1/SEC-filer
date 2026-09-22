export function EmptyState({ message }: { message: string }) {
  return (
    <div className="rounded-xl border border-dashed border-border px-5 py-8 text-center text-sm text-text-muted">
      {message}
    </div>
  );
}
