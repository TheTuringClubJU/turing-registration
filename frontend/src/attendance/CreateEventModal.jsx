import React, { useState } from "react";

export default function CreateEventModal({ isOpen, onClose, token, onEventCreated }) {
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [type, setType] = useState("workshop");
  const [minTeamSize, setMinTeamSize] = useState(1);
  const [maxTeamSize, setMaxTeamSize] = useState(1);
  const [isActive, setIsActive] = useState(false);
  const [regOpenAt, setRegOpenAt] = useState(() => {
    const d = new Date();
    d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
    return d.toISOString().slice(0, 16);
  });
  const [regCloseAt, setRegCloseAt] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  if (!isOpen) return null;

  const handleNameChange = (e) => {
    const val = e.target.value;
    setName(val);
    const generatedSlug = val
      .toLowerCase()
      .trim()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "");
    setSlug(generatedSlug);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!name.trim()) {
      setError("Event name is required");
      return;
    }
    if (!slug.trim()) {
      setError("Slug is required");
      return;
    }
    if (slug.trim().toLowerCase() === "active") {
      setError("'active' is a reserved slug. Choose another slug.");
      return;
    }
    if (minTeamSize > maxTeamSize) {
      setError("Min team size cannot exceed Max team size");
      return;
    }
    if (regCloseAt && new Date(regCloseAt) <= new Date(regOpenAt)) {
      setError("Registration close time must be after opening time");
      return;
    }

    setSubmitting(true);

    try {
      const payload = {
        name: name.trim(),
        slug: slug.trim(),
        type,
        min_team_size: parseInt(minTeamSize, 10),
        max_team_size: parseInt(maxTeamSize, 10),
        is_active: isActive,
        reg_open_at: new Date(regOpenAt).toISOString(),
        reg_close_at: regCloseAt ? new Date(regCloseAt).toISOString() : null,
      };

      const res = await fetch("/events", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Failed to create event");
      }

      onEventCreated(data);
      onClose();
    } catch (err) {
      setError(err.message || "An unexpected error occurred");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={styles.overlay} onClick={onClose} role="dialog" aria-modal="true">
      <div style={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div style={styles.header}>
          <div>
            <h2 style={styles.title}>Create New Event</h2>
            <p style={styles.subtitle}>Configure event parameters, team sizing, and registration window.</p>
          </div>
          <button style={styles.closeBtn} onClick={onClose} type="button" aria-label="Close modal">
            ✕
          </button>
        </div>

        {error && <div style={styles.errorBox}>{error}</div>}

        <form onSubmit={handleSubmit} style={styles.form}>
          <div style={styles.fieldGroup}>
            <label htmlFor="event-name" style={styles.label}>Event Name *</label>
            <input
              id="event-name"
              type="text"
              placeholder="e.g. Turing Live Workshop 2026"
              value={name}
              onChange={handleNameChange}
              required
              style={styles.input}
            />
          </div>

          <div style={styles.fieldRow}>
            <div style={styles.fieldHalf}>
              <label htmlFor="event-slug" style={styles.label}>Event Slug (URL identifier) *</label>
              <input
                id="event-slug"
                type="text"
                placeholder="e.g. turing-live-workshop"
                value={slug}
                onChange={(e) => setSlug(e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, ""))}
                required
                style={styles.input}
              />
            </div>
            <div style={styles.fieldHalf}>
              <label htmlFor="event-type" style={styles.label}>Event Type *</label>
              <select
                id="event-type"
                value={type}
                onChange={(e) => setType(e.target.value)}
                style={styles.select}
              >
                <option value="workshop">Workshop</option>
                <option value="hackathon">Hackathon</option>
                <option value="seminar">Seminar</option>
                <option value="tech_event">Tech Event</option>
                <option value="other">Other</option>
              </select>
            </div>
          </div>

          <div style={styles.fieldRow}>
            <div style={styles.fieldHalf}>
              <label htmlFor="min-team-size" style={styles.label}>Min Team Size (1 - 4) *</label>
              <input
                id="min-team-size"
                type="number"
                min="1"
                max="4"
                value={minTeamSize}
                onChange={(e) => setMinTeamSize(Number(e.target.value))}
                required
                style={styles.input}
              />
            </div>
            <div style={styles.fieldHalf}>
              <label htmlFor="max-team-size" style={styles.label}>Max Team Size (1 - 4) *</label>
              <input
                id="max-team-size"
                type="number"
                min="1"
                max="4"
                value={maxTeamSize}
                onChange={(e) => setMaxTeamSize(Number(e.target.value))}
                required
                style={styles.input}
              />
            </div>
          </div>

          <div style={styles.fieldRow}>
            <div style={styles.fieldHalf}>
              <label htmlFor="reg-open-at" style={styles.label}>Registration Open At *</label>
              <input
                id="reg-open-at"
                type="datetime-local"
                value={regOpenAt}
                onChange={(e) => setRegOpenAt(e.target.value)}
                required
                style={styles.input}
              />
            </div>
            <div style={styles.fieldHalf}>
              <label htmlFor="reg-close-at" style={styles.label}>Registration Close At (Optional)</label>
              <input
                id="reg-close-at"
                type="datetime-local"
                value={regCloseAt}
                onChange={(e) => setRegCloseAt(e.target.value)}
                style={styles.input}
              />
            </div>
          </div>

          <div style={styles.checkboxRow}>
            <label style={styles.checkboxLabel}>
              <input
                type="checkbox"
                checked={isActive}
                onChange={(e) => setIsActive(e.target.checked)}
                style={styles.checkbox}
              />
              <span>Set as Active Event (Note: Only one event can be active at a time)</span>
            </label>
          </div>

          <div style={styles.footer}>
            <button
              type="button"
              onClick={onClose}
              disabled={submitting}
              style={styles.cancelBtn}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              style={styles.submitBtn}
            >
              {submitting ? "Creating..." : "Create Event"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

const styles = {
  overlay: {
    position: "fixed",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: "rgba(0, 0, 0, 0.75)",
    backdropFilter: "blur(8px)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    zIndex: 9999,
    padding: "16px",
  },
  modal: {
    backgroundColor: "#161617",
    border: "1px solid #2d2d2d",
    borderRadius: "16px",
    width: "100%",
    maxWidth: "560px",
    maxHeight: "90vh",
    overflowY: "auto",
    padding: "28px",
    boxShadow: "0 24px 48px rgba(0, 0, 0, 0.6)",
    color: "#ffffff",
    fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Display', Roboto, sans-serif",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: "20px",
  },
  title: {
    fontSize: "20px",
    fontWeight: "600",
    color: "#ffffff",
    margin: "0 0 6px 0",
    letterSpacing: "-0.01em",
  },
  subtitle: {
    fontSize: "13px",
    color: "#86868b",
    margin: 0,
  },
  closeBtn: {
    background: "transparent",
    border: "none",
    color: "#86868b",
    fontSize: "18px",
    cursor: "pointer",
    padding: "4px 8px",
    borderRadius: "6px",
    lineHeight: "1",
  },
  errorBox: {
    backgroundColor: "rgba(255, 69, 58, 0.12)",
    border: "1px solid rgba(255, 69, 58, 0.3)",
    color: "#ff453a",
    padding: "10px 14px",
    borderRadius: "8px",
    fontSize: "13px",
    marginBottom: "16px",
  },
  form: {
    display: "flex",
    flexDirection: "column",
    gap: "16px",
  },
  fieldGroup: {
    display: "flex",
    flexDirection: "column",
    gap: "6px",
  },
  fieldRow: {
    display: "flex",
    gap: "12px",
    flexWrap: "wrap",
  },
  fieldHalf: {
    flex: "1 1 calc(50% - 6px)",
    minWidth: "200px",
    display: "flex",
    flexDirection: "column",
    gap: "6px",
  },
  label: {
    fontSize: "12px",
    fontWeight: "500",
    color: "#a1a1a6",
    textTransform: "uppercase",
    letterSpacing: "0.03em",
  },
  input: {
    backgroundColor: "#0d0d0d",
    border: "1px solid #2d2d2d",
    borderRadius: "8px",
    padding: "10px 14px",
    color: "#ffffff",
    fontSize: "14px",
    outline: "none",
    transition: "border-color 0.15s ease",
    boxSizing: "border-box",
    width: "100%",
  },
  select: {
    backgroundColor: "#0d0d0d",
    border: "1px solid #2d2d2d",
    borderRadius: "8px",
    padding: "10px 14px",
    color: "#ffffff",
    fontSize: "14px",
    outline: "none",
    boxSizing: "border-box",
    width: "100%",
  },
  checkboxRow: {
    marginTop: "4px",
  },
  checkboxLabel: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    fontSize: "13px",
    color: "#a1a1a6",
    cursor: "pointer",
  },
  checkbox: {
    width: "16px",
    height: "16px",
    accentColor: "#ffffff",
    cursor: "pointer",
  },
  footer: {
    display: "flex",
    justifyContent: "flex-end",
    gap: "10px",
    marginTop: "12px",
    paddingTop: "16px",
    borderTop: "1px solid #242426",
  },
  cancelBtn: {
    backgroundColor: "transparent",
    border: "1px solid #333336",
    borderRadius: "8px",
    padding: "10px 18px",
    color: "#a1a1a6",
    fontSize: "13px",
    fontWeight: "500",
    cursor: "pointer",
  },
  submitBtn: {
    backgroundColor: "#ffffff",
    border: "none",
    borderRadius: "8px",
    padding: "10px 22px",
    color: "#000000",
    fontSize: "13px",
    fontWeight: "600",
    cursor: "pointer",
  },
};
