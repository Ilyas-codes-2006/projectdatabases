import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach } from "vitest";
import ResetPassword from "../pages/ResetPassword";

const mockShowMessage = vi.fn();
const mockClearMessage = vi.fn();
const mockNavigate = vi.fn();

vi.mock("react-router-dom", () => ({
  useNavigate: () => mockNavigate,
  useSearchParams: () => [
    {
      get: (key: string) => (key === "token" ? "reset-token" : null),
    },
  ],
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

describe("ResetPassword page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("submits new password and redirects to login on success", async () => {
    vi.stubGlobal("fetch", vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({
            message: "Wachtwoord succesvol gewijzigd! Je kunt nu inloggen.",
          }),
      } as Response)
    ));

    render(<ResetPassword />);

    fireEvent.change(screen.getByLabelText("Nieuw wachtwoord"), {
      target: { value: "password123" },
    });
    fireEvent.change(screen.getByLabelText("Bevestig wachtwoord"), {
      target: { value: "password123" },
    });

    fireEvent.click(
      screen.getByRole("button", { name: "Wachtwoord instellen" })
    );

    await waitFor(() =>
      expect(mockNavigate).toHaveBeenCalledWith("/login", {
        state: {
          message: "Wachtwoord succesvol gewijzigd! Je kunt nu inloggen.",
          type: "success",
        },
      })
    );
  });
});

