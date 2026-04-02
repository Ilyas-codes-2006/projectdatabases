import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach } from "vitest";
import JoinTeams from "../pages/JoinTeams";

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

describe("JoinTeams page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem("token", "fake-token");
    vi.stubGlobal("fetch", vi.fn((url: RequestInfo | URL) => {
      if (typeof url === "string" && url === "/api/teams") {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              success: true,
              teams: [
  {
    team_id: 1,
                  team_name: "Team One",
                  member_count: 1,
                  team_size: 2,
                  members: [],
                  ladder_name: "Test",
                },
              ],
            }),
        } as Response);
      }

      if (typeof url === "string" && url === "/api/teams/1/join") {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ success: true }),
        } as Response);
      }

      return Promise.resolve({
        ok: false,
        json: () => Promise.resolve({ success: false }),
      } as Response);
    }));
  });

  it("joins a team and shows success message", async () => {
    render(<JoinTeams />);

    await waitFor(() =>
      expect(screen.getByText("Team One")).toBeInTheDocument()
    );

    fireEvent.click(screen.getByRole("button", { name: "Join" }));

    await waitFor(() =>
      expect(mockShowMessage).toHaveBeenCalledWith(
        "You joined the team!",
        "success"
      )
    );
  });
});

