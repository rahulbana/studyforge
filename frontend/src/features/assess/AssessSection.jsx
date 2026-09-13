import { useState } from "react";
import {
  Badge,
  Box,
  Button,
  Center,
  Flex,
  HStack,
  IconButton,
  Spinner,
  Stack,
  Text,
  useToast,
} from "@chakra-ui/react";
import { FiBarChart2, FiPlus, FiTrash2 } from "react-icons/fi";
import { deleteAssessment } from "../../api/assessments";
import { useAssessments } from "../../hooks/useAssessments";
import { useAssessmentWorkspace } from "../../hooks/useAssessmentWorkspace";
import NewTestForm from "./NewTestForm";
import TestRunner from "./TestRunner";
import ResultsView from "./ResultsView";
import ProgressDashboard from "./ProgressDashboard";

const STATUS_BADGE = {
  generating: { label: "Generating", color: "purple" },
  ready: { label: "Ready", color: "blue" },
  grading: { label: "Grading", color: "purple" },
  error: { label: "Error", color: "red" },
};

function AttemptRow({ a, active, onOpen, onDelete }) {
  const graded = a.status === "graded";
  const badge = STATUS_BADGE[a.status];
  return (
    <Flex
      align="center"
      justify="space-between"
      px={3}
      py={2}
      borderRadius="md"
      cursor="pointer"
      bg={active ? "accentSubtle" : "transparent"}
      _hover={{ bg: active ? "accentSubtle" : "surfaceMuted" }}
      onClick={() => onOpen(a.id)}
    >
      <Box overflow="hidden">
        <Text fontSize="sm" fontWeight={600} noOfLines={1}>
          {a.topic}
        </Text>
        <Text fontSize="xs" color="gray.500" noOfLines={1}>
          {a.subject}
        </Text>
      </Box>
      <HStack spacing={1} flexShrink={0}>
        {graded ? (
          <Badge colorScheme={a.score >= 60 ? "green" : "red"}>{a.score}%</Badge>
        ) : (
          badge && <Badge colorScheme={badge.color}>{badge.label}</Badge>
        )}
        <IconButton
          aria-label="delete attempt"
          icon={<FiTrash2 />}
          size="xs"
          variant="ghost"
          colorScheme="red"
          onClick={(e) => {
            e.stopPropagation();
            onDelete(a.id);
          }}
        />
      </HStack>
    </Flex>
  );
}

export default function AssessSection() {
  const toast = useToast();
  const { assessments, refresh } = useAssessments();
  const workspace = useAssessmentWorkspace({
    onSettled: refresh,
    onError: (msg) => toast({ title: msg, status: "error" }),
  });
  const { attempt } = workspace;
  const [view, setView] = useState("workspace"); // "workspace" | "progress"

  const newTest = () => {
    setView("workspace");
    workspace.clear();
  };
  const openAttempt = (id) => {
    setView("workspace");
    workspace.open(id);
  };

  const removeAttempt = async (id) => {
    if (!window.confirm("Delete this test attempt?")) return;
    await deleteAssessment(id);
    if (attempt?.id === id) workspace.clear();
    refresh();
  };

  const renderMain = () => {
    if (!attempt) return <NewTestForm onStart={workspace.start} busy={workspace.busy} />;
    if (workspace.loading) {
      return (
        <Center py={20}>
          <Spinner size="xl" color="brand.500" />
        </Center>
      );
    }
    switch (attempt.status) {
      case "generating":
        return (
          <Center py={20} flexDir="column" gap={4}>
            <Spinner size="xl" color="brand.500" thickness="3px" />
            <Text color="gray.600">Generating your test…</Text>
          </Center>
        );
      case "grading":
        return (
          <Center py={20} flexDir="column" gap={4}>
            <Spinner size="xl" color="brand.500" thickness="3px" />
            <Text color="gray.600">Grading your answers and preparing feedback…</Text>
          </Center>
        );
      case "ready":
        return <TestRunner attempt={attempt} onSubmit={workspace.submit} busy={workspace.busy} />;
      case "graded":
        return <ResultsView attempt={attempt} onRetake={workspace.clear} />;
      case "error":
        return (
          <Center py={20} flexDir="column" gap={4} textAlign="center">
            <Text color="red.500" fontWeight={600}>
              Something went wrong with this test.
            </Text>
            <Text color="gray.500" fontSize="sm">
              {attempt.error}
            </Text>
            <Button colorScheme="brand" onClick={workspace.clear}>
              Start a new test
            </Button>
          </Center>
        );
      default:
        return null;
    }
  };

  return (
    <Flex flex="1" overflow="hidden">
      <Box
        w={{ base: "40%", md: "300px" }}
        minW="220px"
        borderRightWidth="1px"
        bg="surface"
        overflowY="auto"
        p={3}
      >
        <Button
          leftIcon={<FiPlus />}
          colorScheme="brand"
          size="sm"
          w="100%"
          mb={2}
          onClick={newTest}
        >
          New test
        </Button>
        <Button
          leftIcon={<FiBarChart2 />}
          variant={view === "progress" ? "solid" : "outline"}
          colorScheme="brand"
          size="sm"
          w="100%"
          mb={3}
          onClick={() => setView("progress")}
        >
          Progress
        </Button>
        <Text fontSize="xs" fontWeight={700} color="gray.500" textTransform="uppercase" px={2} mb={2}>
          Past attempts
        </Text>
        {assessments.length === 0 && (
          <Text fontSize="sm" color="gray.400" px={2}>
            No tests yet.
          </Text>
        )}
        <Stack spacing={1}>
          {assessments.map((a) => (
            <AttemptRow
              key={a.id}
              a={a}
              active={view === "workspace" && attempt?.id === a.id}
              onOpen={openAttempt}
              onDelete={removeAttempt}
            />
          ))}
        </Stack>
      </Box>

      <Box flex="1" overflowY="auto" p={{ base: 4, md: 6 }}>
        {view === "progress" ? <ProgressDashboard /> : renderMain()}
      </Box>
    </Flex>
  );
}
