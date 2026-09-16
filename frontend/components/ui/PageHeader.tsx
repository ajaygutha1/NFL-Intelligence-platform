export function PageHeader({
  eyebrow,
  title,
  description,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
}) {
  return (
    <div className="mb-10">
      {eyebrow && (
        <div className="text-xs font-medium uppercase tracking-widest text-muted mb-2">
          {eyebrow}
        </div>
      )}
      <h1 className="text-3xl font-semibold tracking-tight">{title}</h1>
      {description && (
        <p className="mt-2 max-w-2xl text-sm text-muted">{description}</p>
      )}
    </div>
  );
}
