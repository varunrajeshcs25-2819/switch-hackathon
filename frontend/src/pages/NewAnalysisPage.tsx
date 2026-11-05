import React, {useState, useEffect, useRef} from "react"
import {
  Camera as UilCamera,
  X as UilCross,
  CheckCircle as UilCheckCircled,
  AlertCircle as UilAlertCircle,
  Download as UilDownload,
} from "lucide-react"

// Real backend integration. Override with VITE_API_BASE if the API runs elsewhere.
const API_BASE =
  (import.meta as any).env?.VITE_API_BASE || "http://localhost:8000"

const AIService = {
  /**
   * Runs the full real pipeline on the FastAPI backend:
   * POST /issues/ (vision -> triage -> investigation) then GET /reports/{id}.
   */
  async runWorkflow(
    file: File | null,
    description: string,
    sourceCode: string
  ): Promise<any> {
    const form = new FormData()
    if (file) {
      form.append("file", file)
    }
    form.append(
      "issue_description",
      description || (file ? "Visual bug reported from screenshot" : "")
    )
    if (sourceCode.trim()) {
      form.append("source_code", sourceCode)
    }

    const res = await fetch(`${API_BASE}/issues/`, {
      method: "POST",
      body: form,
    })
    if (!res.ok) {
      const detail = await res.text()
      throw new Error(
        `Backend returned ${res.status}: ${detail.slice(0, 200)}`
      )
    }

    const created = await res.json()
    const reportRes = await fetch(`${API_BASE}/reports/${created.issue_id}`)
    if (!reportRes.ok) {
      throw new Error(`Could not load report: ${reportRes.status}`)
    }
    const { report } = await reportRes.json()

    const vision = report.vision_observations || {}
    const triage = report.triage_classification || {}
    const investigation = report.investigation_findings || {}

    return {
      issueId: created.issue_id,
      report,
      vision: {
        errorMessages: vision.error_messages || [],
        affectedComponents: vision.affected_components || [],
        confidence: vision.confidence || "uncertain",
        uncertainties: vision.uncertainties || [],
        rawObservation:
          vision.raw_observation || "No observations were returned.",
      },
      triage: {
        classification: triage.classification || "unknown",
        severity: triage.severity || "medium",
        issueSummary: triage.issue_summary || "",
        affectedComponents: triage.affected_components || [],
        missingInformation: triage.missing_information || [],
        investigationObjective: triage.investigation_objective || "",
        assignedAgent: triage.assigned_agent || "investigation",
        reasonForDelegation: triage.reason_for_delegation || "",
      },
      investigation: {
        investigationSummary: investigation.investigation_summary || "",
        suspectedRootCause:
          investigation.suspected_root_cause || "Not determined",
        relevantSourceFiles: investigation.relevant_source_files || [],
        relevantCodeLocations: investigation.relevant_code_locations || [],
        supportingEvidence: investigation.supporting_evidence || [],
        reasoning: investigation.reasoning || "",
        proposedFix: investigation.proposed_fix || "",
        proposedCodeChanges: investigation.proposed_code_changes || null,
        recommendedTests: investigation.recommended_tests || [],
        actualTestResults: investigation.actual_test_results || null,
        confidence: investigation.confidence || "medium",
        remainingUncertainties: investigation.remaining_uncertainties || [],
      },
    }
  },
}

