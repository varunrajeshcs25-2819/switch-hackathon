import React, {useState, useEffect} from "react"
import {
  CheckCircle as UilCheckCircled,
  Eye as UilEye,
  ArrowLeft as UilArrowLeft,
  AlertCircle as UilAlertCircle,
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

const severityColor = (severity?: string | null) => {
  switch ((severity || "").toLowerCase()) {
    case "critical":
      return "bg-red-100 text-red-700 border-red-200"
    case "high":
      return "bg-orange-100 text-orange-700 border-orange-200"
    case "medium":
      return "bg-yellow-100 text-yellow-700 border-yellow-200"
    case "low":
      return "bg-green-100 text-green-700 border-green-200"
    default:
      return "bg-gray-100 text-gray-600 border-gray-200"
  }
}

export const InvestigationReportsPage = () => {
  const [issues, setIssues] = useState<IssueRow[]>([])
  const [selected, setSelected] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [detailLoading, setDetailLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadIssues = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/issues/`)
      if (!res.ok) throw new Error(`Backend returned ${res.status}`)
      setIssues(await res.json())
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadIssues()
  }, [])

  const openReport = async (issueId: string) => {
    setDetailLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/reports/${issueId}`)
      if (!res.ok) throw new Error(`Backend returned ${res.status}`)
      const body = await res.json()
      setSelected(body.report)
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setDetailLoading(false)
    }
  }

  if (selected) {
    const vision = selected.vision_observations || {}
    const triage = selected.triage_classification || {}
    const inv = selected.investigation_findings || {}

    return (
      <div className="p-6 max-w-4xl mx-auto">
        <button
          onClick={() => setSelected(null)}
          className="inline-flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 mb-4"
        >
          <UilArrowLeft className="w-4 h-4" /> Back to reports
        </button>

        <h2 className="text-2xl font-bold mb-1">Investigation Report</h2>
        <p className="text-sm text-gray-500 mb-6 break-all">
          Issue {selected.issue_id} · status {selected.status}
        </p>

        <section className="bg-white border rounded-xl p-5 shadow-sm mb-4">
          <h3 className="font-medium mb-2">Original report</h3>
          <p className="text-gray-700">{selected.original_description}</p>
        </section>

        <section className="bg-blue-50 border border-blue-200 rounded-xl p-5 mb-4">
          <h3 className="font-medium mb-2">Vision Agent observations</h3>
          <p className="text-gray-700">
            {vision.raw_observation || "No raw observation recorded."}
          </p>
          <dl className="mt-3 text-sm text-gray-700 space-y-1">
            <div>
              <dt className="inline font-medium">Error messages: </dt>
              <dd className="inline break-all">
                {(vision.error_messages || []).join(", ") || "None detected"}
              </dd>
            </div>
            <div>
              <dt className="inline font-medium">Affected components: </dt>
              <dd className="inline break-all">
                {(vision.affected_components || []).join(", ") || "None identified"}
              </dd>
            </div>
            <div>
              <dt className="inline font-medium">Confidence: </dt>
              <dd className="inline">{vision.confidence || "unknown"}</dd>
            </div>
          </dl>
        </section>

        <section className="bg-orange-50 border border-orange-200 rounded-xl p-5 mb-4">
          <h3 className="font-medium mb-2">Triage classification</h3>
          <div className="flex flex-wrap gap-2 text-sm">
            <span className="px-2 py-0.5 rounded border bg-white">
              {triage.classification || "unknown"}
            </span>
            <span className={`px-2 py-0.5 rounded border ${severityColor(triage.severity)}`}>
              {triage.severity || "unknown"}
            </span>
          </div>
          <p className="text-gray-700 mt-3">
            {triage.issue_summary || "No summary provided."}
          </p>
          <p className="text-sm text-gray-600 mt-2">
            <span className="font-medium">Investigation objective: </span>
            {triage.investigation_objective || "—"}
          </p>
          <p className="text-sm text-gray-600 mt-1 break-all">
            <span className="font-medium">Missing information: </span>
            {(triage.missing_information || []).join(", ") || "None"}
          </p>
        </section>

        <section className="bg-green-50 border border-green-200 rounded-xl p-5 mb-4">
          <h3 className="font-medium mb-2">Investigation findings</h3>
          <p className="text-sm text-gray-700">
            <span className="font-medium">Root cause: </span>
            {inv.suspected_root_cause || "Not determined"}
          </p>
          <p className="text-sm text-gray-700 mt-2">
            <span className="font-medium">Summary: </span>
            {inv.investigation_summary || "—"}
          </p>
          <p className="text-sm text-gray-700 mt-2">
            <span className="font-medium">Proposed fix: </span>
            {inv.proposed_fix || "—"}
          </p>
          <p className="text-sm text-gray-700 mt-2">
            <span className="font-medium">Reasoning: </span>
            {inv.reasoning || "—"}
          </p>
          <p className="text-sm text-gray-700 mt-2 break-all">
            <span className="font-medium">Recommended tests: </span>
            {(inv.recommended_tests || []).join("; ") || "None"}
          </p>
          <p className="text-sm text-gray-700 mt-2 break-all">
            <span className="font-medium">Remaining uncertainties: </span>
            {(inv.remaining_uncertainties || []).join("; ") || "None"}
          </p>
        </section>

        <section className="bg-white border rounded-xl p-5 shadow-sm">
          <h3 className="font-medium mb-3">Agent activity</h3>
          {(selected.agent_activity_history || []).length === 0 ? (
            <p className="text-sm text-gray-500">No activity recorded.</p>
          ) : (
            <ul className="text-sm space-y-2">
              {selected.agent_activity_history.map((a: any, i: number) => (
                <li key={i} className="border-l-2 border-gray-200 pl-3">
                  <span className="font-medium capitalize">{a.agent_role}</span>{" "}
                  <span className="text-gray-500">· {a.action}</span>
                  {a.details ? (
                    <p className="text-gray-600 break-all">{a.details}</p>
                  ) : null}
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    )
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold">Investigation Reports</h2>
          <p className="text-gray-600 text-sm mt-1">
            Reports come from the live backend at {API_BASE}.
          </p>
        </div>
        <button
          onClick={loadIssues}
          className="px-4 py-2 text-sm rounded-md border bg-white hover:bg-gray-50"
        >
          Refresh
        </button>
      </div>

      {error && (
        <div className="mb-4 flex items-start gap-2 text-sm text-red-700 bg-red-50 border border-red-200 rounded p-3 break-all">
          <UilAlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <p className="text-gray-600">Loading reports...</p>
      ) : issues.length === 0 ? (
        <div className="bg-white border rounded-xl p-6 text-center shadow-sm">
          <p className="text-gray-700 font-medium">No reports yet</p>
          <p className="text-sm text-gray-500 mt-1">
            Run an analysis from the New Analysis screen to create one.
          </p>
        </div>
      ) : (
        <ul className="space-y-3">
          {issues.map((issue) => (
            <li
              key={issue.issue_id}
              className="bg-white border rounded-xl p-4 shadow-sm flex items-start justify-between gap-4"
            >
              <div className="min-w-0">
                <p className="font-medium truncate">{issue.description}</p>
                <p className="text-xs text-gray-500 mt-1 break-all">
                  {issue.issue_id} · {new Date(issue.created_at).toLocaleString()}
                </p>
                <div className="flex flex-wrap gap-2 mt-2 text-xs">
                  <span className="px-2 py-0.5 rounded border bg-gray-50">
                    {issue.classification || "unclassified"}
                  </span>
                  <span className={`px-2 py-0.5 rounded border ${severityColor(issue.severity)}`}>
                    {issue.severity || "unknown"}
                  </span>
                  <span className="px-2 py-0.5 rounded border bg-gray-50 flex items-center gap-1">
                    <UilCheckCircled className="w-3 h-3" /> {issue.status}
                  </span>
                </div>
              </div>
              <button
                onClick={() => openReport(issue.issue_id)}
                disabled={detailLoading}
                className="shrink-0 inline-flex items-center gap-2 px-3 py-2 text-sm rounded-md bg-primary text-white hover:bg-primary/90 disabled:opacity-50"
              >
                <UilEye className="w-4 h-4" /> Open
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
