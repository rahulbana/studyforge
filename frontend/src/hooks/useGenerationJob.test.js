import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import * as questionsApi from "../api/questions";
import { useGenerationJob } from "./useGenerationJob";

vi.mock("../api/questions");

describe("useGenerationJob", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("starts a job and polls until done, then calls onDone", async () => {
    questionsApi.startGeneration.mockResolvedValue({ id: 7, status: "pending" });
    questionsApi.getGenerationJob
      .mockResolvedValueOnce({ id: 7, status: "running" })
      .mockResolvedValueOnce({ id: 7, status: "done", result_count: 5 });

    const onDone = vi.fn();
    const { result } = renderHook(() => useGenerationJob({ chapterId: 1, onDone }));

    await act(async () => {
      await result.current.start({ counts: { mcq: 5 } });
    });
    expect(questionsApi.startGeneration).toHaveBeenCalledWith(1, { counts: { mcq: 5 } });
    expect(result.current.isRunning).toBe(true);

    // First poll -> running, second poll -> done.
    await act(async () => {
      await vi.advanceTimersByTimeAsync(3000);
    });
    expect(onDone).not.toHaveBeenCalled();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(3000);
    });
    expect(onDone).toHaveBeenCalledTimes(1);
    expect(onDone.mock.calls[0][0].result_count).toBe(5);
    expect(result.current.isRunning).toBe(false);
  });

  it("reports errors via onError when a job fails", async () => {
    questionsApi.startGeneration.mockResolvedValue({ id: 8, status: "pending" });
    questionsApi.getGenerationJob.mockResolvedValueOnce({
      id: 8,
      status: "error",
      error: "boom",
    });
    const onError = vi.fn();
    const { result } = renderHook(() => useGenerationJob({ chapterId: 1, onError }));

    await act(async () => {
      await result.current.start({ counts: { mcq: 1 } });
    });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(3000);
    });
    expect(onError).toHaveBeenCalledWith("boom");
  });
});
