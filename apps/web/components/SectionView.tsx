export function SectionView({ title, body }: { title: string; body: string }) {
  return (
    <article className="sectionView">
      <h3>{title}</h3>
      <pre>{body}</pre>
    </article>
  );
}
