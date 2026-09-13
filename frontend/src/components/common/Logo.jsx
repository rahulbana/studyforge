// StudyForge mark: a forge "spark" above an open book, on an indigo badge.
// Legible in both light and dark (self-contained colors, no theme dependency).
export default function Logo({ size = 28, ...props }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-label="StudyForge logo"
      {...props}
    >
      <rect width="32" height="32" rx="7" fill="#4f46e5" />
      {/* forge spark */}
      <path
        d="M16 5.5c.45 3.4 3.1 6.05 6.5 6.5-3.4.45-6.05 3.1-6.5 6.5-.45-3.4-3.1-6.05-6.5-6.5 3.4-.45 6.05-3.1 6.5-6.5Z"
        fill="#ffffff"
      />
      {/* open book */}
      <path d="M6.5 21c4-1.6 8-1.6 9.5 0v5.2c-1.5-1.6-5.5-1.6-9.5 0V21Z" fill="#c7d2fe" />
      <path d="M25.5 21c-4-1.6-8-1.6-9.5 0v5.2c1.5-1.6 5.5-1.6 9.5 0V21Z" fill="#ffffff" />
    </svg>
  );
}
