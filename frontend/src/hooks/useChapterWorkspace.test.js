import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import * as chaptersApi from "../api/chapters";
import * as questionsApi from "../api/questions";
import { useChapterWorkspace } from "./useChapterWorkspace";

vi.mock("../api/chapters");
vi.mock("../api/questions");

describe("useChapterWorkspace", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("opens a pending chapter and polls until notes are ready", async () => {
    chaptersApi.getChapter
      .mockResolvedValueOnce({ id: 1, notes_status: "pending" }) // open()
      .mockResolvedValueOnce({ id: 1, notes_status: "ready" }); // first poll
    questionsApi.listQuestions.mockResolvedValue([]);

    const onNotesSettled = vi.fn();
    const { result } = renderHook(() => useChapterWorkspace({ onNotesSettled }));

    await act(async () => {
      await result.current.open(1);
    });
    expect(result.current.chapter.notes_status).toBe("pending");

    await act(async () => {
      await vi.advanceTimersByTimeAsync(4000); // one poll interval
    });
    expect(result.current.chapter.notes_status).toBe("ready");
    expect(onNotesSettled).toHaveBeenCalled();
  });
});
