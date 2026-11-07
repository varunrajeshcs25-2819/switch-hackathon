import React, { useEffect, useRef } from "react"
import cyberpunkCirclesGif from "../assets/cyberpunk-circles.gif"

export const CyberpunkCirclesBackground: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    let animInstance: any = null
    let isMounted = true

    // Dynamically load lottie-web for crisp vector rendering if available
    import("lottie-web")
      .then((lottieModule) => {
        if (!isMounted || !containerRef.current) return
        const lottie = lottieModule.default || lottieModule
        import("../assets/cyberpunk-circles.json").then((animData) => {
          if (!isMounted || !containerRef.current) return
          containerRef.current.innerHTML = ""
          animInstance = lottie.loadAnimation({
            container: containerRef.current,
            renderer: "svg",
            loop: true,
            autoplay: true,
            animationData: animData.default || animData,
          })
        }).catch(() => {})
      })
      .catch(() => {})

    return () => {
      isMounted = false
      if (animInstance) {
        animInstance.destroy()
      }
    }
  }, [])

  return (
    <div
      className="sage-only-circles pointer-events-none fixed inset-0 overflow-hidden z-0 select-none"
      aria-hidden="true"
    >
      {/* Top right subtle rotating concentric circles */}
      <div className="absolute -top-32 -right-32 w-[600px] h-[600px] opacity-[0.07] pointer-events-none transform rotate-12">
        <div ref={containerRef} className="w-full h-full" />
        {/* GIF fallback if lottie doesn't render immediately */}
        <img
          src={cyberpunkCirclesGif}
          alt=""
          className="w-full h-full object-contain absolute inset-0 -z-10"
        />
      </div>

      {/* Bottom left subtle concentric circles for aesthetic balance */}
      <div className="absolute -bottom-48 -left-48 w-[700px] h-[700px] opacity-[0.05] pointer-events-none transform -rotate-45">
        <img
          src={cyberpunkCirclesGif}
          alt=""
          className="w-full h-full object-contain"
        />
      </div>
    </div>
  )
}

