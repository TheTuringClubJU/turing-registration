function ResultDisplay({ result, onClear }) {
  if (!result) return null;

  const isSuccess = result.type === "success";
  const isAlreadyCheckedIn = result.type === "already_checked_in";

  return (
    <div role="status" style={styles.card}>
      <div style={styles.header}>
        <div style={styles.statusRow}>
          <span style={styles.bullet}>•</span>
          <span style={styles.title}>
            {isSuccess
              ? "Checked in"
              : isAlreadyCheckedIn
              ? "Already checked in"
              : "Check-in unsuccessful"}
          </span>
        </div>
        {onClear && (
          <button onClick={onClear} style={styles.dismissBtn} title="Dismiss">
            Dismiss
          </button>
        )}
      </div>

      <p style={styles.message}>{result.message}</p>

      {result.data && (
        <div style={styles.metaBox}>
          <div style={styles.metaRow}>
            <span style={styles.metaLabel}>ID</span>
            <span style={styles.metaVal}>{result.data.registration_id}</span>
          </div>
          {result.data.method && (
            <div style={styles.metaRow}>
              <span style={styles.metaLabel}>Method</span>
              <span style={styles.metaVal}>{result.data.method.toUpperCase()}</span>
            </div>
          )}
          {result.data.checked_in_at && (
            <div style={styles.metaRow}>
              <span style={styles.metaLabel}>Timestamp</span>
              <span style={styles.metaVal}>
                {new Date(result.data.checked_in_at).toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                  second: "2-digit",
                })}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

const styles = {
  card: {
    backgroundColor: "#161617",
    border: "1px solid #2c2c2e",
    borderRadius: "12px",
    padding: "16px 18px",
    marginTop: "16px",
    marginBottom: "8px",
    fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Text', sans-serif",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "6px",
  },
  statusRow: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
  },
  bullet: {
    color: "#ffffff",
    fontSize: "14px",
  },
  title: {
    fontSize: "14px",
    fontWeight: "600",
    color: "#ffffff",
    letterSpacing: "-0.01em",
  },
  dismissBtn: {
    background: "transparent",
    border: "none",
    color: "#86868b",
    fontSize: "12px",
    cursor: "pointer",
    padding: "2px 6px",
  },
  message: {
    margin: "0 0 12px 0",
    color: "#a1a1a6",
    fontSize: "13px",
    lineHeight: "1.4",
  },
  metaBox: {
    borderTop: "1px solid #222224",
    paddingTop: "10px",
    display: "flex",
    flexDirection: "column",
    gap: "6px",
  },
  metaRow: {
    display: "flex",
    justifyContent: "space-between",
    fontSize: "12px",
  },
  metaLabel: {
    color: "#6e6e73",
  },
  metaVal: {
    color: "#f5f5f7",
    fontFamily: "ui-monospace, monospace",
  },
};

export default ResultDisplay;
