import { render, screen, fireEvent } from "@testing-library/react";
import { vi, describe, it, expect } from "vitest";
import NotFound from "../pages/notfound";
import ServerError from "../pages/servererror";

describe("NotFound page", () => {
  it("renders 404 content and back button", () => {
    const originalLocation = window.location;

    // Override window.location with a partial mock
    delete (window as Partial<typeof window>).location;
    (window as Partial<typeof window>).location = { href: "/" } as unknown as Location;

    render(<NotFound />);
    expect(screen.getByText("404")).toBeInTheDocument();
    const btn = screen.getByRole("button", { name: "Back to Home" });
    fireEvent.click(btn);

    // Restore original window.location
    window.location = originalLocation as unknown as Location;
  });
});

describe("ServerError page", () => {
  it("renders 500 content and reloads on button click", () => {
    const reloadMock = vi.fn();
    const originalLocation = window.location;

    // Override window.location with a mock object
    delete (window as Partial<typeof window>).location;
    (window as Partial<typeof window>).location = {
      ...originalLocation,
      reload: reloadMock,
    } as unknown as Location;

    render(<ServerError />);
    expect(screen.getByText("500")).toBeInTheDocument();
    const btn = screen.getByRole("button", { name: "Try Again" });
    fireEvent.click(btn);
    expect(reloadMock).toHaveBeenCalled();

    // Restore original window.location
    window.location = originalLocation as unknown as Location;
  });
});