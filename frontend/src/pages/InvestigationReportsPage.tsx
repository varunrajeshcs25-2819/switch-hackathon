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

  const loadIssues = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API_BASE}/issues/`)
      if (!res.ok) throw new Error("Could not load issues")
      const data = await res.json()
      setIssues(data)
      if (data.length && !selectedReport) {
        openReport(data[0].issue_id)
      }
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const openReport = async (issueId: string) => {
    try {
      const res = await fetch(`${API_BASE}/reports/${issueId}`)
      if (!res.ok) throw new Error("Could not load report")
      const body = await res.json()
      setSelectedReport(body.report)
    } catch (e) {
      console.error(e)
    }
  }

  const copyPatch = (text: string) => {
    navigator.clipboard.writeText(text)
    setCopiedCode(true)
    setTimeout(() => setCopiedCode(false), 2000)
  }

  useEffect(() => {
    loadIssues()
  }, [])

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#30363d] pb-6">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <span>Investigation Reports</span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#21262d] text-[#71c9ce] border border-[#30363d]">
              Audited Findings
            </span>
          </h1>
          <p className="text-xs text-[#8b949e] mt-1">
            Exhaustive engineering post-mortems separating directly observed visual facts from inferred mechanisms and proposed patches.
          </p>
        </div>

        {/* Issue Selector Dropdown */}
        <div className="flex items-center space-x-3">
          <label className="text-xs text-[#8b949e] font-mono">Report Callset:</label>
          <select
            value={selectedReport?.issue_id || ""}
            onChange={(e) => openReport(e.target.value)}
            className="bg-[#161b22] border border-[#30363d] rounded-lg px-3 py-1.5 text-xs text-white font-mono focus:outline-none focus:border-[#71c9ce]"
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
        <div className="p-12 text-center text-[#8b949e] text-xs font-mono">
          No reports found. Submit a bug analysis to generate an audited report.
        </div>
      ) : (
        <div className="space-y-6">
          {/* Metadata Card */}
          <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-6 space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#30363d] pb-4">
              <div className="space-y-1">
                <span className="text-[10px] font-mono text-[#484f58]">ISSUE REFERENCE ID</span>
                <div className="text-sm font-bold font-mono text-white flex items-center gap-2">
                  <span>{selectedReport.issue_id}</span>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 uppercase">
                    {selectedReport.status}
                  </span>
                </div>
              </div>
              <div className="text-xs font-mono text-[#8b949e]">
                Generated {new Date(selectedReport.created_at).toLocaleString()}
              </div>
            </div>

            <div className="space-y-1.5">
              <span className="text-[10px] font-mono uppercase tracking-wider text-[#8b949e]">
                Original Defect Report
              </span>
              <p className="text-xs text-[#e6edf3] font-mono leading-relaxed bg-[#0d1117] p-3 rounded-lg border border-[#30363d]">
                {selectedReport.original_description}
              </p>
            </div>
          </div>

          {/* Epistemological 5-Tier Evidence Breakdown */}
          {selectedReport.evidence_breakdown && (
            <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-6 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-mono font-semibold uppercase tracking-wider text-white">
                  5-Tier Evidence & Epistemological Taxonomy
                </h3>
                <span className="text-[10px] font-mono text-[#71c9ce]">Zero-Hallucination Guard</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 font-mono text-xs">
                {/* 1. OBSERVED */}
                <div className="p-3 bg-[#0d1117] border border-[#30363d] rounded-lg space-y-1.5">
                  <span className="text-[10px] font-bold text-blue-400 flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-blue-400"></span> [OBSERVED] Direct Facts
                  </span>
                  <ul className="text-[11px] text-[#c9d1d9] space-y-1 list-disc pl-3">
                    {selectedReport.evidence_breakdown.OBSERVED?.length ? (
                      selectedReport.evidence_breakdown.OBSERVED.map((e: string, i: number) => (
                        <li key={i} className="line-clamp-2">{e}</li>
                      ))
                    ) : (
                      <li className="text-[#484f58]">None explicitly observed</li>
                    )}
                  </ul>
                </div>

                {/* 2. CODE_VERIFIED */}
                <div className="p-3 bg-[#0d1117] border border-[#30363d] rounded-lg space-y-1.5">
                  <span className="text-[10px] font-bold text-emerald-400 flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span> [CODE VERIFIED] Inspected
                  </span>
                  <ul className="text-[11px] text-[#c9d1d9] space-y-1 list-disc pl-3">
                    {selectedReport.evidence_breakdown.CODE_VERIFIED?.length ? (
                      selectedReport.evidence_breakdown.CODE_VERIFIED.map((e: string, i: number) => (
                        <li key={i} className="line-clamp-2">{e}</li>
                      ))
                    ) : (
                      <li className="text-[#484f58]">No code inspected</li>
                    )}
                  </ul>
                </div>

                {/* 3. PROPOSED */}
                <div className="p-3 bg-[#0d1117] border border-[#30363d] rounded-lg space-y-1.5">
                  <span className="text-[10px] font-bold text-[#71c9ce] flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#71c9ce]"></span> [PROPOSED] Unverified Patch
                  </span>
                  <ul className="text-[11px] text-[#c9d1d9] space-y-1 list-disc pl-3">
                    {selectedReport.evidence_breakdown.PROPOSED?.length ? (
                      selectedReport.evidence_breakdown.PROPOSED.map((e: string, i: number) => (
                        <li key={i} className="line-clamp-2">{e}</li>
                      ))
                    ) : (
                      <li className="text-[#484f58]">No patch proposed yet</li>
                    )}
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* Root Cause & Remediation Patch */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Root Cause Card */}
            <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-6 space-y-3">
              <div className="text-[10px] font-mono uppercase tracking-wider text-rose-400 font-bold flex items-center justify-between">
                <span>Suspected Root Cause</span>
                <span className="text-[10px] text-[#8b949e]">
                  Confidence: {selectedReport.investigation_findings?.confidence || "MEDIUM"}
                </span>
              </div>
              <p className="text-xs text-[#e6edf3] font-mono leading-relaxed bg-[#0d1117] p-3 rounded-lg border border-[#30363d]">
                {selectedReport.investigation_findings?.suspected_root_cause || "Investigation could not isolate a single root cause."}
              </p>
              {selectedReport.investigation_findings?.relevant_source_files?.length > 0 && (
                <div className="text-[11px] font-mono text-[#8b949e]">
                  Affected Files: {selectedReport.investigation_findings.relevant_source_files.join(", ")}
                </div>
              )}
            </div>

            {/* Proposed Fix Card */}
            <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-6 space-y-3">
              <div className="text-[10px] font-mono uppercase tracking-wider text-emerald-400 font-bold flex items-center justify-between">
                <span>Proposed Technical Fix</span>
                {selectedReport.investigation_findings?.proposed_fix && (
                  <button
                    onClick={() => copyPatch(selectedReport.investigation_findings.proposed_fix)}
                    className="text-[10px] text-[#8b949e] hover:text-white flex items-center gap-1"
                  >
                    {copiedCode ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                    <span>{copiedCode ? "Copied" : "Copy"}</span>
                  </button>
                )}
              </div>
              <p className="text-xs text-[#e6edf3] font-mono leading-relaxed bg-[#0d1117] p-3 rounded-lg border border-[#30363d]">
                {selectedReport.investigation_findings?.proposed_fix || "No code fix recommended."}
              </p>
            </div>
          </div>

          {/* Unified Diff Patch View */}
          {selectedReport.investigation_findings?.proposed_code_changes && (
            <div className="bg-[#161b22] border border-[#30363d] rounded-xl overflow-hidden">
              <div className="px-5 py-3 border-b border-[#30363d] flex items-center justify-between bg-[#161b22]">
                <span className="text-xs font-mono font-semibold uppercase tracking-wider text-white">
                  Unified Diff Code Patch
                </span>
                <button
                  onClick={() => copyPatch(selectedReport.investigation_findings.proposed_code_changes)}
                  className="btn-secondary text-[11px] py-1 px-2.5 flex items-center gap-1"
                >
                  <Copy className="w-3 h-3" />
                  <span>Copy Diff</span>
                </button>
              </div>
              <pre className="p-4 bg-[#0d1117] text-xs font-mono text-[#71c9ce] overflow-x-auto leading-relaxed">
                {selectedReport.investigation_findings.proposed_code_changes}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
