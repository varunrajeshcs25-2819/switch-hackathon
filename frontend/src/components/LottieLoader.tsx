import React, {useState, useEffect} from "react"
import loadingGif from "../assets/loading-transparent.gif"
import loadingAnimation from "../assets/loading-lottie.json"

interface LottieLoaderProps {
  size?: number
  className?: string
  text?: string
}

export const LottieLoader: React.FC<LottieLoaderProps> = ({
  size = 130,
  className = "",
  text,
}) => {
  const [lottieLoaded, setLottieLoaded] = useState(false)

  // Asynchronously render lottie-web SVG if supported, while guaranteed instant transparent GIF renders always
  useEffect(() => {
    let animItem: any = null
    let container = document.getElementById("lottie-player-canvas")

    import("lottie-web")
      .then((lottie) => {
        if (container) {
          container.innerHTML = ""
          animItem = lottie.default.loadAnimation({
            container: container,
            renderer: "svg",
            loop: true,
            autoplay: true,
            animationData: loadingAnimation,
          })
          setLottieLoaded(true)
        }
      })
      .catch((err) => {
        console.warn("Lottie web load fallback to gif:", err)
      })

    return () => {
      if (animItem) {
        animItem.destroy()
      }
    }
  }, [])

  return (
    <div className={`flex flex-col items-center justify-center ${className}`}>
      {/* 
        High-visibility glowing container matching Cyberpunk & Dark Mode palettes.
        Guaranteed instant display of the exact Lottie animation via high-fps transparent GIF,
        plus vector SVG lottie-web integration.
      */}
      <div
        style={{
          width: size,
          height: size,
        }}
        className="relative flex items-center justify-center rounded-2xl p-2 bg-[#0e0e18] border border-[var(--border-subtle)] shadow-[0_0_30px_rgba(252,238,10,0.25)] select-none overflow-hidden"
      >
        {/* Subtle Cyberpunk Corner Accents */}
        <div className="absolute top-1 left-1 w-2 h-2 border-t-2 border-l-2 border-[var(--accent-primary)] pointer-events-none opacity-80" />
        <div className="absolute top-1 right-1 w-2 h-2 border-t-2 border-r-2 border-[var(--accent-primary)] pointer-events-none opacity-80" />
        <div className="absolute bottom-1 left-1 w-2 h-2 border-b-2 border-l-2 border-[var(--accent-primary)] pointer-events-none opacity-80" />
        <div className="absolute bottom-1 right-1 w-2 h-2 border-b-2 border-r-2 border-[var(--accent-primary)] pointer-events-none opacity-80" />

        {/* Guaranteed 100% visible Animated Character (the exact Ahmed loading-OIlHh8cNez animation) */}
        <img
          src={loadingGif}
          alt="Loading animation"
          className="w-full h-full object-contain filter drop-shadow-[0_0_12px_rgba(252,238,10,0.4)]"
          style={{imageRendering: "auto"}}
        />

        {/* Vector SVG player overlay */}
        <div
          id="lottie-player-canvas"
          className={`absolute inset-0 w-full h-full flex items-center justify-center pointer-events-none transition-opacity duration-300 ${
            lottieLoaded ? "opacity-100" : "opacity-0"
          }`}
        />
      </div>

      {text && (
        <p className="mt-3 text-xs font-mono font-medium tracking-wider text-[var(--accent-primary)] animate-pulse uppercase text-center">
          {text}
        </p>
      )}
    </div>
  )
}
