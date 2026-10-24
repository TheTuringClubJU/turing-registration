import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import ManualCheckinInput from "../attendance/ManualCheckinInput";

describe("ManualCheckinInput Regression Tests", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders text input and submits registration ID to /attendance/manual-checkin", async () => {
    const onCheckinComplete = vi.fn();
    const token = "mock-token";

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        registration_id: "c2534f3b-01c5-4a57-b08e-17cfc704f056",
        status: "checked_in",
        method: "manual",
        checked_in_at: "2026-10-24T12:00:00Z",
      }),
    });

    render(
      <ManualCheckinInput
        token={token}
        onCheckinComplete={onCheckinComplete}
        disabled={false}
      />
    );

    const input = screen.getByLabelText(/registration id/i);
    fireEvent.change(input, {
      target: { value: "c2534f3b-01c5-4a57-b08e-17cfc704f056" },
    });

    fireEvent.click(screen.getByRole("button", { name: /check in/i }));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith("/attendance/manual-checkin", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer mock-token`,
        },
        body: JSON.stringify({
          registration_id: "c2534f3b-01c5-4a57-b08e-17cfc704f056",
        }),
      });
      expect(onCheckinComplete).toHaveBeenCalledWith(
        expect.objectContaining({
          type: "success",
        })
      );
    });
  });

  it("handles 404 registration not found properly", async () => {
    const onCheckinComplete = vi.fn();

    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      json: async () => ({ detail: "Registration not found" }),
    });

    render(
      <ManualCheckinInput
        token="tok"
        onCheckinComplete={onCheckinComplete}
        disabled={false}
      />
    );

    const input = screen.getByLabelText(/registration id/i);
    fireEvent.change(input, { target: { value: "invalid-uuid" } });
    fireEvent.click(screen.getByRole("button", { name: /check in/i }));

    await waitFor(() => {
      expect(onCheckinComplete).toHaveBeenCalledWith(
        expect.objectContaining({
          type: "error",
          message: "Registration not found",
        })
      );
    });
  });
});
