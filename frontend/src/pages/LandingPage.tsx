import React, {useState, useEffect, useRef} from "react"
import {
  Terminal,
  Bug,
  Network,
  Cpu,
  ShieldCheck,
  Zap,
  ArrowRight,
  CheckCircle2,
  Copy,
  Check,
  ChevronDown,
  Layers,
  Sparkles,
  ExternalLink,
  Code2,
  Eye,
  FileCheck,
  AlertTriangle,
  GitPullRequest,
  RefreshCw,
} from "lucide-react"
import {ButterflyIcon} from "../components/ButterflyIcon"
import {InteractiveButterflyFlock} from "../components/InteractiveButterflyFlock"

interface LandingPageProps {
  onNavigate: (page: string) => void
  onToggleTheme?: () => void
  currentTheme?: "dark" | "sage"
}

export const LandingPage: React.FC<LandingPageProps> = ({
  onNavigate,
  onToggleTheme,
  currentTheme = "dark",
}) => {
  const [copiedCode, setCopiedCode] = useState(false)
  const [selectedDemo, setSelectedDemo] = useState<"syntax" | "type" | "ui">("syntax")
  const [viewMode, setViewMode] = useState<"code" | "diff">("code")
  const [diffOpen, setDiffOpen] = useState(false)
  const footerRef = useRef<HTMLElement>(null)

  // Silky smooth scroll reveal observer for content entering the viewport
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-revealed")
          }
        })
      },
      {
        threshold: 0.1,
        rootMargin: "0px 0px -40px 0px",
      }
    )

    const revealElements = document.querySelectorAll(".scroll-reveal")
    revealElements.forEach((el) => observer.observe(el))

    return () => observer.disconnect()
  }, [])

  // Real bug demonstrations reflecting our actual test suite & agent capabilities
  const demoScenarios = {
    syntax: {
      id: "syntax",
      title: "SyntaxError: Unclosed Bracket",
      sourceFile: "backend/auth/session.py",
      line: 42,
      severity: "High",
      category: "Syntax Error",
      ocrExtracted: 'SyntaxError: \'{\' was never closed in session.py at line 42: "def verify_token(req): payload = {"',
      triageAnalysis:
        "AST tokenizer detected an unclosed dictionary literal in verify_token(). Immediate compile-time crash preventing server boot.",
      correctedCode: `def verify_token(request_headers: dict) -> dict:
    """Verifies caller authorization bearer token with complete payload dictionary."""
    if "Authorization" not in request_headers:
        raise ValueError("Missing bearer token in authorization header")

    token = request_headers["Authorization"].replace("Bearer ", "")
    payload = {
        "valid": True,
        "token_hash": hash(token),
        "status": "authenticated"
    }
    return payload`,
      unifiedDiff: `--- backend/auth/session.py (original)
+++ backend/auth/session.py (corrected)
@@ -40,4 +40,8 @@
-    token = request_headers["Authorization"].replace("Bearer ", "")
-    payload = {
+    token = request_headers["Authorization"].replace("Bearer ", "")
+    payload = {
+        "valid": True,
+        "token_hash": hash(token),
+        "status": "authenticated"
+    }
+    return payload`,
    },
    type: {
      id: "type",
      title: "TypeError: NoneType Subscript",
      sourceFile: "services/event_dispatcher.py",
      line: 88,
      severity: "Critical",
      category: "Runtime Crash",
      ocrExtracted: "TypeError: 'NoneType' object is not subscriptable at handle_event() line 88",
      triageAnalysis:
        "Null safety violation. Variable `room_state` evaluated to None before accessing `room_state['participants']`.",
      correctedCode: `def handle_event(room_id: str, event_data: dict) -> bool:
    """Safely dispatches event with defensive NoneType validation on room state."""
    room_state = get_room_state(room_id)
    if room_state is None:
        logger.warning("Room %s uninitialized. Initializing fallback state.", room_id)
        room_state = {"participants": [], "status": "idle"}

    participants = room_state.get("participants", [])
    return broadcast_payload(participants, event_data)`,
      unifiedDiff: `--- services/event_dispatcher.py (original)
+++ services/event_dispatcher.py (corrected)
@@ -86,3 +86,7 @@
     room_state = get_room_state(room_id)
-    participants = room_state["participants"]
+    if room_state is None:
+        logger.warning("Room %s uninitialized. Initializing fallback state.", room_id)
+        room_state = {"participants": [], "status": "idle"}
+    participants = room_state.get("participants", [])
     return broadcast_payload(participants, event_data)`,
    },
    ui: {
      id: "ui",
      title: "CSS Layout Overflow: Truncated Card",
      sourceFile: "frontend/components/TelemetryCard.tsx",
      line: 19,
      severity: "Medium",
      category: "Visual Bug",
      ocrExtracted: "RapidOCR detected text bounding box collision at pixel coordinates (420, 190): text clipping 'Agent ...'",
      triageAnalysis:
        "Container width fixed without flex-wrap or overflow containment causing visual clipping on mobile viewport.",
      correctedCode: `export const TelemetryCard = ({ title, status, latency }: CardProps) => {
  return (
    <div className="flex flex-wrap items-center justify-between p-4 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] min-w-0 overflow-hidden">
      <div className="flex items-center space-x-2 truncate">
        <span className="w-2 h-2 rounded-full bg-emerald-400 shrink-0" />
        <span className="font-mono text-xs font-semibold truncate text-[var(--text-main)]">{title}</span>
      </div>
      <span className="font-mono text-[11px] text-[var(--accent-primary)] font-bold shrink-0">{latency}ms</span>
    </div>
  );
};`,
      unifiedDiff: `--- frontend/components/TelemetryCard.tsx (original)
+++ frontend/components/TelemetryCard.tsx (corrected)
@@ -17,2 +17,3 @@
-    <div className="flex items-center justify-between w-64 p-4">
+    <div className="flex flex-wrap items-center justify-between p-4 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] min-w-0 overflow-hidden">
+      <div className="flex items-center space-x-2 truncate">`,
    },
  }

  const activeDemo = demoScenarios[selectedDemo]

  const handleCopyCode = () => {
    navigator.clipboard.writeText(activeDemo.correctedCode)
    setCopiedCode(true)
    setTimeout(() => setCopiedCode(false), 2000)
  }

  return (
    <div className="min-h-screen bg-[var(--bg-canvas)] text-[var(--text-main)] selection:bg-[var(--accent-primary)] selection:text-[var(--bg-canvas)] transition-colors duration-200">
      {/* =========================================================================
          01 // EDITORIAL HERO WITH BUTTERFLY METAMORPHISM MOTIF
          ========================================================================= */}
      <section className="relative pt-12 pb-20 md:pt-20 md:pb-32 px-6 lg:px-16 border-b border-[var(--border-subtle)] overflow-hidden">
        {/* Architectural Editorial Grid Lines */}
        <div
          className="absolute inset-0 pointer-events-none opacity-[0.03]"
          style={{
            backgroundImage:
              "linear-gradient(to right, var(--text-main) 1px, transparent 1px), linear-gradient(to bottom, var(--text-main) 1px, transparent 1px)",
            backgroundSize: "64px 64px",
          }}
        />

        <div className="max-w-7xl mx-auto relative z-10">
          {/* Asymmetric Split Layout: Typography Left, Butterfly Centerpiece Right */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center">
            {/* Left Column: Bold Typography & Narrative */}
            <div className="lg:col-span-7 space-y-8">
              <div className="space-y-4">
                <div className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-full text-xs font-mono font-medium bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-[var(--accent-primary)] shadow-sm">
                  <Sparkles className="w-3.5 h-3.5 text-[var(--accent-primary)]" />
                  <span>The Autonomous Multi-Agent Debugging Swarm</span>
                </div>

                <h1 className="text-4xl sm:text-6xl xl:text-7xl font-bold tracking-tight leading-[1.08] text-[var(--text-main)]">
                  Turn Broken Code <br />
                  <span className="text-transparent bg-clip-text bg-gradient-to-r from-[var(--hero-grad-start)] via-[var(--hero-grad-mid)] to-[var(--hero-grad-end)] drop-shadow-sm">
                    Into Verified Patches.
                  </span>
                </h1>

                <p className="text-base sm:text-lg text-[var(--text-secondary)] max-w-2xl font-normal leading-relaxed">
                  PatchPilot pairs on-device <span className="text-[var(--text-main)] font-semibold">RapidOCR vision analysis</span> with 
                  decentralized <span className="text-[var(--text-main)] font-semibold">Switch Room agents</span> and deterministic 
                  <span className="text-[var(--text-main)] font-semibold"> AST patch synthesis</span>. We close the visual-to-code gap 
                  without hallucinatory single-agent errors.
                </p>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-wrap items-center gap-4 pt-2">
                <button
                  onClick={() => onNavigate("New Bug Analysis")}
                  className="btn-primary px-6 py-3.5 text-sm font-semibold flex items-center space-x-2 shadow-sm"
                >
                  <Bug className="w-4 h-4" />
                  <span>Analyze a Bug Now</span>
                  <ArrowRight className="w-4 h-4" />
                </button>

                <button
                  onClick={() => onNavigate("Live Agent Workspace")}
                  className="btn-secondary px-6 py-3.5 text-sm font-medium flex items-center space-x-2"
                >
                  <Network className="w-4 h-4 text-[var(--accent-primary)]" />
                  <span>Open Live Swarm Workspace</span>
                </button>

                <button
                  onClick={() => onNavigate("Command Center")}
                  className="px-4 py-3.5 text-sm font-mono text-[var(--text-secondary)] hover:text-[var(--text-main)] transition-colors flex items-center space-x-1"
                >
                  <span>Command Center</span>
                  <ExternalLink className="w-3.5 h-3.5 ml-1 opacity-70" />
                </button>
              </div>

              {/* Verified Metrics Strip */}
              <div className="grid grid-cols-3 gap-4 pt-6 border-t border-[var(--border-subtle)] text-xs font-mono">
                <div>
                  <div className="text-2xl font-bold text-[var(--accent-secondary)] tracking-tight">38 / 38</div>
                  <div className="text-[var(--text-secondary)] text-[11px] mt-0.5">Automated Tests Passed</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-[var(--accent-secondary)] tracking-tight">&lt; 420ms</div>
                  <div className="text-[var(--text-secondary)] text-[11px] mt-0.5">Groq Swarm Inference</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-[var(--accent-secondary)] tracking-tight">100%</div>
                  <div className="text-[var(--text-secondary)] text-[11px] mt-0.5">Offline Zero-API Failover</div>
                </div>
              </div>
            </div>

            {/* Right Column: Butterfly Metamorphic Core & Live Telemetry Glass */}
            <div className="lg:col-span-5 flex flex-col items-center justify-center relative">
              <div className="relative w-full max-w-md flex flex-col items-center justify-center p-8 sm:p-10 rounded-2xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] shadow-xl overflow-hidden group">
                {/* Metamorphic Butterfly Emblem */}
                <div className="z-10 py-4">
                  <ButterflyIcon size="hero" interactive={true} />
                </div>

                {/* Sub-label explaining the Metamorphism */}
                <div className="z-10 text-center mt-3 space-y-2 max-w-sm">
                  <div className="text-xs font-mono font-bold tracking-widest text-[var(--accent-primary)] uppercase">
                    The Butterfly Effect in Code
                  </div>
                  <p className="text-xs text-[var(--text-secondary)] font-sans leading-relaxed">
                    A single missing token triggers runtime failure. PatchPilot isolates the ripple, traces the AST, and metamorphoses errors into running software.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          02 // THE REAL-WORLD DEVELOPER CRISIS (PROBLEM STATEMENT)
          ========================================================================= */}
      <section className="scroll-reveal py-20 px-6 lg:px-16 border-b border-[var(--border-subtle)] bg-[var(--bg-surface-subtle)]/40">
        <div className="max-w-7xl mx-auto space-y-12">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 border-b border-[var(--border-subtle)] pb-6">
            <div>
              <span className="font-mono text-xs text-[var(--accent-secondary)] font-semibold tracking-wider uppercase">
                02 // The Engineering Friction
              </span>
              <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-[var(--text-main)] mt-2">
                Why Traditional Debugging Breaks Down.
              </h2>
            </div>
            <p className="text-sm text-[var(--text-secondary)] max-w-md font-sans leading-relaxed">
              Modern development moves faster than ever, yet triage and root-cause analysis remain painfully manual.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Crisis Item 1 */}
            <div className="card-lift scroll-reveal reveal-stagger-1 cursor-pointer p-8 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] space-y-4">
              <div className="w-10 h-10 rounded-lg bg-rose-500/10 border border-rose-500/20 flex items-center justify-center text-rose-500 font-mono text-sm font-bold">
                01
              </div>
              <h3 className="text-lg font-bold text-[var(--text-main)]">The Visual-to-Code Void</h3>
              <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
                Screenshots of failing tests, IDE tracebacks, and broken CSS flexboxes are posted in Slack, Discord, or Jira. Developers must manually retype obscure filenames and trace lines across multiple repos.
              </p>
              <div className="font-mono text-[11px] text-rose-500 pt-2 border-t border-[var(--border-subtle)]">
                Average developer triage lag: 45+ minutes
              </div>
            </div>

            {/* Crisis Item 2 */}
            <div className="card-lift scroll-reveal reveal-stagger-2 cursor-pointer p-8 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] space-y-4">
              <div className="w-10 h-10 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-500 font-mono text-sm font-bold">
                02
              </div>
              <h3 className="text-lg font-bold text-[var(--text-main)]">The "Diff Dilemma" & AI Hallucinations</h3>
              <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
                Standard single-agent LLMs emit broken unified diff markers (`+`, `-`, `@@`) mixed into Markdown, or delete unrelated functions entirely. Engineers spend more time untangling the AI's diff than writing the fix.
              </p>
              <div className="font-mono text-[11px] text-amber-500 pt-2 border-t border-[var(--border-subtle)]">
                Unusable patch rejection rate: 62%
              </div>
            </div>

            {/* Crisis Item 3 */}
            <div className="card-lift scroll-reveal reveal-stagger-3 cursor-pointer p-8 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] space-y-4">
              <div className="w-10 h-10 rounded-lg bg-[var(--accent-primary)]/10 border border-[var(--accent-primary)]/20 flex items-center justify-center text-[var(--accent-primary)] font-mono text-sm font-bold">
                03
              </div>
              <h3 className="text-lg font-bold text-[var(--text-main)]">Single-Point LLM Rate Limits</h3>
              <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
                Cloud-dependent AI tools freeze the moment an API key expires, rate limits hit, or connectivity drops during a live demo or sprint crunch. Debugging cannot stop because of a 429 quota error.
              </p>
              <div className="font-mono text-[11px] text-[var(--accent-primary)] pt-2 border-t border-[var(--border-subtle)]">
                Zero fallback capability in standard tools
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          03 // THE MULTI-AGENT SWARM SOLUTION (SWITCH PROTOCOL)
          ========================================================================= */}
      <section className="scroll-reveal py-20 px-6 lg:px-16 border-b border-[var(--border-subtle)]">
        <div className="max-w-7xl mx-auto space-y-12">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 border-b border-[var(--border-subtle)] pb-6">
            <div>
              <span className="font-mono text-xs text-[var(--accent-secondary)] font-semibold tracking-wider uppercase">
                03 // Architecture & Collaboration
              </span>
              <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-[var(--text-main)] mt-2">
                Decentralized Multi-Agent Swarm with Switch.
              </h2>
            </div>
            <p className="text-sm text-[var(--text-secondary)] max-w-md font-sans leading-relaxed">
              Instead of one overworked model hallucinating, PatchPilot deploys four specialized autonomous agents inside a Switch Room Protocol.
            </p>
          </div>

          {/* 4 Specialized Agent Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Agent 1: Vision */}
            <div className="card-lift scroll-reveal reveal-stagger-1 cursor-pointer p-6 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] flex flex-col justify-between space-y-4">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="w-9 h-9 rounded-lg bg-blue-500/10 text-blue-400 flex items-center justify-center font-bold border border-blue-500/20">
                    <Eye className="w-5 h-5" />
                  </div>
                  <span className="font-mono text-[10px] text-blue-400 border border-blue-500/20 px-2 py-0.5 rounded-full font-bold">
                    AGENT 01
                  </span>
                </div>
                <h3 className="text-base font-bold text-[var(--text-main)]">Vision Agent</h3>
                <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
                  Dual-scale preprocessing + RapidOCR. Slices UI screenshots, identifies coordinate bounds, and extracts terminal stack traces with zero cloud transmission lag.
                </p>
              </div>
              <div className="font-mono text-[11px] text-[var(--text-secondary)] border-t border-[var(--border-subtle)] pt-3">
                Output: Structured OCR Tokens
              </div>
            </div>

            {/* Agent 2: Triage */}
            <div className="card-lift scroll-reveal reveal-stagger-2 cursor-pointer p-6 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] flex flex-col justify-between space-y-4">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="w-9 h-9 rounded-lg bg-amber-500/10 text-amber-500 flex items-center justify-center font-bold border border-amber-500/20">
                    <Layers className="w-5 h-5" />
                  </div>
                  <span className="font-mono text-[10px] text-amber-500 border border-amber-500/20 px-2 py-0.5 rounded-full font-bold">
                    AGENT 02
                  </span>
                </div>
                <h3 className="text-base font-bold text-[var(--text-main)]">Triage Agent</h3>
                <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
                  Calculates impact severity (Critical to Low), classifies fault architecture (syntax, logic, API, UI), and synthesizes a calibrated investigation directive.
                </p>
              </div>
              <div className="font-mono text-[11px] text-[var(--text-secondary)] border-t border-[var(--border-subtle)] pt-3">
                Output: Scoped Task Delegation
              </div>
            </div>

            {/* Agent 3: Investigation */}
            <div className="card-lift scroll-reveal reveal-stagger-3 cursor-pointer p-6 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] flex flex-col justify-between space-y-4">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="w-9 h-9 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center font-bold border border-emerald-500/20">
                    <Code2 className="w-5 h-5" />
                  </div>
                  <span className="font-mono text-[10px] text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded-full font-bold">
                    AGENT 03
                  </span>
                </div>
                <h3 className="text-base font-bold text-[var(--text-main)]">Investigation Agent</h3>
                <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
                  Executes AST static tracing against ground truth code symbols. Synthesizes complete usable replacement code and secondary unified diffs.
                </p>
              </div>
              <div className="font-mono text-[11px] text-[var(--text-secondary)] border-t border-[var(--border-subtle)] pt-3">
                Output: Verified Usable Code
              </div>
            </div>

            {/* Agent 4: Empirical Reviewer */}
            <div className="card-lift scroll-reveal reveal-stagger-4 cursor-pointer p-6 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] flex flex-col justify-between space-y-4">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="w-9 h-9 rounded-lg bg-purple-500/10 text-purple-400 flex items-center justify-center font-bold border border-purple-500/20">
                    <ShieldCheck className="w-5 h-5" />
                  </div>
                  <span className="font-mono text-[10px] text-purple-400 border border-purple-500/20 px-2 py-0.5 rounded-full font-bold">
                    AGENT 04
                  </span>
                </div>
                <h3 className="text-base font-bold text-[var(--text-main)]">Review & Challenge</h3>
                <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
                  Acts as peer reviewer. Issues empirical challenges when proposed fixes alter unrelated code or omit critical imports, producing final consensus.
                </p>
              </div>
              <div className="font-mono text-[11px] text-[var(--text-secondary)] border-t border-[var(--border-subtle)] pt-3">
                Output: Formal Pass/Fail Verdict
              </div>
            </div>
          </div>

          {/* Switch Room Protocol Diagram */}
          <div className="scroll-reveal reveal-stagger-2 p-6 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] font-mono text-xs">
            <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-3 mb-4">
              <span className="text-[var(--accent-primary)] font-bold flex items-center gap-2">
                <Network className="w-4 h-4 text-[var(--accent-primary)]" />
                PEER-TO-PEER MESSAGE TOPOLOGY (ROOM_PROTOCOL)
              </span>
              <span className="text-[var(--text-secondary)] text-[11px]">ENFORCED LOOP GUARDS & TIMEOUTS</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-[11px]">
              <div className="card-lift cursor-pointer p-4 rounded-lg bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] space-y-1">
                <div className="text-blue-400 font-bold">Step 1: Observation</div>
                <div className="text-[var(--text-secondary)]">Vision broadcasts OCR tokens and bounding coordinates into room.</div>
              </div>
              <div className="card-lift cursor-pointer p-4 rounded-lg bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] space-y-1">
                <div className="text-amber-500 font-bold">Step 2: Classification</div>
                <div className="text-[var(--text-secondary)]">Triage categorizes root layer & assigns target file to investigation.</div>
              </div>
              <div className="card-lift cursor-pointer p-4 rounded-lg bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] space-y-1">
                <div className="text-emerald-400 font-bold">Step 3: Synthesis</div>
                <div className="text-[var(--text-secondary)]">Investigation performs AST tracing and crafts the corrected code.</div>
              </div>
              <div className="card-lift cursor-pointer p-4 rounded-lg bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] space-y-1">
                <div className="text-purple-400 font-bold">Step 4: Consensus</div>
                <div className="text-[var(--text-secondary)]">Reviewer validates syntax, tests constraints, and writes final report.</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          04 // DEDICATED PATCHPILOT INTERACTIVE SHOWCASE (THE CORE ENGINE)
          ========================================================================= */}
      <section className="scroll-reveal py-20 px-6 lg:px-16 border-b border-[var(--border-subtle)] bg-[var(--bg-surface-subtle)]/40">
        <div className="max-w-7xl mx-auto space-y-10">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 border-b border-[var(--border-subtle)] pb-6">
            <div>
              <span className="font-mono text-xs text-[var(--accent-secondary)] font-semibold tracking-wider uppercase">
                04 // Live Interactive Patch Lab
              </span>
              <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-[var(--text-main)] mt-2">
                Experience Verified Code Generation.
              </h2>
            </div>
            <p className="text-sm text-[var(--text-secondary)] max-w-md font-sans leading-relaxed">
              Test how PatchPilot eliminates diff confusion by delivering complete, syntax-validated code ready for immediate use.
            </p>
          </div>

          {/* Scenario Selector Pills */}
          <div className="flex flex-wrap items-center gap-3">
            {(["syntax", "type", "ui"] as const).map((key) => {
              const item = demoScenarios[key]
              const isSelected = selectedDemo === key
              return (
                <button
                  key={key}
                  onClick={() => setSelectedDemo(key)}
                  className={`px-4 py-2 rounded-full text-xs font-mono font-medium transition-all flex items-center space-x-2 cursor-pointer ${
                    isSelected
                      ? "bg-[var(--btn-primary-bg)] text-[var(--btn-primary-text)] shadow-sm scale-105"
                      : "bg-[var(--bg-surface)] text-[var(--text-secondary)] border border-[var(--border-subtle)] hover:text-[var(--text-main)] hover:border-[var(--border-highlight)]"
                  }`}
                >
                  <span>{item.title}</span>
                  <span
                    className={`text-[10px] px-1.5 py-0.5 rounded-full ${
                      isSelected
                        ? "bg-black/20 text-inherit font-bold"
                        : "bg-[var(--bg-surface-subtle)] text-[var(--accent-primary)] font-semibold"
                    }`}
                  >
                    {item.severity}
                  </span>
                </button>
              )
            })}
          </div>

          {/* Interactive Inspection Workspace */}
          <div className="rounded-2xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] overflow-hidden shadow-xl">
            {/* Telemetry Header */}
            <div className="p-4 bg-[var(--bg-surface-subtle)] border-b border-[var(--border-subtle)] flex flex-wrap items-center justify-between gap-4 font-mono text-xs">
              <div className="flex items-center space-x-3">
                <span className="font-bold text-[var(--text-main)]">{activeDemo.sourceFile}</span>
                <span className="text-[var(--text-secondary)]">Line {activeDemo.line}</span>
                <span className="px-2 py-0.5 rounded-full bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-[var(--accent-primary)] text-[11px] font-medium">
                  {activeDemo.category}
                </span>
              </div>

              {/* View Switcher: Complete Code vs Unified Diff */}
              <div className="flex items-center space-x-2">
                <div className="flex bg-[var(--bg-surface)] border border-[var(--border-subtle)] p-0.5 rounded-lg">
                  <button
                    onClick={() => setViewMode("code")}
                    className={`px-3 py-1 rounded-md text-xs font-medium transition-all cursor-pointer ${
                      viewMode === "code"
                        ? "bg-[var(--btn-primary-bg)] text-[var(--btn-primary-text)] font-semibold"
                        : "text-[var(--text-secondary)] hover:text-[var(--text-main)]"
                    }`}
                  >
                    Complete Code (Usable)
                  </button>
                  <button
                    onClick={() => setViewMode("diff")}
                    className={`px-3 py-1 rounded-md text-xs font-medium transition-all cursor-pointer ${
                      viewMode === "diff"
                        ? "bg-[var(--btn-primary-bg)] text-[var(--btn-primary-text)] font-semibold"
                        : "text-[var(--text-secondary)] hover:text-[var(--text-main)]"
                    }`}
                  >
                    Unified Diff
                  </button>
                </div>

                <button
                  onClick={handleCopyCode}
                  className="btn-primary px-3 py-1 text-xs font-mono flex items-center space-x-1.5"
                  title="Copy usable code to clipboard"
                >
                  {copiedCode ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copiedCode ? "Copied!" : "Copy Code"}</span>
                </button>
              </div>
            </div>

            {/* Split Inspection Pane */}
            <div className="grid grid-cols-1 lg:grid-cols-12 divide-y lg:divide-y-0 lg:divide-x divide-[var(--border-subtle)]">
              {/* Left Column: Vision & Triage Diagnostic Evidence */}
              <div className="lg:col-span-4 p-6 space-y-6 bg-[var(--bg-surface)] text-xs">
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-[var(--text-main)] font-mono font-medium">
                    <span className="flex items-center gap-1.5">
                      <Eye className="w-4 h-4 text-blue-400" /> 1. RapidOCR Extraction
                    </span>
                    <span className="text-[10px] text-emerald-500 font-mono">0.08s</span>
                  </div>
                  <div className="p-4 rounded-lg bg-[var(--bg-surface-elevated)] border border-[var(--border-subtle)] border-l-4 border-l-[var(--accent-secondary)] font-mono text-[11px] text-[var(--text-secondary)] leading-relaxed break-words">
                    {activeDemo.ocrExtracted}
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between text-[var(--text-main)] font-mono font-medium">
                    <span className="flex items-center gap-1.5">
                      <Layers className="w-4 h-4 text-amber-500" /> 2. Triage Reasoning
                    </span>
                    <span className="text-[10px] text-emerald-500 font-mono">0.14s</span>
                  </div>
                  <div className="p-4 rounded-lg bg-[var(--bg-surface-elevated)] border border-[var(--border-subtle)] border-l-4 border-l-[var(--accent-primary)] font-sans text-xs text-[var(--text-secondary)] leading-relaxed">
                    {activeDemo.triageAnalysis}
                  </div>
                </div>

                {/* Features & Guarantees box */}
                <div className="p-4 rounded-lg bg-[var(--bg-surface-elevated)] border border-[var(--border-subtle)] border-l-4 border-l-emerald-500 space-y-2.5">
                  <div className="font-mono font-bold text-[var(--text-main)] text-xs flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                    PatchPilot Verification
                  </div>
                  <ul className="space-y-1.5 text-xs text-[var(--text-secondary)]">
                    <li className="flex items-center gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" /> Valid Python/TypeScript AST Syntax
                    </li>
                    <li className="flex items-center gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" /> Complete replacement (No partial markers)
                    </li>
                    <li className="flex items-center gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" /> Preserves existing function context
                    </li>
                  </ul>
                </div>
              </div>

              {/* Right Column: Code Presentation Window */}
              <div className="lg:col-span-8 p-6 bg-[var(--bg-canvas)]">
                {viewMode === "code" ? (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between text-xs font-mono text-[var(--text-secondary)]">
                      <span className="font-bold text-[var(--text-main)]">Primary Usable Output (Ready to paste)</span>
                      <span className="text-emerald-500 font-medium">Zero Markdown diff markers</span>
                    </div>
                    <pre className="p-4 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-subtle)] border-l-4 border-l-emerald-500 text-xs font-mono text-emerald-400 overflow-x-auto leading-relaxed">
                      <code>{activeDemo.correctedCode}</code>
                    </pre>
                  </div>
                ) : (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between text-xs font-mono text-[var(--text-secondary)]">
                      <span className="font-bold text-[var(--text-main)]">Secondary Collapsible Diff (Auditing only)</span>
                      <span className="text-amber-500 font-medium">Unified Diff Format</span>
                    </div>
                    <pre className="p-4 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-subtle)] border-l-4 border-l-amber-500 text-xs font-mono text-[var(--text-main)] overflow-x-auto leading-relaxed">
                      <code>{activeDemo.unifiedDiff}</code>
                    </pre>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          05 // DUAL-ENGINE ZERO-API RESILIENCE ARCHITECTURE
          ========================================================================= */}
      <section className="scroll-reveal py-20 px-6 lg:px-16 border-b border-[var(--border-subtle)]">
        <div className="max-w-7xl mx-auto space-y-12">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 border-b border-[var(--border-subtle)] pb-6">
            <div>
              <span className="font-mono text-xs text-[var(--accent-secondary)] font-semibold tracking-wider uppercase">
                05 // Reliability Engineering
              </span>
              <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-[var(--text-main)] mt-2">
                Engineered to Never Crash on Key Expirations.
              </h2>
            </div>
            <p className="text-sm text-[var(--text-secondary)] max-w-md font-sans leading-relaxed">
              Built with an automated failover hierarchy: lightning-fast Groq LPUs with 100% offline fallback to deterministic AST algorithms.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-stretch">
            {/* Tier 1: Groq LPUs */}
            <div className="card-lift scroll-reveal reveal-stagger-1 cursor-pointer p-8 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] flex flex-col justify-between space-y-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="w-10 h-10 rounded-lg bg-[var(--accent-primary)]/10 text-[var(--accent-primary)] flex items-center justify-center font-bold border border-[var(--accent-primary)]/20">
                    <Zap className="w-5 h-5 text-[var(--accent-primary)]" />
                  </div>
                  <span className="font-mono text-xs text-emerald-500 border border-emerald-500/20 px-2.5 py-0.5 rounded-full font-bold">
                    PRIMARY ENGINE
                  </span>
                </div>
                <h3 className="text-xl font-bold text-[var(--text-main)]">Groq GPT-OSS-120B / Llama 3.3</h3>
                <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
                  Leverages Groq's Language Processing Units (LPUs) to execute multi-agent debates with near-zero latency (&lt;420ms). Fast enough to analyze bugs in real-time while teammates chat.
                </p>
              </div>

              <div className="p-4 rounded-lg bg-[var(--bg-surface-elevated)] border border-[var(--border-subtle)] border-l-4 border-l-[var(--accent-secondary)] font-mono text-xs space-y-2">
                <div className="text-[var(--text-main)] font-semibold">Features:</div>
                <div className="text-[var(--text-secondary)]">· High-speed token generation (500+ tokens/sec)</div>
                <div className="text-[var(--text-secondary)]">· Deep cross-file reasoning and AST symbol resolution</div>
                <div className="text-[var(--text-secondary)]">· Structured JSON validation using Pydantic schemas</div>
              </div>
            </div>

            {/* Tier 2: Option 1 AST Engine */}
            <div className="card-lift scroll-reveal reveal-stagger-2 cursor-pointer p-8 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] flex flex-col justify-between space-y-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="w-10 h-10 rounded-lg bg-emerald-500/10 text-emerald-500 flex items-center justify-center font-bold border border-emerald-500/20">
                    <Cpu className="w-5 h-5 text-emerald-500" />
                  </div>
                  <span className="font-mono text-xs text-[var(--accent-primary)] border border-[var(--accent-primary)]/20 px-2.5 py-0.5 rounded-full font-bold">
                    FAILOVER ENGINE (ZERO-API)
                  </span>
                </div>
                <h3 className="text-xl font-bold text-[var(--text-main)]">Deterministic AST Offline Synthesis</h3>
                <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
                  If Groq API keys are absent, hit rate limits, or network fails, PatchPilot automatically triggers Option 1 AST synthesis. Analyzes token bracket stacks and fixes code 100% offline with zero external network requests.
                </p>
              </div>

              <div className="p-4 rounded-lg bg-[var(--bg-surface-elevated)] border border-[var(--border-subtle)] border-l-4 border-l-[var(--accent-primary)] font-mono text-xs space-y-2">
                <div className="text-[var(--text-main)] font-semibold">Failover Guarantees:</div>
                <div className="text-emerald-500">· 0% reliance on third-party cloud availability</div>
                <div className="text-emerald-500">· 0 API cost during offline development</div>
                <div className="text-emerald-500">· Mathematically deterministic bracket balancing</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          06 // TECHNICAL SPECIFICATIONS MATRIX
          ========================================================================= */}
      <section className="scroll-reveal py-20 px-6 lg:px-16 border-b border-[var(--border-subtle)] bg-[var(--bg-surface-subtle)]/40">
        <div className="max-w-7xl mx-auto space-y-12">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 border-b border-[var(--border-subtle)] pb-6">
            <div>
              <span className="font-mono text-xs text-[var(--accent-secondary)] font-semibold tracking-wider uppercase">
                06 // Engineering Matrix
              </span>
              <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-[var(--text-main)] mt-2">
                The Technical Stack.
              </h2>
            </div>
            <p className="text-sm text-[var(--text-secondary)] max-w-md font-sans leading-relaxed">
              Built on production-grade asynchronous Python, modern React 19, and the Switch Protocol.
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 font-mono text-xs">
            <div className="card-lift scroll-reveal reveal-stagger-1 cursor-pointer p-5 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] space-y-2">
              <div className="text-[var(--text-secondary)] text-[11px] uppercase">BACKEND FRAMEWORK</div>
              <div className="text-sm font-bold text-[var(--text-main)]">FastAPI + Uvicorn</div>
              <div className="text-xs text-[var(--text-secondary)]">Async endpoints, non-blocking swarm execution</div>
            </div>

            <div className="card-lift scroll-reveal reveal-stagger-2 cursor-pointer p-5 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] space-y-2">
              <div className="text-[var(--text-secondary)] text-[11px] uppercase">COMPUTER VISION</div>
              <div className="text-sm font-bold text-[var(--text-main)]">RapidOCR Engine</div>
              <div className="text-xs text-[var(--text-secondary)]">Local CPU OCR, zero cloud latency, multi-scale tracing</div>
            </div>

            <div className="card-lift scroll-reveal reveal-stagger-3 cursor-pointer p-5 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] space-y-2">
              <div className="text-[var(--text-secondary)] text-[11px] uppercase">COLLABORATION PROTOCOL</div>
              <div className="text-sm font-bold text-[var(--text-main)]">Switch Room Protocol</div>
              <div className="text-xs text-[var(--text-secondary)]">Peer-to-peer message interchange, challenge negotiation</div>
            </div>

            <div className="card-lift scroll-reveal reveal-stagger-4 cursor-pointer p-5 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] space-y-2">
              <div className="text-[var(--text-secondary)] text-[11px] uppercase">FRONTEND SUITE</div>
              <div className="text-sm font-bold text-[var(--text-main)]">React 19 + Tailwind v4</div>
              <div className="text-xs text-[var(--text-secondary)]">Dual-theme architectural UI, high-contrast typography</div>
            </div>

            <div className="card-lift scroll-reveal reveal-stagger-5 cursor-pointer p-5 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] space-y-2">
              <div className="text-[var(--text-secondary)] text-[11px] uppercase">TRACE PERSISTENCE</div>
              <div className="text-sm font-bold text-[var(--text-main)]">SQLite Engine</div>
              <div className="text-xs text-[var(--text-secondary)]">Full room message histories, session replay, audit logs</div>
            </div>

            <div className="card-lift scroll-reveal reveal-stagger-6 cursor-pointer p-5 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] space-y-2">
              <div className="text-[var(--text-secondary)] text-[11px] uppercase">DATA VALIDATION</div>
              <div className="text-sm font-bold text-[var(--text-main)]">Pydantic v2 Models</div>
              <div className="text-xs text-[var(--text-secondary)]">Strict schema boundaries across all agent message payloads</div>
            </div>

            <div className="card-lift scroll-reveal reveal-stagger-7 cursor-pointer p-5 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] space-y-2">
              <div className="text-[var(--text-secondary)] text-[11px] uppercase">CODE REASONING</div>
              <div className="text-sm font-bold text-[var(--text-main)]">AST Parser + Groq LPU</div>
              <div className="text-xs text-[var(--text-secondary)]">Abstract syntax tree traversal + LLM code repair</div>
            </div>

            <div className="card-lift scroll-reveal reveal-stagger-8 cursor-pointer p-5 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] space-y-2">
              <div className="text-[var(--text-secondary)] text-[11px] uppercase">TEST COVERAGE</div>
              <div className="text-sm font-bold text-emerald-500">100% Passing Tests</div>
              <div className="text-xs text-[var(--text-secondary)]">38 unit, integration, and E2E multiagent test specs</div>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          07 // WORKFLOW STEP-BY-STEP
          ========================================================================= */}
      <section className="scroll-reveal py-20 px-6 lg:px-16 border-b border-[var(--border-subtle)]">
        <div className="max-w-7xl mx-auto space-y-12">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 border-b border-[var(--border-subtle)] pb-6">
            <div>
              <span className="font-mono text-xs text-[var(--accent-secondary)] font-semibold tracking-wider uppercase">
                07 // How It Works
              </span>
              <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-[var(--text-main)] mt-2">
                From Traceback to Pull Request in 4 Steps.
              </h2>
            </div>
            <p className="text-sm text-[var(--text-secondary)] max-w-md font-sans leading-relaxed">
              A continuous, auditable pipeline where human engineers and autonomous agents stay perfectly synchronized.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 font-mono text-xs">
            <div className="card-lift scroll-reveal reveal-stagger-1 cursor-pointer p-6 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] space-y-3">
              <div className="text-3xl font-black text-[var(--accent-secondary)]">01</div>
              <h4 className="font-bold text-sm text-[var(--text-main)]">Submit Artifact</h4>
              <p className="text-xs text-[var(--text-secondary)] font-sans leading-relaxed">
                Paste a code snippet, upload a screenshot of your terminal/IDE crash, or type an issue description.
              </p>
            </div>

            <div className="card-lift scroll-reveal reveal-stagger-2 cursor-pointer p-6 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] space-y-3">
              <div className="text-3xl font-black text-[var(--accent-secondary)]">02</div>
              <h4 className="font-bold text-sm text-[var(--text-main)]">Vision & Triage</h4>
              <p className="text-xs text-[var(--text-secondary)] font-sans leading-relaxed">
                RapidOCR extracts the exact file name and failing line number. Triage classifies impact and directs the swarm.
              </p>
            </div>

            <div className="card-lift scroll-reveal reveal-stagger-3 cursor-pointer p-6 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] space-y-3">
              <div className="text-3xl font-black text-[var(--accent-secondary)]">03</div>
              <h4 className="font-bold text-sm text-[var(--text-main)]">Swarm Investigation</h4>
              <p className="text-xs text-[var(--text-secondary)] font-sans leading-relaxed">
                Agents debate in the Switch Room, validating against the AST to ensure no non-existent imports or syntax errors.
              </p>
            </div>

            <div className="card-lift scroll-reveal reveal-stagger-4 cursor-pointer p-6 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] space-y-3">
              <div className="text-3xl font-black text-[var(--accent-secondary)]">04</div>
              <h4 className="font-bold text-sm text-[var(--text-main)]">Apply Verified Fix</h4>
              <p className="text-xs text-[var(--text-secondary)] font-sans leading-relaxed">
                Click "Copy Code" to grab the complete, usable file or function, or review original changes in Unified Diff.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          08 // CLOSING SECTION & STUDIO LAUNCHPAD WITH INTERACTIVE FLOCK
          ========================================================================= */}
      <section
        ref={footerRef}
        className="scroll-reveal relative overflow-hidden py-24 px-6 lg:px-16 border-t border-[var(--border-subtle)]"
        style={{
          background:
            "radial-gradient(ellipse 90% 70% at 50% 30%, var(--footer-glow) 0%, var(--footer-tint) 45%, var(--bg-canvas) 90%)",
        }}
      >
        {/* Soft Ambient Horizon Tint Beam */}
        <div
          className="absolute top-0 left-1/2 -translate-x-1/2 w-4/5 h-44 pointer-events-none blur-3xl opacity-40"
          style={{
            background: "radial-gradient(ellipse at top, var(--accent-primary) 0%, transparent 70%)",
          }}
        />

        {/* Interactive Floating Butterfly Flock (pointer-events: none, protects text) */}
        <InteractiveButterflyFlock containerRef={footerRef} />

        {/* Foreground Protected Content */}
        <div className="max-w-5xl mx-auto text-center space-y-8 relative z-10">
          <div className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-full text-xs font-mono font-medium bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-[var(--accent-primary)]">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
            <span>Autonomous Debugging & AST Patch Synthesis</span>
          </div>

          <h2 className="text-4xl sm:text-5xl font-bold tracking-tight text-[var(--text-main)]">
            Start Debugging with <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-[var(--hero-grad-start)] via-[var(--hero-grad-mid)] to-[var(--hero-grad-end)] drop-shadow-sm">
              Autonomous Confidence.
            </span>
          </h2>

          <p className="text-base text-[var(--text-secondary)] max-w-xl mx-auto font-sans leading-relaxed">
            Eliminate hours of manual stack trace deciphering. Enter the PatchPilot studio and experience how multi-agent swarms build verified software patches.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
            <button
              onClick={() => onNavigate("New Bug Analysis")}
              className="btn-primary px-8 py-4 text-sm font-semibold flex items-center space-x-2 shadow-lg"
            >
              <Bug className="w-4 h-4" />
              <span>Launch Bug Analysis Studio</span>
              <ArrowRight className="w-4 h-4" />
            </button>

            <button
              onClick={() => onNavigate("Live Agent Workspace")}
              className="btn-secondary px-8 py-4 text-sm font-medium flex items-center space-x-2"
            >
              <Network className="w-4 h-4 text-[var(--accent-primary)]" />
              <span>Enter Live Agent Workspace</span>
            </button>
          </div>

          {/* Bottom Branding & Links */}
          <div className="pt-16 border-t border-[var(--border-subtle)] flex flex-col sm:flex-row items-center justify-between gap-4 font-mono text-xs text-[var(--text-secondary)]">
            <div className="flex items-center space-x-3">
              <ButterflyIcon size="sm" interactive={false} />
              <span className="font-bold text-[var(--text-main)] tracking-wide">PATCHPILOT</span>
              <span>· VISUAL SOFTWARE DEBUGGING PLATFORM</span>
            </div>
            <div className="text-[var(--text-secondary)] uppercase tracking-wider text-[11px]">
              Multi-Agent Telemetry & AST Verification
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
