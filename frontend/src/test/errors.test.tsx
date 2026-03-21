import { render, screen, fireEvent } from "@testing-library/react";
import { vi, describe, it, expect, afterEach } from "vitest";
import NotFound from "../pages/notfound";
import ServerError from "../pages/servererror";

describe("NotFound page", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders 404 content and back button", () => {
    vi.stubGlobal("location", { href: "/" });

    render(<NotFound />);

    expect(screen.getByText("404")).toBeInTheDocument();
    const btn = screen.getByRole("button", { name: "Back to Home" });
    fireEvent.click(btn);
  });
});

describe("ServerError page", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders 500 content and reloads on button click", () => {
    const reloadMock = vi.fn();

    vi.stubGlobal("location", {
      ...window.location,
      reload: reloadMock,
    });

    render(<ServerError />);

    expect(screen.getByText("500")).toBeInTheDocument();
    const btn = screen.getByRole("button", { name: "Try Again" });
    fireEvent.click(btn);

    expect(reloadMock).toHaveBeenCalled();
  });
});
