import { useCallback, useEffect, useRef, useState } from "react";
import { getChapter, regenerateNotes } from "../api/chapters";
import { listQuestions } from "../api/questions";
import { errorMessage } from "../lib/apiClient";

const POLL_INTERVAL_MS = 4000;

/**
 * Owns the currently-open chapter: its detail, questions, notes polling, and
 * regeneration. Keeps the top-level component free of data plumbing.
 */
export function useChapterWorkspace({ onNotesSettled, onError } = {}) {
  const [selectedId, setSelectedId] = useState(null);
  const [chapter, setChapter] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [regenerating, setRegenerating] = useState(false);
  const pollRef = useRef(null);

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  // Poll while notes are still being generated in the background.
  const maybePoll = useCallback(
    (c) => {
      stopPolling();
      if (c.notes_status !== "pending") return;
      pollRef.current = setInterval(async () => {
        try {
          const fresh = await getChapter(c.id);
          if (fresh.notes_status !== "pending") {
            stopPolling();
            setChapter(fresh);
            onNotesSettled?.();
          }
        } catch {
          stopPolling();
        }
      }, POLL_INTERVAL_MS);
    },
    [stopPolling, onNotesSettled],
  );

  const open = useCallback(
    async (id) => {
      setSelectedId(id);
      setLoading(true);
      try {
        const [c, qs] = await Promise.all([getChapter(id), listQuestions(id)]);
        setChapter(c);
        setQuestions(qs);
        maybePoll(c);
      } catch (err) {
        onError?.(errorMessage(err, "Could not load chapter"));
      } finally {
        setLoading(false);
      }
    },
    [maybePoll, onError],
  );

  const clear = useCallback(() => {
    stopPolling();
    setSelectedId(null);
    setChapter(null);
    setQuestions([]);
  }, [stopPolling]);

  // Refetch a chapter's detail in place (e.g. when notes streaming completes),
  // without the full-panel loading spinner.
  const reloadChapter = useCallback(async (id) => {
    try {
      const fresh = await getChapter(id);
      setChapter((current) => (current && current.id === id ? fresh : current));
    } catch {
      /* poll remains the fallback */
    }
  }, []);

  const regenerate = useCallback(async () => {
    if (!chapter) return;
    setRegenerating(true);
    try {
      const c = await regenerateNotes(chapter.id);
      setChapter(c);
      maybePoll(c);
    } catch (err) {
      onError?.(errorMessage(err, "Could not regenerate notes"));
    } finally {
      setRegenerating(false);
    }
  }, [chapter, maybePoll, onError]);

  useEffect(() => stopPolling, [stopPolling]);

  return {
    selectedId,
    chapter,
    questions,
    setQuestions,
    loading,
    regenerating,
    open,
    clear,
    regenerate,
    reloadChapter,
  };
}
