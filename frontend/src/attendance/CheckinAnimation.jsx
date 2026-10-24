import { useEffect, useState } from "react";

function CheckinAnimation({ type, name, onClose }) {
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setVisible(false);
      if (onClose) onClose();
    }, 1500);

    return () => clearTimeout(timer);
  }, [onClose]);

  if (!visible) return null;

  const isSuccess = type === "success";

  return (
    <div style={styles.overlay}>
      <div style={styles.modal}>
        {/* Animated Circle Icon */}
        <div
          style={{
            ...styles.circle,
            backgroundColor: isSuccess ? "#10b981" : "#ef4444",
            boxShadow: isSuccess
              ? "0 0 35px rgba(16, 185, 129, 0.6)"
              : "0 0 35px rgba(239, 68, 68, 0.6)",
          }}
        >
          {isSuccess ? (
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#ffffff" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="20 6 9 17 4 12" />
            </svg>
          ) : (
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#ffffff" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          )}
        </div>

        <div style={styles.title}>
          {isSuccess ? "ADMITTED" : "REJECTED"}
        </div>

        {name && <div style={styles.subtitle}>{name}</div>}
      </div>
    </div>
  );
}

const styles = {
  overlay: {
    position: "fixed",
    inset: 0,
    zIndex: 9999,
    backgroundColor: "rgba(0, 0, 0, 0.75)",
    backdropFilter: "blur(8px)",
    WebkitBackdropFilter: "blur(8px)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    animation: "fadeIn 0.15s ease",
  },
  modal: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    transform: "scale(1)",
    animation: "popIn 0.25s cubic-bezier(0.175, 0.885, 0.32, 1.275)",
  },
  circle: {
    width: "90px",
    height: "90px",
    borderRadius: "50%",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    marginBottom: "16px",
  },
  title: {
    fontSize: "22px",
    fontWeight: "800",
    color: "#ffffff",
    letterSpacing: "1.5px",
    textTransform: "uppercase",
  },
  subtitle: {
    fontSize: "16px",
    fontWeight: "600",
    color: "#a1a1a6",
    marginTop: "6px",
    maxWidth: "300px",
    textAlign: "center",
  },
};

export default CheckinAnimation;
