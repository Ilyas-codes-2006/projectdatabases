import { render, screen, waitFor } from "@testing-library/react";
import { vi, describe, it, expect } from "vitest";
import BadGateway from "../pages/badgateway";


describe("BadGateway", () => {
    it("Badgateway in message", async () => {
        // Test of the component correctly renders the BadGateway message
        render(<BadGateway />);
        await waitFor(() => expect(screen.getByText("The server is temporarily unavailable. Please try again in a moment.")).toBeInTheDocument());
    });

    it("Badgateway button", async () => {
       // Test of the "Try Again" button is present and functional
         render(<BadGateway />);
         const button = screen.getByRole("button", { name: /Try Again/i });
        expect(button).toBeInTheDocument();
        // Mock window.location.reload and simulate a click on the button
        const reloadMock = vi.fn();
        vi.stubGlobal("window", { location: { reload: reloadMock } });
        button.click();
        expect(reloadMock).toHaveBeenCalled();
    });
});