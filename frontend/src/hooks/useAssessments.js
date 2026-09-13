import { useCallback, useEffect, useState } from "react";
import { listAssessments } from "../api/assessments";

// Owns the assessment history list and its refresh.
export function useAssessments() {
  const [assessments, setAssessments] = useState([]);

  const refresh = useCallback(async () => {
    try {
      setAssessments(await listAssessments());
    } catch {
      /* header banner surfaces backend availability */
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { assessments, refresh };
}
