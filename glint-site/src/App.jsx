import { useEffect, useMemo, useState } from 'react'
import './App.css'
import { InterviewerPrompt } from './data/prompts'
import {
  INITIAL_PROFILE,
  PILLARS,
  STYLE_TAG_DEFINITIONS,
  TYPE_PILLARS,
} from './data/pillarsDefinition'

const safeJsonParse = (value) => {
  if (typeof value !== 'string') return null
  const cleaned = value
    .trim()
    .replace(/^```json/i, '')
    .replace(/^```/i, '')
    .replace(/```$/, '')
    .trim()
  try {
    return JSON.parse(cleaned)
  } catch (error) {
    const start = cleaned.indexOf('{')
    const end = cleaned.lastIndexOf('}')
    if (start === -1 || end === -1 || end <= start) return null
    try {
      return JSON.parse(cleaned.slice(start, end + 1))
    } catch (nestedError) {
      return null
    }
  }
}

function App() {
  const [, setTick] = useState(0)
  const [chatHistory, setChatHistory] = useState([
    {
      role: 'agent',
      text: 'Hi! I’m here to learn about you gently and at your pace. What is your name?',
    },
  ])
  const [userProfile, setUserProfile] = useState(INITIAL_PROFILE)
  const [parserRaw, setParserRaw] = useState('')
  const [parserUpdatedAt, setParserUpdatedAt] = useState(null)
  const [input, setInput] = useState('')
  const [finalized, setFinalized] = useState(false)

  useEffect(() => {
    const interval = setInterval(() => {
      setTick((prev) => prev + 1)
    }, 800)
    return () => clearInterval(interval)
  }, [])

  const allPillarsConfident = useMemo(
    () =>
      PILLARS.every((pillar) => {
        const data = userProfile[pillar.key]
        return (data?.confidence || 0) >= 0.7
      }),
    [userProfile]
  )

  const handleMessage = async (message) => {
    const apiKey = "sk-fb7494a1e69846f2940cfc751f2d28de" //import.meta.env.VITE_DEEPSEEK_API_KEY
    if (!apiKey) {
      throw new Error('Missing VITE_DEEPSEEK_API_KEY')
    }

    const userMessage = { role: 'user', text: message }
    const updatedHistory = [...chatHistory, userMessage]

    if (allPillarsConfident) {
      const closingReply =
        'Thank you — I feel I have a clear picture across all pillars.'
      setChatHistory([...updatedHistory, { role: 'agent', text: closingReply }])
      return
    }

    const updatedTranscript = updatedHistory
      .map((m) => `${m.role}: ${m.text}`)
      .join('\n')

    // Agent A (Interviewer) call (single prompt):
    const interviewerResponse = await fetch(
      'https://api.deepseek.com/chat/completions',
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${apiKey}`,
        },
        body: JSON.stringify({
          model: 'deepseek-chat',
          messages: [
            {
              role: 'user',
              content: InterviewerPrompt(
                updatedTranscript,
                JSON.stringify(PILLARS, null, 2),
                JSON.stringify(STYLE_TAG_DEFINITIONS, null, 2),
                JSON.stringify(userProfile, null, 2)
              ),
            },
          ],
          temperature: 0.6,
        }),
      }
    )
    const interviewerJson = await interviewerResponse.json()
    const agentReply =
      interviewerJson?.choices?.[0]?.message?.content ||
      'Thanks for sharing. Could you tell me more?'

    const nextHistory = [...updatedHistory, { role: 'agent', text: agentReply }]
    setChatHistory(nextHistory)

    // Agent B (Parser) call:
    // System prompt goes here to enforce JSON-only pillar updates.
    // User prompt goes here with the full transcript to update scores/confidence.
    const parserResponse = await fetch(
      'https://api.deepseek.com/chat/completions',
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${apiKey}`,
        },
        body: JSON.stringify({
          model: 'deepseek-chat',
          messages: [
            {
              role: 'system',
              content:
                `You are Agent B, a hidden parser. Return ONLY valid JSON with the 14 pillars: ${PILLARS.map(
                  (pillar) => pillar.key
                ).join(
                  ', '
                )}. ALL pillars are type pillars: return {type: string, confidence: 0.0-1.0} for every pillar. Use the style tag definitions to pick clear, concise tags. Update confidence based on evidence in the transcript so far. No extra text.`,
            },
            {
              role: 'user',
              content: `Style tag definitions:\n${JSON.stringify(
                STYLE_TAG_DEFINITIONS,
                null,
                2
              )}\n\nTranscript:\n${nextHistory
                .map((m) => `${m.role}: ${m.text}`)
                .join('\n')}\n\nReturn JSON in this shape:\n${JSON.stringify(
                INITIAL_PROFILE,
                null,
                2
              )}`,
            },
          ],
          temperature: 0.2,
        }),
      }
    )
    const parserJson = await parserResponse.json()
    const rawContent = parserJson?.choices?.[0]?.message?.content || '{}'
    setParserRaw(rawContent)
    setParserUpdatedAt(new Date())
    console.info('Agent B raw response:', rawContent)
    const parsedProfile = safeJsonParse(rawContent)
    if (parsedProfile) {
      setUserProfile(parsedProfile)
    } else {
      console.warn('Parser returned invalid JSON:', rawContent)
    }
  }

  const onSubmit = async (event) => {
    event.preventDefault()
    if (!input.trim()) return
    const message = input.trim()
    setInput('')
    await handleMessage(message)
  }

  return (
    <div className="page">
      <header className="hero">
        <div>
          <p className="eyebrow">Psychological Onboarding Demo</p>
          <h1>Dual-Agent Interview + Live Pillar Dashboard</h1>
          <p className="subtitle">
            Agent A keeps the conversation warm. Agent B silently parses your
            profile across 14 pillars.
          </p>
        </div>
        <button className="finalize" onClick={() => setFinalized(true)}>
          Finalize
        </button>
      </header>

      <main className="layout">
        <section className="chat">
          <div className="chat-window">
            {chatHistory.map((message, index) => (
              <div
                key={`${message.role}-${index}`}
                className={`bubble ${message.role}`}
              >
                <span className="role">
                  {message.role === 'agent' ? 'Agent A' : 'You'}
                </span>
                <p>{message.text}</p>
              </div>
            ))}
          </div>
          <form className="composer" onSubmit={onSubmit}>
            <input
              type="text"
              value={input}
              placeholder="Type your response..."
              onChange={(event) => setInput(event.target.value)}
            />
            <button type="submit">Send</button>
          </form>
        </section>

        <section className="dashboard">
          <h2>Live Pillar Dashboard</h2>
          <p className="parser-hint">
            Parser last update:{' '}
            {parserUpdatedAt
              ? parserUpdatedAt.toLocaleTimeString()
              : 'Waiting for Agent B...'}
          </p>
          <div className="pillar-list">
            {PILLARS.map((pillar) => {
              const data = userProfile[pillar.key]
              return (
                <div className="pillar" key={pillar.key}>
                  <div className="pillar-meta">
                    <span className="pillar-label">{pillar.label}</span>
                    <span className="pillar-group">{pillar.group}</span>
                  </div>
                  <div className="pillar-stats">
                    {TYPE_PILLARS.has(pillar.key) ? (
                      <>
                        <span className="score">Type: {data.type}</span>
                        <div className="confidence">
                          <div
                            className="confidence-bar"
                            style={{ width: `${data.confidence * 100}%` }}
                          />
                        </div>
                        <span className="confidence-label">
                          Confidence: {(data.confidence * 100).toFixed(0)}%
                        </span>
                      </>
                    ) : (
                      <>
                        <span className="score">Score: {data.score}</span>
                        <div className="confidence">
                          <div
                            className="confidence-bar"
                            style={{ width: `${data.confidence * 100}%` }}
                          />
                        </div>
                        <span className="confidence-label">
                          Confidence: {(data.confidence * 100).toFixed(0)}%
                        </span>
                      </>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
          {finalized && (
            <pre className="final-json">
              {JSON.stringify(userProfile, null, 2)}
            </pre>
          )}
          {parserRaw && (
            <details className="parser-debug">
              <summary>Agent B raw response</summary>
              <pre>{parserRaw}</pre>
            </details>
          )}
        </section>
      </main>
    </div>
  )
}

export default App
