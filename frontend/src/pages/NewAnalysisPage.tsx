import React, {useState, useRef} from "react"
import {
  UploadCloud,
  FileCode,
  CheckCircle2,
  AlertCircle,
  X,
  Play,
  RotateCcw,
  ArrowRight,
  Clipboard,
  Eraser,
} from "lucide-react"
import {LottieLoader} from "../components/LottieLoader"

const API_BASE =
  (import.meta as any).env?.VITE_API_BASE || "http://localhost:8000"

export const NewAnalysisPage = ({onNavigate}: {onNavigate: (page: string) => void}) => {
  const [screenshotFile, setScreenshotFile] = useState<File | null>(null)
  const [screenshotPreview, setScreenshotPreview] = useState<string | null>(null)
  const [userDescription, setUserDescription] = useState("")
  const [sourceCode, setSourceCode] = useState("")
  const [devLanguage, setDevLanguage] = useState("auto")
  const [applicationContext, setApplicationContext] = useState("")
  const [isProcessing, setIsProcessing] = useState(false)
  const [swarmStage, setSwarmStage] = useState<"idle" | "bottom" | "center" | "navigating">("idle")
  const [analysisResult, setAnalysisResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFile = (file: File) => {
    if (!file.type.startsWith("image/")) {
      setError("Unsupported file format. Please upload a PNG, JPEG, or WEBP screenshot.")
      return
    }
    if (file.size > 10 * 1024 * 1024) {
      setError("Screenshot file exceeds 10MB limit. Please upload a smaller image.")
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
    setDevLanguage("auto")
    setApplicationContext("")
    setAnalysisResult(null)
    setError(null)
    if (fileInputRef.current) fileInputRef.current.value = ""
  }

  const handlePasteCode = async () => {
    try {
      const text = await navigator.clipboard.readText()
      if (text) setSourceCode(text)
    } catch {
      // ignore clipboard permission error
    }
  }

  const handleSubmit = async () => {
    if (!screenshotFile && !userDescription.trim()) {
      setError("Please provide at least a screenshot or an incident description to begin analysis.")
      return
    }

    setIsProcessing(true)
    setSwarmStage("bottom")
    setError(null)
    setAnalysisResult(null)

    // Smoothly lift from bottom to center of the screen
    setTimeout(() => {
      setSwarmStage("center")
    }, 450)

    const formData = new FormData()
    if (screenshotFile) {
      formData.append("file", screenshotFile)
    }
    formData.append("issue_description", userDescription)
    if (sourceCode.trim()) {
      formData.append("source_code", sourceCode)
    }
    const contextItems = []
    if (devLanguage !== "auto") contextItems.push(`Language: ${devLanguage}`)
    if (applicationContext.trim()) contextItems.push(applicationContext.trim())
    if (contextItems.length) {
      formData.append("developer_notes", contextItems.join(" | "))
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

      // Store active issue ID so the Investigation Reports page immediately highlights & renders this issue
      localStorage.setItem("patchpilot_active_issue", created.issue_id)

      // Animate smoothly forward to the report page
      setSwarmStage("navigating")
      setTimeout(() => {
        setIsProcessing(false)
        onNavigate("Investigation Reports")
      }, 750)
    } catch (err) {
      setIsProcessing(false)
      setSwarmStage("idle")
      setError(err instanceof Error ? err.message : String(err))
    }
  }

  const canSubmit = Boolean(screenshotFile || userDescription.trim())

  return (
    <div className="py-8 px-4 sm:px-6 max-w-4xl mx-auto space-y-6">
      {/* Top Header Card */}
      <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-sm">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-[var(--text-main)] flex items-center gap-2">
            <span>New Bug Analysis</span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-[var(--bg-surface-subtle)] text-[var(--accent-primary)] font-semibold border border-[var(--border-subtle)]">
              Agent Swarm
            </span>
          </h1>
          <p className="text-xs text-[var(--text-secondary)] mt-1">
            Sequential multi-agent intake: Vision OCR breakdown, impact-driven triage, and AST code patch synthesis.
          </p>
        </div>

        {(screenshotFile || userDescription || sourceCode || analysisResult) && (
          <button
            onClick={handleReset}
            className="btn-secondary text-xs flex items-center gap-1.5 self-start sm:self-auto"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset & New Bug</span>
          </button>
        )}
      </div>

      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-500 text-xs font-mono flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Sequential Clean Workflow Form */}
      <div className="space-y-6">
        {/* SECTION 01: Screenshot Evidence */}
        <section className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl p-6 space-y-3 shadow-sm">
          <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-3">
            <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-[var(--text-main)] flex items-center gap-2">
              <span className="w-5 h-5 rounded-full bg-[var(--accent-primary)] text-[#0b0f14] flex items-center justify-center text-[10px] font-black">
                01
              </span>
              <span>Screenshot Evidence</span>
            </h2>
            <span className="text-[11px] font-mono text-[var(--text-secondary)]">
              {screenshotFile ? "1 file attached" : "Optional if text supplied"}
            </span>
          </div>

          {screenshotPreview ? (
            <div className="relative rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface-subtle)] overflow-hidden group">
              <div className="absolute top-3 right-3 z-10">
                <button
                  type="button"
                  onClick={() => {
                    setScreenshotFile(null)
                    setScreenshotPreview(null)
                    if (fileInputRef.current) fileInputRef.current.value = ""
                  }}
                  className="p-1.5 bg-black/70 hover:bg-rose-500 text-white rounded-md backdrop-blur-sm transition-colors"
                  title="Remove screenshot"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
              <img
                src={screenshotPreview}
                alt="Bug Screenshot"
                className="w-full max-h-72 object-contain bg-[var(--bg-surface-subtle)]"
              />
              <div className="p-3 border-t border-[var(--border-subtle)] bg-[var(--bg-surface)] flex items-center justify-between text-[11px] font-mono text-[var(--text-secondary)]">
                <span>{screenshotFile?.name}</span>
                <span>{((screenshotFile?.size || 0) / 1024).toFixed(1)} KB</span>
              </div>
            </div>
          ) : (
            <div
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-[var(--border-subtle)] hover:border-[var(--accent-primary)] rounded-xl p-6 bg-[var(--bg-surface-subtle)]/50 hover:bg-[var(--bg-surface-subtle)] text-center cursor-pointer transition-all flex flex-col items-center justify-center space-y-2 min-h-[140px]"
            >
              <div className="w-9 h-9 rounded-full bg-[var(--bg-surface)] border border-[var(--border-subtle)] flex items-center justify-center text-[var(--accent-primary)]">
                <UploadCloud className="w-4 h-4" />
              </div>
              <div className="space-y-0.5">
                <p className="text-xs font-semibold text-[var(--text-main)]">
                  Drop screenshot here, or click to browse
                </p>
                <p className="text-[11px] text-[var(--text-secondary)]">
                  Supports PNG, JPEG, WEBP up to 10MB · RapidOCR on-device parsing active
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
        </section>

        {/* SECTION 02: Incident Description */}
        <section className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl p-6 space-y-3 shadow-sm">
          <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-3">
            <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-[var(--text-main)] flex items-center gap-2">
              <span className="w-5 h-5 rounded-full bg-[var(--accent-primary)] text-[#0b0f14] flex items-center justify-center text-[10px] font-black">
                02
              </span>
              <span>Incident Description</span>
            </h2>
            <span className="text-[11px] font-mono text-[var(--text-secondary)]">
              Optional if screenshot supplied
            </span>
          </div>

          <textarea
            value={userDescription}
            onChange={(e) => setUserDescription(e.target.value)}
            placeholder="Describe what happened, what you expected to happen, or any error messages (Optional if screenshot provided)."
            rows={4}
            className="w-full bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] focus:border-[var(--accent-primary)] rounded-xl p-3.5 text-xs text-[var(--text-main)] font-mono placeholder:text-[var(--text-muted)] focus:outline-none transition-colors"
          />
        </section>

        {/* SECTION 03: Relevant Source Code */}
        <section className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl p-6 space-y-3 shadow-sm">
          <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-3">
            <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-[var(--text-main)] flex items-center gap-2">
              <span className="w-5 h-5 rounded-full bg-[var(--accent-primary)] text-[#0b0f14] flex items-center justify-center text-[10px] font-black">
                03
              </span>
              <span>Relevant Source Code (Optional)</span>
            </h2>
            <div className="flex items-center space-x-2">
              <button
                type="button"
                onClick={handlePasteCode}
                className="text-[10px] font-mono text-[var(--text-secondary)] hover:text-[var(--text-main)] flex items-center gap-1"
              >
                <Clipboard className="w-3 h-3" />
                <span>Paste</span>
              </button>
              {sourceCode && (
                <button
                  type="button"
                  onClick={() => setSourceCode("")}
                  className="text-[10px] font-mono text-rose-500 hover:text-rose-400 flex items-center gap-1"
                >
                  <Eraser className="w-3 h-3" />
                  <span>Clear</span>
                </button>
              )}
            </div>
          </div>

          <textarea
            value={sourceCode}
            onChange={(e) => setSourceCode(e.target.value)}
            placeholder={"// Supply file, class, or function for Investigation Agent to trace:\n\npublic class App {\n    public static void main(String[] args) {\n        System.out.println(\"Hello World (\n    }\n}"}
            rows={8}
            className="w-full bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] focus:border-[var(--accent-primary)] rounded-xl p-3.5 text-xs text-[var(--text-main)] font-mono placeholder:text-[var(--text-muted)] focus:outline-none transition-colors leading-relaxed"
          />
          <p className="text-[10px] text-[var(--text-secondary)] font-mono">
            Supplying complete files produces complete replacement files; supplying partial functions yields clean contextual replacements.
          </p>
        </section>

        {/* SECTION 04: Developer Context */}
        <section className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl p-6 space-y-3 shadow-sm">
          <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-3">
            <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-[var(--text-main)] flex items-center gap-2">
              <span className="w-5 h-5 rounded-full bg-[var(--accent-primary)] text-[#0b0f14] flex items-center justify-center text-[10px] font-black">
                04
              </span>
              <span>Developer Context (Optional)</span>
            </h2>
            <span className="text-[11px] font-mono text-[var(--text-secondary)]">Optional Environment Specs</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="text-[11px] font-mono text-[var(--text-secondary)] block mb-1">
                Language / Stack
              </label>
              <select
                value={devLanguage}
                onChange={(e) => setDevLanguage(e.target.value)}
                className="w-full bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] rounded-lg px-3 py-2 text-xs text-[var(--text-main)] font-mono focus:outline-none focus:border-[var(--accent-primary)]"
              >
                <option value="auto">Auto-detect</option>
                <option value="python">Python</option>
                <option value="java">Java</option>
                <option value="typescript">TypeScript / React</option>
                <option value="javascript">JavaScript / Node</option>
                <option value="go">Go</option>
                <option value="csharp">C# / .NET</option>
              </select>
            </div>

            <div className="sm:col-span-2">
              <label className="text-[11px] font-mono text-[var(--text-secondary)] block mb-1">
                Environment / Runtime / Database
              </label>
              <input
                type="text"
                value={applicationContext}
                onChange={(e) => setApplicationContext(e.target.value)}
                placeholder="e.g. Java 17 OpenJDK, Gradle 8.2, Docker Alpine"
                className="w-full bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] focus:border-[var(--accent-primary)] rounded-lg px-3 py-2 text-xs text-[var(--text-main)] font-mono placeholder:text-[var(--text-muted)] focus:outline-none transition-colors"
              />
            </div>
          </div>
        </section>

        {/* Loading Button Placeholder or Dispatch Action */}
        <button
          onClick={handleSubmit}
          disabled={isProcessing || !canSubmit}
          className={`w-full py-4 rounded-xl font-mono text-xs font-bold uppercase tracking-wider transition-all flex items-center justify-center space-x-2 shadow-md ${
            isProcessing || !canSubmit
              ? "bg-[var(--bg-surface-hover)] text-[var(--text-muted)] border border-[var(--border-subtle)] cursor-not-allowed"
              : "btn-primary"
          }`}
        >
          {isProcessing ? (
            <span className="flex items-center gap-2">
              <span className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"></span>
              <span>Autonomous Swarm Dispatched...</span>
            </span>
          ) : (
            <span className="flex items-center gap-2">
              <Play className="w-4 h-4 fill-current" />
              <span>Dispatch Agent Investigation</span>
            </span>
          )}
        </button>
      </div>

      {/* 
        Full-Screen Stage Choreography:
        1. "bottom": Starts at bottom of screen where user clicked dispatch
        2. "center": Smoothly glides up to center of the viewport with ambient blur backdrop
        3. "navigating": Glides forward/scales smoothly into the investigation report
      */}
      {isProcessing && (
        <div
          className={`fixed inset-0 z-50 flex items-center justify-center pointer-events-none transition-all duration-700 ease-out ${
            swarmStage === "bottom"
              ? "bg-black/10 backdrop-blur-[2px]"
              : swarmStage === "navigating"
              ? "bg-black/80 backdrop-blur-xl opacity-0 scale-105"
              : "bg-black/60 backdrop-blur-md opacity-100"
          }`}
        >
          <div
            className={`flex flex-col items-center justify-center transition-all duration-700 ease-out will-change-transform ${
              swarmStage === "bottom"
                ? "translate-y-[280px] scale-90 opacity-70"
                : swarmStage === "navigating"
                ? "translate-y-[-80px] scale-110 opacity-0"
                : "translate-y-0 scale-100 opacity-100"
            }`}
          >
            {/* Animation Card */}
            <div className="relative p-6 rounded-3xl bg-[var(--bg-surface)]/95 border-2 border-[var(--accent-primary)] shadow-[0_0_40px_var(--hero-grad-shadow)] flex flex-col items-center space-y-4 max-w-sm mx-auto backdrop-blur-xl animate-swarm-float">
              {/* Corner Sci-Fi Tech Accents */}
              <div className="absolute top-2 left-2 w-3 h-3 border-t-2 border-l-2 border-[var(--accent-primary)]" />
              <div className="absolute top-2 right-2 w-3 h-3 border-t-2 border-r-2 border-[var(--accent-primary)]" />
              <div className="absolute bottom-2 left-2 w-3 h-3 border-b-2 border-l-2 border-[var(--accent-primary)]" />
              <div className="absolute bottom-2 right-2 w-3 h-3 border-b-2 border-r-2 border-[var(--accent-primary)]" />

              <LottieLoader size={140} />

              <div className="text-center space-y-1.5 px-2">
                <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] text-[10px] font-mono text-[var(--accent-primary)] font-bold uppercase tracking-wider">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
                  Agent Swarm Active
                </div>
                <h3 className="text-base font-bold font-mono tracking-tight text-[var(--text-main)]">
                  INVESTIGATING INCIDENT
                </h3>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Immediate Pipeline Result Banner */}
      {analysisResult && (
        <div className="mt-8 border border-[var(--border-subtle)] bg-[var(--bg-surface)] rounded-xl p-6 space-y-4 shadow-sm">
          <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-4">
            <div className="flex items-center space-x-3">
              <CheckCircle2 className="w-5 h-5 text-emerald-500" />
              <div>
                <h3 className="text-sm font-semibold text-[var(--text-main)] font-mono">
                  Analysis Compiled · Issue {analysisResult.issueId.slice(0, 8)}
                </h3>
                <span className="text-[11px] text-[var(--text-secondary)]">Status: {analysisResult.report?.status || "COMPLETED"}</span>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <button
                type="button"
                onClick={handleReset}
                className="btn-secondary text-xs flex items-center gap-1.5"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>New Bug</span>
              </button>
              <button
                onClick={() => onNavigate("Investigation Reports")}
                className="btn-primary text-xs flex items-center gap-1.5"
              >
                <span>View Full Report & Copy Code</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          <div className="p-3 bg-[var(--bg-surface-subtle)] rounded-lg text-xs font-mono text-[var(--text-secondary)]">
            Investigation Agent isolated root cause in{" "}
            <span className="text-[var(--text-main)] font-bold">
              {analysisResult.report?.investigation_findings?.relevant_source_files?.[0] || "source snippet"}
            </span>
            . Complete corrected code is ready for review.
          </div>
        </div>
      )}
    </div>
  )
}
