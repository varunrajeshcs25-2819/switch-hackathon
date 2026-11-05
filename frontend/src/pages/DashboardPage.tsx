import React, {useEffect, useState} from "react"
import {AlertCircle, CheckCircle, Activity, Clock} from "lucide-react"

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

export const DashboardPage = () => {
  const [stats, setStats] = useState<Stats | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/stats`)
      if (!res.ok) throw new Error(`Backend returned ${res.status}`)
      setStats(await res.json())
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  if (loading) return <div className="p-6 text-gray-500">Loading dashboard…</div>
  if (error)
    return (
      <div className="p-6">
        <div className="p-4 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
          Could not load stats from {API_BASE}: {error}
        </div>
        <button onClick={load} className="mt-3 btn-secondary">
          Retry
        </button>
      </div>
    )

  const cards = [
    {label: "Total Issues", value: stats?.total_issues ?? 0},
    {label: "Open Investigations", value: stats?.open_investigations ?? 0},
    {label: "Critical Issues", value: stats?.critical_issues ?? 0},
    {label: "High Severity", value: stats?.high_issues ?? 0},
  ]

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <button onClick={load} className="btn-secondary text-sm">
          Refresh
        </button>
      </div>

      {!stats?.model_configured && (
        <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded text-sm text-amber-800 flex items-center">
          <AlertCircle className="w-4 h-4 mr-2 shrink-0" />
          No GEMINI_API_KEY configured. Agents run in honest fallback mode — results
          are clearly marked as uncertain rather than fabricated.
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {cards.map((card) => (
          <div key={card.label} className="bg-white p-6 rounded-xl shadow-sm border">
            <h3 className="text-2xl font-bold">{card.value}</h3>
            <p className="text-gray-500 mt-2 text-sm">{card.label}</p>
          </div>
        ))}
      </div>

      <div className="grid md:grid-cols-2 gap-4 mt-6">
        <div className="bg-white p-6 rounded-xl shadow-sm border">
          <div className="flex items-center mb-3">
            <AlertCircle className="w-5 h-5 mr-2 text-orange-500" />
            <h3 className="font-medium">Awaiting Developer Attention</h3>
          </div>
          <p className="text-2xl font-bold">{stats?.awaiting_attention ?? 0}</p>
          <p className="text-sm text-gray-500 mt-1">
            Critical/high severity issues that are not completed.
          </p>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border">
          <div className="flex items-center mb-3">
            <Activity className="w-5 h-5 mr-2 text-blue-500" />
            <h3 className="font-medium">Recent Agent Activity</h3>
          </div>
          {stats?.recent_activity?.length ? (
            <ul className="space-y-2 max-h-56 overflow-auto">
              {stats.recent_activity.map((item, index) => (
                <li key={index} className="text-sm flex items-start">
                  {item.success === false ? (
                    <AlertCircle className="w-4 h-4 mr-2 mt-0.5 text-red-500 shrink-0" />
                  ) : (
                    <CheckCircle className="w-4 h-4 mr-2 mt-0.5 text-green-500 shrink-0" />
                  )}
                  <div>
                    <span className="font-medium capitalize">{item.agent_role}</span>{" "}
                    <span className="text-gray-500">{item.action}</span>
                    {item.details && (
                      <div className="text-gray-600 break-words">{item.details}</div>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-gray-500">
              No activity yet. Run an analysis to see real agent events here.
            </p>
          )}
        </div>
      </div>

      <p className="mt-6 text-xs text-gray-400 flex items-center">
        <Clock className="w-3 h-3 mr-1" /> Live data from {API_BASE}/stats
      </p>
    </div>
  )
}
