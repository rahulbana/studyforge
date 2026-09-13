import { useState } from "react";
import {
  Alert,
  AlertIcon,
  Box,
  Button,
  Checkbox,
  Flex,
  Grid,
  Heading,
  HStack,
  NumberDecrementStepper,
  NumberIncrementStepper,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  Select,
  Text,
  useToast,
} from "@chakra-ui/react";
import { FiZap } from "react-icons/fi";
import { QUESTION_TYPES } from "../../constants";
import { useGenerationJob } from "../../hooks/useGenerationJob";

const DEFAULT_COUNTS = QUESTION_TYPES.reduce((acc, t) => ({ ...acc, [t.key]: 3 }), {});

export default function QuestionGenerator({ chapterId, onCompleted }) {
  const [counts, setCounts] = useState(DEFAULT_COUNTS);
  const [difficulty, setDifficulty] = useState("mixed");
  const [verify, setVerify] = useState(true);
  const toast = useToast();

  const { start, isRunning } = useGenerationJob({
    chapterId,
    onDone: (job) => {
      toast({
        title: `Generated ${job.result_count} questions`,
        description: "Your question bank has been updated.",
        status: "success",
        duration: 4000,
      });
      onCompleted?.();
    },
    onError: (msg) =>
      toast({ title: "Generation failed", description: msg, status: "error", duration: 7000 }),
  });

  const total = Object.values(counts).reduce((a, b) => a + (Number(b) || 0), 0);
  const setCount = (key, val) => setCounts((c) => ({ ...c, [key]: val }));

  const run = async () => {
    const payload = {
      counts: Object.fromEntries(
        Object.entries(counts)
          .filter(([, n]) => Number(n) > 0)
          .map(([k, n]) => [k, Number(n)]),
      ),
      difficulty,
      verify,
    };
    if (Object.keys(payload.counts).length === 0) {
      toast({ title: "Pick at least one question type", status: "warning" });
      return;
    }
    await start(payload);
  };

  return (
    <Box borderWidth="1px" borderRadius="lg" bg="surface" p={5}>
      <Flex justify="space-between" align="center" mb={4} wrap="wrap" gap={2}>
        <Heading size="sm">Generate questions</Heading>
        <HStack>
          <Text fontSize="sm" color="gray.500">
            Difficulty
          </Text>
          <Select size="sm" w="130px" value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
            <option value="easy">Easy</option>
            <option value="medium">Medium</option>
            <option value="hard">Hard</option>
            <option value="mixed">Mixed</option>
          </Select>
        </HStack>
      </Flex>

      <Grid templateColumns={{ base: "1fr", sm: "repeat(2, 1fr)", lg: "repeat(3, 1fr)" }} gap={3}>
        {QUESTION_TYPES.map((t) => (
          <Flex
            key={t.key}
            justify="space-between"
            align="center"
            borderWidth="1px"
            borderRadius="md"
            px={3}
            py={2}
          >
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

      <Flex justify="space-between" align="center" mt={4} wrap="wrap" gap={3}>
        <Checkbox isChecked={verify} onChange={(e) => setVerify(e.target.checked)} colorScheme="brand">
          Auto-verify & fix answers
        </Checkbox>
        <Button
          leftIcon={<FiZap />}
          colorScheme="brand"
          onClick={run}
          isLoading={isRunning}
          loadingText="Generating…"
          isDisabled={total === 0 || isRunning}
        >
          Generate {total > 0 ? `(${total})` : ""}
        </Button>
      </Flex>

      {isRunning && (
        <Alert status="info" mt={4} borderRadius="md" fontSize="sm">
          <AlertIcon />
          Generating in the background — feel free to keep working. We'll update the question bank
          and notify you when it's ready.
        </Alert>
      )}
    </Box>
  );
}
