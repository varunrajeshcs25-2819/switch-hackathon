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
    <div className="min-h-screen bg-gray-100">
      <header className="bg-white border-b shadow-sm px-6 py-4 flex items-center justify-between">
        <h1 className="text-xl font-medium">PatchPilot</h1>
        <span className="text-sm text-gray-500">
          AI-powered visual bug investigation
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
