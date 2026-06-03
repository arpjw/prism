import { fetchRegistry, getReadmeUrl } from "../../../lib/registry";
import { notFound } from "next/navigation";
import MarkdownRenderer from "../../../components/MarkdownRenderer";
import CopyButton from "../../../components/CopyButton";

export const revalidate = 300;

interface Props {
  params: { slug: string };
}

const TRANSPORT_LABELS: Record<string, string> = {
  websocket: "WebSocket",
  rest: "REST",
  push: "Push",
};

export default async function ConnectorPage({ params }: Props) {
  const registry = await fetchRegistry();
  const connector = registry.connectors.find(c => c.slug === params.slug);

  if (!connector) notFound();

  let readme = "";
  try {
    const res = await fetch(getReadmeUrl(connector), { next: { revalidate: 600 } });
    if (res.ok) readme = await res.text();
  } catch {}

  return (
    <div style={{ maxWidth: 800, margin: "0 auto", padding: "96px 32px 80px" }}>
      {/* Breadcrumb */}
      <div style={{
        fontFamily: "'DM Mono', monospace",
        fontSize: 12,
        color: "var(--text-tertiary)",
        marginBottom: 32,
      }}>
        <a href="/" style={{ color: "var(--text-tertiary)" }}>PRISM</a>
        {" / "}
        <span style={{ color: "var(--text-secondary)" }}>{connector.slug}</span>
      </div>

      {/* Hero */}
      <h1 style={{
        fontFamily: "'DM Serif Display', serif",
        fontSize: 42,
        color: "var(--text-primary)",
        marginBottom: 12,
      }}>
        {connector.name}
      </h1>
      <p style={{ fontSize: 17, color: "var(--text-secondary)", marginBottom: 24, lineHeight: 1.6 }}>
        {connector.description}
      </p>

      {/* Badge row */}
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 40 }}>
        {[
          connector.transport.toUpperCase(),
          connector.source_type.replace("_", " "),
          connector.auth_required ? "AUTH REQUIRED" : "PUBLIC",
          ...(connector.verified ? ["✓ VERIFIED"] : []),
        ].map(badge => (
          <span key={badge} style={{
            fontFamily: "'DM Mono', monospace",
            fontSize: 10,
            padding: "4px 10px",
            borderRadius: 4,
            background: badge.includes("VERIFIED") ? "rgba(179,255,0,0.08)" : "var(--surface)",
            color: badge.includes("VERIFIED") ? "var(--neon)" : "var(--text-secondary)",
            border: badge.includes("VERIFIED") ? "1px solid var(--neon)" : "1px solid var(--border)",
            letterSpacing: "0.06em",
          }}>
            {badge}
          </span>
        ))}
      </div>

      {/* Install section */}
      <section style={{
        marginBottom: 40,
        borderLeft: "3px solid var(--neon)",
        background: "var(--surface)",
        padding: "20px 24px",
        borderRadius: "0 6px 6px 0",
      }}>
        <div style={{
          fontFamily: "'DM Mono', monospace",
          fontSize: 11,
          color: "var(--neon)",
          letterSpacing: "0.1em",
          marginBottom: 12,
        }}>
          INSTALL
        </div>
        {["pip install prism-signal", `prism install ${connector.slug}`].map(cmd => (
          <div key={cmd} style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            background: "var(--bg)",
            border: "1px solid var(--border)",
            borderRadius: 4,
            padding: "8px 14px",
            marginBottom: 6,
          }}>
            <code style={{
              fontFamily: "'DM Mono', monospace",
              fontSize: 13,
              color: "var(--text-primary)",
            }}>
              {cmd}
            </code>
            <CopyButton text={cmd} />
          </div>
        ))}
      </section>

      {/* Auth fields */}
      {connector.auth_fields.length > 0 && (
        <section style={{ marginBottom: 32, borderLeft: "3px solid var(--neon)", background: "var(--surface)", padding: "20px 24px", borderRadius: "0 6px 6px 0" }}>
          <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 11, color: "var(--neon)", letterSpacing: "0.1em", marginBottom: 12 }}>AUTH REQUIRED</div>
          {connector.auth_fields.map(field => (
            <div key={field} style={{ fontFamily: "'DM Mono', monospace", fontSize: 13, color: "var(--text-secondary)", marginBottom: 6 }}>
              <code style={{ color: "var(--prism-blue)" }}>{field}</code>
            </div>
          ))}
        </section>
      )}

      {/* Contract slugs */}
      <section style={{ marginBottom: 32, borderLeft: "3px solid var(--neon)", background: "var(--surface)", padding: "20px 24px", borderRadius: "0 6px 6px 0" }}>
        <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 11, color: "var(--neon)", letterSpacing: "0.1em", marginBottom: 12 }}>CONTRACT SLUGS</div>
        {connector.contract_slugs.map(slug => (
          <div key={slug} style={{ fontFamily: "'DM Mono', monospace", fontSize: 13, color: "var(--text-secondary)", marginBottom: 4 }}>
            {slug}
          </div>
        ))}
      </section>

      {/* Tags */}
      <section style={{ marginBottom: 40 }}>
        <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 11, color: "var(--text-tertiary)", letterSpacing: "0.1em", marginBottom: 12 }}>TAGS</div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
          {connector.tags.map(tag => (
            <span key={tag} style={{
              fontFamily: "'DM Mono', monospace",
              fontSize: 11,
              background: "#1a1a1a",
              color: "var(--text-secondary)",
              padding: "4px 12px",
              borderRadius: 100,
            }}>
              {tag}
            </span>
          ))}
        </div>
      </section>

      {/* README */}
      {readme && (
        <section style={{ marginBottom: 40, borderTop: "1px solid var(--border)", paddingTop: 32 }}>
          <MarkdownRenderer content={readme} />
        </section>
      )}

      {/* Back link */}
      <a href="/" style={{
        fontFamily: "'DM Mono', monospace",
        fontSize: 12,
        color: "var(--text-secondary)",
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        marginTop: 16,
      }}>
        ← Back to registry
      </a>
    </div>
  );
}
