import React from "react"
import {
  Camera as UilCamera,
  Eye as UilEye,
  Filter as UilFilter,
  CheckCircle as UilCheckCircled,
  X as UilCross,
  AlertCircle as UilAlertCircle,
  Package as UilPackage,
  Trash2 as UilTrash2,
} from "lucide-react"

type NavLink = {
  name: string
  icon: React.ComponentType<{className?: string}>
  path: string
}

type SidebarNavProps = {
  navLinks: NavLink[]
  activeLink: string
  onSelect: (name: string) => void
}

export const SidebarNav = ({navLinks, activeLink, onSelect}: SidebarNavProps) => {
  return (
    <nav className="bg-white border-r border-[#cbf1f5] p-6 w-64 shrink-0 shadow-sm min-h-[calc(100vh-65px)]">
      <ul className="space-y-3">
        {navLinks.map((link) => {
          const isActive = activeLink === link.name
          return (
            <li key={link.name}>
              <button
                onClick={() => onSelect(link.name)}
                className={`w-full flex items-center px-4 py-3 text-sm font-semibold rounded-lg transition-all ${
                  isActive
                    ? "bg-[#71c9ce] text-white shadow-sm"
                    : "text-gray-700 hover:bg-[#cbf1f5]/50"
                }`}
              >
                <link.icon
                  className={`w-5 h-5 mr-3 ${isActive ? "text-white" : "text-[#71c9ce]"}`}
                />
                <span>{link.name}</span>
              </button>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}
