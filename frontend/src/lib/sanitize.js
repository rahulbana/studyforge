import DOMPurify from "dompurify";

// Sanitize model-generated SVG/HTML before injecting it into the DOM.
export function sanitizeSvg(markup) {
  return DOMPurify.sanitize(String(markup ?? ""), {
    USE_PROFILES: { svg: true, svgFilters: true },
    ADD_TAGS: ["foreignObject"],
  });
}
