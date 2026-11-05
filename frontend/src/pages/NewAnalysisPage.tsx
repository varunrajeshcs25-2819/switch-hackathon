import React, {useState, useRef} from "react"
import {
  UploadCloud,
  FileCode,
  CheckCircle2,
  AlertCircle,
  X,
  Play,
  Layers,
  ArrowRight,
  Info,
  RotateCcw,
  Sparkles,
} from "lucide-react"

const API_BASE =
  (import.meta as any).env?.VITE_API_BASE || "http://localhost:8000"

export const NewAnalysisPage = ({onNavigate}: {onNavigate: (page: string) => void}) => {
  const [screenshotFile, setScreenshotFile] = useState<File | null>(null)
  const [screenshotPreview, setScreenshotPreview] = useState<string | null>(null)
  const [userDescription, setUserDescription] = useState("")
  const [sourceCode, setSourceCode] = useState("")
  const [applicationContext, setApplicationContext] = useState("")
  const [isProcessing, setIsProcessing] = useState(false)
  const [analysisResult, setAnalysisResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFile = (file: File) => {
    if (!file.type.startsWith("image/")) {
      setError("Unsupported file format. Please upload a PNG, JPEG, or WEBP screenshot.")
      return
    }
    setError(null)
    setScreenshotFile(file)
    setScreenshotPreview(URL.createObjectURL(file))
  }

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    if (e.dataTransfer.files?.[0]) {
      handleFile(e.dataTransfer.files[0])
    }
  }

  const handleReset = () => {
    setScreenshotFile(null)
    setScreenshotPreview(null)
    setUserDescription("")
    setSourceCode("")
    setApplicationContext("")
    setAnalysisResult(null)
    setError(null)
    if (fileInputRef.current) fileInputRef.current.value = ""
  }

  const handleSubmit = async () => {
    if (!screenshotFile && !userDescription.trim()) {
      setError("Please provide at least a screenshot or an issue description to begin.")
      return
    }

    setIsProcessing(true)
    setError(null)
    setAnalysisResult(null)

    const formData = new FormData()
    if (screenshotFile) {
      formData.append("file", screenshotFile)
    }
    formData.append("issue_description", userDescription)
    if (sourceCode.trim()) {
      formData.append("source_code", sourceCode)
    }
    if (applicationContext.trim()) {
      formData.append("developer_notes", applicationContext)
    }

    try {
      const res = await fetch(`${API_BASE}/issues/`, {
        method: "POST",
        body: formData,
      })

      if (!res.ok) {
        const detail = await res.text()
        throw new Error(`Pipeline error (${res.status}): ${detail.slice(0, 200)}`)
      }

      const created = await res.json()
      const repRes = await fetch(`${API_BASE}/reports/${created.issue_id}`)
      if (!repRes.ok) throw new Error("Could not retrieve compiled investigation report.")

      const repData = await repRes.json()
      setAnalysisResult({
        issueId: created.issue_id,
        report: repData.report,
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setIsProcessing(false)
    }
  }

  const canSubmit = Boolean(screenshotFile || userDescription.trim())

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#30363d] pb-6">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <span>New Visual Bug Analysis</span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#21262d] text-[#71c9ce] border border-[#30363d]">
              Agent Swarm Ready
            </span>
          </h1>
          <p className="text-xs text-[#8b949e] mt-1">
            Provide a screenshot, stack trace, or source code. The Vision, Triage, and Investigation agents will isolate root cause and formulate verified patches.
          </p>
        </div>

        {(screenshotFile || userDescription || sourceCode || analysisResult) && (
          <button
            onClick={handleReset}
            className="btn-secondary text-xs flex items-center gap-1.5"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset & Add New Bug</span>
          </button>
        )}
      </div>

      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-400 text-xs font-mono flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Main Submission Form */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: Visual Screenshot Dropzone */}
        <div className="space-y-4">
          <label className="text-xs font-mono font-semibold uppercase tracking-wider text-[#8b949e] flex items-center justify-between">
            <span>1. Screenshot Evidence</span>
            <span className="text-[#484f58] lowercase text-[11px]">(optional if description provided)</span>
          </label>

          {screenshotPreview ? (
            <div className="relative rounded-xl border border-[#30363d] bg-[#161b22] overflow-hidden group">
              <div className="absolute top-3 right-3 z-10">
                <button
                  type="button"
                  onClick={() => {
                    setScreenshotFile(null)
                    setScreenshotPreview(null)
                    if (fileInputRef.current) fileInputRef.current.value = ""
                  }}
                  className="p-1.5 bg-[#0d1117]/80 hover:bg-rose-500 text-white rounded-md backdrop-blur-sm transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
              <img
                src={screenshotPreview}
                alt="Bug Screenshot"
                className="w-full max-h-72 object-contain bg-[#0b0f14]"
              />
              <div className="p-3 border-t border-[#30363d] bg-[#161b22] flex items-center justify-between text-[11px] font-mono text-[#8b949e]">
                <span>{screenshotFile?.name}</span>
                <span>{((screenshotFile?.size || 0) / 1024).toFixed(1)} KB</span>
              </div>
            </div>
          ) : (
            <div
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-[#30363d] hover:border-[#71c9ce] rounded-xl p-8 bg-[#161b22]/50 hover:bg-[#161b22] text-center cursor-pointer transition-all flex flex-col items-center justify-center space-y-3 min-h-[220px]"
            >
              <div className="w-10 h-10 rounded-full bg-[#21262d] flex items-center justify-center text-[#71c9ce]">
                <UploadCloud className="w-5 h-5" />
              </div>
              <div className="space-y-1">
                <p className="text-xs font-semibold text-white">
                  Drop screenshot here, or click to browse
                </p>
                <p className="text-[11px] text-[#8b949e]">
                  Supports PNG, JPEG, WEBP up to 10MB
                </p>
              </div>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
                className="hidden"
              />
            </div>
          )}

          {/* Issue Description */}
          <div className="space-y-2">
            <label className="text-xs font-mono font-semibold uppercase tracking-wider text-[#8b949e] flex items-center justify-between">
              <span>2. Incident Description</span>
              <span className="text-[#484f58] lowercase text-[11px]">(symptoms or expected behaviour)</span>
            </label>
            <textarea
              value={userDescription}
              onChange={(e) => setUserDescription(e.target.value)}
              placeholder="e.g. When processing structured JSON payloads, the aggregate calculation crashes unexpectedly with ZeroDivisionError..."
              rows={4}
              className="w-full bg-[#161b22] border border-[#30363d] focus:border-[#71c9ce] rounded-xl p-3 text-xs text-white font-mono placeholder:text-[#484f58] focus:outline-none transition-colors"
            />
          </div>
        </div>

        {/* Right Column: Code & Execution Context */}
        <div className="space-y-4">
          <div className="space-y-2">
            <label className="text-xs font-mono font-semibold uppercase tracking-wider text-[#8b949e] flex items-center justify-between">
              <span>3. Relevant Source Code</span>
              <span className="text-[#71c9ce] text-[10px] font-mono">ENHANCES ACCURACY</span>
            </label>
            <textarea
              value={sourceCode}
              onChange={(e) => setSourceCode(e.target.value)}
              placeholder={"# Paste the relevant function or module for Investigation Agent to inspect:\n\ndef compute_aggregates(item):\n    return item['total'] / item.get('weight', 0)\n"}
              rows={9}
              className="w-full bg-[#161b22] border border-[#30363d] focus:border-[#71c9ce] rounded-xl p-3 text-xs text-white font-mono placeholder:text-[#484f58] focus:outline-none transition-colors"
            />
            <p className="text-[10px] text-[#8b949e] font-mono">
              Note: Agent operates under strict privacy boundaries and only inspects explicitly supplied snippets.
            </p>
          </div>

          <div className="space-y-2">
            <label className="text-xs font-mono font-semibold uppercase tracking-wider text-[#8b949e]">
              4. Developer Context (optional)
            </label>
            <input
              type="text"
              value={applicationContext}
              onChange={(e) => setApplicationContext(e.target.value)}
              placeholder="e.g. FastAPI v0.115, Python 3.12, PostgreSQL db"
              className="w-full bg-[#161b22] border border-[#30363d] focus:border-[#71c9ce] rounded-xl px-3 py-2 text-xs text-white font-mono placeholder:text-[#484f58] focus:outline-none transition-colors"
            />
          </div>

          <button
            onClick={handleSubmit}
            disabled={isProcessing || !canSubmit}
            className={`w-full py-3.5 rounded-xl font-mono text-xs font-semibold uppercase tracking-wider transition-all flex items-center justify-center space-x-2 ${
              isProcessing || !canSubmit
                ? "bg-[#21262d] text-[#484f58] border border-[#30363d] cursor-not-allowed"
                : "bg-[#71c9ce] hover:bg-[#8fe0e5] text-[#0b0f14] shadow-md cursor-pointer"
            }`}
          >
            {isProcessing ? (
              <span className="flex items-center gap-2">
                <span className="w-3.5 h-3.5 border-2 border-[#0b0f14] border-t-transparent rounded-full animate-spin"></span>
                <span>Swarm Running: Vision → Triage → Investigation...</span>
              </span>
            ) : (
              <span className="flex items-center gap-2">
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Dispatch Multi-Agent Workflow</span>
              </span>
            )}
          </button>
        </div>
      </div>

      {/* Immediate Pipeline Result Cards */}
      {analysisResult && (
        <div className="mt-10 border border-[#30363d] bg-[#161b22] rounded-xl p-6 space-y-6">
          <div className="flex items-center justify-between border-b border-[#30363d] pb-4">
            <div className="flex items-center space-x-3">
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              <div>
                <h3 className="text-sm font-semibold text-white font-mono">
                  Multi-Agent Consensus Reached · Issue {analysisResult.issueId.slice(0, 8)}
                </h3>
                <span className="text-[11px] text-[#8b949e]">Status: {analysisResult.report?.status || "COMPLETED"}</span>
              </div>
            </div>
            <button
              onClick={() => onNavigate("Investigation Reports")}
              className="btn-primary text-xs flex items-center gap-1.5"
            >
              <span>Open Detailed Report</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono text-xs">
            {/* Vision card */}
            <div className="bg-[#0d1117] border border-[#30363d] p-4 rounded-lg space-y-2">
              <div className="text-[10px] text-blue-400 font-semibold uppercase flex items-center justify-between">
                <span>Vision Agent</span>
                <span>{analysisResult.report?.vision_observations?.confidence}</span>
              </div>
              <p className="text-[#c9d1d9] text-[11px] line-clamp-3">
                {analysisResult.report?.vision_observations?.raw_observation || "No visual defects detected"}
              </p>
            </div>

            {/* Triage card */}
            <div className="bg-[#0d1117] border border-[#30363d] p-4 rounded-lg space-y-2">
              <div className="text-[10px] text-amber-400 font-semibold uppercase flex items-center justify-between">
                <span>Triage Agent</span>
                <span className="uppercase text-rose-400">{analysisResult.report?.triage_classification?.severity}</span>
              </div>
              <p className="text-[#c9d1d9] text-[11px] line-clamp-3">
                {analysisResult.report?.triage_classification?.issue_summary || "Classification pending"}
              </p>
            </div>

            {/* Investigation card */}
            <div className="bg-[#0d1117] border border-[#30363d] p-4 rounded-lg space-y-2">
              <div className="text-[10px] text-emerald-400 font-semibold uppercase flex items-center justify-between">
                <span>Investigation Agent</span>
                <span>{analysisResult.report?.investigation_findings?.confidence}</span>
              </div>
              <p className="text-[#c9d1d9] text-[11px] line-clamp-3">
                {analysisResult.report?.investigation_findings?.suspected_root_cause || "Empirical review complete"}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
