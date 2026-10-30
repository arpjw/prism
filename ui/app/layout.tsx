import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Prism — Connector Registry",
  description:
    "Open connector format for velocity signal engines. Browse, install, and build connectors.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <Header />
        <main>{children}</main>
        <Footer />
      </body>
    </html>
  );
}

function Header() {
  return (
    <header style={{
      position: "fixed",
      top: 0,
      left: 0,
      right: 0,
      zIndex: 100,
      background: "rgba(8,8,8,0.92)",
      backdropFilter: "blur(12px)",
      borderBottom: "1px solid var(--border)",
      padding: "0 32px",
      height: 56,
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
    }}>
      <Link href="/" style={{ display: "flex", alignItems: "center", gap: 10, textDecoration: "none" }}>
        <PrismIcon />
        <span style={{
          fontFamily: "'DM Mono', monospace",
          fontSize: 15,
          letterSpacing: "0.2em",
          color: "var(--text-primary)",
          fontWeight: 500,
        }}>
          PRISM
        </span>
      </Link>
      <nav style={{ display: "flex", gap: 28 }}>
        {[
          { label: "GitHub", href: "https://github.com/arpjw/prism" },
          { label: "Docs", href: "/docs" },
          { label: "arpjw", href: "https://aryasomu.com" },
        ].map(({ label, href }) => (
          <a
            key={label}
            href={href}
            style={{
              fontFamily: "'DM Mono', monospace",
              fontSize: 12,
              color: "var(--text-secondary)",
              letterSpacing: "0.05em",
              transition: "color 0.15s",
            }}
          >
            {label}
          </a>
        ))}
      </nav>
    </header>
  );
}

function PrismIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M10 2L2 16h16L10 2z" stroke="var(--neon)" strokeWidth="1.5" fill="none" strokeLinejoin="round" />
      <path d="M10 2L16 16" stroke="var(--prism-blue)" strokeWidth="1" opacity="0.6" />
      <path d="M10 2L6 16" stroke="var(--prism-violet)" strokeWidth="0.8" opacity="0.4" />
    </svg>
  );
}

function Footer() {
  return (
    <footer style={{
      borderTop: "1px solid var(--border)",
      padding: "48px 48px 32px",
      marginTop: 80,
    }}>
      <div style={{
        maxWidth: 1200,
        margin: "0 auto",
        display: "grid",
        gridTemplateColumns: "1fr 1fr 1fr",
        gap: 48,
      }}>
        <div>
          <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 12, color: "var(--neon)", marginBottom: 12, letterSpacing: "0.1em" }}>PRISM</div>
          <p style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.7 }}>
            Open connector format for velocity signal engines.
          </p>
        </div>
        <div>
          <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 11, color: "var(--text-tertiary)", marginBottom: 12, letterSpacing: "0.1em" }}>LINKS</div>
          {[
            { label: "GitHub", href: "https://github.com/arpjw/prism" },
            { label: "Contributing", href: "/docs" },
            { label: "Issues", href: "https://github.com/arpjw/prism/issues" },
          ].map(({ label, href }) => (
            <div key={label} style={{ marginBottom: 6 }}>
              <a href={href} style={{ fontSize: 13, color: "var(--text-secondary)" }}>{label}</a>
            </div>
          ))}
        </div>
        <div>
          <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 11, color: "var(--text-tertiary)", marginBottom: 12, letterSpacing: "0.1em" }}>PACKAGE</div>
          <a href="https://pypi.org/project/prism-signal/" style={{ fontSize: 13, color: "var(--text-secondary)", display: "block", marginBottom: 6 }}>
            prism-signal on PyPI
          </a>
          <a href="https://aryasomu.com" style={{ fontSize: 13, color: "var(--text-secondary)", display: "block" }}>
            arpjw.com
          </a>
        </div>
      </div>
      <div style={{
        maxWidth: 1200,
        margin: "32px auto 0",
        paddingTop: 24,
        borderTop: "1px solid var(--border)",
        fontFamily: "'DM Mono', monospace",
        fontSize: 11,
        color: "var(--text-tertiary)",
      }}>
        MIT License — © 2026 Arya Somu
      </div>
    </footer>
  );
}
