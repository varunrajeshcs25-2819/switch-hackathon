import React from "react"
import {NavLink} from "../App"

type SidebarNavProps = {
  navLinks: NavLink[]
  activeLink: string
  onSelect: (name: string) => void
}

export const SidebarNav = ({navLinks, activeLink, onSelect}: SidebarNavProps) => {
  return (
    <nav className="bg-[var(--bg-surface)] border-r border-[var(--border-subtle)] w-64 shrink-0 flex flex-col justify-between p-4 min-h-[calc(100vh-3.5rem)] transition-colors duration-200">
      <div className="space-y-6">
        <div>
          <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-[var(--text-secondary)] px-3">
            Investigation Suite
          </span>
          <ul className="space-y-1.5 mt-2">
            {navLinks.map((link) => {
              const isActive = activeLink === link.name
              return (
                <li key={link.name}>
                  <button
                    onClick={() => onSelect(link.name)}
                    className={`w-full flex items-center justify-between px-3 py-2 text-xs font-medium rounded-lg transition-all ${
                      isActive
                        ? "bg-[var(--bg-surface-hover)] text-[var(--text-main)] border-l-2 border-[var(--border-highlight)] shadow-sm"
                        : "text-[var(--text-secondary)] hover:text-[var(--text-main)] hover:bg-[var(--bg-surface-hover)]/60"
                    }`}
                  >
                    <div className="flex items-center space-x-3">
                      <link.icon
                        className={`w-4 h-4 ${isActive ? "text-[var(--accent-primary)]" : "text-[var(--text-secondary)]"}`}
                      />
                      <span>{link.name}</span>
                    </div>
                  </button>
                </li>
              )
            })}
          </ul>
        </div>
      </div>
    </nav>
  )
}
