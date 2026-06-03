export default function SkeletonCard() {
  return (
    <div style={{
      background: "var(--surface)",
      border: "1px solid var(--border)",
      borderRadius: 8,
      padding: 24,
      animation: "pulse 1.5s ease-in-out infinite",
    }}>
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
      `}</style>
      <div style={{ height: 20, background: "var(--surface-elevated)", borderRadius: 4, width: "60%", marginBottom: 8 }} />
      <div style={{ height: 12, background: "var(--surface-elevated)", borderRadius: 4, width: "40%", marginBottom: 16 }} />
      <div style={{ height: 14, background: "var(--surface-elevated)", borderRadius: 4, width: "90%", marginBottom: 6 }} />
      <div style={{ height: 14, background: "var(--surface-elevated)", borderRadius: 4, width: "70%", marginBottom: 20 }} />
      <div style={{ display: "flex", gap: 8 }}>
        <div style={{ height: 22, background: "var(--surface-elevated)", borderRadius: 100, width: 60 }} />
        <div style={{ height: 22, background: "var(--surface-elevated)", borderRadius: 100, width: 80 }} />
      </div>
    </div>
  );
}
