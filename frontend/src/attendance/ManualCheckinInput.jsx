import { useState } from "react";

function ManualCheckinInput({ token, onCheckinComplete, disabled }) {
  const [ticketInput, setTicketInput] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const cleanCode = ticketInput.trim();
    if (!cleanCode) return;

    setLoading(true);

    try {
      const response = await fetch("/attendance/manual-checkin", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ registration_id: cleanCode }),
      });

      const data = await response.json();

      if (!response.ok) {
        onCheckinComplete({
          type: "error",
          message: data.detail || `Ticket '${cleanCode}' not found`,
        });
        return;
      }

      if (data.status === "checked_in" && data.method !== "manual") {
        onCheckinComplete({
          type: "already_checked_in",
          message: `Ticket already checked in earlier via ${data.method ? data.method.toUpperCase() : "scanner"}.`,
          data,
        });
      } else {
        onCheckinComplete({
          type: "success",
          message: `Ticket ${cleanCode.toUpperCase()} admitted successfully.`,
          data,
        });
        setTicketInput("");
      }
    } catch (err) {
      onCheckinComplete({
        type: "error",
        message: err.message || "Network error. Please try again.",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} style={styles.form}>
      <div style={styles.row}>
        <input
          type="text"
          value={ticketInput}
          onChange={(e) => setTicketInput(e.target.value.toUpperCase())}
          placeholder="Code (e.g. TTC-8K1M) or UUID"
          disabled={loading || disabled}
          style={styles.input}
          aria-label="Ticket Code"
          autoCapitalize="characters"
          autoCorrect="off"
        />
        <button
          type="submit"
          disabled={loading || disabled || !ticketInput.trim()}
          style={
            loading || disabled || !ticketInput.trim()
              ? { ...styles.button, opacity: 0.4, cursor: "not-allowed" }
              : styles.button
          }
        >
          {loading ? "Checking..." : "Admit"}
        </button>
      </div>
    </form>
  );
}

const styles = {
  form: {
    width: "100%",
    maxWidth: "500px",
    margin: "0 auto",
  },
  row: {
    display: "flex",
    gap: "8px",
    width: "100%",
  },
  input: {
    flex: 1,
    minWidth: 0,
    padding: "14px",
    backgroundColor: "#161617",
    border: "1px solid #2c2c2e",
    borderRadius: "12px",
    color: "#ffffff",
    fontSize: "16px", // 16px prevents iOS Safari auto-zoom
    fontFamily: "ui-monospace, monospace",
    letterSpacing: "1px",
    fontWeight: "600",
    outline: "none",
    boxSizing: "border-box",
  },
  button: {
    padding: "14px 20px",
    backgroundColor: "#ffffff",
    color: "#000000",
    border: "none",
    borderRadius: "12px",
    fontSize: "14px",
    fontWeight: "600",
    cursor: "pointer",
    whiteSpace: "nowrap",
  },
};

export default ManualCheckinInput;
