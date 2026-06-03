import MarkdownRenderer from "../../components/MarkdownRenderer";

export const revalidate = 3600;

const CONTRIBUTING_URL =
  "https://raw.githubusercontent.com/arpjw/prism/main/CONTRIBUTING_CONNECTORS.md";

export default async function DocsPage() {
  let content = "";
  try {
    const res = await fetch(CONTRIBUTING_URL, { next: { revalidate: 3600 } });
    if (res.ok) content = await res.text();
  } catch {}

  const sections = content
    .split("\n")
    .filter(line => line.startsWith("## "))
    .map(line => line.slice(3).trim());

  return (
    <div style={{ display: "flex", maxWidth: 1100, margin: "0 auto", padding: "96px 32px 80px", gap: 64 }}>
      {/* Sidebar */}
      <nav style={{
        width: 200,
        flexShrink: 0,
        position: "sticky",
        top: 80,
        alignSelf: "flex-start",
        height: "fit-content",
      }}>
        <div style={{
          fontFamily: "'DM Mono', monospace",
          fontSize: 10,
          color: "var(--text-tertiary)",
          letterSpacing: "0.1em",
          marginBottom: 16,
        }}>
          CONTRIBUTING GUIDE
        </div>
        {sections.map(section => (
          <a
            key={section}
            href={`#${section.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`}
            style={{
              display: "block",
              fontFamily: "'DM Mono', monospace",
              fontSize: 12,
              color: "var(--text-secondary)",
              marginBottom: 10,
              lineHeight: 1.4,
            }}
          >
            {section}
          </a>
        ))}
      </nav>

      {/* Content */}
      <article style={{ flex: 1, minWidth: 0 }}>
        {content ? (
          <MarkdownRenderer content={content} />
        ) : (
          <div style={{
            fontFamily: "'DM Mono', monospace",
            fontSize: 13,
            color: "var(--text-tertiary)",
            padding: "80px 0",
            textAlign: "center",
          }}>
            Loading documentation...
          </div>
        )}
      </article>
    </div>
  );
}
