import React, {useEffect, useState} from "react"
import {
  AlertCircle,
  CheckCircle2,
  Activity,
  Clock,
  ArrowRight,
  ShieldAlert,
  Flame,
  Search,
  ExternalLink,
  PlusCircle,
  FileCode,
} from "lucide-react"

const API_BASE =
  (import.meta as any).env?.VITE_API_BASE || "http://localhost:8000"

type Stats = {
  total_issues: number
  open_investigations: number
  critical_issues: number
  high_issues: number
  awaiting_attention: number
  model_configured: boolean
  recent_activity: Array<{
    timestamp: string
    agent_role: string
    action: string
    details?: string
    success?: boolean
    issue_id?: string
  }>
}

type IssueRow = {
  issue_id: string
  description: string
  status: string
  classification?: string | null
  severity?: string | null
  created_at: string
}

const severityBadge = (severity?: string | null) => {
  switch ((severity || "").toLowerCase()) {
    case "critical":
      return "bg-rose-500/10 text-rose-400 border-rose-500/30"
    case "high":
      return "bg-orange-500/10 text-orange-400 border-orange-500/30"
    case "medium":
      return "bg-amber-500/10 text-amber-400 border-amber-500/30"
    case "low":
      return "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
    default:
      return "bg-slate-500/10 text-slate-400 border-slate-500/30"
  }
}

