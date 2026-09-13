import { useState } from "react";
import {
  Alert,
  AlertIcon,
  Box,
  Button,
  Center,
  Flex,
  Icon,
  Text,
  useDisclosure,
  useToast,
} from "@chakra-ui/react";
import { FiFileText, FiPlus } from "react-icons/fi";
import { deleteChapter } from "./api/chapters";
import { useHealth } from "./hooks/useHealth";
import { useChapters } from "./hooks/useChapters";
import { useChapterWorkspace } from "./hooks/useChapterWorkspace";
import FullPageLoader from "./components/common/FullPageLoader";
import Header from "./components/layout/Header";
import Sidebar from "./components/layout/Sidebar";
import UploadModal from "./features/chapters/UploadModal";
import ChapterWorkspace from "./features/chapters/ChapterWorkspace";
import AssessSection from "./features/assess/AssessSection";

export default function App() {
  const toast = useToast();
  const uploadModal = useDisclosure();
  const health = useHealth();
  const [mode, setMode] = useState("study");
  const { chapters, refresh, loading: chaptersLoading } = useChapters();
  const workspace = useChapterWorkspace({
    onNotesSettled: refresh,
    onError: (msg) => toast({ title: msg, status: "error" }),
  });

  const onCreated = async (chapter) => {
    await refresh();
    workspace.open(chapter.id);
  };

  const removeChapter = async (id) => {
    if (!window.confirm("Delete this chapter and all its questions?")) return;
    await deleteChapter(id);
    if (workspace.selectedId === id) workspace.clear();
    refresh();
  };

  return (
    <Flex direction="column" h="100vh">
      {(chaptersLoading || workspace.loading) && (
        <FullPageLoader label={chaptersLoading ? "Loading your chapters…" : "Opening chapter…"} />
      )}
      <Header
        health={health}
        mode={mode}
        onModeChange={setMode}
        onUpload={uploadModal.onOpen}
      />

      {health && !health.openai_configured && (
        <Alert status="warning" fontSize="sm">
          <AlertIcon />
          Add your <code>&nbsp;OPENAI_API_KEY&nbsp;</code> to <code>&nbsp;backend/.env&nbsp;</code>{" "}
          and restart the backend to enable generation.
        </Alert>
      )}

      {mode === "assess" ? (
        <AssessSection />
      ) : (
        <Flex flex="1" overflow="hidden">
        <Sidebar
          chapters={chapters}
          selectedId={workspace.selectedId}
          onSelect={workspace.open}
          onDelete={removeChapter}
        />

        <Box flex="1" overflowY="auto" p={{ base: 4, md: 6 }}>
          {!workspace.chapter ? (
            <Center h="100%" flexDir="column" gap={3} color="gray.400" textAlign="center">
              <Icon as={FiFileText} boxSize={12} />
              <Text>Select a chapter, or upload a new PDF to get started.</Text>
              <Button
                leftIcon={<FiPlus />}
                colorScheme="brand"
                variant="outline"
                onClick={uploadModal.onOpen}
              >
                Upload chapter PDF
              </Button>
            </Center>
          ) : (
            <ChapterWorkspace
              chapter={workspace.chapter}
              questions={workspace.questions}
              setQuestions={workspace.setQuestions}
              regenerating={workspace.regenerating}
              onRegenerate={workspace.regenerate}
              onStreamComplete={(id) => {
                workspace.reloadChapter(id);
                refresh();
              }}
            />
          )}
        </Box>
        </Flex>
      )}

      <UploadModal
        isOpen={uploadModal.isOpen}
        onClose={uploadModal.onClose}
        onCreated={onCreated}
      />
    </Flex>
  );
}
