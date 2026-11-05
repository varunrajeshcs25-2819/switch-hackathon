import React, {useState} from "react"
import {
  Camera as UilCamera,
  Eye as UilEye,
  CheckCircle as UilCheckCircled,
  Package as UilPackage,
} from "lucide-react"
import {SidebarNav} from "./components/SidebarNav"
import {DashboardPage} from "./pages/DashboardPage"
import {NewAnalysisPage} from "./pages/NewAnalysisPage"
import {AgentCollaborationPage} from "./pages/AgentCollaborationPage"
import {InvestigationReportsPage} from "./pages/InvestigationReportsPage"

type NavLink = {
  name: string
  icon: React.ComponentType<{className?: string}>
  path: string
}

export const App = () => {
  const [navLinks] = useState<NavLink[]>([
    {name: "Dashboard", icon: UilPackage, path: "/"},
    {name: "New Analysis", icon: UilCamera, path: "/new"},
    {name: "Agent Collaboration", icon: UilEye, path: "/collaboration"},
    {name: "Investigation Reports", icon: UilCheckCircled, path: "/reports"},
  ])

  const [activeLink, setActiveLink] = useState("Dashboard")

  let pageContent = null
  if (activeLink === "Dashboard") {
    pageContent = <DashboardPage />
  } else if (activeLink === "New Analysis") {
    pageContent = <NewAnalysisPage />
  } else if (activeLink === "Agent Collaboration") {
    pageContent = <AgentCollaborationPage />
  } else if (activeLink === "Investigation Reports") {
    pageContent = <InvestigationReportsPage />
  }

  return (
    <div className="min-h-screen bg-[#e3fdfd]/30">
      <header className="bg-white border-b border-[#cbf1f5] shadow-sm px-6 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg bg-[#71c9ce] flex items-center justify-center text-white font-bold text-lg shadow-sm">
            P
          </div>
          <h1 className="text-xl font-bold tracking-tight text-gray-800">PatchPilot</h1>
        </div>
        <span className="text-sm font-medium px-3 py-1 bg-[#cbf1f5] text-[#2c7a7e] rounded-full">
          AI-Powered Visual Bug Investigation
        </span>
      </header>

      <div className="flex">
        <SidebarNav
          navLinks={navLinks}
          activeLink={activeLink}
          onSelect={setActiveLink}
        />
        <main className="flex-1 overflow-auto">{pageContent}</main>
      </div>
    </div>
  )
}
