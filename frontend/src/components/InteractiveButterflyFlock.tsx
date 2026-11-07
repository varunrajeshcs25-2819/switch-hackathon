import React, {useEffect, useRef} from "react"

interface ButterflyData {
  id: number
  homeXRatio: number
  homeYRatio: number
  currentX: number
  currentY: number
  targetX: number
  targetY: number
  size: number
  orbitRadius: number
  orbitSpeed: number
  orbitAngle: number
  lerpSpeed: number
  flapSpeed: number
  glideSpeed: number
  opacity: number
  scale: number
  isGliding: boolean
}

interface InteractiveButterflyFlockProps {
  containerRef: React.RefObject<HTMLElement | null>
}

export const InteractiveButterflyFlock: React.FC<InteractiveButterflyFlockProps> = ({
  containerRef,
}) => {
  const butterflyRefs = useRef<(HTMLDivElement | null)[]>([])
  const animFrameRef = useRef<number | null>(null)
  const isHoveredRef = useRef(false)
  const mousePosRef = useRef({x: 0, y: 0})
  const timeRef = useRef(0)

  // 7 distinct miniature butterflies with lifelike flapping parameters
  const butterfliesRef = useRef<ButterflyData[]>([
    {
      id: 1,
      homeXRatio: 0.12,
      homeYRatio: 0.25,
      currentX: 0,
      currentY: 0,
      targetX: 0,
      targetY: 0,
      size: 34,
      orbitRadius: 55,
      orbitSpeed: 0.9,
      orbitAngle: 0.4,
      lerpSpeed: 0.048,
      flapSpeed: 0.32,
      glideSpeed: 1.6,
      opacity: 0.88,
      scale: 0.95,
      isGliding: false,
    },
    {
      id: 2,
      homeXRatio: 0.16,
      homeYRatio: 0.75,
      currentX: 0,
      currentY: 0,
      targetX: 0,
      targetY: 0,
      size: 28,
      orbitRadius: 85,
      orbitSpeed: -0.7,
      orbitAngle: 1.8,
      lerpSpeed: 0.038,
      flapSpeed: 0.36,
      glideSpeed: 1.9,
      opacity: 0.78,
      scale: 0.82,
      isGliding: false,
    },
    {
      id: 3,
      homeXRatio: 0.85,
      homeYRatio: 0.22,
      currentX: 0,
      currentY: 0,
      targetX: 0,
      targetY: 0,
      size: 36,
      orbitRadius: 65,
      orbitSpeed: 0.8,
      orbitAngle: 3.2,
      lerpSpeed: 0.052,
      flapSpeed: 0.29,
      glideSpeed: 1.5,
      opacity: 0.9,
      scale: 1.0,
      isGliding: false,
    },
    {
      id: 4,
      homeXRatio: 0.88,
      homeYRatio: 0.78,
      currentX: 0,
      currentY: 0,
      targetX: 0,
      targetY: 0,
      size: 26,
      orbitRadius: 95,
      orbitSpeed: -0.6,
      orbitAngle: 4.6,
      lerpSpeed: 0.032,
      flapSpeed: 0.4,
      glideSpeed: 2.1,
      opacity: 0.72,
      scale: 0.75,
      isGliding: false,
    },
    {
      id: 5,
      homeXRatio: 0.32,
      homeYRatio: 0.18,
      currentX: 0,
      currentY: 0,
      targetX: 0,
      targetY: 0,
      size: 30,
      orbitRadius: 75,
      orbitSpeed: 0.65,
      orbitAngle: 2.3,
      lerpSpeed: 0.042,
      flapSpeed: 0.34,
      glideSpeed: 1.7,
      opacity: 0.82,
      scale: 0.88,
      isGliding: false,
    },
    {
      id: 6,
      homeXRatio: 0.68,
      homeYRatio: 0.15,
      currentX: 0,
      currentY: 0,
      targetX: 0,
      targetY: 0,
      size: 28,
      orbitRadius: 105,
      orbitSpeed: -0.75,
      orbitAngle: 5.4,
      lerpSpeed: 0.035,
      flapSpeed: 0.38,
      glideSpeed: 2.0,
      opacity: 0.75,
      scale: 0.82,
      isGliding: false,
    },
    {
      id: 7,
      homeXRatio: 0.92,
      homeYRatio: 0.48,
      currentX: 0,
      currentY: 0,
      targetX: 0,
      targetY: 0,
      size: 32,
      orbitRadius: 80,
      orbitSpeed: 0.85,
      orbitAngle: 0.9,
      lerpSpeed: 0.045,
      flapSpeed: 0.31,
      glideSpeed: 1.6,
      opacity: 0.82,
      scale: 0.9,
      isGliding: false,
    },
  ])

  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    // Accessibility check
    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches
    if (prefersReducedMotion) {
      const rect = container.getBoundingClientRect()
      butterfliesRef.current.forEach((b, idx) => {
        const el = butterflyRefs.current[idx]
        if (el) {
          const x = b.homeXRatio * rect.width
          const y = b.homeYRatio * rect.height
          el.style.transform = `translate3d(${x}px, ${y}px, 0)`
          el.style.opacity = `${b.opacity * 0.7}`
        }
      })
      return
    }

    const initRect = container.getBoundingClientRect()
    butterfliesRef.current.forEach((b) => {
      const startX = b.homeXRatio * initRect.width
      const startY = b.homeYRatio * initRect.height
      b.currentX = startX
      b.currentY = startY
      b.targetX = startX
      b.targetY = startY
    })

    const handleMouseMove = (e: MouseEvent) => {
      const rect = container.getBoundingClientRect()
      mousePosRef.current = {
        x: e.clientX - rect.left,
        y: e.clientY - rect.top,
      }
      isHoveredRef.current = true
    }

    const handleMouseEnter = (e: MouseEvent) => {
      const rect = container.getBoundingClientRect()
      mousePosRef.current = {
        x: e.clientX - rect.left,
        y: e.clientY - rect.top,
      }
      isHoveredRef.current = true
    }

    const handleMouseLeave = () => {
      isHoveredRef.current = false
    }

    container.addEventListener("mousemove", handleMouseMove, {passive: true})
    container.addEventListener("mouseenter", handleMouseEnter, {passive: true})
    container.addEventListener("mouseleave", handleMouseLeave, {passive: true})

    // High performance RAF compositor animation loop
    const animate = () => {
      timeRef.current += 0.016
      const time = timeRef.current
      const rect = container.getBoundingClientRect()
      const width = rect.width
      const height = rect.height

      butterfliesRef.current.forEach((b, idx) => {
        const el = butterflyRefs.current[idx]
        if (!el) return

        if (isHoveredRef.current) {
          const orbitAngle = b.orbitAngle + time * b.orbitSpeed
          const offsetX = Math.cos(orbitAngle) * b.orbitRadius
          const offsetY = Math.sin(orbitAngle) * (b.orbitRadius * 0.65)
          const wanderX = Math.sin(time * 2.2 + b.id) * 14
          const wanderY = Math.cos(time * 2.0 + b.id) * 10

          b.targetX = mousePosRef.current.x + offsetX + wanderX
          b.targetY = mousePosRef.current.y + offsetY + wanderY
        } else {
          const homeX = b.homeXRatio * width
          const homeY = b.homeYRatio * height
          const wanderX = Math.sin(time * 0.8 + b.id * 1.3) * 24
          const wanderY = Math.cos(time * 0.7 + b.id * 1.1) * 18

          b.targetX = homeX + wanderX
          b.targetY = homeY + wanderY
        }

        b.targetX = Math.max(16, Math.min(width - 32, b.targetX))
        b.targetY = Math.max(16, Math.min(height - 32, b.targetY))

        const dx = b.targetX - b.currentX
        const dy = b.targetY - b.currentY

        b.currentX += dx * b.lerpSpeed
        b.currentY += dy * b.lerpSpeed

        const velocity = Math.hypot(dx, dy)
        const tilt = Math.max(-28, Math.min(28, dx * 0.95))
        const pitch = Math.max(-18, Math.min(18, dy * 0.5))

        const shouldGlide = velocity < 0.85 && (Math.sin(time * 1.2 + b.id) > 0.45)
        if (b.isGliding !== shouldGlide) {
          b.isGliding = shouldGlide
          if (shouldGlide) {
            el.classList.add("flock-gliding")
          } else {
            el.classList.remove("flock-gliding")
          }
        }

        el.style.transform = `translate3d(${b.currentX}px, ${b.currentY}px, 0) rotateZ(${tilt}deg) rotateX(${pitch}deg) scale(${b.scale})`
      })

      animFrameRef.current = requestAnimationFrame(animate)
    }

    animFrameRef.current = requestAnimationFrame(animate)

    return () => {
      container.removeEventListener("mousemove", handleMouseMove)
      container.removeEventListener("mouseenter", handleMouseEnter)
      container.removeEventListener("mouseleave", handleMouseLeave)
      if (animFrameRef.current) {
        cancelAnimationFrame(animFrameRef.current)
      }
    }
  }, [containerRef])

  return (
    <div
      className="pointer-events-none absolute inset-0 z-0 overflow-hidden select-none"
      aria-hidden="true"
    >
      {butterfliesRef.current.map((b, idx) => (
        <div
          key={b.id}
          ref={(el) => {
            butterflyRefs.current[idx] = el
          }}
          className="absolute top-0 left-0 transition-opacity duration-700 flock-butterfly-wrap"
          style={
            {
              width: `${b.size}px`,
              height: `${b.size * 0.72}px`,
              opacity: b.opacity,
              willChange: "transform",
              "--flap-speed": `${b.flapSpeed}s`,
              "--glide-speed": `${b.glideSpeed}s`,
            } as React.CSSProperties
          }
        >
          {/* 3-Part 3D Architecture */}
          <div className="flock-wing-container">
            {/* Left Wing (Hinged to the right at 100% 50%) */}
            <div
              className="flock-wing-l"
              style={{
                width: `${b.size * 0.46}px`,
                height: `${b.size * 0.72}px`,
              }}
            >
              <svg
                viewBox="0 0 115 180"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                className="w-full h-full overflow-visible"
                style={{filter: "var(--butterfly-filter)"}}
              >
                <defs>
                  <linearGradient id={`flockGradL_${b.id}`} x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="var(--wing-grad-start)" stopOpacity="0.95" />
                    <stop offset="50%" stopColor="var(--wing-grad-mid)" stopOpacity="0.9" />
                    <stop offset="100%" stopColor="var(--wing-grad-end)" stopOpacity="0.95" />
                  </linearGradient>
                </defs>
                {/* Forewing */}
                <path
                  d="M 115 88 C 100 45, 60 12, 22 18 C 3 22, -6 50, 10 78 C 22 96, 52 114, 113 94 Z"
                  fill={`url(#flockGradL_${b.id})`}
                  stroke="var(--wing-stroke)"
                  strokeWidth="1.2"
                />
                {/* Hindwing */}
                <path
                  d="M 113 96 C 76 110, 28 124, 32 152 C 36 170, 70 170, 89 148 C 101 134, 110 116, 115 106 Z"
                  fill="var(--wing-subtle-start)"
                  fillOpacity="0.75"
                  stroke="var(--wing-subtle-stroke)"
                  strokeWidth="1.2"
                />
              </svg>
            </div>

            {/* Center Thorax, Head & Antennae */}
            <div
              className="flock-body relative z-10 flex-shrink-0"
              style={{
                width: `${b.size * 0.08}px`,
                height: `${b.size * 0.72}px`,
              }}
            >
              <svg
                viewBox="0 0 20 180"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                className="w-full h-full overflow-visible"
              >
                <path
                  d="M 8 68 C 2 50, -10 38, -18 36"
                  stroke="var(--butterfly-antennae)"
                  strokeWidth="1.2"
                  strokeLinecap="round"
                />
                <path
                  d="M 12 68 C 18 50, 30 38, 38 36"
                  stroke="var(--butterfly-antennae)"
                  strokeWidth="1.2"
                  strokeLinecap="round"
                />
                <circle cx="10" cy="70" r="4.5" fill="var(--butterfly-antennae-tip)" />
                <ellipse cx="10" cy="100" rx="4.5" ry="30" fill="var(--wing-subtle-mid)" stroke="var(--wing-stroke)" strokeWidth="1.2" />
              </svg>
            </div>

            {/* Right Wing (Hinged to the left at 0% 50%) */}
            <div
              className="flock-wing-r"
              style={{
                width: `${b.size * 0.46}px`,
                height: `${b.size * 0.72}px`,
              }}
            >
              <svg
                viewBox="0 0 115 180"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                className="w-full h-full overflow-visible"
                style={{filter: "var(--butterfly-filter)"}}
              >
                <defs>
                  <linearGradient id={`flockGradR_${b.id}`} x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="var(--wing-grad-start)" stopOpacity="0.95" />
                    <stop offset="50%" stopColor="var(--wing-grad-mid)" stopOpacity="0.9" />
                    <stop offset="100%" stopColor="var(--wing-grad-end)" stopOpacity="0.95" />
                  </linearGradient>
                </defs>
                <path
                  d="M 0 88 C 15 45, 55 12, 93 18 C 112 22, 121 50, 105 78 C 93 96, 63 114, 2 94 Z"
                  fill={`url(#flockGradR_${b.id})`}
                  stroke="var(--wing-stroke)"
                  strokeWidth="1.2"
                />
                <path
                  d="M 2 96 C 39 110, 87 124, 83 152 C 79 170, 45 170, 26 148 C 14 134, 5 116, 0 106 Z"
                  fill="var(--wing-subtle-start)"
                  fillOpacity="0.75"
                  stroke="var(--wing-subtle-stroke)"
                  strokeWidth="1.2"
                />
              </svg>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
