// Background Component

"use client";

export default function Background() {
  return (
    <div className="absolute inset-0 bg-white">
      <svg
        className="absolute inset-0 w-full h-full opacity-70 text-gray-300"
        xmlns="http://www.w3.org/2000/svg"
        preserveAspectRatio="xMidYMid slice"
      >
        <defs>
          <pattern
            id="veritium-bg"
            width="120"
            height="120"
            patternUnits="userSpaceOnUse"
          >
            {/* Magnifying glass */}
            <circle
              cx="20"
              cy="20"
              r="8"
              stroke="currentColor"
              strokeWidth="1"
              fill="none"
            />
            <line
              x1="26"
              y1="26"
              x2="35"
              y2="35"
              stroke="currentColor"
              strokeWidth="1"
            />
            {/* Check mark */}
            <path
              d="M60 25 l5 5 l10 -10"
              stroke="currentColor"
              strokeWidth="1.5"
              fill="none"
            />
            {/* X mark */}
            <path
              d="M90 15 l10 10 M100 15 l-10 10"
              stroke="currentColor"
              strokeWidth="1.5"
            />
            {/* Document */}
            <rect
              x="60"
              y="60"
              width="20"
              height="25"
              rx="2"
              stroke="currentColor"
              strokeWidth="1"
              fill="none"
            />
            <line
              x1="62"
              y1="65"
              x2="78"
              y2="65"
              stroke="currentColor"
              strokeWidth="0.8"
            />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#veritium-bg)" />
      </svg>
    </div>
  );
}
