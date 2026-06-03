"use client";

interface Props {
  search: string;
  setSearch: (v: string) => void;
  typeFilter: string;
  setTypeFilter: (v: string) => void;
  transportFilter: string;
  setTransportFilter: (v: string) => void;
  sort: string;
  setSort: (v: string) => void;
}

const TYPE_FILTERS = ["All", "prediction_market", "alternative_data", "news", "custom"];
const TRANSPORT_FILTERS = ["All", "websocket", "rest", "push"];
const SORTS = ["A-Z", "Most Downloaded", "Newest"];

const TYPE_LABELS: Record<string, string> = {
  All: "All",
  prediction_market: "Prediction Market",
  alternative_data: "Alternative Data",
  news: "News",
  custom: "Custom",
};

const TRANSPORT_LABELS: Record<string, string> = {
  All: "All",
  websocket: "WebSocket",
  rest: "REST",
  push: "Push",
};

function Pill({
  label, active, onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      style={{
        fontFamily: "'DM Mono', monospace",
        fontSize: 11,
        padding: "5px 12px",
        borderRadius: 100,
        border: active ? "1px solid var(--neon)" : "1px solid var(--border)",
        background: active ? "rgba(179,255,0,0.08)" : "transparent",
        color: active ? "var(--neon)" : "var(--text-secondary)",
        cursor: "pointer",
        transition: "all 0.15s",
        whiteSpace: "nowrap",
        letterSpacing: "0.04em",
      }}
    >
      {label}
    </button>
  );
}

export default function FilterBar({
  search, setSearch,
  typeFilter, setTypeFilter,
  transportFilter, setTransportFilter,
  sort, setSort,
}: Props) {
  return (
    <div style={{
      position: "sticky",
      top: 56,
      zIndex: 50,
      background: "rgba(8,8,8,0.9)",
      backdropFilter: "blur(12px)",
      borderBottom: "1px solid var(--border)",
      padding: "12px 48px",
    }}>
      <div style={{ maxWidth: 1200, margin: "0 auto", display: "flex", flexWrap: "wrap", gap: 12, alignItems: "center" }}>
        <input
          type="text"
          placeholder="Search connectors..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          style={{
            fontFamily: "'DM Mono', monospace",
            fontSize: 13,
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: 6,
            padding: "7px 14px",
            color: "var(--text-primary)",
            outline: "none",
            width: 240,
          }}
        />
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
          {TYPE_FILTERS.map(t => (
            <Pill
              key={t}
              label={TYPE_LABELS[t]}
              active={typeFilter === t}
              onClick={() => setTypeFilter(t)}
            />
          ))}
        </div>
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
          {TRANSPORT_FILTERS.map(t => (
            <Pill
              key={t}
              label={TRANSPORT_LABELS[t]}
              active={transportFilter === t}
              onClick={() => setTransportFilter(t)}
            />
          ))}
        </div>
        <select
          value={sort}
          onChange={e => setSort(e.target.value)}
          style={{
            fontFamily: "'DM Mono', monospace",
            fontSize: 11,
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: 6,
            padding: "6px 10px",
            color: "var(--text-secondary)",
            cursor: "pointer",
            outline: "none",
            marginLeft: "auto",
          }}
        >
          {SORTS.map(s => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>
    </div>
  );
}
