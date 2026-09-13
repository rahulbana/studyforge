// Canonical question types (mirrors the backend enum).
export const QUESTION_TYPES = [
  { key: "true_false", label: "True / False" },
  { key: "mcq", label: "Multiple Choice" },
  { key: "fill_blank", label: "Fill in the Blanks" },
  { key: "one_word", label: "One Word Answer" },
  { key: "short_answer", label: "Short Answer" },
  { key: "long_answer", label: "Long Answer" },
  { key: "case_based", label: "Case Based" },
];

export const QUESTION_TYPE_LABEL = QUESTION_TYPES.reduce(
  (acc, t) => ({ ...acc, [t.key]: t.label }),
  {},
);
