import { render, screen, waitFor } from "@testing-library/react";
import { vi, describe, it, beforeEach, expect } from "vitest";
import Teams from "../pages/Teams";

const mockShowMessage = vi.fn();
const mockClearMessage = vi.fn();
const mockNavigate = vi.fn();

vi.mock("react-router-dom", () => ({
  useNavigate: () => mockNavigate,
}));

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

describe("Teams page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem("token", "fake-token");

    vi.stubGlobal("fetch", vi.fn((url: RequestInfo | URL) => {
      if (typeof url === "string" && url === "/api/teams/my-teams") {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            success: true,
            teams: [
              {
                team_id: 1,
                team_name: "My Team",
                ladder_name: "Test Ladder",
                team_size: 2,
                member_count: 2,
                members: ["Alice", "Bob"],
                is_solo: false,
                elo: 100,
              },
            ],
          }),
        } as Response);
      }

      return Promise.resolve({
        ok: false,
        json: () => Promise.resolve({ success: false }),
      } as Response);
    }));
  });

  it("renders teams and shows Join button", async () => {
    render(<Teams />);
    
    expect(screen.getByText("Join a Team")).toBeInTheDocument();

    await waitFor(() =>
      expect(screen.queryByText("Loading your teams…")).not.toBeInTheDocument()
    );

    expect(screen.getByText("My Team")).toBeInTheDocument();
    expect(screen.getByText(/Members: Alice & Bob/)).toBeInTheDocument();
    expect(screen.getByText(/2\/2 players · ELO: 100/)).toBeInTheDocument();
  });
});