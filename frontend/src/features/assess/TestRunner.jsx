import { useState } from "react";
import {
  Badge,
  Box,
  Button,
  Flex,
  Heading,
  HStack,
  Input,
  Radio,
  RadioGroup,
  Stack,
  Text,
  Textarea,
} from "@chakra-ui/react";
import { FiCheckCircle } from "react-icons/fi";
import { QUESTION_TYPE_LABEL } from "../../constants";

function AnswerInput({ q, value, onChange }) {
  if (q.qtype === "mcq") {
    return (
      <RadioGroup value={value} onChange={onChange}>
        <Stack>
          {q.options.map((opt, i) => (
            <Radio key={i} value={opt} colorScheme="brand">
              {opt}
            </Radio>
          ))}
        </Stack>
      </RadioGroup>
    );
  }
  if (q.qtype === "true_false") {
    return (
      <RadioGroup value={value} onChange={onChange}>
        <HStack spacing={6}>
          <Radio value="True" colorScheme="brand">
            True
          </Radio>
          <Radio value="False" colorScheme="brand">
            False
          </Radio>
        </HStack>
      </RadioGroup>
    );
  }
  if (q.qtype === "fill_blank" || q.qtype === "one_word") {
    return (
      <Input value={value} onChange={(e) => onChange(e.target.value)} placeholder="Your answer" />
    );
  }
  const rows = q.qtype === "short_answer" ? 3 : 6;
  return (
    <Textarea
      value={value}
      onChange={(e) => onChange(e.target.value)}
      rows={rows}
      placeholder="Write your answer"
    />
  );
}

export default function TestRunner({ attempt, onSubmit, busy }) {
  const [answers, setAnswers] = useState({});
  const setAnswer = (id, val) => setAnswers((a) => ({ ...a, [id]: val }));

  const answered = attempt.questions.filter((q) => (answers[q.id] || "").trim()).length;
  const total = attempt.questions.length;

  const submit = () => {
    if (answered < total && !window.confirm(`You've answered ${answered} of ${total}. Submit anyway?`)) {
      return;
    }
    onSubmit(answers);
  };

  return (
    <Box maxW="820px" mx="auto">
      <Flex justify="space-between" align="flex-start" mb={4} wrap="wrap" gap={2}>
        <Box>
          <Heading size="md">{attempt.topic}</Heading>
          <Text color="gray.500">
            {attempt.class_name ? `${attempt.class_name} · ` : ""}
            {attempt.subject}
          </Text>
        </Box>
        <Badge colorScheme="brand" fontSize="0.9em" px={2} py={1} borderRadius="md">
          {answered}/{total} answered
        </Badge>
      </Flex>

      <Stack spacing={4}>
        {attempt.questions.map((q, i) => (
          <Box key={q.id} borderWidth="1px" borderRadius="md" bg="surface" p={4}>
            <Flex justify="space-between" align="flex-start" gap={3} mb={3}>
              <Text fontWeight={600}>
                {i + 1}. {q.question}
              </Text>
              <Badge flexShrink={0} variant="subtle">
                {QUESTION_TYPE_LABEL[q.qtype] || q.qtype} · {q.max_points} pt
              </Badge>
            </Flex>
            <AnswerInput q={q} value={answers[q.id] || ""} onChange={(v) => setAnswer(q.id, v)} />
          </Box>
        ))}
      </Stack>

      <Button
        mt={5}
        leftIcon={<FiCheckCircle />}
        colorScheme="brand"
        size="lg"
        onClick={submit}
        isLoading={busy}
        loadingText="Submitting…"
      >
        Submit for grading
      </Button>
    </Box>
  );
}
