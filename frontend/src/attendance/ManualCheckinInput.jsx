import { useState } from "react";

function ManualCheckinInput({ token, onCheckinComplete, disabled }) {
  const [registrationId, setRegistrationId] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const cleanId = registrationId.trim();
    if (!cleanId) return;

    setLoading(true);

    try {
      const response = await fetch("/attendance/manual-checkin", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ registration_id: cleanId }),
      });

      const data = await response.json();

      if (!response.ok) {
        onCheckinComplete({
          type: "error",
          message: data.detail || "Registration identifier not found",
        });
        return;
      }

      if (data.status === "checked_in" && data.method !== "manual") {
        onCheckinComplete({
          type: "already_checked_in",
          message: `This attendee was previously checked in via ${data.method ? data.method.toUpperCase() : "scanner"}.`,
          data,
        });
      } else {
        onCheckinComplete({
          type: "success",
          message: "Check-in recorded successfully.",
          data,
        });
        setRegistrationId("");
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
          value={registrationId}
          onChange={(e) => setRegistrationId(e.target.value)}
          placeholder="Registration UUID"
          disabled={loading || disabled}
          style={styles.input}
          aria-label="Registration ID"
        />
        <button
          type="submit"
          disabled={loading || disabled || !registrationId.trim()}
          style={
            loading || disabled || !registrationId.trim()
              ? { ...styles.button, opacity: 0.4, cursor: "not-allowed" }
              : styles.button
          }
        >
          {loading ? "Checking in..." : "Check In"}
        </button>
      </div>
    </form>
  );
}

const styles = {
  form: {
    width: "100%",
  },
  row: {
    display: "flex",
    gap: "10px",
  },
  input: {
    flex: 1,
    padding: "11px 14px",
    backgroundColor: "#161617",
    border: "1px solid #2c2c2e",
    borderRadius: "10px",
    color: "#ffffff",
    fontSize: "14px",
    fontFamily: "ui-monospace, monospace",
    outline: "none",
  },
  button: {
    padding: "11px 20px",
    backgroundColor: "#ffffff",
    color: "#000000",
    border: "none",
    borderRadius: "10px",
    fontSize: "13px",
    fontWeight: "600",
    cursor: "pointer",
    whiteSpace: "nowrap",
  },
};

export default ManualCheckinInput;
