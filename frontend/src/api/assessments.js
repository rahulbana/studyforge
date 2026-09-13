import { apiClient } from "../lib/apiClient";

export const listAssessments = () => apiClient.get("/assessments").then((r) => r.data);

export const getProgress = () => apiClient.get("/assessments/progress").then((r) => r.data);

export const getAssessment = (id) => apiClient.get(`/assessments/${id}`).then((r) => r.data);

export const createAssessment = (payload) =>
  apiClient.post("/assessments", payload).then((r) => r.data);

export const submitAssessment = (id, answers) =>
  apiClient.post(`/assessments/${id}/submit`, { answers }).then((r) => r.data);

export const deleteAssessment = (id) =>
  apiClient.delete(`/assessments/${id}`).then((r) => r.data);
