import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach } from "vitest";
import Register from "../pages/Register";

const mockNavigate = vi.fn();
const mockShowMessage = vi.fn();
const mockClearMessage = vi.fn();

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

describe("Register page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows error when passwords do not match", async () => {
    render(<Register />);

    fireEvent.change(screen.getByLabelText("Voornaam"), {
      target: { value: "Jan" },
    });
    fireEvent.change(screen.getByLabelText("Achternaam"), {
      target: { value: "Janssen" },
    });
    fireEvent.change(screen.getByLabelText("E-mailadres"), {
      target: { value: "jan@example.com" },
    });
    fireEvent.change(screen.getByLabelText("Geboortedatum"), {
      target: { value: "1990-01-01" },
    });
    fireEvent.change(screen.getByLabelText("Wachtwoord"), {
      target: { value: "password1" },
    });
    fireEvent.change(screen.getByLabelText("Bevestig wachtwoord"), {
      target: { value: "password2" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Account aanmaken" }));

    await waitFor(() =>
      expect(mockShowMessage).toHaveBeenCalledWith(
        "Wachtwoorden komen niet overeen",
        "error"
      )
    );
  });
});