export const DashboardPage = ({onNavigate}: {onNavigate: (page: string) => void}) => {
  const [stats, setStats] = useState<Stats | null>(null)
  const [issues, setIssues] = useState<IssueRow[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [statsRes, issuesRes] = await Promise.all([
        fetch(`${API_BASE}/stats`),
        fetch(`${API_BASE}/issues/`),
      ])
      if (!statsRes.ok) throw new Error(`Stats endpoint returned ${statsRes.status}`)
      if (!issuesRes.ok) throw new Error(`Issues endpoint returned ${issuesRes.status}`)

      setStats(await statsRes.json())
      setIssues(await issuesRes.json())
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  if (loading) {
    return (
      <div className="p-8 text-center text-[#8b949e] font-mono text-sm">
        Initializing telemetry and loading engineering state...
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-8 max-w-4xl mx-auto">
        <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-lg text-rose-400 text-sm font-mono flex items-center justify-between">
          <span>Failed to connect to backend at {API_BASE}: {error}</span>
          <button onClick={loadData} className="btn-secondary text-xs">
            Retry Connection
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#30363d] pb-6">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2.5">
            Command Center
            <span className="text-xs px-2 py-0.5 rounded font-mono font-medium bg-[#21262d] text-[#8b949e] border border-[#30363d]">
              Live Swarm
            </span>
          </h1>
          <p className="text-xs text-[#8b949e] mt-1">
            Real-time multi-agent triage, visual OCR breakdown, and verified code patch orchestration.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button onClick={loadData} className="btn-secondary text-xs">
            Refresh State
          </button>
          <button
            onClick={() => onNavigate("New Bug Analysis")}
            className="btn-primary text-xs flex items-center gap-1.5"
          >
            <PlusCircle className="w-3.5 h-3.5" />
            <span>Submit New Bug</span>
          </button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-5">
          <div className="text-[11px] font-mono uppercase tracking-wider text-[#8b949e]">
            Total Ingested Issues
          </div>
          <div className="text-3xl font-black text-white mt-2 font-mono">
            {stats?.total_issues ?? 0}
          </div>
          <div className="text-[11px] text-[#484f58] mt-1">Persisted in SQLite database</div>
        </div>

        <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-5">
          <div className="text-[11px] font-mono uppercase tracking-wider text-[#8b949e] flex items-center justify-between">
            <span>Critical Severity</span>
            <Flame className="w-3.5 h-3.5 text-rose-400" />
          </div>
          <div className="text-3xl font-black text-rose-400 mt-2 font-mono">
            {stats?.critical_issues ?? 0}
          </div>
          <div className="text-[11px] text-[#484f58] mt-1">System breaking issues</div>
        </div>

        <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-5">
          <div className="text-[11px] font-mono uppercase tracking-wider text-[#8b949e] flex items-center justify-between">
            <span>High Severity</span>
            <ShieldAlert className="w-3.5 h-3.5 text-orange-400" />
          </div>
          <div className="text-3xl font-black text-orange-400 mt-2 font-mono">
            {stats?.high_issues ?? 0}
          </div>
          <div className="text-[11px] text-[#484f58] mt-1">Impacts core workflow</div>
        </div>

        <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-5">
          <div className="text-[11px] font-mono uppercase tracking-wider text-[#8b949e]">
            Awaiting Dev Attention
          </div>
          <div className="text-3xl font-black text-[#71c9ce] mt-2 font-mono">
            {stats?.awaiting_attention ?? 0}
          </div>
          <div className="text-[11px] text-[#484f58] mt-1">Needs review or patch merge</div>
        </div>
      </div>

      {/* Main Grid: Persisted Issues List & Recent Agent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Issues List (2 Cols) */}
        <div className="lg:col-span-2 bg-[#161b22] border border-[#30363d] rounded-xl overflow-hidden">
          <div className="px-5 py-4 border-b border-[#30363d] flex items-center justify-between bg-[#161b22]">
            <h2 className="text-sm font-semibold text-white">Active Bug Callsets & Investigations</h2>
            <span className="text-xs font-mono text-[#8b949e]">{issues.length} records</span>
          </div>

          {issues.length === 0 ? (
            <div className="p-8 text-center text-[#8b949e] text-xs font-mono">
              No issues submitted yet. Click "Submit New Bug" to run the Vision → Triage → Investigation pipeline.
            </div>
          ) : (
            <div className="divide-y divide-[#30363d]">
              {issues.map((issue) => (
                <div
                  key={issue.issue_id}
                  className="p-4 hover:bg-[#21262d]/40 transition-colors flex items-center justify-between gap-4"
                >
                  <div className="space-y-1.5 flex-1 min-w-0">
                    <div className="flex items-center space-x-2">
                      <span className={`text-[10px] font-mono px-2 py-0.5 rounded border uppercase ${severityBadge(issue.severity)}`}>
                        {issue.severity || "medium"}
                      </span>
                      <span className="text-[11px] font-mono text-[#71c9ce] truncate">
                        {issue.classification || "UNKNOWN"}
                      </span>
                      <span className="text-[10px] font-mono text-[#484f58]">
                        ID: {issue.issue_id.slice(0, 8)}
                      </span>
                    </div>
                    <div className="text-xs text-[#e6edf3] font-medium truncate">
                      {issue.description}
                    </div>
                    <div className="text-[10px] text-[#8b949e] font-mono flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      <span>{new Date(issue.created_at).toLocaleString()}</span>
                    </div>
                  </div>

                  <button
                    onClick={() => onNavigate("Investigation Reports")}
                    className="btn-secondary text-[11px] px-3 py-1.5 shrink-0 flex items-center gap-1"
                  >
                    <span>View Report</span>
                    <ArrowRight className="w-3 h-3" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Live Swarm Activity Log (1 Col) */}
        <div className="bg-[#161b22] border border-[#30363d] rounded-xl overflow-hidden flex flex-col">
          <div className="px-5 py-4 border-b border-[#30363d] flex items-center justify-between">
            <h2 className="text-sm font-semibold text-white flex items-center gap-2">
              <Activity className="w-4 h-4 text-[#71c9ce]" />
              <span>Agent Room Activity</span>
            </h2>
            <span className="text-[10px] font-mono text-emerald-400">REAL-TIME</span>
          </div>

          <div className="p-4 flex-1 overflow-y-auto max-h-[380px] space-y-3 font-mono text-xs">
            {stats?.recent_activity?.length ? (
              stats.recent_activity.map((item, idx) => (
                <div
                  key={idx}
                  className="p-2.5 rounded bg-[#0d1117] border border-[#30363d] space-y-1"
                >
                  <div className="flex items-center justify-between text-[10px]">
                    <span className="text-[#71c9ce] font-semibold uppercase">{item.agent_role}</span>
                    <span className="text-[#484f58]">{new Date(item.timestamp).toLocaleTimeString()}</span>
                  </div>
                  <div className="text-white text-[11px] font-medium">{item.action}</div>
                  {item.details && (
                    <div className="text-[#8b949e] text-[10px] line-clamp-2 leading-relaxed">
                      {item.details}
                    </div>
                  )}
                </div>
              ))
            ) : (
              <div className="text-center text-[#8b949e] py-12 text-[11px]">
                No recent agent events in room buffer.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
