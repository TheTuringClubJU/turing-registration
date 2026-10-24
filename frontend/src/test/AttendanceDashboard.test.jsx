import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import AttendanceDashboard from "../attendance/AttendanceDashboard";

describe("AttendanceDashboard Regression Tests", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("fetches and displays summary and attendee list for an event", async () => {
    const mockSummary = {
      total_registered: 50,
      checked_in: 20,
      remaining: 30,
    };

    const mockList = [
      {
        registration_id: "reg-001",
        team_name: "Code Crafters",
        participant_names: ["Alice", "Bob"],
        status: "checked_in",
        method: "qr",
        checked_in_at: "2026-10-24T10:00:00Z",
      },
      {
        registration_id: "reg-002",
        team_name: null,
        participant_names: ["Charlie"],
        status: "not_checked_in",
        method: null,
        checked_in_at: null,
      },
    ];

    global.fetch = vi.fn().mockImplementation((url) => {
      if (url.includes("/attendance/summary")) {
        return Promise.resolve({
          ok: true,
          json: async () => mockSummary,
        });
      }
      if (url.includes("/attendance/list")) {
        return Promise.resolve({
          ok: true,
          json: async () => mockList,
        });
      }
      return Promise.reject(new Error("unknown URL"));
    });

    render(<AttendanceDashboard token="valid-token" onLogout={vi.fn()} />);

    const eventInput = screen.getByPlaceholderText(/enter event uuid/i);
    fireEvent.change(eventInput, { target: { value: "event-123" } });

    await waitFor(() => {
      expect(screen.getByText("50")).toBeInTheDocument();
      expect(screen.getByText("20")).toBeInTheDocument();
      expect(screen.getByText("30")).toBeInTheDocument();
      expect(screen.getByText("reg-001")).toBeInTheDocument();
      expect(screen.getByText("reg-002")).toBeInTheDocument();
      expect(screen.getByText(/Alice, Bob/i)).toBeInTheDocument();
    });
  });

  it("calls onLogout if API returns 401 Unauthorized", async () => {
    const onLogout = vi.fn();

    global.fetch = vi.fn().mockResolvedValue({
      status: 401,
      ok: false,
    });

    render(<AttendanceDashboard token="expired-token" onLogout={onLogout} />);

    const eventInput = screen.getByPlaceholderText(/enter event uuid/i);
    fireEvent.change(eventInput, { target: { value: "event-123" } });

    await waitFor(() => {
      expect(onLogout).toHaveBeenCalled();
    });
  });
});
