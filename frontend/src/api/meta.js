import { apiClient } from "../lib/apiClient";

export const getHealth = () => apiClient.get("/health").then((r) => r.data);
