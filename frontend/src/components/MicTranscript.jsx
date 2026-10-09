import { useEffect, useRef, useState } from 'react'
import { Mic, Square, Trash2 } from 'lucide-react'

const getRecognitionConstructor = () => {
  if (typeof window === 'undefined') return null
  return window.SpeechRecognition || window.webkitSpeechRecognition || null
}

const getRecognitionErrorMessage = (code) => {
  const messages = {
    'not-allowed': 'Microphone permission was denied. Allow microphone access in your browser settings and try again.',
    'service-not-allowed': 'The browser speech-recognition service is not allowed. Check your browser settings.',
    'audio-capture': 'No microphone was found. Connect or enable a microphone, then try again.',
    network: 'The browser could access the microphone but could not reach its speech-to-text service. Open this app in Google Chrome, check your internet connection, and retry. A VPN, proxy, firewall, or managed-browser policy may block speech recognition. You can still type or paste a transcript below.',
    'no-speech': 'Speech recognition started but did not receive clear speech. Check that Chrome is using the correct microphone (Chrome site controls → Microphone), then check Windows Settings → System → Sound → Input to confirm the input meter moves. Click Start Listening, wait for “Microphone listening,” and speak continuously near the microphone. This browser feature transcribes speech heard by your microphone; it cannot hear cellular-call audio.',
    'language-not-supported': 'English speech recognition is not available in this browser.',
    aborted: 'Speech recognition was interrupted. You can start listening again.',
  }
  return messages[code] || `Speech recognition failed${code ? ` (${code})` : ''}. Please try again.`
}

function getPermissionErrorMessage(error) {
  if (error?.name === 'NotAllowedError' || error?.name === 'SecurityError') {
    return 'Microphone permission was denied. Allow microphone access for this site in your browser settings and try again.'
  }
  if (error?.name === 'NotFoundError' || error?.name === 'DevicesNotFoundError') {
    return 'No microphone was found. Connect or enable a microphone, then try again.'
  }
  if (error?.name === 'NotReadableError' || error?.name === 'TrackStartError') {
    return 'The microphone is unavailable or being used by another application. Close other apps using it and try again.'
  }
  return 'Could not access the microphone. Check browser permissions and make sure this site is using a secure connection.'
}

