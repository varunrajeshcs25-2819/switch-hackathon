import React, {useEffect, useState} from "react"
import {AlertCircle, CheckCircle, Eye, Filter, RefreshCw, Server} from "lucide-react"

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

const KIND_STYLES: Record<string, string> = {
  observation: "bg-blue-100 text-blue-800 border-blue-200",
  classification: "bg-orange-100 text-orange-800 border-orange-200",
  task: "bg-purple-100 text-purple-800 border-purple-200",
  findings: "bg-green-100 text-green-800 border-green-200",
  challenge: "bg-red-100 text-red-800 border-red-200",
  verdict: "bg-gray-100 text-gray-800 border-gray-200",
  error: "bg-red-100 text-red-800 border-red-200",
  system: "bg-slate-100 text-slate-700 border-slate-200",
}

const AGENT_COLORS: Record<string, string> = {
  vision: "text-blue-700",
  triage: "text-orange-700",
  investigation: "text-green-700",
  system: "text-gray-500",
}

export const AgentCollaborationPage = () => {
  const [issues, setIssues] = useState<Issue[]>([])
  const [selected, setSelected] = useState<string>("")
  const [messages, setMessages] = useState<AgentMessage[]>([])
  const [counts, setCounts] = useState<Record<string, number>>({})
  const [sourceCodeSupplied, setSourceCodeSupplied] = useState(false)
  const [loadingIssues, setLoadingIssues] = useState(true)
  const [loadingMessages, setLoadingMessages] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [expanded, setExpanded] = useState<string | null>(null)

  const loadIssues = async () => {
    setLoadingIssues(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/issues/`)
      if (!res.ok) throw new Error(`Backend returned ${res.status}`)
      const data: Issue[] = await res.json()
      setIssues(data)
      if (data.length && !selected) setSelected(data[0].issue_id)
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setLoadingIssues(false)
    }
  }

  const loadMessages = async (issueId: string) => {
    if (!issueId) return
    setLoadingMessages(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/issues/${issueId}/messages`)
      if (!res.ok) throw new Error(`Backend returned ${res.status}`)
      const data = await res.json()
      setMessages(data.messages || [])
      setCounts(data.counts || {})
      setSourceCodeSupplied(Boolean(data.source_code_supplied))
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setLoadingMessages(false)
    }
  }

  useEffect(() => {
    loadIssues()
  }, [])

  useEffect(() => {
    if (selected) loadMessages(selected)
  }, [selected])

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-2xl font-bold flex items-center">
          <Eye className="w-6 h-6 mr-2" /> Agent Collaboration
        </h2>
        <button
          onClick={() => {
            loadIssues()
            if (selected) loadMessages(selected)
          }}
          className="btn-secondary text-sm flex items-center"
        >
          <RefreshCw className="w-4 h-4 mr-1" /> Refresh
        </button>
      </div>
      <p className="text-gray-600 mb-4 text-sm">
        Live transcript of the Switch-style room for a real issue. Every message
        below is produced by an agent run — nothing here is a scripted demo.
      </p>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
          {error}
        </div>
      )}

      <div className="bg-white rounded-xl border shadow-sm p-4 mb-4 flex flex-wrap items-center gap-3">
        <label className="text-sm font-medium text-gray-700">Issue:</label>
        <select
          value={selected}
          onChange={(e) => setSelected(e.target.value)}
          className="border rounded px-2 py-1 text-sm max-w-xl flex-1"
          disabled={loadingIssues || issues.length === 0}
        >
          {issues.length === 0 && <option value="">No issues yet</option>}
          {issues.map((issue) => (
            <option key={issue.issue_id} value={issue.issue_id}>
              {issue.issue_id.slice(0, 8)} — {issue.description.slice(0, 70)}
            </option>
          ))}
        </select>
        {selected && (
          <span className="text-xs text-gray-500 font-mono">{selected.slice(0, 8)}</span>
        )}
        {sourceCodeSupplied && (
          <span className="text-xs px-2 py-1 rounded bg-green-100 text-green-800 border border-green-200">
            source code supplied
          </span>
        )}
      </div>

      {Object.keys(counts).length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {Object.entries(counts).map(([agent, count]) => (
            <span
              key={agent}
              className={`text-xs px-2 py-1 rounded border bg-white ${AGENT_COLORS[agent] || "text-gray-600"}`}
            >
              {agent}: {count} msg
            </span>
          ))}
        </div>
      )}

      {loadingMessages ? (
        <div className="text-gray-500">Loading transcript…</div>
      ) : messages.length === 0 ? (
        <div className="bg-white border rounded-xl p-8 text-center text-gray-500">
          <Server className="w-8 h-8 mx-auto mb-2 text-gray-400" />
          No messages for this issue yet. Run a new analysis to generate a real
          agent conversation.
        </div>
      ) : (
        <ol className="space-y-3">
          {messages.map((message) => {
            const isOpen = expanded === message.message_id
            return (
              <li key={message.message_id} className="bg-white border rounded-xl p-4 shadow-sm">
                <div className="flex flex-wrap items-center gap-2 mb-2">
                  <span className={`font-medium ${AGENT_COLORS[message.sender] || "text-gray-700"}`}>
                    {message.sender}
                  </span>
                  <span className="text-gray-400">→</span>
                  <span className={`font-medium ${AGENT_COLORS[message.recipient] || "text-gray-700"}`}>
                    {message.recipient}
                  </span>
                  <span
                    className={`text-xs px-2 py-0.5 rounded border ${KIND_STYLES[message.kind] || "bg-gray-50 text-gray-600"}`}
                  >
                    {message.kind}
                  </span>
                  <span className="text-xs text-gray-400 ml-auto">
                    {new Date(message.created_at).toLocaleTimeString()}
                  </span>
                </div>
                <p className="text-gray-800 text-sm break-words">{message.summary}</p>
                <button
                  onClick={() => setExpanded(isOpen ? null : message.message_id)}
                  className="mt-2 text-xs text-blue-600 hover:underline flex items-center"
                >
                  <Filter className="w-3 h-3 mr-1" />
                  {isOpen ? "Hide payload" : "Show payload"}
                </button>
                {isOpen && (
                  <pre className="mt-2 text-xs bg-gray-50 border rounded p-3 overflow-auto max-h-72">
                    {JSON.stringify(message.content, null, 2)}
                  </pre>
                )}
              </li>
            )
          })}
        </ol>
      )}

      <div className="mt-6 flex items-start text-xs text-gray-500">
        {messages.some((m) => m.kind === "error") ? (
          <AlertCircle className="w-4 h-4 mr-1 text-red-500" />
        ) : (
          <CheckCircle className="w-4 h-4 mr-1 text-green-500" />
        )}
        Messages are persisted with the issue and survive a backend restart.
      </div>
    </div>
  )
}
