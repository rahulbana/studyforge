import { useState } from "react";
import {
  Badge,
  Box,
  Button,
  Collapse,
  Flex,
  HStack,
  IconButton,
  List,
  ListItem,
  Text,
  Tooltip,
  useToast,
} from "@chakra-ui/react";
import { FiChevronDown, FiChevronUp, FiShield, FiTrash2 } from "react-icons/fi";
import { deleteQuestion, verifyQuestion } from "../../api/questions";
import { errorMessage } from "../../lib/apiClient";

const STATUS_META = {
  verified: { color: "green", label: "Verified" },
  corrected: { color: "orange", label: "Corrected" },
  needs_review: { color: "red", label: "Needs review" },
  unverified: { color: "gray", label: "Unverified" },
};

const DIFF_COLOR = { easy: "green", medium: "blue", hard: "purple", mixed: "gray" };

export default function QuestionCard({ index, question, onChanged, onDeleted }) {
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const toast = useToast();

  const status = STATUS_META[question.verification_status] || STATUS_META.unverified;

  const doVerify = async () => {
    setBusy(true);
    try {
      const updated = await verifyQuestion(question.id);
      onChanged(updated);
      toast({ title: `Answer ${updated.verification_status}`, status: "success", duration: 2000 });
    } catch (err) {
      toast({ title: "Verify failed", description: errorMessage(err), status: "error" });
    } finally {
      setBusy(false);
    }
  };

  const doDelete = async () => {
    setBusy(true);
    try {
      await deleteQuestion(question.id);
      onDeleted(question.id);
    } catch {
      toast({ title: "Delete failed", status: "error" });
      setBusy(false);
    }
  };

  return (
    <Box borderWidth="1px" borderRadius="md" p={4} bg="surface">
      <Flex justify="space-between" align="flex-start" gap={3}>
        <Text fontWeight={600}>
          {index}. {question.question}
        </Text>
        <HStack flexShrink={0}>
          <Badge colorScheme={status.color}>{status.label}</Badge>
          <Badge variant="subtle" colorScheme={DIFF_COLOR[question.difficulty] || "gray"}>
            {question.difficulty}
          </Badge>
        </HStack>
      </Flex>

      {question.options?.length > 0 && (
        <List spacing={1} mt={2} pl={1}>
          {question.options.map((opt, i) => (
            <ListItem key={i} fontSize="sm" color="gray.700">
              {String.fromCharCode(97 + i)}) {opt}
            </ListItem>
          ))}
        </List>
      )}

      <Collapse in={open} animateOpacity>
        <Box mt={3} p={3} bg="surfaceMuted" borderRadius="md">
          <Text fontSize="sm">
            <b>Answer:</b> {question.answer || <i>(none)</i>}
          </Text>
          {question.explanation && (
            <Text fontSize="sm" mt={2} color="gray.600">
              <b>Explanation:</b> {question.explanation}
            </Text>
          )}
          {question.verification_note && (
            <Text fontSize="xs" mt={2} color="gray.500" fontStyle="italic">
              Verifier: {question.verification_note}
            </Text>
          )}
        </Box>
      </Collapse>

      <Flex mt={3} justify="space-between" align="center">
        <Button
          size="xs"
          variant="ghost"
          rightIcon={open ? <FiChevronUp /> : <FiChevronDown />}
          onClick={() => setOpen((o) => !o)}
        >
          {open ? "Hide answer" : "Show answer"}
        </Button>
        <HStack>
          <Tooltip label="Verify & auto-fix this answer">
            <IconButton
              aria-label="verify"
              size="sm"
              icon={<FiShield />}
              onClick={doVerify}
              isLoading={busy}
              variant="outline"
            />
          </Tooltip>
          <Tooltip label="Delete question">
            <IconButton
              aria-label="delete"
              size="sm"
              icon={<FiTrash2 />}
              colorScheme="red"
              variant="ghost"
              onClick={doDelete}
              isDisabled={busy}
            />
          </Tooltip>
        </HStack>
      </Flex>
    </Box>
  );
}
