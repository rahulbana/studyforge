import { useState } from "react";
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
  Select,
  Stack,
  Textarea,
  useToast,
} from "@chakra-ui/react";
import { QUESTION_TYPES } from "../../constants";
import { addManualQuestion } from "../../api/questions";
import { errorMessage } from "../../lib/apiClient";

const EMPTY = {
  qtype: "mcq",
  question: "",
  answer: "",
  options: "",
  explanation: "",
  difficulty: "medium",
};

export default function AddQuestionModal({ isOpen, onClose, chapterId, onAdded }) {
  const [form, setForm] = useState(EMPTY);
  const [busy, setBusy] = useState(false);
  const toast = useToast();

  const close = () => {
    setForm(EMPTY);
    onClose();
  };

  const submit = async () => {
    if (!form.question.trim()) {
      toast({ title: "Question text is required", status: "warning" });
      return;
    }
    setBusy(true);
    try {
      const payload = {
        qtype: form.qtype,
        question: form.question.trim(),
        answer: form.answer.trim(),
        explanation: form.explanation.trim(),
        difficulty: form.difficulty,
        options:
          form.qtype === "mcq"
            ? form.options.split("\n").map((s) => s.trim()).filter(Boolean)
            : [],
      };
      const created = await addManualQuestion(chapterId, payload);
      onAdded(created);
      toast({ title: "Question added", status: "success" });
      close();
    } catch (err) {
      toast({ title: "Could not add", description: errorMessage(err), status: "error" });
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={close} size="lg">
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>Add a question manually</ModalHeader>
        <ModalCloseButton />
        <ModalBody>
          <Stack spacing={3}>
            <FormControl>
              <FormLabel>Type</FormLabel>
              <Select value={form.qtype} onChange={(e) => setForm({ ...form, qtype: e.target.value })}>
                {QUESTION_TYPES.map((t) => (
                  <option key={t.key} value={t.key}>
                    {t.label}
                  </option>
                ))}
              </Select>
            </FormControl>
            <FormControl isRequired>
              <FormLabel>Question</FormLabel>
              <Textarea
                value={form.question}
                onChange={(e) => setForm({ ...form, question: e.target.value })}
                rows={3}
              />
            </FormControl>
            {form.qtype === "mcq" && (
              <FormControl>
                <FormLabel>Options (one per line)</FormLabel>
                <Textarea
                  value={form.options}
                  onChange={(e) => setForm({ ...form, options: e.target.value })}
                  rows={4}
                  placeholder={"Option A\nOption B\nOption C\nOption D"}
                />
              </FormControl>
            )}
            <FormControl>
              <FormLabel>Answer</FormLabel>
              <Textarea
                value={form.answer}
                onChange={(e) => setForm({ ...form, answer: e.target.value })}
                rows={2}
              />
            </FormControl>
            <FormControl>
              <FormLabel>Explanation (optional)</FormLabel>
              <Input
                value={form.explanation}
                onChange={(e) => setForm({ ...form, explanation: e.target.value })}
              />
            </FormControl>
          </Stack>
        </ModalBody>
        <ModalFooter>
          <Button variant="ghost" mr={3} onClick={close}>
            Cancel
          </Button>
          <Button colorScheme="brand" onClick={submit} isLoading={busy}>
            Add question
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}
