import { useEffect, useState } from "react";
import {
  Alert,
  AlertIcon,
  Badge,
  Box,
  Button,
  Center,
  HStack,
  Spinner,
  Stack,
  Text,
} from "@chakra-ui/react";
import { FiRefreshCw } from "react-icons/fi";
import Markdown from "../../components/common/Markdown";

// Streams the notes live over SSE while a chapter is being generated.
function StreamingNotes({ chapter, onComplete }) {
  const [text, setText] = useState("");

  useEffect(() => {
    setText("");
    const es = new EventSource(`/api/chapters/${chapter.id}/notes/stream`);
    es.addEventListener("chunk", (e) => {
      try {
        const { text: t } = JSON.parse(e.data);
        if (t) setText((prev) => prev + t);
      } catch {
        /* ignore malformed frame */
      }
    });
    es.addEventListener("done", () => {
      es.close();
      onComplete?.(chapter.id);
    });
    es.addEventListener("error", (e) => {
      // Named server error carries data; transport errors don't. Either way,
      // stop streaming — the chapter poll will surface the final state.
      if (e?.data) es.close();
    });
    return () => es.close();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chapter.id]);

  return (
    <Stack spacing={4}>
      <HStack color="gray.600">
        <Spinner size="sm" color="brand.500" />
        <Text>Researching the topic online and writing your notes… (live)</Text>
      </HStack>
      {text ? (
        <Box bg="surface" borderWidth="1px" borderRadius="lg" p={{ base: 4, md: 6 }}>
          <Markdown>{text}</Markdown>
        </Box>
      ) : (
        <Center py={10}>
          <Text fontSize="sm" color="gray.400">
            Searching the web and organising the chapter…
          </Text>
        </Center>
      )}
    </Stack>
  );
}

export default function NotesPanel({ chapter, onRegenerate, regenerating, onStreamComplete }) {
  if (chapter.notes_status === "pending") {
    return <StreamingNotes chapter={chapter} onComplete={onStreamComplete} />;
  }

  if (chapter.notes_status === "error") {
    return (
      <Stack spacing={4}>
        <Alert status="error" borderRadius="md">
          <AlertIcon />
          <Box>
            <Text fontWeight={600}>Note generation failed</Text>
            <Text fontSize="sm">{chapter.notes_error || "Unknown error."}</Text>
          </Box>
        </Alert>
        <Button
          leftIcon={<FiRefreshCw />}
          colorScheme="brand"
          alignSelf="flex-start"
          onClick={onRegenerate}
          isLoading={regenerating}
        >
          Try again
        </Button>
      </Stack>
    );
  }

  return (
    <Stack spacing={4}>
      <HStack justify="flex-end">
        {chapter.sources?.length > 0 && (
          <Badge colorScheme="gray" variant="subtle">
            {chapter.sources.length} sources
          </Badge>
        )}
        <Button
          leftIcon={<FiRefreshCw />}
          size="sm"
          variant="outline"
          onClick={onRegenerate}
          isLoading={regenerating}
        >
          Regenerate notes
        </Button>
      </HStack>
      <Box bg="surface" borderWidth="1px" borderRadius="lg" p={{ base: 4, md: 6 }}>
        <Markdown>{chapter.notes}</Markdown>
      </Box>
    </Stack>
  );
}
