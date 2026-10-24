import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import ResultDisplay from "../attendance/ResultDisplay";

describe("ResultDisplay Component Tests", () => {
  it("renders nothing when result is null", () => {
    const { container } = render(<ResultDisplay result={null} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders success state correctly", () => {
    const mockResult = {
      type: "success",
      message: "Check-in successful!",
      data: {
        registration_id: "test-reg-id",
        method: "qr",
        checked_in_at: "2026-10-24T10:00:00Z",
      },
    };

    render(<ResultDisplay result={mockResult} onClear={vi.fn()} />);

    expect(screen.getByText("Checked in")).toBeInTheDocument();
    expect(screen.getByText("Check-in successful!")).toBeInTheDocument();
    expect(screen.getByText("test-reg-id")).toBeInTheDocument();
    expect(screen.getByText(/QR/i)).toBeInTheDocument();
  });

  it("renders already checked in idempotent state correctly", () => {
    const mockResult = {
      type: "already_checked_in",
      message: "Attendee was already checked in via QR.",
      data: {
        registration_id: "duplicate-reg-id",
        method: "qr",
      },
    };

    render(<ResultDisplay result={mockResult} />);
    expect(screen.getByText("Already checked in")).toBeInTheDocument();
    expect(screen.getByText("Attendee was already checked in via QR.")).toBeInTheDocument();
  });

  it("calls onClear when close button is clicked", () => {
    const onClear = vi.fn();
    const mockResult = { type: "error", message: "Scan failed" };

    render(<ResultDisplay result={mockResult} onClear={onClear} />);
    fireEvent.click(screen.getByTitle(/dismiss/i));
    expect(onClear).toHaveBeenCalledTimes(1);
  });
});
