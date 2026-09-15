export function StatTile({
  label,
  value,
  sublabel,
}: {
  label: string;
  value: string;
  sublabel?: string;
}) {
  return (
    <div className="rounded-xl border border-border bg-surface p-5">
      <div className="text-xs font-medium uppercase tracking-widest text-muted">
        {label}
      </div>
      <div className="mt-2 text-2xl font-semibold tracking-tight font-mono-tabular">
        {value}
      </div>
      {sublabel && <div className="mt-1 text-xs text-muted">{sublabel}</div>}
    </div>
  );
}
