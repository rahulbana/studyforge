import { Box, useToken } from "@chakra-ui/react";

// Minimal responsive line chart for a 0-100 score series. `points` is an array
// of { score, label }. Renders as inline SVG (no chart dependency).
export default function LineChart({ points, height = 200 }) {
  const [brand, grid, muted] = useToken("colors", ["brand.500", "borderSubtle", "gray.500"]);

  const W = 640;
  const H = height;
  const padL = 34;
  const padR = 12;
  const padT = 12;
  const padB = 26;
  const innerW = W - padL - padR;
  const innerH = H - padT - padB;

  const n = points.length;
  const x = (i) => (n <= 1 ? padL + innerW / 2 : padL + (i / (n - 1)) * innerW);
  const y = (score) => padT + (1 - Math.max(0, Math.min(100, score)) / 100) * innerH;

  const line = points.map((p, i) => `${x(i)},${y(p.score)}`).join(" ");

  return (
    <Box overflowX="auto">
      <svg
        viewBox={`0 0 ${W} ${H}`}
        width="100%"
        style={{ maxWidth: "100%", height: "auto" }}
        role="img"
        aria-label="Score over time"
      >
        {/* gridlines + y labels at 0/50/100 */}
        {[0, 50, 100].map((v) => (
          <g key={v}>
            <line
              x1={padL}
              x2={W - padR}
              y1={y(v)}
              y2={y(v)}
              stroke={grid}
              strokeWidth="1"
            />
            <text x={padL - 6} y={y(v) + 3} textAnchor="end" fontSize="10" fill={muted}>
              {v}
            </text>
          </g>
        ))}

        {/* the score line */}
        {n > 1 && <polyline points={line} fill="none" stroke={brand} strokeWidth="2.5" />}

        {/* points + first/last date labels */}
        {points.map((p, i) => (
          <g key={i}>
            <circle cx={x(i)} cy={y(p.score)} r="3.5" fill={brand} />
            {(i === 0 || i === n - 1) && p.label && (
              <text
                x={x(i)}
                y={H - 8}
                textAnchor={i === 0 ? "start" : "end"}
                fontSize="10"
                fill={muted}
              >
                {p.label}
              </text>
            )}
          </g>
        ))}
      </svg>
    </Box>
  );
}
