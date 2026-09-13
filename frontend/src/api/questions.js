import { apiClient } from "../lib/apiClient";

export const listQuestions = (chapterId) =>
  apiClient.get(`/chapters/${chapterId}/questions`).then((r) => r.data);

// Kicks off background generation; returns a job to poll.
export const startGeneration = (chapterId, payload) =>
  apiClient.post(`/chapters/${chapterId}/questions/generate`, payload).then((r) => r.data);

export const getGenerationJob = (jobId) =>
  apiClient.get(`/generation-jobs/${jobId}`).then((r) => r.data);

export const addManualQuestion = (chapterId, payload) =>
  apiClient.post(`/chapters/${chapterId}/questions`, payload).then((r) => r.data);

export const updateQuestion = (questionId, payload) =>
  apiClient.put(`/questions/${questionId}`, payload).then((r) => r.data);

export const deleteQuestion = (questionId) =>
  apiClient.delete(`/questions/${questionId}`).then((r) => r.data);

export const verifyQuestion = (questionId) =>
  apiClient.post(`/questions/${questionId}/verify`).then((r) => r.data);

export const verifyAllQuestions = (chapterId) =>
  apiClient.post(`/chapters/${chapterId}/questions/verify-all`).then((r) => r.data);
