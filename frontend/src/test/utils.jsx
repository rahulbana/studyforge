import { render } from "@testing-library/react";
import { ChakraProvider } from "@chakra-ui/react";
import { theme } from "../theme";

export function renderWithChakra(ui, options) {
  return render(<ChakraProvider theme={theme}>{ui}</ChakraProvider>, options);
}
