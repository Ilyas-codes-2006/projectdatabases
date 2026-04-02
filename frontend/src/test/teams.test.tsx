import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach } from "vitest";
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

    vi.stubGlobal("fetch", vi.fn((url: RequestInfo | URL, options?: RequestInit) => {
      if (typeof url === "string") {
        if (url === "/api/teams/my-teams") {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({
              success: true,
              teams: [
                {
                  id: "1",
                  team_name: "My Team",
                  ladder_name: "Test Ladder",
                  is_solo: false,
                },
              ],
            }),
          } as Response);
        }

        if (url === "/api/teams" && options?.method === "POST") {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ success: true }),
          } as Response);
        }
      }

      return Promise.resolve({
        ok: false,
        json: () => Promise.resolve({ success: false }),
      } as Response);
    }));
  });

  it("creates a team and shows success message", async () => {
    render(<Teams />);

    fireEvent.change(screen.getByPlaceholderText("Team name…"), {
      target: { value: "My Team" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Create Team" }));

    await waitFor(() =>
      expect(mockShowMessage).toHaveBeenCalledWith("Team created!", "success")
    );
  });
});