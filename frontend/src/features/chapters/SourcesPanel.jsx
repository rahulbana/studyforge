import { Box, Link, Stack, Text } from "@chakra-ui/react";
import { FiExternalLink } from "react-icons/fi";

function hostname(url) {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

// Only allow http(s) links; anything else (e.g. javascript:) is not linkable.
function safeHref(url) {
  try {
    const u = new URL(url);
    return u.protocol === "http:" || u.protocol === "https:" ? u.href : null;
  } catch {
    return null;
  }
}

export default function SourcesPanel({ chapter }) {
  const sources = (chapter.sources || []).filter((s) => safeHref(s.url));

  if (sources.length === 0) {
    return (
      <Box
        borderWidth="1px"
        borderStyle="dashed"
        borderRadius="lg"
        p={8}
        textAlign="center"
        color="gray.500"
      >
        <Text fontWeight={600} mb={1}>
          No web sources recorded for this chapter.
        </Text>
        <Text fontSize="sm">
          Sources are captured when the notes agent researches the topic online. They may be
          empty if web search was disabled, unavailable, or the notes were built from the PDF
          alone. Regenerate the notes to try again.
        </Text>
      </Box>
    );
  }

  return (
    <Stack spacing={3}>
      <Text fontSize="sm" color="gray.500">
        These are the web pages the notes agent consulted while researching this chapter.
      </Text>
      {sources.map((s, i) => (
        <Link
          key={i}
          href={s.url}
          isExternal
          _hover={{ textDecoration: "none", borderColor: "brand.400", bg: "accentSubtle" }}
          borderWidth="1px"
          borderRadius="md"
          bg="surface"
          p={3}
          display="block"
        >
          <Text fontWeight={600} color="brand.500" noOfLines={2}>
            {s.title || s.url} <FiExternalLink style={{ display: "inline", verticalAlign: "-2px" }} />
          </Text>
          <Text fontSize="xs" color="gray.500" noOfLines={1}>
            {hostname(s.url)}
          </Text>
        </Link>
      ))}
    </Stack>
  );
}
