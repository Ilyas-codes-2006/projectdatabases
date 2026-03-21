import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach } from "vitest";
import Clubs from "../pages/Clubs";

const mockShowMessage = vi.fn();
const mockClearMessage = vi.fn();

vi.mock("../hooks/useMessage", () => ({
  useMessage: () => ({
    message: "",
    clearMessage: mockClearMessage,
    showMessage: mockShowMessage,
  }),
}));

vi.mock("../context/AuthContext", () => ({
  useAuth: () => ({
    isClubAdmin: false,
  }),
}));

vi.mock("../components/MessageBanner", () => ({
  default: ({ message }: { message: string }) =>
    message ? <div>{message}</div> : null,
}));

const mockClubs = [
  {
    id: 1,
    name: "Club One",
    city: "Antwerp",
    sports: ["Tennis"],
    request_status: "none" as const,
  },
  {
    id: 2,
    name: "Club Two",
    city: "Brussels",
    sports: ["Padel"],
    request_status: "member" as const,
  },
  {
    id: 3,
    name: "Club Three",
    city: "Ghent",
    sports: [],
    request_status: "pending" as const,
  },
];

describe("Clubs page", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    localStorage.setItem("token", "fake-token");

    vi.stubGlobal(
      "fetch",
      vi.fn((url: RequestInfo | URL, options?: RequestInit) => {
        if (typeof url === "string" && url === "/api/clubs") {
          return Promise.resolve({
            ok: true,
            json: () =>
              Promise.resolve({
                success: true,
                clubs: mockClubs,
                user_club: 2,
              }),
          } as Response);
        }

        if (
          typeof url === "string" &&
          url === "/api/clubs/1/join-request" &&
          options?.method === "POST"
        ) {
          return Promise.resolve({
            ok: true,
            json: () =>
              Promise.resolve({
                success: true,
                message: "join_request_created",
              }),
          } as Response);
        }

        if (
          typeof url === "string" &&
          url === `/api/clubs/2/leave` &&
          options?.method === "POST"
        ) {
          return Promise.resolve({
            ok: true,
            json: () =>
              Promise.resolve({ success: true, message: "left_club" }),
          } as Response);
        }

        return Promise.resolve({
          ok: false,
          json: () => Promise.resolve({ success: false }),
        } as Response);
      }),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders clubs after loading", async () => {
    render(<Clubs />);

    await waitFor(() => {
      expect(screen.getByText("Club One")).toBeInTheDocument();
      expect(screen.getByText("Club Two")).toBeInTheDocument();
      expect(screen.getByText("Club Three")).toBeInTheDocument();
    });
  });

  it("shows correct button labels and states", async () => {
    render(<Clubs />);

    await waitFor(() =>
      expect(screen.getByText("Club One")).toBeInTheDocument(),
    );
  });

  it("leaves club and updates status", async () => {
    render(<Clubs />);

    await waitFor(() =>
      expect(screen.getByText("Club Two")).toBeInTheDocument(),
    );

    const leaveButton = screen.getByRole("button", { name: "Leave" });
    fireEvent.click(leaveButton);

    await waitFor(() =>
      expect(mockShowMessage).toHaveBeenCalledWith(
        "You have left the club",
        "success",
      ),
    );
  });

  it("sends join request and updates status", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((url: RequestInfo | URL, options?: RequestInit) => {
        if (typeof url === "string" && url === "/api/clubs") {
          return Promise.resolve({
            ok: true,
            json: () =>
              Promise.resolve({
                success: true,
                clubs: mockClubs,
                user_club: null,
              }), // User is NOT in a club
          } as Response);
        }
        if (
          typeof url === "string" &&
          url === "/api/clubs/1/join-request" &&
          options?.method === "POST"
        ) {
          return Promise.resolve({
            ok: true,
            json: () =>
              Promise.resolve({
                success: true,
              }),
          } as Response);
        }
        return Promise.resolve({
          ok: false,
          json: () => Promise.resolve({ success: false }),
        } as Response);
      }),
    );

    render(<Clubs />);

    await waitFor(() =>
      expect(screen.getByText("Club One")).toBeInTheDocument(),
    );
    const aanvragenButton = screen.getAllByRole("button", {
      name: "Aanvragen",
    })[0];
    fireEvent.click(aanvragenButton);

    const sturenButton = await screen.findByRole("button", {
      name: "✓ Aanvraag versturen",
    });
    fireEvent.click(sturenButton);
    await waitFor(() =>
      expect(mockShowMessage).toHaveBeenCalledWith(
        "Aanvraag verstuurd naar de club admin van Club One!",
        "success",
      ),
    );

    const pendingBadges = screen.getAllByText("⏳ Aanvraag ingediend");
    expect(pendingBadges).toHaveLength(2); // Club One (just requested) + Club Three (already pending)
  });
});