function MicTranscript({ onUseTranscript }) {
  const [transcript, setTranscript] = useState('')
  const [isListening, setIsListening] = useState(false)
  const [isRequestingPermission, setIsRequestingPermission] = useState(false)
  const [error, setError] = useState('')
  const [status, setStatus] = useState('Microphone is off.')
  const [isSupported, setIsSupported] = useState(true)
  const recognitionRef = useRef(null)
  const transcriptRef = useRef('')
  const sessionBaseRef = useRef('')
  const sessionResultsRef = useRef(null)
  const mountedRef = useRef(true)
  const requestIdRef = useRef(0)
  const stoppedByUserRef = useRef(false)

  useEffect(() => {
    mountedRef.current = true
    if (!getRecognitionConstructor()) {
      setIsSupported(false)
      setError('Speech recognition is not supported in this browser. You can still type or paste a transcript below.')
    }

    return () => {
      mountedRef.current = false
      requestIdRef.current += 1
      const recognition = recognitionRef.current
      if (recognition) {
        recognition.onresult = null
        recognition.onerror = null
        recognition.onend = null
        recognition.abort()
        recognitionRef.current = null
      }
    }
  }, [])

  const updateTranscript = (value) => {
    transcriptRef.current = value
    setTranscript(value)
  }

  const startListening = async () => {
    const Recognition = getRecognitionConstructor()
    if (!Recognition) {
      setIsSupported(false)
      setError('Speech recognition is not supported in this browser. You can still type or paste a transcript below.')
      return
    }
    if (!navigator.mediaDevices?.getUserMedia) {
      setError('This browser cannot request microphone access here. Open the app on localhost or a secure HTTPS site, or type your transcript below.')
      return
    }

    setError('')
    setIsRequestingPermission(true)
    setStatus('Requesting microphone permission…')
    const requestId = requestIdRef.current + 1
    requestIdRef.current = requestId

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      stream.getTracks().forEach((track) => track.stop())
      if (!mountedRef.current || requestId !== requestIdRef.current) return

      const recognition = new Recognition()
      const previousTranscript = transcriptRef.current.trim()
      const sessionResults = new Map()
      sessionBaseRef.current = previousTranscript
      sessionResultsRef.current = sessionResults
      recognition.lang = 'en-US'
      recognition.continuous = true
      recognition.interimResults = true

      recognition.onresult = (event) => {
        for (let index = event.resultIndex; index < event.results.length; index += 1) {
          const result = event.results[index]
          sessionResults.set(index, {
            text: result[0].transcript.trim(),
          })
        }

        const recognizedText = Array.from(sessionResults.values())
          .map((result) => result.text)
          .filter(Boolean)
          .join(' ')
        updateTranscript([sessionBaseRef.current, recognizedText].filter(Boolean).join(' '))
      }

      recognition.onerror = (event) => {
        if (!mountedRef.current) return
        if (event.error === 'aborted' && stoppedByUserRef.current) return
        setError(getRecognitionErrorMessage(event.error))
        setStatus('Listening stopped.')
      }

      recognition.onend = () => {
        if (!mountedRef.current) return
        recognitionRef.current = null
        setIsListening(false)
        setStatus(stoppedByUserRef.current ? 'Listening stopped.' : 'Listening ended. Start again to continue.')
      }

      stoppedByUserRef.current = false
      recognitionRef.current = recognition
      recognition.start()
      setIsListening(true)
      setStatus('Listening in English. Speak clearly into your microphone.')
    } catch (permissionError) {
      if (!mountedRef.current || requestId !== requestIdRef.current) return
      setError(getPermissionErrorMessage(permissionError))
      setStatus('Microphone is off.')
    } finally {
      if (mountedRef.current && requestId === requestIdRef.current) {
        setIsRequestingPermission(false)
      }
    }
  }

  const stopListening = () => {
    requestIdRef.current += 1
    setIsRequestingPermission(false)
    stoppedByUserRef.current = true
    const recognition = recognitionRef.current
    if (recognition) {
      recognition.stop()
      setStatus('Stopping speech recognition…')
    } else {
      setStatus('Listening stopped.')
      setIsListening(false)
    }
  }

  const clearTranscript = () => {
    updateTranscript('')
    sessionBaseRef.current = ''
    sessionResultsRef.current?.clear()
    setError('')
    setStatus(isListening ? 'Listening in English. Speak clearly into your microphone.' : 'Transcript cleared. Microphone is off.')
  }

  return (
    <section
      aria-labelledby="mic-transcript-heading"
      className="mb-5 rounded-2xl border border-cyan-500/30 bg-slate-950/70 p-4"
    >
      <div className="mb-3 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 id="mic-transcript-heading" className="text-lg font-semibold text-white">
            Microphone transcription
          </h3>
          <p className="mt-1 text-sm text-slate-300">
            English speech is transcribed here only. Nothing is sent for analysis automatically.
          </p>
        </div>
        <div
          role="status"
          aria-live="polite"
          className={`inline-flex items-center gap-2 rounded-full px-3 py-2 text-sm font-semibold ${
            isListening ? 'bg-red-500/15 text-red-200' : 'bg-slate-800 text-slate-200'
          }`}
        >
          <span className={`h-2.5 w-2.5 rounded-full ${isListening ? 'animate-pulse bg-red-400' : 'bg-slate-500'}`} />
          {isListening ? 'Microphone listening' : status}
        </div>
      </div>

      <div className="mb-3 flex flex-wrap gap-3">
        <button
          type="button"
          onClick={startListening}
          disabled={!isSupported || isListening || isRequestingPermission}
          className="inline-flex min-h-12 items-center justify-center gap-2 rounded-xl bg-cyan-400 px-5 py-3 text-base font-bold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <Mic size={19} />
          {isRequestingPermission ? 'Requesting permission…' : 'Start Listening'}
        </button>
        <button
          type="button"
          onClick={stopListening}
          disabled={!isListening && !isRequestingPermission}
          className="inline-flex min-h-12 items-center justify-center gap-2 rounded-xl border border-slate-600 bg-slate-800 px-5 py-3 text-base font-semibold text-white transition hover:border-red-400 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <Square size={17} />
          Stop Listening
        </button>
      </div>

      {error && (
        <p role="alert" className="mb-3 rounded-xl border border-amber-500/50 bg-amber-500/10 p-3 text-base text-amber-100">
          {error}
        </p>
      )}

      <div
        aria-label="Live microphone transcript"
        aria-live="polite"
        className="min-h-28 whitespace-pre-wrap rounded-xl border border-slate-700 bg-slate-900/80 p-4 text-lg leading-relaxed text-white"
      >
        {transcript || <span className="text-slate-400">Recognized speech will appear here. Your manual transcript remains separate.</span>}
      </div>

      <div className="mt-3 flex flex-wrap gap-3">
        <button
          type="button"
          onClick={() => onUseTranscript(transcript)}
          disabled={!transcript.trim()}
          className="min-h-11 rounded-xl border border-cyan-500/50 px-4 py-2 text-base font-semibold text-cyan-100 transition hover:bg-cyan-500/10 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Use transcript in editor
        </button>
        <button
          type="button"
          onClick={clearTranscript}
          disabled={!transcript && !error}
          className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl border border-slate-600 px-4 py-2 text-base font-semibold text-slate-200 transition hover:border-slate-400 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <Trash2 size={17} />
          Clear transcript
        </button>
      </div>
    </section>
  )
}

export default MicTranscript
