import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import StatCard from '../components/StatCard.jsx'
import SectionHeader from '../components/SectionHeader.jsx'
import { fetchSession } from '../api.js'

function formatTitle(s) {
  if (!s) return ''
  return String(s).replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

function formatDateTime(iso) {
  if (!iso) return ''
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}

function SessionDetail() {
  const { session_id } = useParams()
  const navigate = useNavigate()
  const [session, setSession] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchSession(session_id)
      .then(data => {
        if (data?.detail) {
          setError(data.detail)
        } else {
          setSession(data)
        }
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [session_id])

  if (loading) {
    return <div className="page"><div className="empty">Loading...</div></div>
  }

  if (error || !session) {
    return (
      <div className="page">
        <button className="back-link" onClick={() => navigate('/')}>← All Sessions</button>
        <div className="empty">{error || 'Session not found.'}</div>
      </div>
    )
  }

  const interests = session.interests || []
  const listings = session.listings_referenced || []
  const unanswered = session.unanswered_questions || []
  const gaps = session.content_gaps || []

  return (
    <div className="page">
      <button className="back-link" onClick={() => navigate('/')}>← All Sessions</button>

      <header className="page-header">
        <div className="wordmark session-detail-id">{session.session_id}</div>
        <div className="session-meta">
          <span>Processed {formatDateTime(session.processed_at)}</span>
          {session.client_id && <span>Client: {session.client_id}</span>}
        </div>
      </header>

      <section className="section">
        <SectionHeader title="Summary" />
        <div className="summary-box">{session.session_summary}</div>
      </section>

      <section className="section">
        <SectionHeader title="Key Signals" />
        <div className="stat-grid">
          <StatCard title="Visitor Intent" value={formatTitle(session.visitor_intent) || '—'} />
          <StatCard title="Party Composition" value={formatTitle(session.party_composition) || '—'} />
          <StatCard title="Sentiment" value={formatTitle(session.sentiment) || '—'} />
          <StatCard title="Travel Window" value={session.travel_window || 'Not mentioned'} />
        </div>
      </section>

      <section className="section">
        <SectionHeader title="Interests" />
        {interests.length > 0 ? (
          <div className="pill-list">
            {interests.map(i => <span key={i} className="pill">{formatTitle(i)}</span>)}
          </div>
        ) : <div className="empty">None mentioned</div>}
      </section>

      <section className="section">
        <SectionHeader title="Listings Referenced" />
        {listings.length > 0 ? (
          <div className="pill-list">
            {listings.map(l => <span key={l} className="pill">{l}</span>)}
          </div>
        ) : <div className="empty">None mentioned</div>}
      </section>

      <section className="section">
        <SectionHeader title="Unanswered Questions" />
        {unanswered.length > 0 ? (
          <div className="warning-box">
            <ul>{unanswered.map((q, i) => <li key={i}>{q}</li>)}</ul>
          </div>
        ) : <div className="empty">None</div>}
      </section>

      <section className="section">
        <SectionHeader title="Content Gaps" />
        {gaps.length > 0 ? (
          <div className="danger-box">
            <ul>{gaps.map((g, i) => <li key={i}>{g}</li>)}</ul>
          </div>
        ) : <div className="empty">None</div>}
      </section>
    </div>
  )
}

export default SessionDetail
