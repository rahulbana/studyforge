import { screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { renderWithChakra } from "./test/utils";
import App from "./App";

// Keep the smoke test offline: stub the API calls App makes on mount.
vi.mock("./api/meta", () => ({
  getHealth: () =>
    Promise.resolve({ openai_configured: true, model: "gpt-4o", web_search: true }),
}));
vi.mock("./api/chapters", () => ({
  listChapters: () => Promise.resolve([]),
  getChapter: vi.fn(),
  deleteChapter: vi.fn(),
  regenerateNotes: vi.fn(),
  uploadChapter: vi.fn(),
  exportUrl: () => "",
}));

describe("App", () => {
  it("renders the shell with mode switch and empty state", async () => {
    renderWithChakra(<App />);
    expect(screen.getByRole("img", { name: /studyforge/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /study/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /evaluate/i })).toBeInTheDocument();
    // Empty-state prompt for the study workspace.
    expect(
      await screen.findByText(/Select a chapter, or upload a new PDF/i),
    ).toBeInTheDocument();
  });
});
