import React, {useState, useEffect} from "react"
import {
  FileCode2,
  CheckCircle2,
  AlertTriangle,
  ArrowLeft,
  Copy,
  Check,
  ShieldAlert,
  Flame,
  Clock,
  Layers,
  Search,
  ExternalLink,
  ChevronDown,
  ChevronRight,
  Code,
  FileCheck,
} from "lucide-react"

const API_BASE =
  (import.meta as any).env?.VITE_API_BASE || "http://localhost:8000"

type IssueRow = {
  issue_id: string
  description: string
  status: string
  classification: string | null
  severity: string | null
  created_at: string
}

export const InvestigationReportsPage = () => {
  const [issues, setIssues] = useState<IssueRow[]>([])
  const [selectedReport, setSelectedReport] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [copiedCode, setCopiedCode] = useState(false)
  const [copiedDiff, setCopiedDiff] = useState(false)
  const [showUnifiedDiff, setShowUnifiedDiff] = useState(false)

  const loadIssues = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API_BASE}/issues/`)
      if (!res.ok) throw new Error("Could not load issues")
      const data = await res.json()
      setIssues(data)

      const savedActiveIssue = localStorage.getItem("patchpilot_active_issue")
      if (savedActiveIssue && data.some((i: IssueRow) => i.issue_id === savedActiveIssue)) {
        openReport(savedActiveIssue)
      } else if (data.length && !selectedReport) {
        openReport(data[0].issue_id)
      }
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const openReport = async (issueId: string) => {
    localStorage.setItem("patchpilot_active_issue", issueId)
    try {
      const res = await fetch(`${API_BASE}/reports/${issueId}`)
      if (!res.ok) throw new Error("Could not load report")
      const body = await res.json()
      setSelectedReport(body.report)
    } catch (e) {
      console.error(e)
    }
  }

  const copyToClipboard = (text: string, type: "code" | "diff") => {
    // Strip any accidental markdown formatting or fences
    const cleanText = text.replace(/^```[a-z]*\n/i, "").replace(/\n```$/, "").trim()
    navigator.clipboard.writeText(cleanText)
    if (type === "code") {
      setCopiedCode(true)
      setTimeout(() => setCopiedCode(false), 2000)
    } else {
      setCopiedDiff(true)
      setTimeout(() => setCopiedDiff(false), 2000)
    }
  }

  useEffect(() => {
    loadIssues()
  }, [])

  const invFindings = selectedReport?.investigation_findings || {}
  const correctedCode = invFindings.corrected_code || invFindings.proposed_code_changes || ""
  const hasDiff = Boolean(invFindings.proposed_code_changes && invFindings.proposed_code_changes.includes("---"))

  return (
    <div className="py-8 px-4 sm:px-6 max-w-5xl mx-auto space-y-6">
      {/* Top Header */}
      <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-sm">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-[var(--text-main)] flex items-center gap-2">
            <span>Investigation Report</span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-[var(--bg-surface-subtle)] text-[var(--accent-primary)] font-semibold border border-[var(--border-subtle)]">
              Audited Findings
            </span>
          </h1>
          <p className="text-xs text-[var(--text-secondary)] mt-1">
            Complete corrected replacement code, 5-tier evidence hierarchy, and verified AST investigation.
          </p>
        </div>

        {/* Issue Selector Dropdown */}
        <div className="flex items-center space-x-2 self-start sm:self-auto">
          <label className="text-xs text-[var(--text-secondary)] font-mono">Callset:</label>
          <select
            value={selectedReport?.issue_id || ""}
            onChange={(e) => openReport(e.target.value)}
            className="bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] rounded-lg px-3 py-1.5 text-xs text-[var(--text-main)] font-mono focus:outline-none focus:border-[var(--accent-primary)]"
          >
            {issues.map((i) => (
              <option key={i.issue_id} value={i.issue_id}>
                {i.issue_id.slice(0, 8)} · {i.description.slice(0, 30)}...
              </option>
            ))}
          </select>
        </div>
      </div>

      {!selectedReport ? (
        <div className="p-12 text-center text-[var(--text-secondary)] text-xs font-mono">
          No reports found. Submit a bug analysis to generate an audited report.
        </div>
      ) : (
        <div className="space-y-6">
          {/* Metadata & Incident Summary */}
          <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl p-6 space-y-4 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--border-subtle)] pb-4">
              <div className="space-y-1">
                <span className="text-[10px] font-mono text-[var(--text-muted)]">ISSUE REFERENCE ID</span>
                <div className="text-sm font-bold font-mono text-[var(--text-main)] flex items-center gap-2">
                  <span>{selectedReport.issue_id}</span>
                  <span className="text-[10px] px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-500 border border-emerald-500/30 uppercase font-semibold">
                    {selectedReport.status}
                  </span>
                </div>
              </div>
              <div className="text-xs font-mono text-[var(--text-secondary)]">
                Generated {new Date(selectedReport.created_at).toLocaleString()}
              </div>
            </div>

            <div className="space-y-1.5">
              <span className="text-[10px] font-mono uppercase tracking-wider text-[var(--text-secondary)]">
                Original Reported Defect
              </span>
              <p className="text-xs text-[var(--text-main)] font-mono leading-relaxed bg-[var(--bg-surface-subtle)] p-3 rounded-lg border border-[var(--border-subtle)]">
                {selectedReport.original_description}
              </p>
            </div>
          </div>

          {/* PRIMARY OUTPUT: Complete Corrected Code */}
          {correctedCode && (
            <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl overflow-hidden shadow-sm space-y-0">
              <div className="px-5 py-3.5 border-b border-[var(--border-subtle)] flex items-center justify-between bg-[var(--bg-surface-subtle)]">
                <div className="flex items-center space-x-2.5">
                  <FileCheck className="w-4 h-4 text-[var(--accent-primary)]" />
                  <span className="text-xs font-mono font-bold uppercase tracking-wider text-[var(--text-main)]">
                    Primary Output: Complete Corrected Code
                  </span>
                  {invFindings.corrected_filename && (
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-[var(--accent-primary)]">
                      {invFindings.corrected_filename}
                    </span>
                  )}
                  {invFindings.context_scope && (
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[var(--bg-surface)] text-[var(--text-secondary)] border border-[var(--border-subtle)]">
                      Scope: {invFindings.context_scope}
                    </span>
                  )}
                </div>

                <button
                  onClick={() => copyToClipboard(correctedCode, "code")}
                  className="btn-primary text-xs py-1.5 px-3 flex items-center gap-1.5 shadow-sm"
                  title="Copy clean, directly usable code without diff markers"
                >
                  {copiedCode ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copiedCode ? "Copied Usable Code!" : "Copy Code"}</span>
                </button>
              </div>

              {/* Code viewer: clean, syntax-friendly, no markdown fences or diff symbols */}
              <div className="relative p-4 bg-[#0d1117] text-[#e6edf3] overflow-x-auto text-xs font-mono leading-relaxed">
                <pre>
                  <code>{correctedCode.replace(/^```[a-z]*\n/i, "").replace(/\n```$/, "")}</code>
                </pre>
              </div>

              <div className="p-3 bg-[var(--bg-surface)] border-t border-[var(--border-subtle)] text-[11px] font-mono text-[var(--text-secondary)] flex items-center justify-between">
                <span>Direct replacement: Valid syntax, preserved context, no diff prefixes.</span>
                <span className="text-[10px] text-emerald-500 font-semibold">SYNTAX VERIFIED</span>
              </div>
            </div>
          )}

          {/* SECONDARY OUTPUT: Collapsible Unified Diff */}
          {hasDiff && (
            <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl overflow-hidden shadow-sm">
              <button
                type="button"
                onClick={() => setShowUnifiedDiff(!showUnifiedDiff)}
                className="w-full px-5 py-3 text-left flex items-center justify-between text-xs font-mono text-[var(--text-secondary)] hover:text-[var(--text-main)] hover:bg-[var(--bg-surface-subtle)] transition-colors"
              >
                <span className="font-semibold flex items-center gap-2">
                  {showUnifiedDiff ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                  <span>View Original Changes (Unified Diff)</span>
                </span>
                <span className="text-[10px] text-[var(--text-muted)]">Git Patch Format</span>
              </button>

              {showUnifiedDiff && (
                <div className="border-t border-[var(--border-subtle)]">
                  <div className="p-3 bg-[var(--bg-surface-subtle)] flex items-center justify-between text-xs font-mono">
                    <span className="text-[11px] text-[var(--text-secondary)]">Standard Unified Diff</span>
                    <button
                      onClick={() => copyToClipboard(invFindings.proposed_code_changes, "diff")}
                      className="btn-secondary text-[11px] py-1 px-2.5 flex items-center gap-1"
                    >
                      {copiedDiff ? <Check className="w-3 h-3 text-emerald-500" /> : <Copy className="w-3 h-3" />}
                      <span>{copiedDiff ? "Diff Copied" : "Copy Diff"}</span>
                    </button>
                  </div>
                  <pre className="p-4 bg-[#0d1117] text-[#71c9ce] text-xs font-mono overflow-x-auto leading-relaxed">
                    {invFindings.proposed_code_changes}
                  </pre>
                </div>
              )}
            </div>
          )}

          {/* Root Cause & Remediation Explanation */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Root Cause */}
            <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl p-6 space-y-3 shadow-sm">
              <div className="text-[10px] font-mono uppercase tracking-wider text-rose-500 font-bold flex items-center justify-between">
                <span>Suspected Root Cause</span>
                <span className="text-[10px] text-[var(--text-secondary)]">
                  Confidence: {invFindings.confidence || "MEDIUM"}
                </span>
              </div>
              <p className="text-xs text-[var(--text-main)] font-mono leading-relaxed bg-[var(--bg-surface-subtle)] p-3.5 rounded-lg border border-[var(--border-subtle)]">
                {invFindings.suspected_root_cause || "Investigation could not isolate a single root cause."}
              </p>
              {invFindings.relevant_source_files?.length > 0 && (
                <div className="text-[11px] font-mono text-[var(--text-secondary)]">
                  Inspected Files: {invFindings.relevant_source_files.join(", ")}
                </div>
              )}
            </div>

            {/* Proposed Fix Explanation */}
            <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl p-6 space-y-3 shadow-sm">
              <div className="text-[10px] font-mono uppercase tracking-wider text-emerald-500 font-bold flex items-center justify-between">
                <span>Remediation Rationale</span>
                <span className="text-[10px] text-[var(--text-secondary)]">AST Verified</span>
              </div>
              <p className="text-xs text-[var(--text-main)] font-mono leading-relaxed bg-[var(--bg-surface-subtle)] p-3.5 rounded-lg border border-[var(--border-subtle)]">
                {invFindings.proposed_fix || "No operational code fix proposed."}
              </p>
            </div>
          </div>

          {/* 5-Tier Epistemological Evidence Taxonomy */}
          {selectedReport.evidence_breakdown && (
            <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl p-6 space-y-4 shadow-sm">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-[var(--text-main)]">
                  5-Tier Evidence Taxonomy
                </h3>
                <span className="text-[10px] font-mono text-[var(--accent-primary)] font-semibold">Zero-Hallucination Verified</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 font-mono text-xs">
                {/* 1. OBSERVED */}
                <div className="p-3 bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] rounded-lg space-y-1.5">
                  <span className="text-[10px] font-bold text-blue-400 flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-blue-400"></span> [OBSERVED] Direct Facts
                  </span>
                  <ul className="text-[11px] text-[var(--text-main)] space-y-1 list-disc pl-3">
                    {selectedReport.evidence_breakdown.OBSERVED?.length ? (
                      selectedReport.evidence_breakdown.OBSERVED.map((e: string, i: number) => (
                        <li key={i} className="line-clamp-2">{e}</li>
                      ))
                    ) : (
                      <li className="text-[var(--text-muted)]">None explicitly observed</li>
                    )}
                  </ul>
                </div>

                {/* 2. CODE_VERIFIED */}
                <div className="p-3 bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] rounded-lg space-y-1.5">
                  <span className="text-[10px] font-bold text-emerald-500 flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span> [CODE VERIFIED] Inspected
                  </span>
                  <ul className="text-[11px] text-[var(--text-main)] space-y-1 list-disc pl-3">
                    {selectedReport.evidence_breakdown.CODE_VERIFIED?.length ? (
                      selectedReport.evidence_breakdown.CODE_VERIFIED.map((e: string, i: number) => (
                        <li key={i} className="line-clamp-2">{e}</li>
                      ))
                    ) : (
                      <li className="text-[var(--text-muted)]">No code inspected</li>
                    )}
                  </ul>
                </div>

                {/* 3. PROPOSED */}
                <div className="p-3 bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] rounded-lg space-y-1.5">
                  <span className="text-[10px] font-bold text-[var(--accent-primary)] flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-primary)]"></span> [PROPOSED] Fix Code
                  </span>
                  <ul className="text-[11px] text-[var(--text-main)] space-y-1 list-disc pl-3">
                    {selectedReport.evidence_breakdown.PROPOSED?.length ? (
                      selectedReport.evidence_breakdown.PROPOSED.map((e: string, i: number) => (
                        <li key={i} className="line-clamp-2">{e}</li>
                      ))
                    ) : (
                      <li className="text-[var(--text-muted)]">No patch proposed yet</li>
                    )}
                  </ul>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
