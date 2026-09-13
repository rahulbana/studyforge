import { useEffect, useRef, useState } from "react";
import { Box, Code, Text } from "@chakra-ui/react";
import mermaid from "mermaid";
import { sanitizeSvg } from "../../lib/sanitize";

mermaid.initialize({
  startOnLoad: false,
  theme: "default",
  // "strict" makes Mermaid sanitize its output and disables HTML labels /
  // click bindings — the diagram source is model-generated (untrusted).
  securityLevel: "strict",
  // Don't inject Mermaid's "bomb" error graphic into the DOM when a
  // model-generated diagram has invalid syntax — we fall back to the source.
  suppressErrorRendering: true,
  fontFamily: "Inter, system-ui, sans-serif",
});

let counter = 0;

// LLM output often carries "smart" typography that Mermaid's ASCII grammar
// rejects: en/em dashes break arrows ("––>" instead of "-->"), curly
// quotes break labels, and non-breaking spaces break tokens. Map them to ASCII.
export function normalizeMermaid(src) {
  return String(src || "")
    .replace(/[‐-―−]/g, "-") // hyphen/figure/en/em dash, minus -> "-"
    .replace(/[‘’‛]/g, "'") // curly single quotes -> '
    .replace(/[“”‟]/g, '"') // curly double quotes -> "
    .replace(/[   ]/g, " ") // non-breaking / narrow spaces -> space
    // Quote rectangle labels containing ( ) or <br> — Mermaid rejects
    // those in UNQUOTED labels; already-quoted labels are left untouched.
    .replace(/\[([^\[\]"]*[()<][^\[\]"]*)\]/g, '["$1"]');
}

// Renders a Mermaid diagram from its source. Falls back to showing the source
// if the diagram fails to parse (LLM output isn't always valid Mermaid).
export default function Mermaid({ chart }) {
  const [svg, setSvg] = useState("");
  const [error, setError] = useState(false);
  const idRef = useRef(`mmd-${counter++}`);
  const source = normalizeMermaid(chart);

  useEffect(() => {
    let cancelled = false;
    setError(false);
    setSvg("");

    (async () => {
      try {
        // parse with suppressErrors returns false (never throws) on bad syntax,
        // so we can fall back cleanly without Mermaid drawing an error diagram.
        const ok = await mermaid.parse(source, { suppressErrors: true });
        if (!ok) {
          if (!cancelled) setError(true);
          return;
        }
        const { svg: rendered } = await mermaid.render(idRef.current, source);
        if (!cancelled) setSvg(rendered);
      } catch {
        if (!cancelled) setError(true);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [source]);

  if (error) {
    return (
      <Box my={3}>
        <Text fontSize="xs" color="gray.500" mb={1}>
          Diagram couldn’t be rendered — showing its source:
        </Text>
        <Code display="block" whiteSpace="pre-wrap" p={3} borderRadius="md">
          {source}
        </Code>
      </Box>
    );
  }

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
      dangerouslySetInnerHTML={{ __html: sanitizeSvg(svg) }}
    />
  );
}
