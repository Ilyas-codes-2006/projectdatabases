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

    fireEvent.change(screen.getByLabelText("First name"), {
      target: { value: "Jan" },
    });
    fireEvent.change(screen.getByLabelText("Last name"), {
      target: { value: "Janssen" },
    });
    fireEvent.change(screen.getByLabelText("E-mail"), {
      target: { value: "jan@example.com" },
    });
    fireEvent.change(screen.getByLabelText("Date of birth"), {
      target: { value: "1990-01-01" },
    });
    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "password1" },
    });
    fireEvent.change(screen.getByLabelText("Confirm password"), {
      target: { value: "password2" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Create account" }));

    await waitFor(() =>
      expect(mockShowMessage).toHaveBeenCalledWith(
        "Passwords do not match!",
        "error",
      ),
    );
  });
});
