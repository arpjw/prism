interface Props {
  title?: string;
  children: React.ReactNode;
}

export default function TerminalBlock({ title = "terminal", children }: Props) {
  return (
    <div style={{
      background: "#0a0a0a",
      border: "1px solid var(--border)",
      borderRadius: 8,
      overflow: "hidden",
    }}>
      <div style={{
        padding: "10px 16px",
        borderBottom: "1px solid var(--border)",
        display: "flex",
        alignItems: "center",
        gap: 8,
      }}>
        {["#ff5f57", "#febc2e", "#28c840"].map((color, i) => (
          <div
            key={i}
            style={{ width: 10, height: 10, borderRadius: "50%", background: color }}
          />
        ))}
        <span style={{
          fontFamily: "'DM Mono', monospace",
          fontSize: 11,
          color: "var(--text-tertiary)",
          marginLeft: 8,
        }}>
          {title}
        </span>
      </div>
      <pre style={{
        fontFamily: "'DM Mono', monospace",
        fontSize: 13,
        color: "var(--text-secondary)",
        padding: "20px 24px",
        overflowX: "auto",
        lineHeight: 1.8,
        margin: 0,
      }}>
        {children}
      </pre>
    </div>
  );
}