export const NewAnalysisPage = () => {
  const [screenshotFile, setScreenshotFile] = useState<File | null>(null)
  const [userDescription, setUserDescription] = useState("")
  const [sourceCode, setSourceCode] = useState("")
  const [isProcessing, setIsProcessing] = useState(false)
  const [visionResults, setVisionResults] = useState<any>(null)
  const [triageResults, setTriageResults] = useState<any>(null)
  const [investigationResults, setInvestigationResults] = useState<any>(null)
  const [showReport, setShowReport] = useState(false)
  const [reportJson, setReportJson] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setScreenshotFile(file)
      setUserDescription("")
    }
  }

  const handleAnalyze = async () => {
    if (!screenshotFile && !userDescription.trim()) return

    setIsProcessing(true)
    setVisionResults(null)
    setTriageResults(null)
    setInvestigationResults(null)
    setShowReport(false)
    setReportJson(null)
    setError(null)

    try {
      // Real backend call: vision -> triage -> investigation -> report
      const result = await AIService.runWorkflow(
        screenshotFile,
        userDescription,
        sourceCode
      )
      setVisionResults(result.vision)
      setTriageResults(result.triage)
      setInvestigationResults(result.investigation)
      setReportJson(result.report)
      setShowReport(true)
    } catch (err) {
      console.error("Analysis failed:", err)
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setIsProcessing(false)
    }
  }

  const canSubmit = Boolean(screenshotFile || userDescription.trim())

  return (
    <div className="max-w-2xl mx-auto">
      <h2 className="text-2xl font-bold mb-6">New Visual Bug Analysis</h2>

      <div className="bg-white p-6 rounded-xl shadow mb-6">
        <div className="mb-4">
          <label className="block text-gray-700 font-medium mb-2">
            Describe the issue (optional)
          </label>
          <textarea
            value={userDescription}
            onChange={(e) => setUserDescription(e.target.value)}
            placeholder="e.g., Registration form shows HTTP 500 error when submitted"
            rows={3}
            className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary"
          ></textarea>
        </div>

        <div className="mb-4">
          <label className="block text-gray-700 font-medium mb-2">
            Relevant source code (optional)
          </label>
          <textarea
            value={sourceCode}
            onChange={(e) => setSourceCode(e.target.value)}
            placeholder={"Paste the files you want the Investigation Agent to inspect, e.g.\n\n@app.post('/register')\ndef register(...):\n    ..."}
            rows={8}
            className="w-full border border-gray-300 rounded px-3 py-2 font-mono text-xs focus:outline-none focus:ring-2 focus:ring-primary"
          ></textarea>
          <p className="text-xs text-gray-500 mt-1">
            Only what you paste here is visible to the agent. It never reads your
            filesystem.
          </p>
        </div>

        {screenshotFile && (
          <div className="mt-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-gray-600">Attached Screenshot: {screenshotFile.name}</span>
              <button
                type="button"
                onClick={() => setScreenshotFile(null)}
                className="text-xs text-red-500 hover:underline"
              >
                Remove
              </button>
            </div>
            <img
              src={URL.createObjectURL(screenshotFile)}
              alt="Uploaded screenshot"
              className="mt-1 rounded w-full max-h-64 object-contain border"
            />
          </div>
        )}

        {!screenshotFile && (
          <div className="mt-4 p-6 bg-gray-50 border-2 border-dashed border-[#cbf1f5] rounded-xl text-center">
            <p className="text-gray-600 text-sm">
              Upload screenshot (optional if issue description is provided)
            </p>
            <input
              type="file"
              accept="image/*"
              onChange={handleFileChange}
              ref={fileInputRef}
              className="hidden"
            />
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="mt-3 inline-block btn-primary text-sm"
            >
              Browse Files
            </button>
          </div>
        )}
      </div>

      <button
        onClick={handleAnalyze}
        disabled={isProcessing || !canSubmit}
        className={`w-full mt-6 px-6 py-3 rounded-md font-medium ${
          isProcessing || !canSubmit
            ? "opacity-50 cursor-not-allowed"
            : "bg-primary text-white hover:bg-primary/90 transition-colors"}
        `}>
        {isProcessing
          ? "Analyzing... (Vision → Triage → Investigation)"
          : "Start Agent Workflow"}
      </button>

      {visionResults && (
        <div className="mt-8 p-6 bg-blue-50 rounded-xl border border-blue-200 mb-6">
          <h3 className="text-xl font-medium mb-3">Vision Agent Observations</h3>
          <p className="text-gray-700">{visionResults.rawObservation}</p>
          <div className="grid grid-cols-2 gap-4 mt-4">
            <div>
              <p className="font-medium">Error Messages:</p>
              <p className="mt-1 break-all">{visionResults.errorMessages.join(
                ", "
              ) || "None detected"}</p>
            </div>
            <div>
              <p className="font-medium">Affected Components:</p>
              <p className="mt-1 break-all">{visionResults.affectedComponents.join(
                ", "
              ) || "None identified"}</p>
            </div>
          </div>
          <p className="mt-4 font-medium">Confidence: {visionResults.confidence}</p>
        </div>
      )}

      {triageResults && (
        <div className="mt-8 p-6 bg-orange-50 rounded-xl border border-orange-200 mb-6">
          <h3 className="text-xl font-medium mb-3">Triage Classification</h3>
          <p className="font-medium">Classification: {triageResults.classification}</p>
          <p className="font-medium">Severity: {triageResults.severity}</p>
          <p className="font-medium">Issue Summary:</p>
          <p className="mt-1 break-all">{triageResults.issueSummary}</p>
          <p className="mt-4 text-sm text-gray-600">
            Missing Information: {(
              triageResults.missingInformation ||
              []
            ).join(", ") || "None identified"}
          </p>
        </div>
      )}

      {investigationResults && (
        <div className="mt-8 p-6 bg-green-50 rounded-xl border border-green-200 mb-6">
          <h3 className="text-xl font-medium mb-3">Investigation Findings</h3>
          <p className="font-medium">Root Cause:</p>
          <p className="mt-1 break-all">{investigationResults.suspectedRootCause}</p>
          <p className="font-medium">Investigation Summary:</p>
          <p className="mt-1 break-all">{investigationResults.investigationSummary}</p>
          <p className="font-medium">Recommended Fix:</p>
          <p className="mt-1 break-all">{investigationResults.proposedFix}</p>
          <p className="font-medium">Confidence: {investigationResults.confidence}</p>
          <p className="mt-2 text-sm text-gray-600">
            Remaining Uncertainties:{
              investigationResults.remainingUncertainties &&
              investigationResults.remainingUncertainties.length > 0
                ? (
                  <span>
                    {investigationResults.remainingUncertainties.map(
                      (u: string, i: number) => (
                        <div key={i} className="pl-4 border-l border-gray-300 my-1">
                          {u}
                        </div>
                      )
                    )}
                  </span>
                )
                : "None"}
          </p>
        </div>
      )}

      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded text-red-700 text-sm break-all">
          {error}
        </div>
      )}

      {showReport && reportJson && (
        <button
          onClick={() => {
            const blob = new Blob([JSON.stringify(reportJson, null, 2)], {
              type: "application/json",
            })
            const url = URL.createObjectURL(blob)
            const a = document.createElement("a")
            a.href = url
            a.download = `patchpilot-report-${reportJson.issue_id}.json`
            a.click()
            URL.revokeObjectURL(url)
          }}
          className="mt-6 btn-secondary"
        >
          Download Full Report (JSON)
        </button>
      )}
    </div>
  )
}