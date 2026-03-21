import { render, screen } from "@testing-library/react";
import { vi, describe, it, expect } from "vitest";
import Home from "../pages/Home";

const mockNavigate = vi.fn();
const mockShowMessage = vi.fn();
const mockClearMessage = vi.fn();

vi.mock("react-router-dom", () => ({
  useNavigate: () => mockNavigate,
  useLocation: () => ({ state: undefined }),
}));

vi.mock("../context/AuthContext", () => ({
  useAuth: () => ({ loggedInUser: null }),
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

describe("Home page", () => {
  it("shows hero title and CTA buttons when logged out", () => {
    render(<Home />);
    expect(
      screen.getByText(/Manage your tennis &/i)
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Get Started" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Sign In" })).toBeInTheDocument();
  });
});

