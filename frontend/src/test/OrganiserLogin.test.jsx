import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import OrganiserLogin from "../attendance/OrganiserLogin";

describe("OrganiserLogin Regression Tests", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
  });

  it("renders username handle and password inputs and submit button", () => {
    render(<OrganiserLogin onLoginSuccess={vi.fn()} />);

    expect(screen.getByLabelText(/organiser handle/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /continue/i })).toBeInTheDocument();
  });

  it("submits credentials to /auth/login and stores JWT upon success", async () => {
    const mockSuccessResponse = {
      access_token: "test-jwt-token-12345",
      token_type: "bearer",
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockSuccessResponse,
    });

    const onLoginSuccess = vi.fn();
    render(<OrganiserLogin onLoginSuccess={onLoginSuccess} />);

    fireEvent.change(screen.getByLabelText(/organiser handle/i), {
      target: { value: "techlead@ttc" },
    });
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: "secret123" },
    });

    fireEvent.click(screen.getByRole("button", { name: /continue/i }));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: "techlead@ttc",
          password: "secret123",
        }),
      });
      expect(localStorage.getItem("organiser_token")).toBe("test-jwt-token-12345");
      expect(onLoginSuccess).toHaveBeenCalledWith("test-jwt-token-12345");
    });
  });

  it("displays error alert when API returns 401 unauthorized", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({ detail: "Invalid username or password" }),
    });

    render(<OrganiserLogin onLoginSuccess={vi.fn()} />);

    fireEvent.change(screen.getByLabelText(/organiser handle/i), {
      target: { value: "wrong@ttc" },
    });
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: "badpass" },
    });

    fireEvent.click(screen.getByRole("button", { name: /continue/i }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Invalid username or password");
    });
  });
});
