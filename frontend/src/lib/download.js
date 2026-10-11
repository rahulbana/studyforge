// Trigger a browser download for a same-origin URL (e.g. an export endpoint).
export function downloadFile(url) {
  const a = document.createElement("a");
  a.href = url;
  a.rel = "noopener";
  document.body.appendChild(a);
  a.click();
  a.remove();
}
