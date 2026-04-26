/**
 * Landing page — served at the root domain (not a character site).
 * Minimal marketing/info page.
 */

export default function LandingPage() {
  return (
    <main
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "2rem",
        fontFamily: "system-ui, sans-serif",
        background: "var(--color-background, #f8fafc)",
        color: "var(--color-text-primary, #1e293b)",
      }}
    >
      <div style={{ maxWidth: "600px", textAlign: "center" }}>
        <h1
          style={{
            fontSize: "clamp(2rem, 5vw, 3.5rem)",
            fontWeight: 700,
            marginBottom: "1rem",
            letterSpacing: "-0.02em",
          }}
        >
          Character Websites
        </h1>
        <p
          style={{
            fontSize: "1.25rem",
            color: "var(--color-text-secondary, #64748b)",
            marginBottom: "2rem",
            lineHeight: 1.6,
          }}
        >
          Your personality — rendered as a unique, AI-generated personal
          website. Every detail shaped by who you are.
        </p>
        <div
          style={{
            display: "flex",
            gap: "1rem",
            justifyContent: "center",
            flexWrap: "wrap",
          }}
        >
          <a
            href="/auth/register"
            style={{
              padding: "0.75rem 2rem",
              background: "var(--color-primary, #0f2a4a)",
              color: "#ffffff",
              borderRadius: "var(--radius-md, 8px)",
              fontWeight: 600,
              fontSize: "1rem",
              textDecoration: "none",
            }}
          >
            Loslegen
          </a>
          <a
            href="/auth/login"
            style={{
              padding: "0.75rem 2rem",
              border: "1px solid var(--color-border, #e2e8f0)",
              borderRadius: "var(--radius-md, 8px)",
              fontWeight: 600,
              fontSize: "1rem",
              textDecoration: "none",
              color: "inherit",
            }}
          >
            Anmelden
          </a>
        </div>
      </div>
    </main>
  );
}
