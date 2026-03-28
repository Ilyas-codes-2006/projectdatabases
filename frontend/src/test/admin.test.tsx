import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach } from "vitest";
import Admin from "../pages/Admin";

// Mocks voor navigatie en berichtfuncties
const mockNavigate = vi.fn();
const mockShowMessage = vi.fn();
const mockClearMessage = vi.fn();

// Mock de benodigde modules en hooks
vi.mock("react-router-dom", () => ({ useNavigate: () => mockNavigate }));
vi.mock("../context/AuthContext", () => ({ useAuth: () => ({ isAdmin: true }) }));
vi.mock("../hooks/useMessage", () => ({
    useMessage: () => ({ message: "", clearMessage: mockClearMessage, showMessage: mockShowMessage }),
}));
vi.mock("../components/MessageBanner", () => ({
    default: ({ message }: { message: string }) => message ? <div>{message}</div> : null,
}));

// Mock een voorbeeldgebruiker en data voor clubs/teams
const mockUser = {
  id: 1,
  first_name: "Jan",
  last_name: "Peeters",
  email: "jan@example.com",
  date_of_birth: "1990-01-01",
  created_at: "2024-01-10T00:00:00.000Z",
};
const mockClubs = [{ id: 1, name: "Club One", city: "Antwerp" }];
const mockTeams = [{ id: 1, name: "Team One", member_count: 1 }];

// Genereer een geldig token en sla deze op in localStorage voordat elke test wordt uitgevoerd
beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem("token", "fake-token");
    vi.stubGlobal(
      "fetch",
      vi.fn((url: RequestInfo | URL) => {
        if (typeof url === "string" && url === "/api/admin/users") {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve([mockUser]),
          } as Response);
        }
        if (typeof url === "string" && url === "/api/admin/clubs") {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockClubs),
          } as Response);
        }
        if (typeof url === "string" && url === "/api/admin/teams") {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockTeams),
          } as Response);
        }
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({}),
        } as Response);
      })
    );
});

describe("Admin", () => {
    it("renders users after loading", async () => {
      render(<Admin />);
      await waitFor(() =>
        expect(screen.getByText("Jan")).toBeInTheDocument()
      );
    });

    it("opens edit modal when clicking Edit", async () => {
      render(<Admin />);

      await waitFor(() =>
        expect(screen.getByText("Jan")).toBeInTheDocument()
      );

      fireEvent.click(screen.getByRole("button", { name: "Edit" }));

      await waitFor(() =>
        expect(
          screen.getByText("Gebruiker aanpassen")
        ).toBeInTheDocument()
      );
      expect(
        screen.getByText(/Club One.*Antwerp/i)
      ).toBeInTheDocument();
    });

    it("shows empty state when no users", async () => {
      vi.stubGlobal(
        "fetch",
        vi.fn((url: RequestInfo | URL) => {
          if (typeof url === "string" && url === "/api/admin/users") {
            return Promise.resolve({
              ok: true,
              json: () => Promise.resolve([]),
            } as Response);
          }
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve([]),
          } as Response);
        })
      );
      render(<Admin />);
      await waitFor(() =>
        expect(
          screen.getByText("No users found.")
        ).toBeInTheDocument()
      );
    });

    it("shows error message on fetch failure", async () => {
      vi.stubGlobal(
        "fetch",
        vi.fn(() => Promise.resolve({ ok: false, json: () => Promise.resolve({}) } as Response))
      );
      render(<Admin />);
      await waitFor(() =>
        expect(mockShowMessage).toHaveBeenCalledWith(
          "Kon gebruikers niet laden",
          "error"
        )
      );
    });
});