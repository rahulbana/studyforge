import { useCallback, useEffect, useState } from "react";
import { listChapters } from "../api/chapters";

// Owns the chapter library list and its refresh.
export function useChapters() {
  const [chapters, setChapters] = useState([]);
  // True only until the first load completes; background refreshes don't flip it,
  // so the full-page loader shows on initial load but not on every refresh.
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      setChapters(await listChapters());
    } catch {
      /* the header banner surfaces backend availability */
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { chapters, refresh, loading };
}
