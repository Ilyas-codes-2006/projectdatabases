/**
 * notifications.test.tsx
 *
 * Tests for the notification-related frontend code:
 *   1. MessageBanner component
 *   2. useMessage hook
 *   3. Navbar notification bell (GET /api/notifications + PATCH /api/notifications/read)
 */

import { render, screen, waitFor, fireEvent, act } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest";
import { renderHook } from "@testing-library/react";

import MessageBanner from "../components/MessageBanner";
import { useMessage } from "../hooks/useMessage";
import Navbar from "../components/Navbar";

// Shared fetch mock
const mockFetch = vi.fn();

// Mock react-router-dom (Navbar uses useNavigate + useLocation)

vi.mock("react-router-dom", () => ({
  useNavigate: () => vi.fn(),
  useLocation: () => ({ pathname: "/" }),
}));

// Mock AuthContext
let mockAuthValue = {
  loggedInUser: null as string | null,
  isAdmin: false,
  myClubName: null as string | null,
  myClubId: null as number | null,
  logout: vi.fn(),
};

vi.mock("../context/AuthContext", () => ({
  useAuth: () => mockAuthValue,
}));


// MessageBanner component

describe("MessageBanner", () => {
  it("renders nothing when message is null", () => {
    const { container } = render(
      <MessageBanner message={null} onClose={vi.fn()} />
    );
    expect(container.firstChild).toBeNull();
  });

  it("renders the message text when message is provided", () => {
    render(
      <MessageBanner
        message={{ text: "Something went wrong", type: "error" }}
        onClose={vi.fn()}
      />
    );
    expect(screen.getByText(/Something went wrong/)).toBeInTheDocument();
  });

  it("applies the 'success' CSS class for success messages", () => {
    const { container } = render(
      <MessageBanner
        message={{ text: "Saved!", type: "success" }}
        onClose={vi.fn()}
      />
    );
    expect(container.firstChild).toHaveClass("success");
  });

  it("applies the 'error' CSS class for error messages", () => {
    const { container } = render(
      <MessageBanner
        message={{ text: "Failed!", type: "error" }}
        onClose={vi.fn()}
      />
    );
    expect(container.firstChild).toHaveClass("error");
  });

  it("calls onClose when the banner is clicked", () => {
    const onClose = vi.fn();
    const { container } = render(
      <MessageBanner
        message={{ text: "Click to close", type: "success" }}
        onClose={onClose}
      />
    );
    fireEvent.click(container.firstChild as Element);
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("renders a close icon (×)", () => {
    render(
      <MessageBanner
        message={{ text: "Hello", type: "success" }}
        onClose={vi.fn()}
      />
    );
    expect(screen.getByText("×")).toBeInTheDocument();
  });
});


// useMessage hook

describe("useMessage hook", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("message is null initially", () => {
    const { result } = renderHook(() => useMessage());
    expect(result.current.message).toBeNull();
  });

  it("showMessage sets message with correct text and type", () => {
    const { result } = renderHook(() => useMessage());
    act(() => {
      result.current.showMessage("Test error", "error");
    });
    expect(result.current.message).toEqual({ text: "Test error", type: "error" });
  });

  it("showMessage with type 'success' stores success message", () => {
    const { result } = renderHook(() => useMessage());
    act(() => {
      result.current.showMessage("All good", "success");
    });
    expect(result.current.message).toEqual({ text: "All good", type: "success" });
  });

  it("message auto-clears after 5 seconds", async () => {
    const { result } = renderHook(() => useMessage());
    act(() => {
      result.current.showMessage("Disappearing", "success");
    });
    expect(result.current.message).not.toBeNull();

    act(() => {
      vi.advanceTimersByTime(5000);
    });
    expect(result.current.message).toBeNull();
  });

  it("message is still present before 5 seconds elapse", () => {
    const { result } = renderHook(() => useMessage());
    act(() => {
      result.current.showMessage("Still here", "error");
    });
    act(() => {
      vi.advanceTimersByTime(4999);
    });
    expect(result.current.message).not.toBeNull();
  });

  it("clearMessage removes the message immediately", () => {
    const { result } = renderHook(() => useMessage());
    act(() => {
      result.current.showMessage("Clear me", "error");
    });
    act(() => {
      result.current.clearMessage();
    });
    expect(result.current.message).toBeNull();
  });

  it("calling showMessage again resets the 5-second timer", () => {
    const { result } = renderHook(() => useMessage());

    act(() => {
      result.current.showMessage("First", "success");
    });
    // advance 4 seconds — timer not yet expired
    act(() => {
      vi.advanceTimersByTime(4000);
    });

    // Replace with a new message — timer should reset
    act(() => {
      result.current.showMessage("Second", "error");
    });

    // Another 4 seconds — should NOT have cleared (total 8s from first, but only 4s from second)
    act(() => {
      vi.advanceTimersByTime(4000);
    });
    expect(result.current.message).toEqual({ text: "Second", type: "error" });

    // Complete the 5s from the second call
    act(() => {
      vi.advanceTimersByTime(1001);
    });
    expect(result.current.message).toBeNull();
  });
});

//Navbar notification bell

describe("Navbar notification bell", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem("token", "fake-token");
    vi.stubGlobal("fetch", mockFetch);
  });

  afterEach(() => {
    mockFetch.mockReset();
    localStorage.clear();
    // Reset auth mock to logged-out state between tests
    mockAuthValue = {
      loggedInUser: null,
      isAdmin: false,
      myClubName: null,
      myClubId: null,
      logout: vi.fn(),
    };
  });

  const renderNavbarLoggedIn = (notificationsResponse: object[] = []) => {
    mockAuthValue = {
      loggedInUser: "Alice Wonder",
      isAdmin: false,
      myClubName: null,
      myClubId: null,
      logout: vi.fn(),
    };
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => notificationsResponse,
    });
    return render(<Navbar />);
  };

  it("does not fetch notifications when user is not logged in", () => {
    // loggedInUser stays null
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => [],
    });
    render(<Navbar />);
    // fetch should not have been called for notifications
    expect(mockFetch).not.toHaveBeenCalled();
  });

  it("renders the bell icon when logged in", async () => {
    renderNavbarLoggedIn([]);
    await waitFor(() => {
      expect(screen.getByText("🔔")).toBeInTheDocument();
    });
  });

  it("fetches notifications on mount when logged in", async () => {
    renderNavbarLoggedIn([]);
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        "/api/notifications",
        expect.objectContaining({
          headers: expect.objectContaining({ Authorization: "Bearer fake-token" }),
        })
      );
    });
  });

  it("shows no badge when there are no notifications", async () => {
    renderNavbarLoggedIn([]);
    await waitFor(() => expect(mockFetch).toHaveBeenCalled());
    // A badge would be a red circle with the count — it should not exist
    expect(screen.queryByText("1")).not.toBeInTheDocument();
  });

  it("shows badge count when there are unread notifications", async () => {
    renderNavbarLoggedIn([
      { type: "join_request", message: "Bob wants to join TC Antwerp" },
      { type: "team_event", message: "Carol joined Team A" },
    ]);
    await waitFor(() => {
      expect(screen.getByText("2")).toBeInTheDocument();
    });
  });

  it("shows '1' badge for a single notification", async () => {
    renderNavbarLoggedIn([
      { type: "join_request", message: "Dave wants to join TC Gent" },
    ]);
    await waitFor(() => {
      expect(screen.getByText("1")).toBeInTheDocument();
    });
  });

  it("opens dropdown and shows messages when bell is clicked", async () => {
    renderNavbarLoggedIn([
      { type: "join_request", message: "Eve wants to join TC Leuven" },
    ]);
    await waitFor(() => expect(mockFetch).toHaveBeenCalled());

    fireEvent.click(screen.getByText("🔔"));

    await waitFor(() => {
      expect(screen.getByText("Eve wants to join TC Leuven")).toBeInTheDocument();
    });
  });

  it("shows 'Geen openstaande verzoeken' when dropdown opened with no notifications", async () => {
    renderNavbarLoggedIn([]);
    await waitFor(() => expect(mockFetch).toHaveBeenCalled());

    fireEvent.click(screen.getByText("🔔"));

    await waitFor(() => {
      expect(screen.getByText("Geen openstaande verzoeken")).toBeInTheDocument();
    });
  });

  it("calls PATCH /api/notifications/read when dropdown is closed by clicking bell again", async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [{ type: "team_event", message: "Frank joined Team B" }],
      })
      .mockResolvedValue({ ok: true, json: async () => ({ ok: true }) });

    mockAuthValue = {
      loggedInUser: "Alice Wonder",
      isAdmin: false,
      myClubName: null,
      myClubId: null,
      logout: vi.fn(),
    };
    render(<Navbar />);

    await waitFor(() => expect(mockFetch).toHaveBeenCalled());

    // Open dropdown
    fireEvent.click(screen.getByText("🔔"));

    // Close dropdown by clicking bell again
    fireEvent.click(screen.getByText("🔔"));

    await waitFor(() => {
      const patchCalls = mockFetch.mock.calls.filter(
        (call) => call[1]?.method === "PATCH"
      );
      expect(patchCalls.length).toBeGreaterThan(0);
      expect(patchCalls[0][0]).toBe("/api/notifications/read");
    });
  });

  it("clears notifications from state after marking as read", async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [{ type: "team_event", message: "Grace joined Team C" }],
      })
      .mockResolvedValue({ ok: true, json: async () => ({ ok: true }) });

    mockAuthValue = {
      loggedInUser: "Alice Wonder",
      isAdmin: false,
      myClubName: null,
      myClubId: null,
      logout: vi.fn(),
    };
    render(<Navbar />);

    // Wait for the badge to appear
    await waitFor(() => expect(screen.getByText("1")).toBeInTheDocument());

    // Open dropdown
    fireEvent.click(screen.getByText("🔔"));

    // Close by clicking bell again → triggers markAsRead → clears state
    fireEvent.click(screen.getByText("🔔"));

    await waitFor(() => {
      expect(screen.queryByText("1")).not.toBeInTheDocument();
    });
  });

  it("does not crash when the notifications fetch fails", async () => {
    mockAuthValue = {
      loggedInUser: "Alice Wonder",
      isAdmin: false,
      myClubName: null,
      myClubId: null,
      logout: vi.fn(),
    };
    mockFetch.mockRejectedValue(new Error("Network error"));

    // Should not throw
    render(<Navbar />);
    await waitFor(() => expect(mockFetch).toHaveBeenCalled());
    // Bell still visible, no badge
    expect(screen.getByText("🔔")).toBeInTheDocument();
    expect(screen.queryByText("1")).not.toBeInTheDocument();
  });

  it("displays multiple notification messages in the dropdown", async () => {
    renderNavbarLoggedIn([
      { type: "join_request", message: "Heidi wants to join TC Brussels" },
      { type: "team_event", message: "Ivan joined Team D" },
    ]);
    await waitFor(() => expect(mockFetch).toHaveBeenCalled());

    fireEvent.click(screen.getByText("🔔"));

    await waitFor(() => {
      expect(screen.getByText("Heidi wants to join TC Brussels")).toBeInTheDocument();
      expect(screen.getByText("Ivan joined Team D")).toBeInTheDocument();
    });
  });

  it("shows the 'notifications' header inside the dropdown", async () => {
    renderNavbarLoggedIn([]);
    await waitFor(() => expect(mockFetch).toHaveBeenCalled());

    fireEvent.click(screen.getByText("🔔"));

    await waitFor(() => {
      expect(screen.getByText("notifications")).toBeInTheDocument();
    });
  });
});