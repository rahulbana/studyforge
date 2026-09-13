import { useMemo, useState } from "react";
import {
  Badge,
  Box,
  Button,
  Flex,
  Heading,
  HStack,
  Select,
  Stack,
  Text,
  useDisclosure,
  useToast,
} from "@chakra-ui/react";
import { FiCheckCircle, FiPlus } from "react-icons/fi";
import { QUESTION_TYPES, QUESTION_TYPE_LABEL } from "../../constants";
import { listQuestions, verifyAllQuestions } from "../../api/questions";
import { errorMessage } from "../../lib/apiClient";
import QuestionCard from "./QuestionCard";
import QuestionGenerator from "./QuestionGenerator";
import AddQuestionModal from "./AddQuestionModal";

export default function QuestionsPanel({ chapter, questions, setQuestions }) {
  const [filter, setFilter] = useState("all");
  const [verifying, setVerifying] = useState(false);
  const addModal = useDisclosure();
  const toast = useToast();

  const upsert = (q) => setQuestions((qs) => qs.map((x) => (x.id === q.id ? q : x)));
  const append = (q) => setQuestions((qs) => [...qs, q]);
  const remove = (id) => setQuestions((qs) => qs.filter((x) => x.id !== id));

  // Background generation writes straight to the DB, so reload the full list.
  const reload = async () => {
    try {
      setQuestions(await listQuestions(chapter.id));
    } catch (err) {
      toast({ title: "Could not refresh questions", description: errorMessage(err), status: "error" });
    }
  };

  const grouped = useMemo(() => {
    const filtered = filter === "all" ? questions : questions.filter((q) => q.qtype === filter);
    const g = {};
    for (const q of filtered) (g[q.qtype] ||= []).push(q);
    return g;
  }, [questions, filter]);

  const doVerifyAll = async () => {
    setVerifying(true);
    try {
      setQuestions(await verifyAllQuestions(chapter.id));
      toast({ title: "All answers verified", status: "success" });
    } catch (err) {
      toast({ title: "Verify-all failed", description: errorMessage(err), status: "error" });
    } finally {
      setVerifying(false);
    }
  };

  return (
    <Stack spacing={5}>
      <QuestionGenerator chapterId={chapter.id} onCompleted={reload} />

      <Flex justify="space-between" align="center" wrap="wrap" gap={3}>
        <HStack>
          <Heading size="sm">Question bank</Heading>
          <Badge colorScheme="brand" borderRadius="full" px={2}>
            {questions.length}
          </Badge>
        </HStack>
        <HStack>
          <Select size="sm" value={filter} onChange={(e) => setFilter(e.target.value)} w="180px">
            <option value="all">All types</option>
            {QUESTION_TYPES.map((t) => (
              <option key={t.key} value={t.key}>
                {t.label}
              </option>
            ))}
          </Select>
          <Button size="sm" leftIcon={<FiPlus />} variant="outline" onClick={addModal.onOpen}>
            Add
          </Button>
          <Button
            size="sm"
            leftIcon={<FiCheckCircle />}
            colorScheme="brand"
            variant="outline"
            onClick={doVerifyAll}
            isLoading={verifying}
            isDisabled={questions.length === 0}
          >
            Verify all
          </Button>
        </HStack>
      </Flex>

      {questions.length === 0 ? (
        <Box
          borderWidth="1px"
          borderStyle="dashed"
          borderRadius="lg"
          p={8}
          textAlign="center"
          color="gray.500"
        >
          <Text>No questions yet. Use the panel above to generate some.</Text>
        </Box>
      ) : (
        Object.entries(grouped).map(([qtype, items]) => (
          <Box key={qtype}>
            <Text fontWeight={700} color="gray.600" mb={2}>
              {QUESTION_TYPE_LABEL[qtype] || qtype}{" "}
              <Text as="span" color="gray.400" fontWeight={400}>
                ({items.length})
              </Text>
            </Text>
            <Stack spacing={3}>
              {items.map((q, i) => (
                <QuestionCard
                  key={q.id}
                  index={i + 1}
                  question={q}
                  onChanged={upsert}
                  onDeleted={remove}
                />
              ))}
            </Stack>
          </Box>
        ))
      )}

      <AddQuestionModal
        isOpen={addModal.isOpen}
        onClose={addModal.onClose}
        chapterId={chapter.id}
        onAdded={append}
      />
    </Stack>
  );
}
