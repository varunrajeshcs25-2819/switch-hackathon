import React from "react"
import {NavLink} from "../App"

interface FloatingCapsuleNavProps {
  navLinks: NavLink[]
  activeLink: string
  onSelect: (name: string) => void
  className?: string
}

export const FloatingCapsuleNav: React.FC<FloatingCapsuleNavProps> = ({
  navLinks,
  activeLink,
  onSelect,
  className = "",
}) => {
  return (
    <nav
      className={`inline-flex items-center p-1 sm:p-1.5 rounded-full bg-[var(--bg-surface)]/90 backdrop-blur-md border border-[var(--border-subtle)] shadow-xl transition-all duration-200 capsule-entrance ${className}`}
      aria-label="Floating Capsule Navigation"
    >
      <div className="flex items-center space-x-1 overflow-x-auto scrollbar-none max-w-full">
        {navLinks.map((item) => {
          const isActive = activeLink === item.name
          const IconComponent = item.icon

          return (
            <button
              key={item.name}
              onClick={() => onSelect(item.name)}
              className={`relative flex items-center space-x-1.5 sm:space-x-2 px-3.5 sm:px-4 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap transition-all duration-200 cursor-pointer ${
                isActive
                  ? "bg-[var(--nav-active-bg)] text-[var(--nav-active-text)] shadow-sm scale-[1.02]"
                  : "text-[var(--text-secondary)] hover:text-[var(--text-main)] hover:bg-[var(--bg-surface-hover)]"
              }`}
              title={item.name}
            >
              <IconComponent
                className={`w-3.5 h-3.5 shrink-0 transition-transform duration-200 ${
                  isActive ? "scale-110 text-[var(--nav-active-text)]" : "opacity-80"
                }`}
              />
              <span className="tracking-wide text-[11px] sm:text-xs">{item.name}</span>
            </button>
          )
        })}
      </div>
    </nav>
  )
}
