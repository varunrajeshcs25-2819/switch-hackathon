import React, {useEffect, useState} from "react"
import {
  Network,
  Eye,
  Filter,
  Code2,
  CheckCircle,
  AlertTriangle,
  ArrowRight,
  ChevronDown,
  ChevronRight,
  RefreshCw,
  Terminal,
  ShieldCheck,
  Zap,
} from "lucide-react"

const API_BASE =
  (import.meta as any).env?.VITE_API_BASE || "http://localhost:8000"

type Issue = {
  issue_id: string
  description: string
  status: string
  classification?: string | null
  severity?: string | null
  created_at: string
}

type AgentMessage = {
  message_id: string
  room_id: string
  sender: string
  recipient: string
  kind: string
  summary: string
  content: Record<string, any>
  reply_to?: string | null
  created_at: string
}

const KIND_BADGES: Record<string, {label: string; color: string}> = {
  observation: {label: "OBSERVATION", color: "bg-blue-500/15 text-blue-400 border-blue-500/30"},
  classification: {label: "CLASSIFICATION", color: "bg-amber-500/15 text-amber-400 border-amber-500/30"},
  task: {label: "TASK DELEGATION", color: "bg-purple-500/15 text-purple-400 border-purple-500/30"},
  findings: {label: "TECHNICAL FINDINGS", color: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30"},
  challenge: {label: "INDEPENDENT CHALLENGE", color: "bg-rose-500/15 text-rose-400 border-rose-500/30"},
  verdict: {label: "TRIAGE VERDICT", color: "bg-teal-500/15 text-teal-400 border-teal-500/30"},
  error: {label: "AGENT FAILURE", color: "bg-rose-500/15 text-rose-400 border-rose-500/30"},
  system: {label: "ROOM SYSTEM", color: "bg-slate-500/15 text-slate-400 border-slate-500/30"},
}

export const AgentCollaborationPage = () => {
  const [issues, setIssues] = useState<Issue[]>([])
  const [selectedIssueId, setSelectedIssueId] = useState<string>("")
  const [messages, setMessages] = useState<AgentMessage[]>([])
  const [counts, setCounts] = useState<Record<string, number>>({})
  const [sourceCodeSupplied, setSourceCodeSupplied] = useState(false)
  const [loading, setLoading] = useState(true)
  const [expandedMessageId, setExpandedMessageId] = useState<string | null>(null)

  const loadIssues = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API_BASE}/issues/`)
      if (!res.ok) throw new Error("Could not load issues")
      const data: Issue[] = await res.json()
      setIssues(data)
      if (data.length && !selectedIssueId) {
        setSelectedIssueId(data[0].issue_id)
      }
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const loadTranscript = async (id: string) => {
    if (!id) return
    try {
      const res = await fetch(`${API_BASE}/issues/${id}/messages`)
      if (!res.ok) throw new Error("Could not load room transcript")
      const data = await res.json()
      setMessages(data.messages || [])
      setCounts(data.counts || {})
      setSourceCodeSupplied(Boolean(data.source_code_supplied))
    } catch (e) {
      console.error(e)
    }
  }

  useEffect(() => {
    loadIssues()
  }, [])

  useEffect(() => {
    if (selectedIssueId) {
      loadTranscript(selectedIssueId)
    }
  }, [selectedIssueId])

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[var(--border-subtle)] pb-6">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-[var(--text-main)] flex items-center gap-2">
            <span>Live Agent Workspace</span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded font-bold bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 border border-emerald-500/30">
              SWITCH ROOM PROTOCOL
            </span>
          </h1>
          <p className="text-xs text-[var(--text-secondary)] mt-1">
            Real-time peer-to-peer message interchange across Vision, Triage, and Investigation agents with loop guards and challenge negotiation.
          </p>
        </div>

        {/* Issue Selector Dropdown */}
        <div className="flex items-center space-x-3">
          <label className="text-xs text-[var(--text-secondary)] font-mono font-medium">Select Issue:</label>
          <select
            value={selectedIssueId}
            onChange={(e) => setSelectedIssueId(e.target.value)}
            className="bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] rounded-lg px-3 py-1.5 text-xs text-[var(--text-main)] font-mono focus:outline-none focus:border-[var(--accent-primary)] shadow-sm"
          >
            {issues.map((i) => (
              <option key={i.issue_id} value={i.issue_id}>
                {i.issue_id.slice(0, 8)} · {i.description.slice(0, 35)}...
              </option>
            ))}
          </select>
          <button
            onClick={() => loadTranscript(selectedIssueId)}
            className="btn-secondary text-xs px-2.5 py-1.5 flex items-center gap-1 shadow-sm"
            title="Refresh room transcript"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Visual Workflow Stage Machine */}
      <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl p-5 shadow-sm">
        <div className="text-[10px] font-mono text-[var(--text-secondary)] uppercase tracking-wider mb-4 font-semibold">
          Pipeline Flow & Handoff Topology
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Node 1: Vision */}
          <div className="p-3.5 rounded-lg bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] space-y-2">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-blue-400 font-bold">1. VISION</span>
              <span className="text-[10px] text-[var(--success)] font-bold">PASSED</span>
            </div>
            <p className="text-[11px] text-[var(--text-secondary)] leading-relaxed">
              Extracts OCR tokens, inspects UI dimensions, identifies visual errors.
            </p>
          </div>

          {/* Node 2: Triage */}
          <div className="p-3.5 rounded-lg bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] space-y-2">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-[var(--warning)] font-bold">2. TRIAGE</span>
              <span className="text-[10px] text-[var(--success)] font-bold">PASSED</span>
            </div>
            <p className="text-[11px] text-[var(--text-secondary)] leading-relaxed">
              Classifies architecture layer, computes impact severity, formulates task.
            </p>
          </div>

          {/* Node 3: Investigation */}
          <div className="p-3.5 rounded-lg bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] space-y-2">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-[var(--success)] font-bold">3. INVESTIGATION</span>
              <span className="text-[10px] text-[var(--success)] font-bold">PASSED</span>
            </div>
            <p className="text-[11px] text-[var(--text-secondary)] leading-relaxed">
              AST static tracing, verifies code symbols, drafts unified diff patch.
            </p>
          </div>

          {/* Node 4: Triage Review */}
          <div className="p-3.5 rounded-lg bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] space-y-2">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-[var(--accent-purple)] font-bold">4. REVIEW</span>
              <span className="text-[10px] text-[var(--success)] font-bold">VERDICT</span>
            </div>
            <p className="text-[11px] text-[var(--text-secondary)] leading-relaxed">
              Disagreement challenges, validates deliverables against objective.
            </p>
          </div>
        </div>
      </div>

      {/* Switch Room Transcript Stream */}
      <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl overflow-hidden shadow-sm">
        <div className="px-5 py-4 border-b border-[var(--border-subtle)] flex items-center justify-between bg-[var(--bg-surface)]">
          <h2 className="text-xs font-mono font-semibold uppercase tracking-wider text-[var(--text-main)] flex items-center gap-2">
            <Terminal className="w-4 h-4 text-[var(--accent-primary)]" />
            <span>Switch Room Message Trace · Room {selectedIssueId ? selectedIssueId.slice(0, 8) : "None"}</span>
          </h2>
          <span className="text-xs font-mono text-[var(--text-secondary)]">{messages.length} messages</span>
        </div>

        {messages.length === 0 ? (
          <div className="p-12 text-center text-[var(--text-secondary)] text-xs font-mono">
            No messages logged for this room. Submit a bug to observe genuine agent negotiation.
          </div>
        ) : (
          <div className="divide-y divide-[var(--border-subtle)] font-mono text-xs">
            {messages.map((msg) => {
              const badge = KIND_BADGES[msg.kind] || {label: msg.kind.toUpperCase(), color: "bg-slate-500/15 text-slate-700 dark:text-slate-400 border-slate-500/30"}
              const isExpanded = expandedMessageId === msg.message_id

              return (
                <div key={msg.message_id} className="p-4 hover:bg-[var(--bg-surface-hover)]/40 transition-colors space-y-2.5">
                  {/* Top metadata line */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2.5">
                      <span className={`text-[10px] px-2 py-0.5 rounded border uppercase font-bold ${badge.color}`}>
                        {badge.label}
                      </span>
                      <span className="text-[var(--accent-primary)] font-bold">{msg.sender}</span>
                      <span className="text-[var(--text-muted)]">→</span>
                      <span className="text-[var(--text-main)] font-semibold">{msg.recipient}</span>
                    </div>
                    <span className="text-[10px] text-[var(--text-secondary)]">
                      {new Date(msg.created_at).toLocaleTimeString()}
                    </span>
                  </div>

                  {/* Summary content */}
                  <div className="text-[var(--text-main)] text-xs leading-relaxed pl-1">
                    {msg.summary}
                  </div>

                  {/* Expandable technical payload inspector */}
                  {msg.content && Object.keys(msg.content).length > 0 && (
                    <div className="pt-1">
                      <button
                        onClick={() => setExpandedMessageId(isExpanded ? null : msg.message_id)}
                        className="text-[10px] text-[var(--text-secondary)] hover:text-[var(--accent-primary)] flex items-center gap-1 transition-colors font-semibold"
                      >
                        {isExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                        <span>{isExpanded ? "Hide JSON Payload" : "Inspect Raw Payload"}</span>
                      </button>

                      {isExpanded && (
                        <pre className="mt-2 p-3 bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] rounded-lg text-[11px] text-[var(--text-main)] overflow-x-auto leading-relaxed shadow-inner">
                          {JSON.stringify(msg.content, null, 2)}
                        </pre>
                      )}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
