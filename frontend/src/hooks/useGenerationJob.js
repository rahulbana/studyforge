import { useCallback, useEffect, useRef, useState } from "react";
import { getGenerationJob, startGeneration } from "../api/questions";
import { errorMessage } from "../lib/apiClient";

const POLL_INTERVAL_MS = 3000;

/**
 * Starts a background question-generation job and polls it to completion.
 * Calls onDone(job) when it finishes and onError(message) if it fails.
 */
export function useGenerationJob({ chapterId, onDone, onError } = {}) {
  const [job, setJob] = useState(null);
  const pollRef = useRef(null);

  const stop = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  const poll = useCallback(
    (id) => {
      stop();
      pollRef.current = setInterval(async () => {
        try {
          const j = await getGenerationJob(id);
          setJob(j);
          if (j.status === "done") {
            stop();
            onDone?.(j);
          } else if (j.status === "error") {
            stop();
            onError?.(j.error || "Generation failed");
          }
        } catch (err) {
          stop();
          onError?.(errorMessage(err, "Lost track of the generation job"));
        }
      }, POLL_INTERVAL_MS);
    },
    [stop, onDone, onError],
  );

  const start = useCallback(
    async (payload) => {
      try {
        const j = await startGeneration(chapterId, payload);
        setJob(j);
        poll(j.id);
      } catch (err) {
        onError?.(errorMessage(err, "Could not start generation"));
      }
    },
    [chapterId, poll, onError],
  );

  useEffect(() => stop, [stop]);

  const isRunning = !!job && (job.status === "pending" || job.status === "running");
  return { start, job, isRunning };
}
