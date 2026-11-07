import React, {useState, useEffect} from "react"
import {
  Compass,
  LayoutDashboard,
  Bug,
  Network,
  FileCode2,
  Moon,
  Sparkles,
} from "lucide-react"
import {ButterflyIcon} from "./components/ButterflyIcon"
import {FloatingCapsuleNav} from "./components/FloatingCapsuleNav"
import {LandingPage} from "./pages/LandingPage"
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
  const [activeLink, setActiveLink] = useState("Overview")
  const [theme, setTheme] = useState<"dark" | "sage">(() => {
    return (localStorage.getItem("patchpilot_theme") as "dark" | "sage") || "dark"
  })

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme)
    localStorage.setItem("patchpilot_theme", theme)
  }, [theme])

  const toggleTheme = () => {
    setTheme((prev) => (prev === "dark" ? "sage" : "dark"))
  }

  const navLinks: NavLink[] = [
    {name: "Overview", icon: Compass},
    {name: "Command Center", icon: LayoutDashboard},
    {name: "New Bug Analysis", icon: Bug},
    {name: "Live Agent Workspace", icon: Network},
    {name: "Investigation Reports", icon: FileCode2},
  ]

  let pageContent = null
  if (activeLink === "Overview") {
    pageContent = (
      <LandingPage
        onNavigate={setActiveLink}
        onToggleTheme={toggleTheme}
        currentTheme={theme}
      />
    )
  } else if (activeLink === "Command Center") {
    pageContent = <DashboardPage onNavigate={setActiveLink} />
  } else if (activeLink === "New Bug Analysis") {
    pageContent = <NewAnalysisPage onNavigate={setActiveLink} />
  } else if (activeLink === "Live Agent Workspace") {
    pageContent = <AgentCollaborationPage />
  } else if (activeLink === "Investigation Reports") {
    pageContent = <InvestigationReportsPage />
  }

  return (
    <div className="min-h-screen bg-[var(--bg-canvas)] text-[var(--text-main)] flex flex-col font-sans transition-colors duration-200 relative">
      {/* Top Floating App Bar with 3-Zone Architecture */}
      <header className="relative h-16 bg-[var(--bg-surface)]/80 backdrop-blur-md border-b border-[var(--border-subtle)] px-4 sm:px-6 flex items-center justify-between z-30 sticky top-0 transition-colors duration-200">
        {/* LEFT ZONE: Butterfly Avatar + Brand Name */}
        <div
          className="flex items-center space-x-3 cursor-pointer shrink-0 group select-none z-10"
          onClick={() => setActiveLink("Overview")}
          title="Return to Overview"
        >
          <div className="w-9 h-9 rounded-xl bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] flex items-center justify-center p-1.5 shadow-sm group-hover:border-[var(--border-highlight)] group-hover:scale-105 transition-all">
            <ButterflyIcon size="sm" interactive={false} />
          </div>
          <div className="flex items-center space-x-2">
            <span className="font-bold text-base tracking-tight text-[var(--text-main)]">PatchPilot</span>
          </div>
        </div>

        {/* CENTRE ZONE: Mathematically Centered Floating Capsule Navigation */}
        <div className="hidden md:flex absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 pointer-events-auto z-20">
          <FloatingCapsuleNav
            navLinks={navLinks}
            activeLink={activeLink}
            onSelect={(name) => setActiveLink(name)}
          />
        </div>

        {/* RIGHT ZONE: Switch Status Indicator & Theme Toggle */}
        <div className="flex items-center space-x-3 text-xs shrink-0 z-10">
          {/* Switch Protocol Badge */}
          <div className="hidden sm:flex items-center space-x-2 px-3 py-1.5 rounded-full bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] shadow-sm">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span className="text-[var(--text-secondary)] font-mono text-[11px] font-medium">Switch Room Active</span>
          </div>

          {/* SAGE MODE / DARK MODE Theme Selector */}
          <button
            onClick={toggleTheme}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full border border-[var(--border-subtle)] bg-[var(--bg-surface-subtle)] hover:bg-[var(--bg-surface-hover)] text-[var(--text-main)] text-xs font-mono transition-all shadow-sm"
            title="Toggle theme between Dark Mode and Sage Mode"
          >
            {theme === "dark" ? (
              <>
                <Sparkles className="w-3.5 h-3.5 text-[var(--accent-primary)]" />
                <span className="font-semibold">Sage Mode</span>
              </>
            ) : (
              <>
                <Moon className="w-3.5 h-3.5 text-[var(--accent-secondary)]" />
                <span className="font-semibold">Dark Mode</span>
              </>
            )}
          </button>
        </div>
      </header>

      {/* MOBILE COMPACT CAPSULE BAR (Appears on smaller screens below main header) */}
      <div className="md:hidden flex items-center justify-center py-2 px-4 border-b border-[var(--border-subtle)] bg-[var(--bg-surface)]/75 backdrop-blur-md overflow-x-auto scrollbar-none z-20">
        <FloatingCapsuleNav
          navLinks={navLinks}
          activeLink={activeLink}
          onSelect={(name) => setActiveLink(name)}
        />
      </div>

      {/* Main Workspace Layout (Full width, sidebar eliminated) */}
      <main className="flex-1 w-full overflow-y-auto bg-[var(--bg-canvas)] transition-colors duration-200">
        {pageContent}
      </main>
    </div>
  )
}
