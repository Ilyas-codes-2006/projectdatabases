import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach } from "vitest";
import Profile from "../pages/Profile";

const mockUseAuth = { loggedInUser: "John Doe" };
const mockNavigate = vi.fn();

vi.mock("../context/AuthContext", () => ({
  useAuth: () => mockUseAuth,
}));

vi.mock("react-router-dom", () => ({
  useNavigate: () => mockNavigate,
}));

describe("Profile page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem("token", "fake-token");

    vi.stubGlobal("fetch", vi.fn((url: RequestInfo | URL, options?: RequestInit) => {
      if (typeof url === "string" && url === "/api/profile" && (!options || options.method === undefined)) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              first_name: "John",
              last_name: "Doe",
              email: "john@example.com",
              bio: "Hello!",
              photo_url: "",
              date_of_birth: "1990-01-01",
            }),
        } as Response);
      }

      if (typeof url === "string" && url === "/api/profile" && options?.method === "PUT") {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({}),
        } as Response);
      }

      return Promise.resolve({
        ok: false,
        json: () => Promise.resolve({}),
      } as Response);
    }));
  });

  it("loads and displays profile data", async () => {
    render(<Profile />);

    await waitFor(() =>
      expect(screen.getByText("John Doe")).toBeInTheDocument()
    );
    expect(screen.getByText("john@example.com")).toBeInTheDocument();
  });

  it("allows editing and saving bio", async () => {
    render(<Profile />);

    await waitFor(() =>
      expect(screen.getByText("John Doe")).toBeInTheDocument()
    );

    fireEvent.click(screen.getByRole("button", { name: /Edit Profile/i }));

    const textarea = screen.getByPlaceholderText(
      "Tell us about yourself…"
    ) as HTMLTextAreaElement;
    fireEvent.change(textarea, { target: { value: "New bio" } });

    fireEvent.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() =>
      expect(screen.getByText("New bio")).toBeInTheDocument()
    );
  });
});

