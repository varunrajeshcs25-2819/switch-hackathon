import React from "react"

interface ButterflyIconProps {
  size?: "sm" | "md" | "lg" | "hero"
  interactive?: boolean
  className?: string
}

export const ButterflyIcon: React.FC<ButterflyIconProps> = ({
  size = "md",
  interactive = true,
  className = "",
}) => {
  const sizeMap = {
    sm: "w-7 h-7",
    md: "w-12 h-12",
    lg: "w-24 h-24",
    hero: "w-64 h-64 md:w-80 md:h-80",
  }

  const dimensions = sizeMap[size] || sizeMap.md

  return (
    <div
      className={`relative inline-flex items-center justify-center ${interactive ? "butterfly-container" : ""} ${className}`}
      aria-label="PatchPilot Metamorphic Butterfly Emblem"
    >
      {/* Theme Adaptive Ambient Radiance Aura */}
      <div
        className="absolute inset-0 rounded-full butterfly-glow pointer-events-none"
        style={{
          background: "var(--butterfly-glow-bg)",
          filter: "blur(14px)",
          transform: "scale(1.3)",
        }}
      />

      <svg
        viewBox="0 0 240 200"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className={`${dimensions} select-none transition-transform duration-500 hover:scale-105`}
        style={{
          filter: "var(--butterfly-filter)",
        }}
      >
        <defs>
          {/* Dynamic 135deg Theme Adaptive Linear Gradients */}
          <linearGradient id="wingGradTeal" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="var(--wing-grad-start)" stopOpacity="0.95" />
            <stop offset="50%" stopColor="var(--wing-grad-mid)" stopOpacity="0.92" />
            <stop offset="100%" stopColor="var(--wing-grad-end)" stopOpacity="0.95" />
          </linearGradient>

          <linearGradient id="wingGradMint" x1="100%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="var(--wing-subtle-start)" stopOpacity="0.9" />
            <stop offset="55%" stopColor="var(--wing-subtle-mid)" stopOpacity="0.88" />
            <stop offset="100%" stopColor="var(--wing-subtle-end)" stopOpacity="0.95" />
          </linearGradient>

          <linearGradient id="bodyGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="var(--butterfly-body-start)" />
            <stop offset="50%" stopColor="var(--butterfly-body-mid)" />
            <stop offset="100%" stopColor="var(--butterfly-body-end)" />
          </linearGradient>
        </defs>

        {/* LEFT WING */}
        <g className="butterfly-wing-left" id="leftWingGroup">
          {/* Forewing Main Shell */}
          <path
            d="M 120 95 C 105 50, 65 15, 25 22 C 5 26, -5 55, 12 85 C 24 105, 55 125, 118 102 Z"
            fill="url(#wingGradTeal)"
            stroke="var(--wing-stroke)"
            strokeWidth="1.2"
            strokeOpacity="0.9"
          />
          {/* Forewing Geometric Facet 1 */}
          <path
            d="M 115 90 C 80 55, 45 35, 30 30 C 50 65, 80 85, 115 90 Z"
            fill="var(--wing-facet1-fill)"
            stroke="var(--wing-facet1-stroke)"
            strokeWidth="0.8"
            strokeDasharray="2 2"
          />
          {/* Forewing Geometric Facet 2 */}
          <path
            d="M 30 30 C 15 50, 15 75, 35 90 C 65 92, 95 95, 115 98 Z"
            fill="var(--wing-facet2-fill)"
            stroke="var(--wing-facet2-stroke)"
            strokeWidth="0.8"
          />

          {/* Hindwing Shell */}
          <path
            d="M 118 105 C 80 120, 30 135, 35 165 C 40 185, 75 185, 95 160 C 108 145, 115 125, 120 115 Z"
            fill="url(#wingGradMint)"
            stroke="var(--wing-subtle-stroke)"
            strokeWidth="1.2"
            strokeOpacity="0.9"
          />
          {/* Hindwing Cell Line */}
          <path
            d="M 118 112 C 85 130, 65 150, 60 170"
            stroke="var(--wing-stroke)"
            strokeWidth="0.8"
            strokeOpacity="0.8"
          />
          <circle cx="65" cy="155" r="2.5" fill="var(--butterfly-dots-1)" opacity="0.9" />
          <circle cx="85" cy="140" r="1.8" fill="var(--butterfly-dots-2)" opacity="0.9" />
        </g>

        {/* RIGHT WING */}
        <g className="butterfly-wing-right" id="rightWingGroup">
          {/* Forewing Main Shell */}
          <path
            d="M 120 95 C 135 50, 175 15, 215 22 C 235 26, 245 55, 228 85 C 216 105, 185 125, 122 102 Z"
            fill="url(#wingGradTeal)"
            stroke="var(--wing-stroke)"
            strokeWidth="1.2"
            strokeOpacity="0.9"
          />
          {/* Forewing Geometric Facet 1 */}
          <path
            d="M 125 90 C 160 55, 195 35, 210 30 C 190 65, 160 85, 125 90 Z"
            fill="var(--wing-facet1-fill)"
            stroke="var(--wing-facet1-stroke)"
            strokeWidth="0.8"
            strokeDasharray="2 2"
          />
          {/* Forewing Geometric Facet 2 */}
          <path
            d="M 210 30 C 225 50, 225 75, 205 90 C 175 92, 145 95, 125 98 Z"
            fill="var(--wing-facet2-fill)"
            stroke="var(--wing-facet2-stroke)"
            strokeWidth="0.8"
          />

          {/* Hindwing Shell */}
          <path
            d="M 122 105 C 160 120, 210 135, 205 165 C 200 185, 165 185, 145 160 C 132 145, 125 125, 120 115 Z"
            fill="url(#wingGradMint)"
            stroke="var(--wing-subtle-stroke)"
            strokeWidth="1.2"
            strokeOpacity="0.9"
          />
          {/* Hindwing Cell Line */}
          <path
            d="M 122 112 C 155 130, 175 150, 180 170"
            stroke="var(--wing-stroke)"
            strokeWidth="0.8"
            strokeOpacity="0.8"
          />
          <circle cx="175" cy="155" r="2.5" fill="var(--butterfly-dots-1)" opacity="0.9" />
          <circle cx="155" cy="140" r="1.8" fill="var(--butterfly-dots-2)" opacity="0.9" />
        </g>

        {/* METAMORPHIC CENTRAL CORE (Body & Antennae) */}
        <g id="butterflyBody">
          {/* Antennae */}
          <path
            d="M 119 75 C 112 55, 95 40, 85 38"
            stroke="var(--butterfly-antennae)"
            strokeWidth="1.2"
            strokeLinecap="round"
          />
          <circle cx="85" cy="38" r="2.2" fill="var(--butterfly-antennae-tip)" />

          <path
            d="M 121 75 C 128 55, 145 40, 155 38"
            stroke="var(--butterfly-antennae)"
            strokeWidth="1.2"
            strokeLinecap="round"
          />
          <circle cx="155" cy="38" r="2.2" fill="var(--butterfly-antennae-tip)" />

          {/* Slender Thorax and Abdomen */}
          <ellipse
            cx="120"
            cy="108"
            rx="4.2"
            ry="36"
            fill="url(#bodyGrad)"
            stroke="var(--butterfly-body-stroke)"
            strokeWidth="1"
          />
          {/* Head */}
          <circle cx="120" cy="74" r="4.5" fill="var(--butterfly-head)" />
          <circle cx="119" cy="73" r="1" fill="var(--butterfly-head-eye)" />
          <circle cx="121" cy="73" r="1" fill="var(--butterfly-head-eye)" />

          {/* Cybernetic Segment Rings */}
          <line x1="117" y1="92" x2="123" y2="92" stroke="var(--butterfly-antennae-tip)" strokeWidth="0.8" opacity="0.8" />
          <line x1="116.5" y1="104" x2="123.5" y2="104" stroke="var(--butterfly-antennae-tip)" strokeWidth="0.8" opacity="0.8" />
          <line x1="117" y1="116" x2="123" y2="116" stroke="var(--butterfly-antennae-tip)" strokeWidth="0.8" opacity="0.8" />
          <line x1="118" y1="128" x2="122" y2="128" stroke="var(--butterfly-antennae-tip)" strokeWidth="0.8" opacity="0.8" />
        </g>
      </svg>
    </div>
  )
}
