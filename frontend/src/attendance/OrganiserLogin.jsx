import { useState } from "react";

function OrganiserLogin({ onLoginSuccess }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = await fetch("/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ username, password }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Invalid username or password");
      }

      localStorage.setItem("organiser_token", data.access_token);
      if (onLoginSuccess) {
        onLoginSuccess(data.access_token);
      }
    } catch (err) {
      setError(err.message || "Unable to sign in. Please check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.page}>
      <div style={styles.container}>
        {/* Apple-style minimalist monochrome header */}
        <div style={styles.header}>
          <div style={styles.logoMark}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
              <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
            </svg>
          </div>
          <h1 style={styles.title}>Turing Check-in</h1>
          <p style={styles.subtitle}>Sign in with your organiser handle</p>
        </div>

        {error && (
          <div role="alert" style={styles.errorBox}>
            {error}
          </div>
        )}

        <form onSubmit={handleLogin} style={styles.form}>
          <div style={styles.inputGroup}>
            <label htmlFor="username" style={styles.label}>
              Organiser handle
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="lead@ttc (e.g. techlead@ttc)"
              required
              style={styles.input}
              autoComplete="username"
            />
          </div>

          <div style={styles.inputGroup}>
            <div style={styles.labelRow}>
              <label htmlFor="password" style={styles.label}>
                Password
              </label>
            </div>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
              required
              style={styles.input}
              autoComplete="current-password"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            style={loading ? { ...styles.button, opacity: 0.6 } : styles.button}
          >
            {loading ? "Signing in..." : "Continue"}
          </button>
        </form>

        <p style={styles.footerNote}>
          Restricted to accredited club leads (e.g. techlead@ttc, president@ttc)
        </p>
      </div>
    </div>
  );
}

const styles = {
  page: {
    minHeight: "100vh",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#000000",
    color: "#f5f5f7",
    fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Text', 'SF Pro Icons', 'Helvetica Neue', Helvetica, Arial, sans-serif",
    padding: "24px",
    WebkitFontSmoothing: "antialiased",
  },
  container: {
    width: "100%",
    maxWidth: "360px",
    display: "flex",
    flexDirection: "column",
  },
  header: {
    textAlign: "center",
    marginBottom: "32px",
  },
  logoMark: {
    width: "44px",
    height: "44px",
    margin: "0 auto 16px",
    borderRadius: "12px",
    backgroundColor: "#161617",
    border: "1px solid #2a2a2c",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    color: "#ffffff",
  },
  title: {
    margin: "0 0 6px",
    fontSize: "24px",
    fontWeight: "600",
    letterSpacing: "-0.02em",
    color: "#ffffff",
  },
  subtitle: {
    margin: 0,
    fontSize: "14px",
    color: "#86868b",
    letterSpacing: "-0.01em",
  },
  errorBox: {
    padding: "12px 14px",
    backgroundColor: "#1c1c1e",
    border: "1px solid #3a3a3c",
    borderRadius: "10px",
    color: "#f5f5f7",
    fontSize: "13px",
    marginBottom: "20px",
    textAlign: "center",
  },
  form: {
    display: "flex",
    flexDirection: "column",
    gap: "18px",
  },
  inputGroup: {
    display: "flex",
    flexDirection: "column",
    gap: "6px",
  },
  labelRow: {
    display: "flex",
    justifyContent: "space-between",
  },
  label: {
    fontSize: "12px",
    fontWeight: "500",
    color: "#a1a1a6",
  },
  input: {
    width: "100%",
    padding: "12px 14px",
    backgroundColor: "#161617",
    border: "1px solid #2c2c2e",
    borderRadius: "10px",
    color: "#ffffff",
    fontSize: "15px",
    outline: "none",
    boxSizing: "border-box",
    transition: "border-color 0.15s ease",
  },
  button: {
    width: "100%",
    padding: "13px",
    marginTop: "8px",
    backgroundColor: "#ffffff",
    color: "#000000",
    border: "none",
    borderRadius: "10px",
    fontSize: "14px",
    fontWeight: "600",
    letterSpacing: "-0.01em",
    cursor: "pointer",
    transition: "background-color 0.15s ease, opacity 0.15s ease",
  },
  footerNote: {
    marginTop: "32px",
    textAlign: "center",
    fontSize: "12px",
    color: "#6e6e73",
  },
};

export default OrganiserLogin;
