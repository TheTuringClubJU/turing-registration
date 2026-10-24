export default function ConfirmationScreen({ registration, event }) {
  return (
    <section role="status" style={{ textAlign: "center", padding: "40px 20px" }}>
      <p style={{ letterSpacing: "0.1em", fontSize: "12px", color: "#86868b", textTransform: "uppercase" }}>
        REGISTRATION CONFIRMED
      </p>
      <h1 style={{ fontSize: "2rem", margin: "8px 0 16px" }}>You're registered.</h1>
      <p style={{ color: "#a1a1a6", maxWidth: "480px", margin: "0 auto 24px" }}>
        Your place at <strong>{event.name}</strong> is confirmed. Present your ticket code or QR at the registration desk for check-in.
      </p>

      {registration.ticket_code && (
        <div style={{ margin: "24px auto", background: "#161617", border: "1px solid #242426", borderRadius: "12px", padding: "16px", maxWidth: "280px" }}>
          <p style={{ fontSize: "11px", color: "#86868b", margin: "0 0 6px", textTransform: "uppercase" }}>Short Ticket Code</p>
          <p style={{ fontFamily: "monospace", fontSize: "24px", fontWeight: "bold", letterSpacing: "2px", color: "#ffffff", margin: 0 }}>
            {registration.ticket_code}
          </p>
        </div>
      )}

      <div style={{ margin: "16px auto", color: "#6e6e73", fontSize: "12px" }}>
        <span>Registration ID: </span>
        <code style={{ fontFamily: "monospace" }}>{registration.id}</code>
      </div>

      <p style={{ color: "#86868b", fontSize: "14px", marginTop: "24px" }}>
        Check your inbox for confirmation details from the organisers.
      </p>
      <div style={{ marginTop: "32px" }}>
        <a href="/" style={{ color: "#2997ff", textDecoration: "none", fontSize: "14px" }}>
          ← Back to check-in dashboard
        </a>
      </div>
    </section>
  );
}
