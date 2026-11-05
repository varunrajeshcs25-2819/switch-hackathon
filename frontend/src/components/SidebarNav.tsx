import React from "react"
import {NavLink} from "../App"

type SidebarNavProps = {
  navLinks: NavLink[]
  activeLink: string
  onSelect: (name: string) => void
}

export const SidebarNav = ({navLinks, activeLink, onSelect}: SidebarNavProps) => {
  return (
    <nav className="bg-[#161b22] border-r border-[#30363d] w-64 shrink-0 flex flex-col justify-between p-4 min-h-[calc(100vh-3.5rem)]">
      <div className="space-y-6">
        <div>
          <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-[#8b949e] px-3">
            Investigation Suite
          </span>
          <ul className="space-y-1.5 mt-2">
            {navLinks.map((link) => {
              const isActive = activeLink === link.name
              return (
                <li key={link.name}>
                  <button
                    onClick={() => onSelect(link.name)}
                    className={`w-full flex items-center justify-between px-3 py-2 text-xs font-medium rounded-md transition-all ${
                      isActive
                        ? "bg-[#21262d] text-white border-l-2 border-[#71c9ce] shadow-inner"
                        : "text-[#8b949e] hover:text-white hover:bg-[#21262d]/50"
                    }`}
                  >
                    <div className="flex items-center space-x-3">
                      <link.icon
                        className={`w-4 h-4 ${isActive ? "text-[#71c9ce]" : "text-[#8b949e]"}`}
                      />
                      <span>{link.name}</span>
                    </div>
                  </button>
                </li>
              )
            })}
          </ul>
        </div>

        {/* Live Swarm Telemetry Box */}
        <div className="bg-[#0d1117] border border-[#30363d] rounded-lg p-3 text-[11px] font-mono space-y-2">
          <div className="text-[#8b949e] font-semibold text-[10px] uppercase tracking-wider">
            Agent Network
          </div>
          <div className="flex items-center justify-between text-[#c9d1d9]">
            <span className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-400"></span> Vision Agent
            </span>
            <span className="text-emerald-400 text-[10px]">READY</span>
          </div>
          <div className="flex items-center justify-between text-[#c9d1d9]">
            <span className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400"></span> Triage Agent
            </span>
            <span className="text-emerald-400 text-[10px]">READY</span>
          </div>
          <div className="flex items-center justify-between text-[#c9d1d9]">
            <span className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span> Investigation
            </span>
            <span className="text-emerald-400 text-[10px]">READY</span>
          </div>
        </div>
      </div>

      {/* Persistence Info Footer */}
      <div className="text-[11px] text-[#8b949e] border-t border-[#30363d] pt-3 font-mono">
        <div>Storage: SQLite DB</div>
        <div className="text-[10px] text-[#484f58]">100% Persisted Transcript</div>
      </div>
    </nav>
  )
}
