import { apiClient } from "../lib/apiClient";

export const listChapters = () => apiClient.get("/chapters").then((r) => r.data);

export const getChapter = (id) => apiClient.get(`/chapters/${id}`).then((r) => r.data);

export const deleteChapter = (id) => apiClient.delete(`/chapters/${id}`).then((r) => r.data);

export const regenerateNotes = (id) =>
  apiClient.post(`/chapters/${id}/notes/regenerate`).then((r) => r.data);

export const uploadChapter = (file, meta) => {
  const form = new FormData();
  form.append("file", file);
  form.append("class_name", meta.class_name);
  form.append("subject", meta.subject);
  form.append("chapter_name", meta.chapter_name);
  return apiClient
    .post("/chapters", form, { headers: { "Content-Type": "multipart/form-data" } })
    .then((r) => r.data);
};

export const exportUrl = (chapterId, fmt, include, layout = "full") =>
  `/api/chapters/${chapterId}/export?fmt=${fmt}&include=${include.join(",")}&layout=${layout}`;
