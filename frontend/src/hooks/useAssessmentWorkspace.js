import { useCallback, useEffect, useRef, useState } from "react";
import {
  createAssessment,
  getAssessment,
  submitAssessment,
} from "../api/assessments";
import { errorMessage } from "../lib/apiClient";

const POLL_INTERVAL_MS = 3000;
const TRANSIENT = new Set(["generating", "grading"]);

/**
 * Owns the currently-open test attempt: create -> (poll generate) -> take ->
 * submit -> (poll grade) -> results. Notifies via onSettled when a background
 * phase finishes so the history list can refresh.
 */
export function useAssessmentWorkspace({ onSettled, onError } = {}) {
  const [attempt, setAttempt] = useState(null);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
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
          const fresh = await getAssessment(id);
          setAttempt(fresh);
          if (!TRANSIENT.has(fresh.status)) {
            stop();
            onSettled?.();
          }
        } catch {
          stop();
        }
      }, POLL_INTERVAL_MS);
    },
    [stop, onSettled],
  );

  const start = useCallback(
    async (payload) => {
      setBusy(true);
      try {
        const created = await createAssessment(payload);
        setAttempt(created);
        if (TRANSIENT.has(created.status)) poll(created.id);
        onSettled?.();
      } catch (err) {
        onError?.(errorMessage(err, "Could not start the test"));
      } finally {
        setBusy(false);
      }
    },
    [poll, onSettled, onError],
  );

  const open = useCallback(
    async (id) => {
      setLoading(true);
      try {
        const fresh = await getAssessment(id);
        setAttempt(fresh);
        if (TRANSIENT.has(fresh.status)) poll(fresh.id);
      } catch (err) {
        onError?.(errorMessage(err, "Could not load the test"));
      } finally {
        setLoading(false);
      }
    },
    [poll, onError],
  );

  const submit = useCallback(
    async (answers) => {
      if (!attempt) return;
      setBusy(true);
      try {
        const updated = await submitAssessment(
          attempt.id,
          Object.entries(answers).map(([question_id, answer]) => ({
            question_id: Number(question_id),
            answer,
          })),
        );
        setAttempt(updated);
        if (TRANSIENT.has(updated.status)) poll(updated.id);
      } catch (err) {
        onError?.(errorMessage(err, "Could not submit the test"));
      } finally {
        setBusy(false);
      }
    },
    [attempt, poll, onError],
  );

  const clear = useCallback(() => {
    stop();
    setAttempt(null);
  }, [stop]);

  useEffect(() => stop, [stop]);

  return { attempt, loading, busy, start, open, submit, clear };
}
