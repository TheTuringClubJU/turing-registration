import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import ManualCheckinInput from "../attendance/ManualCheckinInput";

describe("ManualCheckinInput Regression Tests", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders text input and submits ticket code to /attendance/manual-checkin", async () => {
    const onCheckinComplete = vi.fn();
    const token = "mock-token";

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        registration_id: "c2534f3b-01c5-4a57-b08e-17cfc704f056",
        ticket_code: "TTC-8K1M",
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

    const input = screen.getByLabelText(/ticket code/i);
    fireEvent.change(input, {
      target: { value: "TTC-8K1M" },
    });

    fireEvent.click(screen.getByRole("button", { name: /admit/i }));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith("/attendance/manual-checkin", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer mock-token`,
        },
        body: JSON.stringify({
          registration_id: "TTC-8K1M",
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

    const input = screen.getByLabelText(/ticket code/i);
    fireEvent.change(input, { target: { value: "TTC-FAKE" } });
    fireEvent.click(screen.getByRole("button", { name: /admit/i }));

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
