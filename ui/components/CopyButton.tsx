"use client";
import { useState } from "react";

interface Props {
  text: string;
  style?: React.CSSProperties;
}

export default function CopyButton({ text, style }: Props) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <button
      onClick={handleCopy}
      style={{
        background: "none",
        border: "1px solid var(--border)",
        color: copied ? "var(--neon)" : "var(--text-tertiary)",
        cursor: "pointer",
        fontFamily: "'DM Mono', monospace",
        fontSize: 10,
        padding: "3px 8px",
        borderRadius: 4,
        transition: "all 0.15s",
        whiteSpace: "nowrap",
        ...style,
      }}
    >
      {copied ? "Copied!" : "Copy"}
    </button>
  );
}
