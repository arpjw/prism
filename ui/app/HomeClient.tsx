"use client";
import { useState, useMemo } from "react";
import type { Connector } from "../lib/registry";
import ConnectorCard from "../components/ConnectorCard";
import FilterBar from "../components/FilterBar";
import SkeletonCard from "../components/SkeletonCard";
import TerminalBlock from "../components/TerminalBlock";
import CopyButton from "../components/CopyButton";

interface Props {
  initialConnectors: Connector[];
  initialError: string | null;
}

const TERMINAL_OUTPUT = `$ prism list --registry

  NAME                   SLUG               VERSION  TRANSPORT
  ─────────────────────────────────────────────────────────────
  Kalshi Fed Markets     kalshi_fed         1.0.0    websocket
  Polymarket Macro       polymarket_macro   1.0.0    websocket
  Metaculus Macro        metaculus_macro    1.0.0    rest
  Manifold Macro         manifold_macro     1.0.0    rest
  FRED Macro             fred_macro         1.0.0    rest

  5 connectors available. Use 'prism install <slug>' to install.`;

export default function HomeClient({ initialConnectors, initialError }: Props) {
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("All");
  const [transportFilter, setTransportFilter] = useState("All");
  const [sort, setSort] = useState("A-Z");

  const filtered = useMemo(() => {
    let list = [...initialConnectors];

    if (search) {
      const q = search.toLowerCase();
      list = list.filter(c =>
        c.name.toLowerCase().includes(q) ||
        c.slug.toLowerCase().includes(q) ||
        c.description.toLowerCase().includes(q) ||
        c.tags.some(t => t.toLowerCase().includes(q))
      );
    }

    if (typeFilter !== "All") {
      list = list.filter(c => c.source_type === typeFilter);
    }

    if (transportFilter !== "All") {
      list = list.filter(c => c.transport === transportFilter);
    }

    if (sort === "A-Z") {
      list.sort((a, b) => a.name.localeCompare(b.name));
    } else if (sort === "Most Downloaded") {
      list.sort((a, b) => b.downloads - a.downloads);
    }
    // "Newest" = registry order (already sorted)

    return list;
  }, [initialConnectors, search, typeFilter, transportFilter, sort]);

  return (
    <>
      {/* Hero */}
      <section style={{ padding: "96px 48px 64px", maxWidth: 1200, margin: "0 auto" }}>
        <div style={{ display: "grid", gridTemplateColumns: "60% 40%", gap: 64, alignItems: "center" }}>
          <div>
            <div style={{
              fontFamily: "'DM Mono', monospace",
              fontSize: 11,
              color: "var(--neon)",
              letterSpacing: "0.15em",
              marginBottom: 20,
            }}>
              CONNECTOR REGISTRY v1.0
            </div>

            <h1 style={{
              fontFamily: "'DM Serif Display', serif",
              fontSize: 56,
              lineHeight: 1.05,
              color: "var(--text-primary)",
              marginBottom: 4,
            }}>
              Any signal source.
            </h1>
            <h1 style={{
              fontFamily: "'DM Serif Display', serif",
              fontSize: 56,
              lineHeight: 1.05,
              color: "var(--prism-blue)",
              marginBottom: 28,
            }}>
              One interface.
            </h1>

            <p style={{
              fontSize: 17,
              color: "var(--text-secondary)",
              lineHeight: 1.7,
              marginBottom: 32,
              maxWidth: 520,
            }}>
              Prism is an open connector format for velocity signal engines. Browse community
              connectors, install with one command, or build your own in minutes.
            </p>

            <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
              <span style={{
                fontFamily: "'DM Mono', monospace",
                fontSize: 13,
                background: "var(--surface)",
                border: "1px solid var(--border)",
                borderRadius: 100,
                padding: "8px 16px",
                color: "var(--text-secondary)",
              }}>
                {initialConnectors.length} connectors
              </span>
              <span style={{
                fontFamily: "'DM Mono', monospace",
                fontSize: 13,
                background: "var(--surface)",
                border: "1px solid var(--border)",
                borderRadius: 100,
                padding: "8px 16px",
                color: "var(--text-secondary)",
                display: "flex",
                alignItems: "center",
                gap: 8,
              }}>
                pip install prism-signal
                <CopyButton text="pip install prism-signal" />
              </span>
            </div>
          </div>

          <div>
            <TerminalBlock title="prism list --registry">
              {TERMINAL_OUTPUT}
            </TerminalBlock>
          </div>
        </div>
      </section>

      {/* Filter bar */}
      <FilterBar
        search={search} setSearch={setSearch}
        typeFilter={typeFilter} setTypeFilter={setTypeFilter}
        transportFilter={transportFilter} setTransportFilter={setTransportFilter}
        sort={sort} setSort={setSort}
      />

      {/* Registry grid */}
      <section style={{ padding: "48px 48px 80px", maxWidth: 1200, margin: "0 auto" }}>
        {initialError ? (
          <div style={{
            textAlign: "center",
            padding: "80px 0",
            color: "var(--text-secondary)",
            fontFamily: "'DM Mono', monospace",
            fontSize: 13,
          }}>
            <div style={{ color: "var(--red)", marginBottom: 12 }}>{initialError}</div>
            <button
              onClick={() => window.location.reload()}
              style={{
                background: "none",
                border: "1px solid var(--border)",
                color: "var(--text-secondary)",
                padding: "8px 20px",
                borderRadius: 6,
                cursor: "pointer",
                fontFamily: "'DM Mono', monospace",
                fontSize: 12,
              }}
            >
              Retry
            </button>
          </div>
        ) : (
          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(3, 1fr)",
            gap: 16,
          }}>
            {filtered.length === 0 ? (
              <div style={{
                gridColumn: "1 / -1",
                textAlign: "center",
                padding: "80px 0",
                color: "var(--text-tertiary)",
                fontFamily: "'DM Mono', monospace",
                fontSize: 13,
              }}>
                No connectors match your filters.
              </div>
            ) : (
              filtered.map(connector => (
                <ConnectorCard key={connector.slug} connector={connector} />
              ))
            )}
          </div>
        )}
      </section>
    </>
  );
}
