import {
  Badge,
  Box,
  Button,
  ButtonGroup,
  Flex,
  Heading,
  HStack,
  IconButton,
  useColorMode,
} from "@chakra-ui/react";
import { FiBookOpen, FiClipboard, FiMoon, FiSun, FiUploadCloud } from "react-icons/fi";
import Logo from "../common/Logo";

export default function Header({ health, mode, onModeChange, onUpload }) {
  const { colorMode, toggleColorMode } = useColorMode();
  return (
    <Flex
      as="header"
      align="center"
      justify="space-between"
      px={{ base: 4, md: 6 }}
      py={3}
      bg="surface"
      borderBottomWidth="1px"
      boxShadow="sm"
      zIndex={2}
      gap={3}
    >
      <HStack spacing={2.5}>
        <Logo size={28} />
        <Heading size="md" letterSpacing="-0.02em" display={{ base: "none", sm: "block" }}>
          Study
          <Box as="span" color="brand.500">
            Forge
          </Box>
        </Heading>
      </HStack>

      <ButtonGroup size="sm" isAttached variant="outline">
        <Button
          leftIcon={<FiBookOpen />}
          colorScheme={mode === "study" ? "brand" : "gray"}
          variant={mode === "study" ? "solid" : "outline"}
          onClick={() => onModeChange("study")}
        >
          Study
        </Button>
        <Button
          leftIcon={<FiClipboard />}
          colorScheme={mode === "assess" ? "brand" : "gray"}
          variant={mode === "assess" ? "solid" : "outline"}
          onClick={() => onModeChange("assess")}
        >
          Evaluate
        </Button>
      </ButtonGroup>

      <HStack spacing={3}>
        {health && !health.openai_configured && (
          <Badge colorScheme="red" variant="subtle">
            OpenAI key missing
          </Badge>
        )}
        <IconButton
          aria-label="Toggle color mode"
          variant="ghost"
          icon={colorMode === "light" ? <FiMoon /> : <FiSun />}
          onClick={toggleColorMode}
        />
        {mode === "study" && (
          <Button leftIcon={<FiUploadCloud />} colorScheme="brand" onClick={onUpload}>
            Upload chapter
          </Button>
        )}
      </HStack>
    </Flex>
  );
}
