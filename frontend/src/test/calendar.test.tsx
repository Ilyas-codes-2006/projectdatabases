import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest";
import Calendar from "../components/Calendar";

const mockFetch = vi.fn();
const mockNavigate = vi.fn();

// Mock react-router-dom voor de useNavigate hook
vi.mock("react-router-dom", () => ({
  useNavigate: () => mockNavigate,
}));

describe("Calendar Component", () => {
  const mockShowMessage = vi.fn();

  beforeEach(() => {
    vi.spyOn(Storage.prototype, "getItem").mockReturnValue("fake-token");
    globalThis.fetch = mockFetch as any;
  });

  afterEach(() => {
    vi.restoreAllMocks();
    mockFetch.mockReset();
    mockNavigate.mockReset();
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
        "/api/availability", // Aangepast naar relatieve URL
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

  it("renders correctly in readOnly mode and navigates to /availability", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ dates: [] }),
    });

    render(<Calendar showMessage={mockShowMessage} readOnly={true} />);
    await waitFor(() => expect(mockFetch).toHaveBeenCalledTimes(1));

    expect(
      screen.queryByRole("button", { name: /Save Availability/i }),
    ).not.toBeInTheDocument();

    const setAvailButton = screen.getByRole("button", {
      name: /Set your availability/i,
    });
    expect(setAvailButton).toBeInTheDocument();

    fireEvent.click(setAvailButton);
    expect(mockNavigate).toHaveBeenCalledWith("/availability");

    const dayButton = screen.getByText("15", { selector: "button" });
    fireEvent.click(dayButton);
    expect(dayButton).not.toHaveClass("selected");
  });

  it("toggles all days of a weekday when clicking the day header", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ dates: [] }),
    });

    render(<Calendar showMessage={mockShowMessage} readOnly={false} />);
    await waitFor(() => expect(mockFetch).toHaveBeenCalledTimes(1));

    const wednesdayHeader = screen.getByText("We");

    fireEvent.click(wednesdayHeader);

    const selectedButtons = screen
      .getAllByRole("button")
      .filter((btn) => btn.classList.contains("selected"));
    expect(selectedButtons.length).toBeGreaterThanOrEqual(4);

    fireEvent.click(wednesdayHeader);
    const selectedButtonsAfter = screen
      .getAllByRole("button")
      .filter((btn) => btn.classList.contains("selected"));
    expect(selectedButtonsAfter.length).toBe(0);
  });
});
