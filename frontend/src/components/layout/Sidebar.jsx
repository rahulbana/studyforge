import { Badge, Box, Flex, HStack, IconButton, Spinner, Stack, Text } from "@chakra-ui/react";
import { FiTrash2 } from "react-icons/fi";

export default function Sidebar({ chapters, selectedId, onSelect, onDelete }) {
  return (
    <Box
      w={{ base: "40%", md: "300px" }}
      minW="220px"
      borderRightWidth="1px"
      bg="surface"
      overflowY="auto"
      p={3}
    >
      <Text fontSize="xs" fontWeight={700} color="gray.500" textTransform="uppercase" px={2} mb={2}>
        My chapters
      </Text>
      {chapters.length === 0 && (
        <Text fontSize="sm" color="gray.400" px={2}>
          No chapters yet.
        </Text>
      )}
      <Stack spacing={1}>
        {chapters.map((c) => (
          <Flex
            key={c.id}
            align="center"
            justify="space-between"
            px={3}
            py={2}
            borderRadius="md"
            cursor="pointer"
            bg={selectedId === c.id ? "accentSubtle" : "transparent"}
            _hover={{ bg: selectedId === c.id ? "accentSubtle" : "surfaceMuted" }}
            onClick={() => onSelect(c.id)}
          >
            <Box overflow="hidden">
              <Text fontSize="sm" fontWeight={600} noOfLines={1}>
                {c.chapter_name}
              </Text>
              <Text fontSize="xs" color="gray.500" noOfLines={1}>
                {c.class_name} · {c.subject}
              </Text>
            </Box>
            <HStack spacing={1} flexShrink={0}>
              {c.notes_status === "pending" && <Spinner size="xs" color="brand.500" />}
              {c.question_count > 0 && (
                <Badge borderRadius="full" fontSize="0.65rem">
                  {c.question_count}
                </Badge>
              )}
              <IconButton
                aria-label="delete chapter"
                icon={<FiTrash2 />}
                size="xs"
                variant="ghost"
                colorScheme="red"
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete(c.id);
                }}
              />
            </HStack>
          </Flex>
        ))}
      </Stack>
    </Box>
  );
}
