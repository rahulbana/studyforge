import { describe, expect, it } from "vitest";
import { theme } from "./theme";

// Chakra's Button variants reach for these brand shades in dark mode
// (solid bg = brand.200, hover = brand.300, plus brand.800). A missing shade
// makes colorScheme="brand" buttons render invisible in dark mode, which is
// exactly the "Study"/"Upload chapter" disappearing-in-dark-mode bug.
describe("brand color scale", () => {
  it("defines the full 50-900 range", () => {
    const required = [50, 100, 200, 300, 400, 500, 600, 700, 800, 900];
    for (const shade of required) {
      expect(theme.colors.brand[shade], `brand.${shade} must be defined`).toMatch(
        /^#[0-9a-f]{6}$/i,
      );
    }
  });
});
