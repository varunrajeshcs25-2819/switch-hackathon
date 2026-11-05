import React, {useState} from "react"
import {
  LayoutDashboard,
  Bug,
  Network,
  FileCode2,
  Terminal,
  Activity,
  ShieldCheck,
} from "lucide-react"
import {SidebarNav} from "./components/SidebarNav"
import {DashboardPage} from "./pages/DashboardPage"
import {NewAnalysisPage} from "./pages/NewAnalysisPage"
import {AgentCollaborationPage} from "./pages/AgentCollaborationPage"
import {InvestigationReportsPage} from "./pages/InvestigationReportsPage"

export type NavLink = {
  name: string
  icon: React.ComponentType<{className?: string}>
  badge?: string
}

export const App = () => {
  const [activeLink, setActiveLink] = useState("Command Center")

  const navLinks: NavLink[] = [
    {name: "Command Center", icon: LayoutDashboard},
    {name: "New Bug Analysis", icon: Bug},
    {name: "Live Agent Workspace", icon: Network},
    {name: "Investigation Reports", icon: FileCode2},
  ]

  let pageContent = null
  if (activeLink === "Command Center") {
    pageContent = <DashboardPage onNavigate={setActiveLink} />
  } else if (activeLink === "New Bug Analysis") {
    pageContent = <NewAnalysisPage onNavigate={setActiveLink} />
  } else if (activeLink === "Live Agent Workspace") {
    pageContent = <AgentCollaborationPage />
  } else if (activeLink === "Investigation Reports") {
    pageContent = <InvestigationReportsPage />
  }

  return (
    <div className="min-h-screen bg-[#0b0f14] text-[#e6edf3] flex flex-col">
      {/* Top Engineering App Bar */}
      <header className="h-14 bg-[#161b22] border-b border-[#30363d] px-6 flex items-center justify-between z-10">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg bg-[#71c9ce] text-[#0b0f14] flex items-center justify-center font-black text-sm tracking-wider shadow-sm">
            PP
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="font-bold text-base tracking-tight text-white">PatchPilot</span>
            <span className="text-xs text-[#8b949e] font-mono">v2.1 · Enterprise Debug Engine</span>
          </div>
        </div>

        <div className="flex items-center space-x-4 text-xs">
          <div className="flex items-center space-x-2 px-2.5 py-1 rounded bg-[#0d1117] border border-[#30363d]">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span className="text-[#8b949e] font-mono">Switch Room Protocol Active</span>
          </div>
          <div className="flex items-center space-x-1.5 text-[#71c9ce] font-mono">
            <Terminal className="w-3.5 h-3.5" />
            <span>3 Agents Online</span>
          </div>
        </div>
      </header>

      {/* Main App Layout */}
      <div className="flex flex-1 overflow-hidden">
        <SidebarNav
          navLinks={navLinks}
          activeLink={activeLink}
          onSelect={(name) => setActiveLink(name)}
        />
        <main className="flex-1 overflow-y-auto bg-[#0b0f14]">
          {pageContent}
        </main>
      </div>
    </div>
  )
}
