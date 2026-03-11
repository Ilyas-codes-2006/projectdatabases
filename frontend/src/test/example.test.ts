import { describe, it, expect } from "vitest";

function sum(a: number, b: number) {
    return a + b;
}

describe("sum", () => {
    it("adds numbers", () => {
        expect(sum(1, 2)).toBe(3);
    });
});