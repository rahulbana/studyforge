import { describe, expect, it } from "vitest";
import { renderWithChakra } from "../../test/utils";
import Markdown from "./Markdown";

describe("Markdown sanitization", () => {
  it("renders SVG figures but strips event-handler attributes", () => {
    const md = '```svg\n<svg viewBox="0 0 10 10" onload="window.__pwned=1"><text>hi</text></svg>\n```';
    const { container } = renderWithChakra(<Markdown>{md}</Markdown>);
    const svg = container.querySelector("svg");
    expect(svg).not.toBeNull();
    expect(svg.hasAttribute("onload")).toBe(false);
  });

  it("does not render raw HTML like <img onerror> (no rehype-raw)", () => {
    const md = 'Intro <img src=x onerror="window.__pwned=1"> outro';
    const { container } = renderWithChakra(<Markdown>{md}</Markdown>);
    expect(container.querySelector("img")).toBeNull();
  });

  it("renders un-fenced inline SVG through the sanitized path", () => {
    const md = 'Text\n\n<svg viewBox="0 0 10 10" onclick="evil()"><text>x</text></svg>\n\nmore';
    const { container } = renderWithChakra(<Markdown>{md}</Markdown>);
    const svg = container.querySelector("svg");
    expect(svg).not.toBeNull();
    expect(svg.hasAttribute("onclick")).toBe(false);
  });
});
