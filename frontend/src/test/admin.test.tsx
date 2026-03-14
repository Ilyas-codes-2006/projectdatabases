import { render, screen, waitFor } from "@testing-library/react";
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

// Mock een voorbeeldgebruiker die door de API wordt geretourneerd
const mockUser = { id: 1, first_name: "Jan", last_name: "Peeters", email: "jan@example.com", date_of_birth: "1990-01-01", created_at: "2024-01-10T00:00:00.000Z" };

// Genereer een geldig token en sla deze op in localStorage voordat elke test wordt uitgevoerd
beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem("token", "fake-token");
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve({
        ok: true,
        json: () => Promise.resolve([mockUser]),
    })));
});

describe("Admin", () => {
    // Test of de component correct rendert en gebruikers laadt
    it("renders users after loading", async () => {
        render(<Admin />);
        await waitFor(() => expect(screen.getByText("Jan")).toBeInTheDocument());
    });

    it("shows empty state when no users", async () => {
        // Mock fetch om een lege lijst terug te geven
        vi.stubGlobal("fetch", vi.fn(() => Promise.resolve({ ok: true, json: () => Promise.resolve([]) })));
        render(<Admin />);
        await waitFor(() => expect(screen.getByText("No users found.")).toBeInTheDocument());
    });

    it("shows error message on fetch failure", async () => {
        // Mock fetch om een fout te simuleren
        vi.stubGlobal("fetch", vi.fn(() => Promise.reject(new Error("network error"))));
        render(<Admin />);
        await waitFor(() => expect(mockShowMessage).toHaveBeenCalledWith("Kan geen verbinding maken met de server", "error"));
    });
});