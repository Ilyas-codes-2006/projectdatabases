import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach } from "vitest";
import ForgotPassword from "../pages/ForgotPassword";

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

describe("ForgotPassword page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubGlobal("fetch", vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({
            message: "Als dit e-mailadres bij ons bekend is, ontvang je binnen enkele minuten een resetlink.",
          }),
      } as Response)
    ));
  });

  it("submits email and shows success message", async () => {
    render(<ForgotPassword />);

    fireEvent.change(screen.getByLabelText("E-mailadres"), {
      target: { value: "jan@example.com" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Stuur resetlink" }));

    await waitFor(() =>
      expect(mockShowMessage).toHaveBeenCalledWith(
        "Als dit e-mailadres bij ons bekend is, ontvang je binnen enkele minuten een resetlink.",
        "success"
      )
    );
  });
});

