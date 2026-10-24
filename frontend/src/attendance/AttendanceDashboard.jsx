import { useCallback, useEffect, useState } from "react";
import CheckinAnimation from "./CheckinAnimation";
import ManualCheckinInput from "./ManualCheckinInput";
import QRScanner from "./QRScanner";
import ResultDisplay from "./ResultDisplay";

function AttendanceDashboard({ token, onLogout }) {
  const [activeTab, setActiveTab] = useState("scan");
  const [eventId, setEventId] = useState(() => localStorage.getItem("active_event_id") || "");
  const [eventName, setEventName] = useState("");
  const [summary, setSummary] = useState(null);
  const [attendees, setAttendees] = useState([]);
  const [filter, setFilter] = useState("all");
  const [searchTerm, setSearchTerm] = useState("");
  const [lastResult, setLastResult] = useState(null);
  const [animationData, setAnimationData] = useState(null);
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
        throw new Error("Unable to retrieve event records");
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

  // Fetch active event from database if no custom eventId saved
  useEffect(() => {
    async function loadActiveEvent() {
      try {
        const res = await fetch("/attendance/active-event", {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) {
          const data = await res.json();
          if (data?.id) {
            setEventName(data.name || "");
            // If nothing saved in localStorage, or saved was the old initial seed, use DB active event
            if (!localStorage.getItem("active_event_id")) {
              setEventId(data.id);
              localStorage.setItem("active_event_id", data.id);
            }
          }
        }
      } catch (e) {
        console.error("Failed to fetch active event:", e);
      }
    }
    loadActiveEvent();
  }, [token]);

  useEffect(() => {
    if (eventId.trim()) {
      localStorage.setItem("active_event_id", eventId.trim());
      fetchDashboardData();
    }
  }, [eventId, fetchDashboardData]);

  const handleCheckinComplete = (result) => {
    setLastResult(result);

    // Trigger full-screen 1.5s animation
    if (result.type === "success") {
      setAnimationData({
        type: "success",
        name: result.data?.participant_name || "",
      });
      fetchDashboardData();
    } else {
      setAnimationData({
        type: "error",
        name: result.message || "Ticket Not Admitted",
      });
    }
  };

  const filteredAttendees = attendees.filter((item) => {
    if (filter !== "all" && item.status !== filter) return false;
    if (!searchTerm.trim()) return true;

    const term = searchTerm.toLowerCase();
    const codeMatch = item.ticket_code?.toLowerCase().includes(term);
    const idMatch = item.registration_id?.toLowerCase().includes(term);
    const teamMatch = item.team_name?.toLowerCase().includes(term);
    const nameMatch =
      item.participant_name?.toLowerCase().includes(term) ||
      item.participant_names?.some((name) => name.toLowerCase().includes(term));

    return codeMatch || idMatch || teamMatch || nameMatch;
  });

  return (
    <div style={styles.page}>
      {/* 1.5s Fullscreen Visual Feedback Animation */}
      {animationData && (
        <CheckinAnimation
          type={animationData.type}
          name={animationData.name}
          onClose={() => setAnimationData(null)}
        />
      )}

      {/* Responsive Top Bar */}
      <nav style={styles.navBar}>
        <div style={styles.navInner}>
          <div style={styles.navBrand}>
            <span style={styles.brandTitle}>TTC Desk</span>
            <span style={styles.brandDivider}>/</span>
            <span style={styles.brandSub}>Check-in</span>
          </div>

          <button onClick={onLogout} style={styles.signOutBtn}>
            Sign Out
          </button>
        </div>
      </nav>

      <main style={styles.main}>
        {/* Mobile-Friendly Metrics Summary */}
        <section style={styles.section}>
          <div style={styles.eventRow}>
            <input
              id="event-id-input"
              type="text"
              value={eventId}
              onChange={(e) => setEventId(e.target.value)}
              placeholder="Event UUID"
              style={styles.eventInput}
            />
            <button
              onClick={fetchDashboardData}
              disabled={loading || !eventId.trim()}
              style={styles.refreshBtn}
            >
              {loading ? "..." : "Sync"}
            </button>
          </div>

          {error && <div style={styles.errorNotice}>{error}</div>}

          {summary && (
            <div style={styles.statsGrid}>
              <div style={styles.statCard}>
                <span style={styles.statLabel}>Total</span>
                <span style={styles.statNum}>{summary.total_registered}</span>
              </div>
              <div style={styles.statCard}>
                <span style={styles.statLabel}>Admitted</span>
                <span style={{ ...styles.statNum, color: "#ffffff" }}>
                  {summary.checked_in}
                </span>
              </div>
              <div style={styles.statCard}>
                <span style={styles.statLabel}>Pending</span>
                <span style={{ ...styles.statNum, color: "#86868b" }}>
                  {summary.remaining}
                </span>
              </div>
            </div>
          )}
        </section>

        {/* Check-in Module: Segmented Switch */}
        <section style={styles.section}>
          <div style={styles.segmentedControl}>
            <button
              onClick={() => setActiveTab("scan")}
              style={{
                ...styles.segmentBtn,
                ...(activeTab === "scan" ? styles.segmentBtnActive : {}),
              }}
            >
              Camera Scanner
            </button>
            <button
              onClick={() => setActiveTab("manual")}
              style={{
                ...styles.segmentBtn,
                ...(activeTab === "manual" ? styles.segmentBtnActive : {}),
              }}
            >
              Short Code (6-char)
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

        {/* Live Attendee Stream / Roster */}
        <section style={styles.section}>
          <div style={styles.rosterHeader}>
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
                Admitted ({attendees.filter((a) => a.status === "checked_in").length})
              </button>
              <button
                onClick={() => setFilter("not_checked_in")}
                style={filter === "not_checked_in" ? styles.pillActive : styles.pill}
              >
                Pending ({attendees.filter((a) => a.status !== "checked_in").length})
              </button>
            </div>

            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by name, team, code..."
              style={styles.searchInput}
            />
          </div>

          <div style={styles.cardsContainer}>
            {filteredAttendees.length === 0 ? (
              <div style={styles.emptyState}>No attendee records found.</div>
            ) : (
              filteredAttendees.map((att) => {
                const names =
                  att.participant_names && att.participant_names.length > 0
                    ? att.participant_names.join(" • ")
                    : att.participant_name || "Participant";

                return (
                  <div key={att.registration_id} style={styles.attendeeCard}>
                    <div style={styles.cardTop}>
                      <div style={styles.badgeCluster}>
                        <span style={styles.cardCode}>
                          {att.ticket_code || att.registration_id.slice(0, 8)}
                        </span>
                        {att.team_name ? (
                          <span style={styles.teamPill}>
                            Team: {att.team_name}
                          </span>
                        ) : (
                          <span style={styles.soloPill}>Solo Attendee</span>
                        )}
                      </div>

                      <span
                        style={
                          att.status === "checked_in"
                            ? styles.badgeChecked
                            : styles.badgeUnchecked
                        }
                      >
                        {att.status === "checked_in" ? "✓ Admitted" : "• Pending"}
                      </span>
                    </div>

                    {/* Actual Participant & Team Names */}
                    <div style={styles.personBlock}>
                      <span style={styles.personIcon}>👤</span>
                      <span style={styles.cardName}>{names}</span>
                    </div>

                    {att.checked_in_at && (
                      <div style={styles.cardMeta}>
                        Method: {att.method?.toUpperCase()} • Checked in at{" "}
                        {new Date(att.checked_in_at).toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </div>
                    )}
                  </div>
                );
              })
            )}
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
    fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Text', sans-serif",
    WebkitFontSmoothing: "antialiased",
  },
  navBar: {
    borderBottom: "1px solid #1d1d1f",
    backgroundColor: "rgba(0, 0, 0, 0.85)",
    backdropFilter: "saturate(180%) blur(20px)",
    position: "sticky",
    top: 0,
    zIndex: 10,
  },
  navInner: {
    maxWidth: "800px",
    margin: "0 auto",
    padding: "12px 16px",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  navBrand: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
  },
  brandTitle: {
    fontSize: "15px",
    fontWeight: "700",
    color: "#ffffff",
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
    padding: "6px 8px",
  },
  main: {
    maxWidth: "800px",
    margin: "0 auto",
    padding: "16px 12px 32px",
    display: "flex",
    flexDirection: "column",
    gap: "16px",
  },
  section: {
    backgroundColor: "#161617",
    border: "1px solid #242426",
    borderRadius: "16px",
    padding: "16px",
  },
  eventRow: {
    display: "flex",
    gap: "8px",
  },
  eventInput: {
    flex: 1,
    minWidth: 0,
    padding: "10px 12px",
    backgroundColor: "#0a0a0a",
    border: "1px solid #2a2a2c",
    borderRadius: "10px",
    color: "#ffffff",
    fontSize: "13px",
    fontFamily: "ui-monospace, monospace",
    outline: "none",
  },
  refreshBtn: {
    padding: "10px 16px",
    backgroundColor: "#2c2c2e",
    color: "#ffffff",
    border: "none",
    borderRadius: "10px",
    fontSize: "13px",
    fontWeight: "600",
    cursor: "pointer",
  },
  errorNotice: {
    marginTop: "10px",
    padding: "8px 12px",
    backgroundColor: "#1c1c1e",
    border: "1px solid #3a3a3c",
    borderRadius: "8px",
    fontSize: "12px",
  },
  statsGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(3, 1fr)",
    gap: "8px",
    marginTop: "16px",
  },
  statCard: {
    backgroundColor: "#0a0a0a",
    border: "1px solid #222224",
    borderRadius: "10px",
    padding: "12px",
    textAlign: "center",
  },
  statLabel: {
    fontSize: "11px",
    color: "#86868b",
    display: "block",
    marginBottom: "2px",
  },
  statNum: {
    fontSize: "24px",
    fontWeight: "700",
    color: "#ffffff",
  },
  segmentedControl: {
    display: "flex",
    backgroundColor: "#0a0a0a",
    padding: "3px",
    borderRadius: "10px",
    border: "1px solid #222224",
    marginBottom: "16px",
    width: "100%",
  },
  segmentBtn: {
    flex: 1,
    padding: "10px",
    backgroundColor: "transparent",
    color: "#86868b",
    border: "none",
    borderRadius: "8px",
    fontSize: "13px",
    fontWeight: "500",
    cursor: "pointer",
    textAlign: "center",
  },
  segmentBtnActive: {
    backgroundColor: "#242426",
    color: "#ffffff",
    fontWeight: "600",
  },
  actionBody: {
    minHeight: "60px",
  },
  rosterHeader: {
    display: "flex",
    flexDirection: "column",
    gap: "10px",
    marginBottom: "16px",
  },
  filterPills: {
    display: "flex",
    gap: "6px",
    overflowX: "auto",
  },
  pill: {
    flex: 1,
    backgroundColor: "#0a0a0a",
    border: "1px solid #222224",
    color: "#86868b",
    padding: "8px 10px",
    borderRadius: "8px",
    fontSize: "12px",
    cursor: "pointer",
    whiteSpace: "nowrap",
  },
  pillActive: {
    flex: 1,
    backgroundColor: "#ffffff",
    border: "1px solid #ffffff",
    color: "#000000",
    padding: "8px 10px",
    borderRadius: "8px",
    fontSize: "12px",
    fontWeight: "600",
    cursor: "pointer",
    whiteSpace: "nowrap",
  },
  searchInput: {
    width: "100%",
    padding: "12px 14px",
    backgroundColor: "#0a0a0a",
    border: "1px solid #2a2a2c",
    borderRadius: "10px",
    color: "#ffffff",
    fontSize: "14px",
    outline: "none",
    boxSizing: "border-box",
  },
  cardsContainer: {
    display: "flex",
    flexDirection: "column",
    gap: "10px",
  },
  attendeeCard: {
    backgroundColor: "#0a0a0a",
    border: "1px solid #222224",
    borderRadius: "14px",
    padding: "14px 16px",
    display: "flex",
    flexDirection: "column",
    gap: "6px",
  },
  cardTop: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    flexWrap: "wrap",
    gap: "8px",
  },
  badgeCluster: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    flexWrap: "wrap",
  },
  cardCode: {
    fontFamily: "ui-monospace, monospace",
    fontSize: "13px",
    fontWeight: "700",
    color: "#ffffff",
    letterSpacing: "0.5px",
    backgroundColor: "#1c1c1e",
    border: "1px solid #2c2c2e",
    padding: "3px 8px",
    borderRadius: "6px",
  },
  teamPill: {
    fontSize: "12px",
    fontWeight: "600",
    color: "#a1a1a6",
    backgroundColor: "#1c1c1e",
    padding: "3px 8px",
    borderRadius: "6px",
  },
  soloPill: {
    fontSize: "12px",
    color: "#6e6e73",
  },
  personBlock: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    marginTop: "2px",
  },
  personIcon: {
    fontSize: "14px",
    opacity: 0.8,
  },
  cardName: {
    fontSize: "15px",
    fontWeight: "600",
    color: "#ffffff",
    letterSpacing: "-0.01em",
  },
  cardMeta: {
    fontSize: "12px",
    color: "#6e6e73",
    marginTop: "2px",
  },
  badgeChecked: {
    backgroundColor: "#ffffff",
    color: "#000000",
    padding: "3px 8px",
    borderRadius: "6px",
    fontSize: "11px",
    fontWeight: "700",
  },
  badgeUnchecked: {
    backgroundColor: "#242426",
    color: "#86868b",
    padding: "3px 8px",
    borderRadius: "6px",
    fontSize: "11px",
  },
  emptyState: {
    padding: "24px",
    textAlign: "center",
    color: "#6e6e73",
    fontSize: "13px",
  },
};

export default AttendanceDashboard;
