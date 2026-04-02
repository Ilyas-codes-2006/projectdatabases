import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest";
import Calendar from "../components/Calendar";

const mockFetch = vi.fn();

describe("Calendar Component", () => {
  const mockShowMessage = vi.fn();

  beforeEach(() => {
    vi.spyOn(Storage.prototype, "getItem").mockReturnValue("fake-token");

    globalThis.fetch = mockFetch as any;
  });

  afterEach(() => {
    vi.restoreAllMocks();
    mockFetch.mockReset();
  });

  it("renders the calendar and fetches initial availability", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ dates: ["2026-03-15", "2026-03-16"] }),
    });

    render(<Calendar showMessage={mockShowMessage} />);

    expect(
      screen.getByRole("button", { name: /Save Availability/i }),
    ).toBeInTheDocument();

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        "http://localhost:5000/api/availability",
        expect.objectContaining({
          method: "GET",
          headers: { Authorization: "Bearer fake-token" },
        }),
      );
    });
  });

  it("can select and deselect a date by clicking on it", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ dates: [] }),
    });

    render(<Calendar showMessage={mockShowMessage} />);

    await waitFor(() => expect(mockFetch).toHaveBeenCalledTimes(1));

    const dayButton = screen.getByText("15", { selector: "button" });

    fireEvent.click(dayButton);
    expect(dayButton).toHaveClass("selected");

    fireEvent.click(dayButton);
    expect(dayButton).not.toHaveClass("selected");
  });

  it("saves the selected availability and shows a success message", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ dates: [] }),
    });

    render(<Calendar showMessage={mockShowMessage} />);
    await waitFor(() => expect(mockFetch).toHaveBeenCalledTimes(1));

    const dayButton = screen.getByText("10", { selector: "button" });
    fireEvent.click(dayButton);

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ message: "Successfully saved!" }),
    });

    const saveButton = screen.getByRole("button", {
      name: /Save Availability/i,
    });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledTimes(2);
      expect(mockShowMessage).toHaveBeenCalledWith(
        "🎉 Successfully saved!",
        "success",
      );
    });
  });

  it("shows an error message if the save API call fails", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ dates: [] }),
    });

    render(<Calendar showMessage={mockShowMessage} />);
    await waitFor(() => expect(mockFetch).toHaveBeenCalledTimes(1));

    mockFetch.mockResolvedValueOnce({
      ok: false,
      json: async () => ({ error: "Network error" }),
    });

    const saveButton = screen.getByRole("button", {
      name: /Save Availability/i,
    });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(mockShowMessage).toHaveBeenCalledWith(
        "Error: Network error",
        "error",
      );
    });
  });
});
