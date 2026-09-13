import { Box } from "@chakra-ui/react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import Mermaid from "./Mermaid";
import { sanitizeSvg } from "../../lib/sanitize";

// Renders SVG markup after sanitizing it (defense against event-handler / script
// injection in model-generated figures).
function RawSvg({ html }) {
  return (
    <Box
      my={4}
      p={3}
      bg="white"
      borderRadius="md"
      borderWidth="1px"
      borderColor="borderSubtle"
      textAlign="center"
      overflowX="auto"
      sx={{ svg: { maxWidth: "100%", height: "auto" } }}
      dangerouslySetInnerHTML={{ __html: sanitizeSvg(html) }}
    />
  );
}

// Fenced code blocks: ```mermaid -> diagram, ```svg / ```html (or a block that is
// actually SVG) -> sanitized SVG. Everything else is normal code.
const components = {
  code({ className, children, ...props }) {
    const text = String(children ?? "");
    const lang = (/language-(\w+)/.exec(className || "") || [])[1];
    if (lang === "mermaid") {
      return <Mermaid chart={text.replace(/\n$/, "")} />;
    }
    if (lang === "svg" || lang === "html" || text.trim().startsWith("<svg")) {
      return <RawSvg html={text} />;
    }
    return (
      <code className={className} {...props}>
        {children}
      </code>
    );
  },
};

// Drop diagram placeholders that weren't rendered (e.g. diagram pass disabled).
const stripTokens = (md) => String(md || "").replace(/\[\[DIAGRAM:[\s\S]*?\]\]/gi, "");

// Route any raw (un-fenced) <svg>…</svg> through the sanitized ```svg code path,
// without touching content already inside fenced code blocks. Because we do NOT
// enable rehype-raw, all other raw HTML in the notes is rendered as inert text.
function fenceRawSvg(md) {
  return md
    .split(/(```[\s\S]*?```)/g)
    .map((part, i) =>
      i % 2 === 1
        ? part // already a fenced block — leave untouched
        : part.replace(/<svg[\s\S]*?<\/svg>/gi, (m) => `\n\n\`\`\`svg\n${m}\n\`\`\`\n\n`),
    )
    .join("");
}

// Renders Markdown notes. Raw HTML is NOT rendered (no rehype-raw); SVG figures
// are surfaced only through the sanitized code path above.
export default function Markdown({ children }) {
  const content = fenceRawSvg(stripTokens(children));
  return (
    <Box
      sx={{
        "h1, h2, h3, h4": { fontWeight: 700, lineHeight: 1.25, mt: 6, mb: 3 },
        h1: { fontSize: "1.7rem" },
        h2: { fontSize: "1.35rem", borderBottomWidth: "1px", borderColor: "borderSubtle", pb: 1 },
        h3: { fontSize: "1.12rem" },
        p: { mb: 3, lineHeight: 1.75 },
        "ul, ol": { pl: 6, mb: 3 },
        li: { mb: 1 },
        strong: { fontWeight: 700 },
        blockquote: {
          borderLeftWidth: "4px",
          borderColor: "brand.500",
          bg: "accentSubtle",
          px: 4,
          py: 2,
          my: 3,
          borderRadius: "md",
        },
        pre: { my: 3 },
        "pre code": {
          display: "block",
          bg: "gray.900",
          color: "gray.50",
          p: 3,
          borderRadius: "md",
          overflowX: "auto",
        },
        ":not(pre) > code": { bg: "surfaceMuted", px: 1, borderRadius: "sm", fontSize: "0.9em" },
        table: { width: "100%", my: 4, borderCollapse: "collapse", display: "block", overflowX: "auto" },
        "th, td": { border: "1px solid", borderColor: "borderSubtle", px: 3, py: 2, textAlign: "left" },
        th: { bg: "surfaceMuted" },
        svg: { maxWidth: "100%", height: "auto" },
      }}
    >
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {content}
      </ReactMarkdown>
    </Box>
  );
}
