import { useState } from "react";
import {
  Box,
  Button,
  Flex,
  FormControl,
  FormLabel,
  Grid,
  Heading,
  HStack,
  Input,
  NumberDecrementStepper,
  NumberIncrementStepper,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  Radio,
  RadioGroup,
  Select,
  Stack,
  Text,
} from "@chakra-ui/react";
import { FiPlayCircle } from "react-icons/fi";
import { QUESTION_TYPES } from "../../constants";
import { useChapters } from "../../hooks/useChapters";

const DEFAULT_COUNTS = {
  mcq: 5,
  true_false: 3,
  fill_blank: 0,
  one_word: 0,
  short_answer: 2,
  long_answer: 0,
  case_based: 0,
};

export default function NewTestForm({ onStart, busy }) {
  const { chapters } = useChapters();
  const [source, setSource] = useState("topic");
  const [chapterId, setChapterId] = useState("");
  const [meta, setMeta] = useState({ class_name: "", subject: "", topic: "" });
  const [counts, setCounts] = useState(DEFAULT_COUNTS);
  const [difficulty, setDifficulty] = useState("mixed");

  const total = Object.values(counts).reduce((a, b) => a + (Number(b) || 0), 0);
  const setCount = (key, val) => setCounts((c) => ({ ...c, [key]: val }));

  const canStart =
    total > 0 &&
    (source === "chapter" ? !!chapterId : meta.topic.trim() && meta.subject.trim());

  const start = () => {
    const activeCounts = Object.fromEntries(
      Object.entries(counts).filter(([, n]) => Number(n) > 0).map(([k, n]) => [k, Number(n)]),
    );
    const payload =
      source === "chapter"
        ? { source, chapter_id: Number(chapterId), counts: activeCounts, difficulty }
        : { source, ...meta, counts: activeCounts, difficulty };
    onStart(payload);
  };

  return (
    <Box maxW="760px" mx="auto">
      <Heading size="md" mb={1}>
        Start a new test
      </Heading>
      <Text color="gray.500" mb={5}>
        Pick what to be tested on, choose your question mix, and we'll generate a test, grade
        your answers, and show where to focus.
      </Text>

      <Stack spacing={5} bg="surface" borderWidth="1px" borderRadius="lg" p={{ base: 4, md: 6 }}>
        <FormControl>
          <FormLabel>Test me on</FormLabel>
          <RadioGroup value={source} onChange={setSource}>
            <HStack spacing={6}>
              <Radio value="topic" colorScheme="brand">
                A topic
              </Radio>
              <Radio value="chapter" colorScheme="brand" isDisabled={chapters.length === 0}>
                An uploaded chapter{chapters.length === 0 ? " (none yet)" : ""}
              </Radio>
            </HStack>
          </RadioGroup>
        </FormControl>

        {source === "chapter" ? (
          <FormControl isRequired>
            <FormLabel>Chapter</FormLabel>
            <Select
              placeholder="Select a chapter"
              value={chapterId}
              onChange={(e) => setChapterId(e.target.value)}
            >
              {chapters.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.chapter_name} — {c.class_name} · {c.subject}
                </option>
              ))}
            </Select>
          </FormControl>
        ) : (
          <Grid templateColumns={{ base: "1fr", md: "1fr 1fr" }} gap={3}>
            <FormControl>
              <FormLabel>Class / Grade</FormLabel>
              <Input
                placeholder="e.g. Class 10"
                value={meta.class_name}
                onChange={(e) => setMeta({ ...meta, class_name: e.target.value })}
              />
            </FormControl>
            <FormControl isRequired>
              <FormLabel>Subject</FormLabel>
              <Input
                placeholder="e.g. Physics"
                value={meta.subject}
                onChange={(e) => setMeta({ ...meta, subject: e.target.value })}
              />
            </FormControl>
            <FormControl isRequired gridColumn={{ md: "1 / -1" }}>
              <FormLabel>Topic</FormLabel>
              <Input
                placeholder="e.g. Laws of Motion"
                value={meta.topic}
                onChange={(e) => setMeta({ ...meta, topic: e.target.value })}
              />
            </FormControl>
          </Grid>
        )}

        <FormControl>
          <Flex justify="space-between" align="center" mb={2}>
            <FormLabel m={0}>Question mix</FormLabel>
            <HStack>
              <Text fontSize="sm" color="gray.500">
                Difficulty
              </Text>
              <Select size="sm" w="120px" value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
                <option value="easy">Easy</option>
                <option value="medium">Medium</option>
                <option value="hard">Hard</option>
                <option value="mixed">Mixed</option>
              </Select>
            </HStack>
          </Flex>
          <Grid templateColumns={{ base: "1fr", sm: "repeat(2, 1fr)" }} gap={3}>
            {QUESTION_TYPES.map((t) => (
              <Flex key={t.key} justify="space-between" align="center" borderWidth="1px" borderRadius="md" px={3} py={2}>
                <Text fontSize="sm">{t.label}</Text>
                <NumberInput
                  size="sm"
                  maxW="80px"
                  min={0}
                  max={25}
                  value={counts[t.key]}
                  onChange={(_, n) => setCount(t.key, Number.isNaN(n) ? 0 : n)}
                >
                  <NumberInputField />
                  <NumberInputStepper>
                    <NumberIncrementStepper />
                    <NumberDecrementStepper />
                  </NumberInputStepper>
                </NumberInput>
              </Flex>
            ))}
          </Grid>
        </FormControl>

        <Button
          leftIcon={<FiPlayCircle />}
          colorScheme="brand"
          size="lg"
          onClick={start}
          isLoading={busy}
          loadingText="Preparing…"
          isDisabled={!canStart}
          alignSelf="flex-start"
        >
          Start test ({total} question{total === 1 ? "" : "s"})
        </Button>
      </Stack>
    </Box>
  );
}
