import { extendTheme } from "@chakra-ui/react";

export const theme = extendTheme({
  config: {
    initialColorMode: "system",
    useSystemColorMode: false,
  },
  fonts: {
    heading: `'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif`,
    body: `'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif`,
  },
  colors: {
    // Full 50-900 scale. Chakra's solid/outline button variants reach for
    // brand.200/300 (dark mode bg + hover) and brand.800, so every shade must
    // exist or colorScheme="brand" buttons render invisible in dark mode.
    brand: {
      50: "#eef2ff",
      100: "#e0e7ff",
      200: "#c7d2fe",
      300: "#a5b4fc",
      400: "#818cf8",
      500: "#4f46e5",
      600: "#4338ca",
      700: "#3730a3",
      800: "#312e81",
      900: "#1e1b4b",
    },
  },
  // Color-mode-aware tokens: use these instead of hardcoded white/gray values.
  semanticTokens: {
    colors: {
      canvas: { default: "gray.50", _dark: "gray.900" },
      surface: { default: "white", _dark: "gray.800" },
      surfaceMuted: { default: "gray.50", _dark: "gray.700" },
      borderSubtle: { default: "gray.200", _dark: "whiteAlpha.300" },
      accentSubtle: { default: "brand.50", _dark: "rgba(99,102,241,0.16)" },
    },
  },
  styles: {
    global: {
      "html, body, #root": { height: "100%" },
      body: { bg: "canvas" },
    },
  },
});
