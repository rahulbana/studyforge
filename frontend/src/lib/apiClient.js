import axios from "axios";

export const apiClient = axios.create({ baseURL: "/api" });

// Pull a human-readable message out of an axios/FastAPI error.
export function errorMessage(err, fallback = "Something went wrong") {
  const detail = err?.response?.data?.detail;
  if (typeof detail === "string" && detail) return detail;
  if (Array.isArray(detail) && detail.length) {
    return detail.map((d) => d?.msg || String(d)).join("; ");
  }
  return err?.message || fallback;
}
