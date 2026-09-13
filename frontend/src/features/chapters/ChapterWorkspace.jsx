import {
  Badge,
  Box,
  Flex,
  Heading,
  HStack,
  Stack,
  Tab,
  TabList,
  TabPanel,
  TabPanels,
  Tabs,
  Text,
  Tooltip,
} from "@chakra-ui/react";
import NotesPanel from "./NotesPanel";
import ExportMenu from "./ExportMenu";
import SourcesPanel from "./SourcesPanel";
import QuestionsPanel from "../questions/QuestionsPanel";
import { formatUsd } from "../../lib/format";

// The main working area for a single chapter: notes + question bank tabs.
export default function ChapterWorkspace({
  chapter,
  questions,
  setQuestions,
  regenerating,
  onRegenerate,
  onStreamComplete,
}) {
  return (
    <Stack spacing={4} maxW="900px" mx="auto">
      <Flex justify="space-between" align="flex-start" wrap="wrap" gap={3}>
        <Box>
          <Heading size="lg">{chapter.chapter_name}</Heading>
          <Text color="gray.500">
            {chapter.class_name} · {chapter.subject}
          </Text>
        </Box>
        <HStack>
          {chapter.cost_usd > 0 && (
            <Tooltip
              label={`${chapter.tokens_input + chapter.tokens_output} tokens (in ${chapter.tokens_input} / out ${chapter.tokens_output})`}
            >
              <Badge colorScheme="purple" variant="subtle" fontSize="0.8em" px={2} py={1} borderRadius="md">
                ≈ {formatUsd(chapter.cost_usd)}
              </Badge>
            </Tooltip>
          )}
          <ExportMenu chapter={chapter} questionCount={questions.length} />
        </HStack>
      </Flex>

      <Tabs colorScheme="brand" isLazy lazyBehavior="keepMounted">
        <TabList>
          <Tab>Notes</Tab>
          <Tab>
            Questions{" "}
            {questions.length > 0 && (
              <Badge ml={2} borderRadius="full">
                {questions.length}
              </Badge>
            )}
          </Tab>
          <Tab>
            Sources{" "}
            {chapter.sources?.length > 0 && (
              <Badge ml={2} borderRadius="full">
                {chapter.sources.length}
              </Badge>
            )}
          </Tab>
        </TabList>
        <TabPanels>
          <TabPanel px={0}>
            <NotesPanel
              chapter={chapter}
              onRegenerate={onRegenerate}
              regenerating={regenerating}
              onStreamComplete={onStreamComplete}
            />
          </TabPanel>
          <TabPanel px={0}>
            <QuestionsPanel chapter={chapter} questions={questions} setQuestions={setQuestions} />
          </TabPanel>
          <TabPanel px={0}>
            <SourcesPanel chapter={chapter} />
          </TabPanel>
        </TabPanels>
      </Tabs>
    </Stack>
  );
}
