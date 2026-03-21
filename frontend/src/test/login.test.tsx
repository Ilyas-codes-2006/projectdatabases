import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach } from "vitest";
import Login from "../pages/Login";

const mockNavigate = vi.fn();
const mockLogin = vi.fn();
const mockShowMessage = vi.fn();
const mockClearMessage = vi.fn();

vi.mock("react-router-dom", () => ({
  useNavigate: () => mockNavigate,
  useLocation: () => ({ state: undefined }),
}));

vi.mock("../context/AuthContext", () => ({
  useAuth: () => ({ login: mockLogin }),
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

describe("Login page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("submits credentials and calls login on success", async () => {
    vi.stubGlobal("fetch", vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({
            token: "fake-token",
            name: "John Doe",
            is_admin: false,
          }),
      } as Response)
    ));

    render(<Login />);

    fireEvent.change(screen.getByLabelText("E-mailadres"), {
      target: { value: "john@example.com" },
    });
    fireEvent.change(screen.getByLabelText("Wachtwoord"), {
      target: { value: "secret123" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Inloggen" }));

    await waitFor(() =>
      expect(mockLogin).toHaveBeenCalledWith("fake-token", "John Doe", false)
    );
    expect(mockNavigate).toHaveBeenCalledWith("/", {
      state: { message: "Welkom terug, John Doe!", type: "success" },
    });
  });
});

