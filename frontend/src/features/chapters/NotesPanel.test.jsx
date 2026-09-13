import { act, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithChakra } from "../../test/utils";
import NotesPanel from "./NotesPanel";

// Minimal fake EventSource that lets the test drive SSE events.
class FakeEventSource {
  static instances = [];
  constructor(url) {
    this.url = url;
    this.listeners = {};
    this.closed = false;
    FakeEventSource.instances.push(this);
  }
  addEventListener(type, cb) {
    (this.listeners[type] ||= []).push(cb);
  }
  emit(type, data) {
    (this.listeners[type] || []).forEach((cb) => cb({ data }));
  }
  close() {
    this.closed = true;
  }
}

describe("NotesPanel streaming", () => {
  beforeEach(() => {
    FakeEventSource.instances = [];
    global.EventSource = FakeEventSource;
  });
  afterEach(() => {
    delete global.EventSource;
  });

  it("appends streamed chunks and completes on done", () => {
    const chapter = { id: 3, notes_status: "pending", notes: "", sources: [] };
    const onStreamComplete = vi.fn();
    renderWithChakra(<NotesPanel chapter={chapter} onStreamComplete={onStreamComplete} />);

    const es = FakeEventSource.instances[0];
    expect(es.url).toContain("/api/chapters/3/notes/stream");

    act(() => {
      es.emit("chunk", JSON.stringify({ text: "Hello " }));
      es.emit("chunk", JSON.stringify({ text: "world" }));
    });
    expect(screen.getByText(/Hello world/)).toBeInTheDocument();

    act(() => es.emit("done", "{}"));
    expect(onStreamComplete).toHaveBeenCalledWith(3);
    expect(es.closed).toBe(true);
  });

  it("renders final notes when ready", () => {
    const chapter = {
      id: 4,
      notes_status: "ready",
      notes: "# Title\n\nBody text.",
      sources: [],
    };
    renderWithChakra(<NotesPanel chapter={chapter} />);
    expect(screen.getByText("Body text.")).toBeInTheDocument();
  });
});
