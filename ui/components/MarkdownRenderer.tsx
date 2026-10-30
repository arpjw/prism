"use client";
import CopyButton from "./CopyButton";

interface Props {
  content: string;
}

export default function MarkdownRenderer({ content }: Props) {
  const lines = content.split("\n");
  const elements: React.ReactNode[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // Code block
    if (line.startsWith("```")) {
      const codeLines: string[] = [];
      i++;
      while (i < lines.length && !lines[i].startsWith("```")) {
        codeLines.push(lines[i]);
        i++;
      }
      const code = codeLines.join("\n");
      elements.push(
        <div key={i} style={{ position: "relative", marginBottom: 16 }}>
          <div style={{
            background: "#0a0a0a",
            border: "1px solid var(--border)",
            borderRadius: 6,
            padding: "16px 20px",
            overflowX: "auto",
          }}>
            <div style={{ position: "absolute", top: 8, right: 12 }}>
              <CopyButton text={code} />
            </div>
            <pre style={{
              fontFamily: "'DM Mono', monospace",
              fontSize: 13,
              color: "var(--text-secondary)",
              margin: 0,
              lineHeight: 1.7,
            }}>
              <code>{code}</code>
            </pre>
          </div>
        </div>
      );
      i++;
      continue;
    }

    // Headings
    if (line.startsWith("### ")) {
      elements.push(
        <h3 key={i} style={{ fontFamily: "'DM Serif Display', serif", fontSize: 20, color: "var(--text-primary)", margin: "24px 0 8px" }}>
          {line.slice(4)}
        </h3>
      );
    } else if (line.startsWith("## ")) {
      elements.push(
        <h2 key={i} style={{ fontFamily: "'DM Serif Display', serif", fontSize: 26, color: "var(--text-primary)", margin: "32px 0 12px" }}>
          {line.slice(3)}
        </h2>
      );
    } else if (line.startsWith("# ")) {
      elements.push(
        <h1 key={i} style={{ fontFamily: "'DM Serif Display', serif", fontSize: 36, color: "var(--text-primary)", margin: "0 0 16px" }}>
          {line.slice(2)}
        </h1>
      );
    } else if (line.startsWith("| ")) {
      // Table — collect all table rows
      const tableLines: string[] = [line];
      i++;
      while (i < lines.length && lines[i].startsWith("|")) {
        tableLines.push(lines[i]);
        i++;
      }
      const rows = tableLines.filter(l => !l.match(/^\|[-| ]+\|$/));
      elements.push(
        <div key={`table-${i}`} style={{ overflowX: "auto", marginBottom: 16 }}>
          <table style={{ borderCollapse: "collapse", width: "100%", fontFamily: "'DM Mono', monospace", fontSize: 12 }}>
            {rows.map((row, ri) => {
              const cells = row.split("|").filter((_, ci) => ci > 0 && ci < row.split("|").length - 1);
              const Tag = ri === 0 ? "th" : "td";
              return (
                <tr key={ri}>
                  {cells.map((cell, ci) => (
                    <Tag key={ci} style={{
                      border: "1px solid var(--border)",
                      padding: "8px 12px",
                      color: ri === 0 ? "var(--text-primary)" : "var(--text-secondary)",
                      background: ri === 0 ? "var(--surface-elevated)" : "transparent",
                      textAlign: "left",
                      whiteSpace: "nowrap",
                    }}>
                      {cell.trim()}
                    </Tag>
                  ))}
                </tr>
              );
            })}
          </table>
        </div>
      );
      continue;
    } else if (line.startsWith("- ") || line.startsWith("* ")) {
      elements.push(
        <li key={i} style={{ color: "var(--text-secondary)", marginBottom: 4, marginLeft: 20, fontSize: 15 }}>
          {renderInline(line.slice(2))}
        </li>
      );
    } else if (line.match(/^\d+\. /)) {
      elements.push(
        <li key={i} style={{ color: "var(--text-secondary)", marginBottom: 4, marginLeft: 20, fontSize: 15 }}>
          {renderInline(line.replace(/^\d+\. /, ""))}
        </li>
      );
    } else if (line.trim() === "") {
      elements.push(<div key={i} style={{ height: 8 }} />);
    } else {
      elements.push(
        <p key={i} style={{ color: "var(--text-secondary)", fontSize: 15, lineHeight: 1.7, marginBottom: 8 }}>
          {renderInline(line)}
        </p>
      );
    }

    i++;
  }

  return <div>{elements}</div>;
}

function renderInline(text: string): React.ReactNode {
  // Handle `code`, **bold**, *em*, [link](url)
  const parts: React.ReactNode[] = [];
  const re = /(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*|\[[^\]]+\]\([^)]+\))/g;
  let last = 0;
  let match;
  let key = 0;
  while ((match = re.exec(text)) !== null) {
    if (match.index > last) parts.push(text.slice(last, match.index));
    const m = match[0];
    if (m.startsWith("`")) {
      parts.push(<code key={key++} style={{ fontFamily: "'DM Mono', monospace", fontSize: 12, background: "var(--surface-elevated)", padding: "2px 6px", borderRadius: 3, color: "var(--neon)" }}>{m.slice(1, -1)}</code>);
    } else if (m.startsWith("**")) {
      parts.push(<strong key={key++}>{m.slice(2, -2)}</strong>);
    } else if (m.startsWith("*")) {
      parts.push(<em key={key++}>{m.slice(1, -1)}</em>);
    } else if (m.startsWith("[")) {
      const label = m.match(/\[([^\]]+)\]/)?.[1] ?? "";
      const url = m.match(/\(([^)]+)\)/)?.[1] ?? "";
      parts.push(<a key={key++} href={url} style={{ color: "var(--prism-blue)", textDecoration: "underline" }}>{label}</a>);
    }
    last = match.index + m.length;
  }
  if (last < text.length) parts.push(text.slice(last));
  return parts.length === 1 ? parts[0] : parts;
}
