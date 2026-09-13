import { Box, Spinner, Text, VStack } from "@chakra-ui/react";

// A full-viewport overlay loader shown while the sidebar list loads or a chapter
// is being opened.
export default function FullPageLoader({ label = "Loading…" }) {
  return (
    <Box
      position="fixed"
      inset={0}
      zIndex={2000}
      display="flex"
      alignItems="center"
      justifyContent="center"
      bg="blackAlpha.500"
      backdropFilter="blur(2px)"
      role="status"
      aria-live="polite"
      aria-label={label}
    >
      <VStack spacing={3} bg="surface" px={10} py={8} borderRadius="xl" boxShadow="2xl">
        <Spinner size="xl" thickness="4px" speed="0.7s" color="brand.500" emptyColor="borderSubtle" />
        <Text fontWeight={600}>{label}</Text>
      </VStack>
    </Box>
  );
}
