import { describe, expect, it } from "vitest";
import { normalizeMermaid } from "./Mermaid";

describe("normalizeMermaid", () => {
  it("repairs en/em-dash arrows into ASCII -->", () => {
    // The exact breakage seen from LLM notes: en dashes instead of hyphens.
    const bad = "flowchart LR\n  A ––> B\n  B ——> C";
    const out = normalizeMermaid(bad);
    expect(out).toContain("A --> B");
    expect(out).toContain("B --> C");
    expect(out).not.toMatch(/[–—]/);
  });

  it("straightens curly quotes and non-breaking spaces", () => {
    const out = normalizeMermaid("A[“Hi”] --> B[‘x’]");
    expect(out).toBe('A["Hi"] --> B[\'x\']');
  });

  it("leaves already-valid mermaid untouched", () => {
    const ok = "flowchart TD\n  A --> B";
    expect(normalizeMermaid(ok)).toBe(ok);
  });

  it("quotes node labels that contain parentheses or <br>", () => {
    const out = normalizeMermaid("flowchart TD\n  A[Troposphere<br>(0-12 km)] --> B[Plain]");
    expect(out).toContain('A["Troposphere<br>(0-12 km)"]');
    expect(out).toContain("B[Plain]"); // no special chars -> left unquoted
  });

  it("does not double-quote already-quoted labels", () => {
    const src = 'flowchart TD\n  A["X<br>(1-2)"] --> B[Plain]';
    expect(normalizeMermaid(src)).toBe(src);
  });
});
