import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import CreateEventModal from "../attendance/CreateEventModal";
import AttendanceDashboard from "../attendance/AttendanceDashboard";

describe("CreateEventModal Tests", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("does not render when isOpen is false", () => {
    render(
      <CreateEventModal
        isOpen={false}
        onClose={vi.fn()}
        token="test-token"
        onEventCreated={vi.fn()}
      />
    );
    expect(screen.queryByText(/create new event/i)).not.toBeInTheDocument();
  });

  it("renders all fields including min_team_size, max_team_size, dates, slug, type, and active toggle", () => {
    render(
      <CreateEventModal
        isOpen={true}
        onClose={vi.fn()}
        token="test-token"
        onEventCreated={vi.fn()}
      />
    );

    expect(screen.getByText(/create new event/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/e.g. Turing Live Workshop 2026/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/e.g. turing-live-workshop/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/event type/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/min team size/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/max team size/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/registration open at/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/registration close at/i)).toBeInTheDocument();
    expect(screen.getByRole("checkbox")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /create event/i })).toBeInTheDocument();
  });

  it("submits the form and calls onEventCreated on success", async () => {
    const onEventCreated = vi.fn();
    const onClose = vi.fn();

    const mockEvent = {
      id: "new-event-123",
      name: "Turing Hackathon 2026",
      slug: "turing-hackathon-2026",
      type: "hackathon",
      min_team_size: 2,
      max_team_size: 4,
      is_active: false,
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockEvent,
    });

    render(
      <CreateEventModal
        isOpen={true}
        onClose={onClose}
        token="test-token"
        onEventCreated={onEventCreated}
      />
    );

    fireEvent.change(screen.getByPlaceholderText(/e.g. Turing Live Workshop 2026/i), {
      target: { value: "Turing Hackathon 2026" },
    });
    fireEvent.change(screen.getByLabelText(/event type/i), {
      target: { value: "hackathon" },
    });
    fireEvent.change(screen.getByLabelText(/min team size/i), {
      target: { value: "2" },
    });
    fireEvent.change(screen.getByLabelText(/max team size/i), {
      target: { value: "4" },
    });

    fireEvent.click(screen.getByRole("button", { name: /create event/i }));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        "/events",
        expect.objectContaining({
          method: "POST",
          headers: expect.objectContaining({
            Authorization: "Bearer test-token",
            "Content-Type": "application/json",
          }),
        })
      );
      expect(onEventCreated).toHaveBeenCalledWith(mockEvent);
      expect(onClose).toHaveBeenCalled();
    });
  });

  it("shows an error when API returns failure", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      json: async () => ({ detail: "Event slug/code already exists or another event is active" }),
    });

    render(
      <CreateEventModal
        isOpen={true}
        onClose={vi.fn()}
        token="test-token"
        onEventCreated={vi.fn()}
      />
    );

    fireEvent.change(screen.getByPlaceholderText(/e.g. Turing Live Workshop 2026/i), {
      target: { value: "Duplicate Event" },
    });

    fireEvent.click(screen.getByRole("button", { name: /create event/i }));

    await waitFor(() => {
      expect(screen.getByText(/event slug\/code already exists/i)).toBeInTheDocument();
    });
  });

  it("opens create event modal when clicking '+ Create Event' button in AttendanceDashboard", () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({}),
    });

    render(<AttendanceDashboard token="valid-token" onLogout={vi.fn()} />);

    const createBtn = screen.getByRole("button", { name: /\+ create event/i });
    expect(createBtn).toBeInTheDocument();

    fireEvent.click(createBtn);
    expect(screen.getByText(/create new event/i)).toBeInTheDocument();
  });
});
