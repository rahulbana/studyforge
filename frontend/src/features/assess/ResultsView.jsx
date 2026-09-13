import {
  Badge,
  Box,
  Button,
  Divider,
  Flex,
  Heading,
  HStack,
  Icon,
  List,
  ListIcon,
  ListItem,
  Progress,
  SimpleGrid,
  Stack,
  Text,
  Wrap,
  WrapItem,
} from "@chakra-ui/react";
import { FiAlertTriangle, FiCheckCircle, FiRotateCcw, FiXCircle } from "react-icons/fi";
import { QUESTION_TYPE_LABEL } from "../../constants";
import { formatUsd } from "../../lib/format";

const pctColor = (p) => (p >= 80 ? "green" : p >= 60 ? "yellow" : "red");

function ScoreHeader({ attempt }) {
  const score = attempt.score ?? 0;
  return (
    <Flex
      align="center"
      justify="space-between"
      bg="surface"
      borderWidth="1px"
      borderRadius="lg"
      p={5}
      wrap="wrap"
      gap={4}
    >
      <Box>
        <Heading size="md">{attempt.topic}</Heading>
        <Text color="gray.500">
          {attempt.class_name ? `${attempt.class_name} · ` : ""}
          {attempt.subject}
        </Text>
      </Box>
      <Box textAlign="right">
        <Text fontSize="3xl" fontWeight={800} color={`${pctColor(score)}.500`} lineHeight={1}>
          {score}%
        </Text>
        <Text fontSize="sm" color="gray.500">
          {attempt.points_awarded} / {attempt.points_max} points
        </Text>
        {attempt.cost_usd > 0 && (
          <Text fontSize="xs" color="gray.400">
            ≈ {formatUsd(attempt.cost_usd)}
          </Text>
        )}
      </Box>
    </Flex>
  );
}

function ConceptBreakdown({ feedback }) {
  if (!feedback?.concept_breakdown?.length) return null;
  return (
    <Box bg="surface" borderWidth="1px" borderRadius="lg" p={5}>
      <Heading size="sm" mb={4}>
        Performance by concept
      </Heading>
      <Stack spacing={4}>
        {feedback.concept_breakdown.map((c) => (
          <Box key={c.concept}>
            <Flex justify="space-between" mb={1}>
              <Text fontSize="sm" fontWeight={600}>
                {c.concept}
              </Text>
              <Text fontSize="sm" color="gray.500">
                {c.points_awarded}/{c.points_max} · {c.percentage}%
              </Text>
            </Flex>
            <Progress
              value={c.percentage}
              colorScheme={pctColor(c.percentage)}
              borderRadius="full"
              size="sm"
            />
          </Box>
        ))}
      </Stack>
    </Box>
  );
}

function FeedbackCard({ feedback }) {
  if (!feedback) return null;
  return (
    <Box bg="surface" borderWidth="1px" borderRadius="lg" p={5}>
      <Heading size="sm" mb={2}>
        Your report
      </Heading>
      {feedback.summary && <Text mb={4}>{feedback.summary}</Text>}

      <Wrap spacing={2} mb={feedback.recommendations?.length ? 4 : 0}>
        {feedback.weak_concepts?.map((c) => (
          <WrapItem key={c}>
            <Badge colorScheme="red" variant="subtle">
              Needs work: {c}
            </Badge>
          </WrapItem>
        ))}
        {feedback.strong_concepts?.map((c) => (
          <WrapItem key={c}>
            <Badge colorScheme="green" variant="subtle">
              Strong: {c}
            </Badge>
          </WrapItem>
        ))}
      </Wrap>

      {feedback.recommendations?.length > 0 && (
        <>
          <Text fontWeight={600} mb={2}>
            What to focus on
          </Text>
          <List spacing={2}>
            {feedback.recommendations.map((r, i) => (
              <ListItem key={i} fontSize="sm">
                <ListIcon as={FiAlertTriangle} color="orange.400" />
                {r}
              </ListItem>
            ))}
          </List>
        </>
      )}
    </Box>
  );
}

function QuestionReview({ q, index }) {
  const correct = q.is_correct;
  return (
    <Box borderWidth="1px" borderRadius="md" bg="surface" p={4}>
      <Flex justify="space-between" align="flex-start" gap={3}>
        <HStack align="flex-start">
          <Icon
            as={correct ? FiCheckCircle : FiXCircle}
            color={correct ? "green.500" : "red.500"}
            mt={1}
          />
          <Text fontWeight={600}>
            {index}. {q.question}
          </Text>
        </HStack>
        <Badge flexShrink={0} colorScheme={correct ? "green" : "red"}>
          {q.awarded_points}/{q.max_points}
        </Badge>
      </Flex>
      <Stack spacing={1} mt={3} pl={6} fontSize="sm">
        <Text>
          <b>Your answer:</b> {q.student_answer || <i>(blank)</i>}
        </Text>
        {!correct && (
          <Text color="green.700">
            <b>Correct answer:</b> {q.correct_answer}
          </Text>
        )}
        {q.feedback && (
          <Text color="gray.600">
            <b>Feedback:</b> {q.feedback}
          </Text>
        )}
      </Stack>
    </Box>
  );
}

export default function ResultsView({ attempt, onRetake }) {
  return (
    <Box maxW="860px" mx="auto">
      <Stack spacing={4}>
        <ScoreHeader attempt={attempt} />
        <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
          <ConceptBreakdown feedback={attempt.feedback} />
          <FeedbackCard feedback={attempt.feedback} />
        </SimpleGrid>

        {onRetake && (
          <Button leftIcon={<FiRotateCcw />} variant="outline" alignSelf="flex-start" onClick={onRetake}>
            Take a similar test again
          </Button>
        )}

        <Divider />
        <Heading size="sm">Review answers</Heading>
        <Stack spacing={3}>
          {attempt.questions.map((q, i) => (
            <QuestionReview key={q.id} q={q} index={i + 1} />
          ))}
        </Stack>
      </Stack>
    </Box>
  );
}
