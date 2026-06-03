"use client";
import { useState } from "react";
import type { Connector } from "../lib/registry";
import CopyButton from "./CopyButton";

interface Props {
  connector: Connector;
}

const TRANSPORT_LABELS: Record<string, string> = {
  websocket: "WS",
  rest: "REST",
  push: "PUSH",
};

export default function ConnectorCard({ connector }: Props) {
  const [hovered, setHovered] = useState(false);
  const borderColor = hovered
    ? connector.verified ? "var(--neon)" : "var(--prism-blue)"
    : "var(--border)";

  return (
    <a
      href={`/connector/${connector.slug}`}
      style={{
        display: "block",
        background: "var(--surface)",
        border: `1px solid ${borderColor}`,
        borderRadius: 8,
        padding: 24,
        cursor: "pointer",
        textDecoration: "none",
        transition: "border-color 0.15s",
      }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {/* Top row */}
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 4 }}>
        <span style={{ fontFamily: "'DM Serif Display', serif", fontSize: 18, color: "var(--text-primary)" }}>
          {connector.name}
        </span>
        {connector.verified && (
          <span style={{
            fontFamily: "'DM Mono', monospace",
            fontSize: 9,
            color: "var(--neon)",
            border: "1px solid var(--neon)",
            borderRadius: 3,
            padding: "2px 6px",
            letterSpacing: "0.08em",
            whiteSpace: "nowrap",
            marginLeft: 8,
          }}>
            ✓ VERIFIED
          </span>
        )}
      </div>

      {/* Slug */}
      <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 11, color: "var(--text-tertiary)", marginBottom: 12 }}>
        {connector.slug}
      </div>

      {/* Description */}
      <p style={{
        fontSize: 14,
        color: "var(--text-secondary)",
        lineHeight: 1.5,
        marginBottom: 16,
        display: "-webkit-box",
        WebkitLineClamp: 2,
        WebkitBoxOrient: "vertical",
        overflow: "hidden",
      }}>
        {connector.description}
      </p>

      {/* Tags */}
      {connector.tags.length > 0 && (
        <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 16 }}>
          {connector.tags.map(tag => (
            <span key={tag} style={{
              fontFamily: "'DM Mono', monospace",
              fontSize: 10,
              background: "#1a1a1a",
              color: "var(--text-secondary)",
              padding: "3px 8px",
              borderRadius: 100,
            }}>
              {tag}
            </span>
          ))}
        </div>
      )}

      {/* Bottom row */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <span style={{
            fontFamily: "'DM Mono', monospace",
            fontSize: 10,
            background: "rgba(179,255,0,0.08)",
            color: "var(--neon)",
            padding: "3px 8px",
            borderRadius: 4,
            letterSpacing: "0.05em",
          }}>
            {TRANSPORT_LABELS[connector.transport] ?? connector.transport.toUpperCase()}
          </span>
          <span style={{
            fontFamily: "'DM Mono', monospace",
            fontSize: 10,
            background: "var(--surface-elevated)",
            color: "var(--text-secondary)",
            padding: "3px 8px",
            borderRadius: 4,
          }}>
            {connector.auth_required ? "AUTH" : "PUBLIC"}
          </span>
          <span style={{ fontFamily: "'DM Mono', monospace", fontSize: 11, color: "var(--text-tertiary)" }}>
            {connector.author}
          </span>
        </div>
      </div>

      {/* Install command */}
      <div style={{
        marginTop: 12,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        background: "var(--bg)",
        border: "1px solid var(--border)",
        borderRadius: 4,
        padding: "6px 10px",
      }}
        onClick={e => e.preventDefault()}
      >
        <span style={{ fontFamily: "'DM Mono', monospace", fontSize: 11, color: "var(--text-tertiary)" }}>
          prism install {connector.slug}
        </span>
        <CopyButton text={`prism install ${connector.slug}`} />
      </div>
    </a>
  );
}
