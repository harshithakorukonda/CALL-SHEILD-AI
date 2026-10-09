import { useMemo, useState } from 'react'
import {
  AlertTriangle,
  AudioLines,
  BadgeCheck,
  BellRing,
  Gauge,
  PhoneCall,
  ShieldCheck,
  Sparkles,
} from 'lucide-react'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import MicTranscript from './components/MicTranscript'
import { analyzeTranscript } from './services/api'

const scenarioLibrary = [
  {
    label: 'Urgent financial scam',
    transcript:
      'Your account is frozen and the bank is investigating suspicious activity. We need the OTP right now or the police will take action. Do not tell anyone.',
  },
  {
    label: 'Family emergency',
    transcript:
      'This is your grandson. I am in the hospital after an accident and I need money immediately. Please send a UPI payment right now so I can be discharged.',
  },
  {
    label: 'Routine support check',
    transcript:
      'Hello, this is a routine security update. We are reviewing your account and can schedule a callback if needed. Please avoid sharing OTPs with anyone.',
  },
]

const signalLabels = {
  urgency: 'Urgency',
  authority: 'Authority',
  fear: 'Fear/Tension',
  secrecy: 'Secrecy',
  financial_request: 'Financial Ask',
  distress: 'Emergency/Distress',
}

function App() {
  const [transcript, setTranscript] = useState(scenarioLibrary[0].transcript)
  const [assessment, setAssessment] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [liveStatus, setLiveStatus] = useState('Caller connected, waiting for transcript.')
  const [history, setHistory] = useState([])

  const chartData = useMemo(() => {
    const keys = Object.keys(signalLabels)
    return keys.map((key) => ({
      name: signalLabels[key],
      value: assessment?.manipulation_signals?.includes(key) ? 100 : 12,
    }))
  }, [assessment])

  const runAnalysis = async (text) => {
    const cleanText = text.trim()
    if (!cleanText) return

    setIsLoading(true)
    setLiveStatus('Analyzing conversation for manipulation signals...')

    try {
      const result = await analyzeTranscript({ transcript: cleanText, session_id: 'demo-session' })
      setAssessment(result)
      setHistory((previous) => [
        {
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          risk: result.risk_level,
          transcript: cleanText,
        },
        ...previous,
      ].slice(0, 4))
      setLiveStatus(
        result.is_scam
          ? 'High-risk conversation detected. Warning recommended.'
          : 'Conversation appears safe. Monitor for follow-up pressure.',
      )
    } catch (error) {
      setLiveStatus('Analysis failed. Please retry the transcript in a moment.')
      console.error(error)
    } finally {
      setIsLoading(false)
    }
  }

  const startLiveDemo = async () => {
    const selected = scenarioLibrary[0]
    setTranscript(selected.transcript)
    await runAnalysis(selected.transcript)
  }

  const headline = assessment
    ? assessment.is_scam
      ? 'Scam-risk alert'
      : 'Conversation is low-risk'
    : 'Transcript risk review'

  const riskTone = assessment
    ? assessment.risk_level === 'HIGH'
      ? 'border-red-500/50 bg-red-500/10 text-red-200'
      : assessment.risk_level === 'MEDIUM'
        ? 'border-amber-500/50 bg-amber-500/10 text-amber-200'
        : 'border-emerald-500/50 bg-emerald-500/10 text-emerald-200'
    : 'border-cyan-500/50 bg-cyan-500/10 text-cyan-200'

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <header className="mb-8 flex items-center justify-between rounded-2xl border border-slate-800 bg-slate-900/80 p-4 shadow-glow backdrop-blur">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-cyan-500/15 p-2 text-cyan-300">
              <ShieldCheck size={22} />
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-cyan-300">CallShield AI</p>
              <h1 className="text-xl font-semibold">Elder-safe scam detection</h1>
            </div>
          </div>
          <div className="flex items-center gap-2 rounded-full border border-emerald-500/40 bg-emerald-500/10 px-3 py-1 text-sm text-emerald-200">
            <BadgeCheck size={16} />
            Browser-based demo
          </div>
        </header>

        <main className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <section className="rounded-3xl border border-slate-800 bg-slate-900/80 p-5 shadow-glow">
            <div className="mb-5 flex items-center justify-between gap-3">
              <div>
                <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Live call</p>
                <h2 className="mt-1 text-2xl font-bold">Caller simulation</h2>
              </div>
              <div className="flex items-center gap-2 rounded-full bg-cyan-500/10 px-3 py-2 text-sm text-cyan-200">
                <PhoneCall size={16} />
                Demo session
              </div>
            </div>

            <div className="mb-5 grid gap-3 sm:grid-cols-3">
              <button
                onClick={startLiveDemo}
                className="rounded-xl bg-cyan-500 px-4 py-3 font-medium text-slate-950 transition hover:bg-cyan-400"
              >
                Start demo call
              </button>
              <button
                onClick={() => runAnalysis(transcript)}
                className="rounded-xl border border-amber-500/40 bg-amber-500/10 px-4 py-3 font-medium text-amber-100 transition hover:bg-amber-500/20"
              >
                Analyze transcript
              </button>
            </div>

            <MicTranscript onUseTranscript={setTranscript} />

            <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
              <div className="mb-3 flex items-center gap-2 text-sm text-slate-300">
                <AudioLines size={16} className="text-cyan-300" />
                {liveStatus}
              </div>
              <textarea
                value={transcript}
                onChange={(event) => setTranscript(event.target.value)}
                className="h-48 w-full resize-none rounded-xl border border-slate-700 bg-slate-900/80 p-3 text-slate-100 outline-none ring-0 placeholder:text-slate-500 focus:border-cyan-500"
                placeholder="Paste or type the caller transcript here..."
              />
            </div>

            <div className="mt-5 flex flex-wrap gap-2">
              {scenarioLibrary.map((scenario) => (
                <button
                  key={scenario.label}
                  onClick={() => {
                    setTranscript(scenario.transcript)
                    runAnalysis(scenario.transcript)
                  }}
                  className="rounded-full border border-slate-700 bg-slate-800 px-3 py-1.5 text-sm text-slate-200 transition hover:border-cyan-500 hover:text-cyan-200"
                >
                  {scenario.label}
                </button>
              ))}
            </div>
          </section>

          <aside className="rounded-3xl border border-slate-800 bg-slate-900/80 p-5 shadow-glow">
            <div className="mb-4 flex items-start justify-between gap-3">
              <div>
                <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Assessment</p>
                <h2 className="mt-1 text-2xl font-bold">{headline}</h2>
              </div>
              <div className={`rounded-full border px-3 py-1 text-sm ${riskTone}`}>
                {assessment ? assessment.risk_level : 'READY'}
              </div>
            </div>

            <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-1 xl:grid-cols-3">
              <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-3">
                <div className="flex items-center gap-2 text-slate-400">
                  <Gauge size={15} />
                  Score
                </div>
                <div className="mt-2 text-2xl font-bold text-white">
                  {assessment ? `${(assessment.score * 100).toFixed(0)}%` : '—'}
                </div>
              </div>
              <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-3">
                <div className="flex items-center gap-2 text-slate-400">
                  <Sparkles size={15} />
                  Confidence
                </div>
                <div className="mt-2 text-2xl font-bold text-white">
                  {assessment ? `${(assessment.confidence * 100).toFixed(0)}%` : '—'}
                </div>
              </div>
              <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-3">
                <div className="flex items-center gap-2 text-slate-400">
                  <BellRing size={15} />
                  Action
                </div>
                <div className="mt-2 text-sm font-semibold text-white">
                  {assessment ? (assessment.is_scam ? 'Warn user' : 'Follow up') : 'Awaiting input'}
                </div>
              </div>
            </div>

            <div className="mt-5 rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
              <div className="mb-3 flex items-center gap-2 text-sm text-slate-300">
                <AlertTriangle size={16} className="text-amber-300" />
                Risk triggers
              </div>
              <div className="h-40 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#cbd5e1' }} interval={0} angle={-10} />
                    <YAxis tick={{ fontSize: 10, fill: '#cbd5e1' }} />
                    <Tooltip />
                    <Bar dataKey="value" fill="#22d3ee" radius={[8, 8, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="mt-5 rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
              <div className="mb-2 flex items-center gap-2 text-sm text-slate-300">
                <ShieldCheck size={16} className="text-emerald-300" />
                Recommendations
              </div>
              <ul className="space-y-2 text-sm text-slate-200">
                {(assessment?.reasons || ['Upload a live transcript to begin the scam analysis.']).map((reason) => (
                  <li key={reason} className="flex gap-3">
                    <span className="mt-1 h-2 w-2 rounded-full bg-cyan-400" />
                    <span>{reason}</span>
                  </li>
                ))}
              </ul>
            </div>
          </aside>
        </main>

        <section className="mt-6 grid gap-6 lg:grid-cols-[1fr_0.9fr]">
          <div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-5 shadow-glow">
            <div className="mb-4 flex items-center gap-2 text-lg font-semibold">
              <ShieldCheck size={18} className="text-emerald-300" />
              Conversation timeline
            </div>
            <div className="space-y-3">
              {(history.length ? history : [{ time: 'Now', risk: 'READY', transcript: 'Waiting for a new transcript...' }]).map((entry, index) => (
                <div key={`${entry.time}-${index}`} className="rounded-2xl border border-slate-800 bg-slate-950/60 p-3">
                  <div className="mb-1 flex items-center justify-between text-xs uppercase tracking-[0.15em] text-slate-400">
                    <span>{entry.time}</span>
                    <span className="rounded-full border border-slate-700 px-2 py-0.5 text-[10px] text-slate-200">
                      {entry.risk}
                    </span>
                  </div>
                  <p className="text-sm text-slate-200">{entry.transcript}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-5 shadow-glow">
            <div className="mb-4 flex items-center gap-2 text-lg font-semibold">
              <BadgeCheck size={18} className="text-cyan-300" />
              Detection summary
            </div>
            <div className="space-y-3 text-sm text-slate-200">
              <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-3">
                <div className="mb-1 text-slate-400">Intent</div>
                <div className="font-medium text-white">{assessment?.semantic_intent || 'No signal detected'}</div>
              </div>
              <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-3">
                <div className="mb-1 text-slate-400">Detections</div>
                <div className="font-medium text-white">
                  {assessment?.manipulation_signals?.length
                    ? assessment.manipulation_signals.join(', ')
                    : 'No manipulative class detected'}
                </div>
              </div>
              <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-3">
                <div className="mb-1 text-slate-400">Redacted transcript</div>
                <div className="font-medium text-white">{assessment?.redacted_transcript || 'Awaiting transcript review'}</div>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}

export default App
