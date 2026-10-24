import { useCallback, useEffect, useState } from "react";
import ManualCheckinInput from "./ManualCheckinInput";
import QRScanner from "./QRScanner";
import ResultDisplay from "./ResultDisplay";

function AttendanceDashboard({ token, onLogout }) {
  const [activeTab, setActiveTab] = useState("scan");
  const [eventId, setEventId] = useState("");
  const [summary, setSummary] = useState(null);
  const [attendees, setAttendees] = useState([]);
  const [filter, setFilter] = useState("all");
  const [searchTerm, setSearchTerm] = useState("");
  const [lastResult, setLastResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchDashboardData = useCallback(async () => {
    if (!eventId.trim()) return;
    setLoading(true);
    setError("");

    try {
      const [sumRes, listRes] = await Promise.all([
        fetch(`/attendance/summary?event_id=${eventId.trim()}`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        fetch(`/attendance/list?event_id=${eventId.trim()}`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
      ]);

      if (sumRes.status === 401 || listRes.status === 401) {
        onLogout();
        return;
      }

      if (!sumRes.ok || !listRes.ok) {
        throw new Error("Unable to retrieve event attendance records");
      }

      const sumData = await sumRes.json();
      const listData = await listRes.json();

      setSummary(sumData);
      setAttendees(listData);
    } catch (err) {
      setError(err.message || "Failed to load dashboard data");
    } finally {
      setLoading(false);
    }
  }, [eventId, token, onLogout]);

  useEffect(() => {
    if (eventId.trim()) {
      fetchDashboardData();
    }
  }, [eventId, fetchDashboardData]);

  const handleCheckinComplete = (result) => {
    setLastResult(result);
    if (result.type === "success") {
      fetchDashboardData();
    }
  };

  const filteredAttendees = attendees.filter((item) => {
    if (filter !== "all" && item.status !== filter) return false;
    if (!searchTerm.trim()) return true;

    const term = searchTerm.toLowerCase();
    const idMatch = item.registration_id.toLowerCase().includes(term);
    const teamMatch = item.team_name?.toLowerCase().includes(term);
    const nameMatch = item.participant_names?.some((name) =>
      name.toLowerCase().includes(term)
    );

    return idMatch || teamMatch || nameMatch;
  });

  return (
    <div style={styles.page}>
      {/* Apple-style clean minimal navbar */}
      <nav style={styles.navBar}>
        <div style={styles.navInner}>
          <div style={styles.navBrand}>
            <span style={styles.brandTitle}>Turing Check-in</span>
            <span style={styles.brandDivider}>/</span>
            <span style={styles.brandSub}>Organiser Desk</span>
          </div>

          <button onClick={onLogout} style={styles.signOutBtn}>
            Sign Out
          </button>
        </div>
      </nav>

      <main style={styles.main}>
        {/* Event Setup & Headline Metrics */}
        <section style={styles.section}>
          <div style={styles.eventRow}>
            <input
              id="event-id-input"
              type="text"
              value={eventId}
              onChange={(e) => setEventId(e.target.value)}
              placeholder="Enter Event UUID to load records"
              style={styles.eventInput}
            />
            <button
              onClick={fetchDashboardData}
              disabled={loading || !eventId.trim()}
              style={styles.refreshBtn}
            >
              {loading ? "Refreshing" : "Refresh"}
            </button>
          </div>

          {error && <div style={styles.errorNotice}>{error}</div>}

          {summary && (
            <div style={styles.statsGrid}>
              <div style={styles.statCard}>
                <span style={styles.statLabel}>Registered</span>
                <span style={styles.statNum}>{summary.total_registered}</span>
              </div>
              <div style={styles.statCard}>
                <span style={styles.statLabel}>Checked in</span>
                <span style={styles.statNum}>{summary.checked_in}</span>
              </div>
              <div style={styles.statCard}>
                <span style={styles.statLabel}>Remaining</span>
                <span style={styles.statNum}>{summary.remaining}</span>
              </div>
            </div>
          )}
        </section>

        {/* Check-in Module: Scanner & Manual */}
        <section style={styles.section}>
          <div style={styles.segmentedControl}>
            <button
              onClick={() => setActiveTab("scan")}
              style={{
                ...styles.segmentBtn,
                ...(activeTab === "scan" ? styles.segmentBtnActive : {}),
              }}
            >
              QR Scanner
            </button>
            <button
              onClick={() => setActiveTab("manual")}
              style={{
                ...styles.segmentBtn,
                ...(activeTab === "manual" ? styles.segmentBtnActive : {}),
              }}
            >
              Manual Entry
            </button>
          </div>

          <div style={styles.actionBody}>
            {activeTab === "scan" ? (
              <QRScanner
                token={token}
                onScanComplete={handleCheckinComplete}
                disabled={!eventId.trim()}
              />
            ) : (
              <ManualCheckinInput
                token={token}
                onCheckinComplete={handleCheckinComplete}
                disabled={!eventId.trim()}
              />
            )}
          </div>

          <ResultDisplay
            result={lastResult}
            onClear={() => setLastResult(null)}
          />
        </section>

        {/* Registrations List */}
        <section style={styles.section}>
          <div style={styles.tableHeaderBar}>
            <div style={styles.filterPills}>
              <button
                onClick={() => setFilter("all")}
                style={filter === "all" ? styles.pillActive : styles.pill}
              >
                All ({attendees.length})
              </button>
              <button
                onClick={() => setFilter("checked_in")}
                style={filter === "checked_in" ? styles.pillActive : styles.pill}
              >
                Checked In
              </button>
              <button
                onClick={() => setFilter("not_checked_in")}
                style={filter === "not_checked_in" ? styles.pillActive : styles.pill}
              >
                Remaining
              </button>
            </div>

            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search registrant or team"
              style={styles.searchInput}
            />
          </div>

          <div style={styles.tableWrapper}>
            <table style={styles.table}>
              <thead>
                <tr>
                  <th style={styles.th}>Registration</th>
                  <th style={styles.th}>Participant / Team</th>
                  <th style={styles.th}>Status</th>
                  <th style={styles.th}>Method</th>
                  <th style={styles.th}>Checked At</th>
                </tr>
              </thead>
              <tbody>
                {filteredAttendees.length === 0 ? (
                  <tr>
                    <td colSpan={5} style={styles.emptyState}>
                      {eventId
                        ? "No matching records found."
                        : "Enter an Event UUID above to display the attendee roster."}
                    </td>
                  </tr>
                ) : (
                  filteredAttendees.map((att) => (
                    <tr key={att.registration_id} style={styles.tr}>
                      <td style={styles.tdMono}>{att.registration_id}</td>
                      <td style={styles.td}>
                        {att.team_name ? (
                          <span>
                            <strong>{att.team_name}</strong> — {att.participant_names?.join(", ")}
                          </span>
                        ) : (
                          <span>{att.participant_names?.join(", ") || "—"}</span>
                        )}
                      </td>
                      <td style={styles.td}>
                        <span
                          style={
                            att.status === "checked_in"
                              ? styles.badgeChecked
                              : styles.badgeUnchecked
                          }
                        >
                          {att.status === "checked_in" ? "Checked in" : "Pending"}
                        </span>
                      </td>
                      <td style={styles.tdMethod}>
                        {att.method ? att.method.toUpperCase() : "—"}
                      </td>
                      <td style={styles.tdTime}>
                        {att.checked_in_at
                          ? new Date(att.checked_in_at).toLocaleTimeString([], {
                              hour: "2-digit",
                              minute: "2-digit",
                            })
                          : "—"}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>
      </main>
    </div>
  );
}

const styles = {
  page: {
    minHeight: "100vh",
    backgroundColor: "#000000",
    color: "#f5f5f7",
    fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Text', 'SF Pro Icons', 'Helvetica Neue', Helvetica, Arial, sans-serif",
    WebkitFontSmoothing: "antialiased",
  },
  navBar: {
    borderBottom: "1px solid #1d1d1f",
    backgroundColor: "rgba(0, 0, 0, 0.8)",
    backdropFilter: "saturate(180%) blur(20px)",
    position: "sticky",
    top: 0,
    zIndex: 10,
  },
  navInner: {
    maxWidth: "960px",
    margin: "0 auto",
    padding: "16px 24px",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  navBrand: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
  },
  brandTitle: {
    fontSize: "15px",
    fontWeight: "600",
    color: "#ffffff",
    letterSpacing: "-0.01em",
  },
  brandDivider: {
    color: "#424245",
  },
  brandSub: {
    fontSize: "13px",
    color: "#86868b",
  },
  signOutBtn: {
    backgroundColor: "transparent",
    color: "#86868b",
    border: "none",
    fontSize: "13px",
    cursor: "pointer",
    padding: "6px 10px",
    borderRadius: "6px",
    transition: "color 0.15s ease",
  },
  main: {
    maxWidth: "960px",
    margin: "0 auto",
    padding: "32px 24px",
    display: "flex",
    flexDirection: "column",
    gap: "24px",
  },
  section: {
    backgroundColor: "#161617",
    border: "1px solid #242426",
    borderRadius: "16px",
    padding: "24px",
  },
  eventRow: {
    display: "flex",
    gap: "10px",
  },
  eventInput: {
    flex: 1,
    padding: "12px 16px",
    backgroundColor: "#0a0a0a",
    border: "1px solid #2a2a2c",
    borderRadius: "10px",
    color: "#ffffff",
    fontSize: "14px",
    fontFamily: "ui-monospace, monospace",
    outline: "none",
  },
  refreshBtn: {
    padding: "12px 20px",
    backgroundColor: "#2c2c2e",
    color: "#ffffff",
    border: "none",
    borderRadius: "10px",
    fontSize: "13px",
    fontWeight: "600",
    cursor: "pointer",
  },
  errorNotice: {
    marginTop: "12px",
    padding: "10px 14px",
    backgroundColor: "#1c1c1e",
    border: "1px solid #3a3a3c",
    borderRadius: "8px",
    fontSize: "13px",
    color: "#f5f5f7",
  },
  statsGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(3, 1fr)",
    gap: "16px",
    marginTop: "24px",
  },
  statCard: {
    backgroundColor: "#0a0a0a",
    border: "1px solid #222224",
    borderRadius: "12px",
    padding: "20px",
    display: "flex",
    flexDirection: "column",
    gap: "4px",
  },
  statLabel: {
    fontSize: "13px",
    color: "#86868b",
  },
  statNum: {
    fontSize: "32px",
    fontWeight: "600",
    color: "#ffffff",
    letterSpacing: "-0.02em",
  },
  segmentedControl: {
    display: "inline-flex",
    backgroundColor: "#0a0a0a",
    padding: "3px",
    borderRadius: "10px",
    border: "1px solid #222224",
    marginBottom: "20px",
  },
  segmentBtn: {
    padding: "8px 18px",
    backgroundColor: "transparent",
    color: "#86868b",
    border: "none",
    borderRadius: "8px",
    fontSize: "13px",
    fontWeight: "500",
    cursor: "pointer",
    transition: "all 0.15s ease",
  },
  segmentBtnActive: {
    backgroundColor: "#242426",
    color: "#ffffff",
    fontWeight: "600",
  },
  actionBody: {
    minHeight: "60px",
  },
  tableHeaderBar: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: "12px",
    flexWrap: "wrap",
    marginBottom: "20px",
  },
  filterPills: {
    display: "flex",
    gap: "8px",
  },
  pill: {
    backgroundColor: "#0a0a0a",
    border: "1px solid #222224",
    color: "#86868b",
    padding: "6px 14px",
    borderRadius: "8px",
    fontSize: "12px",
    cursor: "pointer",
  },
  pillActive: {
    backgroundColor: "#ffffff",
    border: "1px solid #ffffff",
    color: "#000000",
    padding: "6px 14px",
    borderRadius: "8px",
    fontSize: "12px",
    fontWeight: "600",
    cursor: "pointer",
  },
  searchInput: {
    padding: "8px 14px",
    backgroundColor: "#0a0a0a",
    border: "1px solid #2a2a2c",
    borderRadius: "8px",
    color: "#ffffff",
    fontSize: "13px",
    outline: "none",
    minWidth: "220px",
  },
  tableWrapper: {
    overflowX: "auto",
  },
  table: {
    width: "100%",
    borderCollapse: "collapse",
    fontSize: "13px",
  },
  th: {
    textAlign: "left",
    padding: "12px 14px",
    fontSize: "12px",
    fontWeight: "500",
    color: "#86868b",
    borderBottom: "1px solid #242426",
  },
  tr: {
    borderBottom: "1px solid #1c1c1e",
  },
  td: {
    padding: "14px",
    color: "#f5f5f7",
  },
  tdMono: {
    padding: "14px",
    color: "#a1a1a6",
    fontFamily: "ui-monospace, monospace",
    fontSize: "12px",
  },
  tdMethod: {
    padding: "14px",
    color: "#86868b",
    fontSize: "12px",
  },
  tdTime: {
    padding: "14px",
    color: "#86868b",
    fontSize: "12px",
  },
  badgeChecked: {
    backgroundColor: "#ffffff",
    color: "#000000",
    padding: "4px 8px",
    borderRadius: "6px",
    fontSize: "11px",
    fontWeight: "600",
  },
  badgeUnchecked: {
    backgroundColor: "#242426",
    color: "#86868b",
    padding: "4px 8px",
    borderRadius: "6px",
    fontSize: "11px",
  },
  emptyState: {
    padding: "36px",
    textAlign: "center",
    color: "#6e6e73",
    fontSize: "13px",
  },
};

export default AttendanceDashboard;
