import { useRef, useState } from "react";
import {
  Button,
  FormControl,
  FormLabel,
  Input,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  Stack,
  Text,
  useToast,
} from "@chakra-ui/react";
import { FiUploadCloud } from "react-icons/fi";
import { uploadChapter } from "../../api/chapters";
import { errorMessage } from "../../lib/apiClient";

const EMPTY_META = { class_name: "", subject: "", chapter_name: "" };

// Pick a PDF, then confirm class / subject / chapter name before uploading.
export default function UploadModal({ isOpen, onClose, onCreated }) {
  const [file, setFile] = useState(null);
  const [meta, setMeta] = useState(EMPTY_META);
  const [busy, setBusy] = useState(false);
  const fileRef = useRef(null);
  const toast = useToast();

  const close = () => {
    setFile(null);
    setMeta(EMPTY_META);
    onClose();
  };

  const pickFile = (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setFile(f);
    if (!meta.chapter_name) {
      setMeta((m) => ({ ...m, chapter_name: f.name.replace(/\.pdf$/i, "") }));
    }
  };

  const canSubmit =
    file && meta.class_name.trim() && meta.subject.trim() && meta.chapter_name.trim();

  const submit = async () => {
    if (!canSubmit) return;
    setBusy(true);
    try {
      const chapter = await uploadChapter(file, meta);
      toast({ title: "Uploaded. Generating notes…", status: "success", duration: 2500 });
      onCreated(chapter);
      close();
    } catch (err) {
      toast({ title: "Upload failed", description: errorMessage(err), status: "error", duration: 6000 });
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={close} size="lg" closeOnOverlayClick={!busy}>
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>Upload a chapter PDF</ModalHeader>
        <ModalCloseButton />
        <ModalBody>
          <Stack spacing={4}>
            <Button
              leftIcon={<FiUploadCloud />}
              variant="outline"
              onClick={() => fileRef.current?.click()}
              h="90px"
              borderStyle="dashed"
              borderWidth="2px"
              colorScheme="brand"
            >
              {file ? file.name : "Choose PDF file"}
            </Button>
            <input
              ref={fileRef}
              type="file"
              accept="application/pdf"
              onChange={pickFile}
              style={{ display: "none" }}
            />
            <Text fontSize="sm" color="gray.500">
              We need a little context so the notes and questions are accurate.
            </Text>
            <FormControl isRequired>
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
            <FormControl isRequired>
              <FormLabel>Chapter name</FormLabel>
              <Input
                placeholder="e.g. Light — Reflection and Refraction"
                value={meta.chapter_name}
                onChange={(e) => setMeta({ ...meta, chapter_name: e.target.value })}
              />
            </FormControl>
          </Stack>
        </ModalBody>
        <ModalFooter>
          <Button variant="ghost" mr={3} onClick={close} isDisabled={busy}>
            Cancel
          </Button>
          <Button colorScheme="brand" onClick={submit} isLoading={busy} isDisabled={!canSubmit}>
            Upload & generate notes
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}
