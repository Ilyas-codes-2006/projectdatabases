import { render, screen, waitFor } from "@testing-library/react";
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
            json: () => Promise.resolve({ success: true, clubs: mockClubs }),
          } as Response);
        }

        if (
          typeof url === "string" &&
          url === "/api/clubs/1/request_join" &&
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
          url === "/api/clubs/2/leave" &&
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

  it("renders clubs after loading", async () => {
    render(<Clubs />);

    await waitFor(() => {
      expect(screen.getByText("Club One")).toBeInTheDocument();
      expect(screen.getByText("Club Two")).toBeInTheDocument();
      expect(screen.getByText("Club Three")).toBeInTheDocument();
    });
  });

  it("shows correct button labels and disabled state", async () => {
    render(<Clubs />);

    await waitFor(() => expect(screen.getByText("Club One")).toBeInTheDocument());

    const joinButton = screen.getByRole("button", { name: "Join" });
    expect(joinButton).toBeEnabled();

    const leaveButton = screen.getByRole("button", { name: "Leave" });
    expect(leaveButton).toBeEnabled();

    const pendingButton = screen.getByRole("button", { name: "Request pending" });
    expect(pendingButton).toBeDisabled();
  });

  it("sends join request and updates status", async () => {
    render(<Clubs />);

    await waitFor(() => expect(screen.getByText("Club One")).toBeInTheDocument());

    const joinButton = screen.getByRole("button", { name: "Join" });
    joinButton.click();

    await waitFor(() =>
      expect(mockShowMessage).toHaveBeenCalledWith("Request to join club sent!", "success")
    );

    const pendingButtons = screen.getAllByRole("button", { name: "Request pending" });
    expect(pendingButtons.length).toBeGreaterThanOrEqual(1);
    pendingButtons.forEach((btn) => expect(btn).toBeDisabled());
  });

  it("leaves club and updates status", async () => {
    render(<Clubs />);

    await waitFor(() => expect(screen.getByText("Club Two")).toBeInTheDocument());

    const leaveButton = screen.getByRole("button", { name: "Leave" });
    leaveButton.click();

    await waitFor(() =>
      expect(mockShowMessage).toHaveBeenCalledWith("You have left the club", "success")
    );

    const joinButtons = screen.getAllByRole("button", { name: "Join" });
    expect(joinButtons.length).toBeGreaterThanOrEqual(1);
  });
});

