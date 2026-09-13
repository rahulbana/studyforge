import { useEffect, useState } from "react";
import {
  Badge,
  Box,
  Center,
  Flex,
  Heading,
  HStack,
  Progress,
  SimpleGrid,
  Spinner,
  Stack,
  Stat,
  StatLabel,
  StatNumber,
  Text,
} from "@chakra-ui/react";
import { getProgress } from "../../api/assessments";
import LineChart from "../../components/common/LineChart";

const pctColor = (p) => (p >= 80 ? "green" : p >= 60 ? "yellow" : "red");

function fmtDate(iso) {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleDateString(undefined, { month: "short", day: "numeric" });
  } catch {
    return "";
  }
}

export default function ProgressDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getProgress()
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <Center py={20}>
        <Spinner size="xl" color="brand.500" />
      </Center>
    );
  }

  if (!data || data.total_attempts === 0) {
    return (
      <Box
        maxW="760px"
        mx="auto"
        borderWidth="1px"
        borderStyle="dashed"
        borderRadius="lg"
        p={10}
        textAlign="center"
        color="gray.500"
      >
        <Text fontWeight={600} mb={1}>
          No graded tests yet.
        </Text>
        <Text fontSize="sm">
          Take a test in the Evaluate tab; once it's graded, your score trend and weak areas
          will show up here.
        </Text>
      </Box>
    );
  }

  const chartPoints = data.attempts.map((a) => ({ score: a.score, label: fmtDate(a.created_at) }));

  return (
    <Box maxW="900px" mx="auto">
      <Heading size="lg" mb={4}>
        Your progress
      </Heading>

      <SimpleGrid columns={{ base: 1, sm: 3 }} spacing={4} mb={5}>
        <Stat bg="surface" borderWidth="1px" borderRadius="lg" p={4}>
          <StatLabel color="gray.500">Tests taken</StatLabel>
          <StatNumber>{data.total_attempts}</StatNumber>
        </Stat>
        <Stat bg="surface" borderWidth="1px" borderRadius="lg" p={4}>
          <StatLabel color="gray.500">Average score</StatLabel>
          <StatNumber color={`${pctColor(data.average_score)}.500`}>
            {data.average_score}%
          </StatNumber>
        </Stat>
        <Stat bg="surface" borderWidth="1px" borderRadius="lg" p={4}>
          <StatLabel color="gray.500">Best score</StatLabel>
          <StatNumber color={`${pctColor(data.best_score)}.500`}>{data.best_score}%</StatNumber>
        </Stat>
      </SimpleGrid>

      <Box bg="surface" borderWidth="1px" borderRadius="lg" p={5} mb={5}>
        <Heading size="sm" mb={4}>
          Score over time
        </Heading>
        {chartPoints.length > 1 ? (
          <LineChart points={chartPoints} />
        ) : (
          <Text fontSize="sm" color="gray.500">
            Take at least two tests to see a trend.
          </Text>
        )}
      </Box>

      <Box bg="surface" borderWidth="1px" borderRadius="lg" p={5}>
        <Flex justify="space-between" align="center" mb={4}>
          <Heading size="sm">Concepts to focus on</Heading>
          <Text fontSize="xs" color="gray.500">
            averaged across all attempts
          </Text>
        </Flex>
        <Stack spacing={4}>
          {data.concepts.map((c) => (
            <Box key={c.concept}>
              <Flex justify="space-between" mb={1}>
                <HStack>
                  <Text fontSize="sm" fontWeight={600}>
                    {c.concept}
                  </Text>
                  {c.weak_count >= 2 && (
                    <Badge colorScheme="red" variant="subtle">
                      weak {c.weak_count}×
                    </Badge>
                  )}
                </HStack>
                <Text fontSize="sm" color="gray.500">
                  {c.avg_percentage}% · {c.attempts} test{c.attempts === 1 ? "" : "s"}
                </Text>
              </Flex>
              <Progress
                value={c.avg_percentage}
                colorScheme={pctColor(c.avg_percentage)}
                borderRadius="full"
                size="sm"
              />
            </Box>
          ))}
        </Stack>
      </Box>
    </Box>
  );
}
