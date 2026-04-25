import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from 'recharts'
import StatCard from '../components/StatCard.jsx'
import SectionHeader from '../components/SectionHeader.jsx'
import { fetchOverview, fetchSessions } from '../api.js'

const ACCENT = '#3b82f6'

function topKey(breakdown) {
  if (!breakdown) return '—'
  const entries = Object.entries(breakdown)
  if (entries.length === 0) return '—'
  return entries.reduce((a, b) => (b[1] > a[1] ? b : a))[0]
}

function toSortedChartData(breakdown, key) {
  return Object.entries(breakdown || {})
    .map(([name, count]) => ({ [key]: name, count }))
    .sort((a, b) => b.count - a.count)
}

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

function HBarChart({ data, dataKey, height = 280 }) {
  return (
    <div className="chart-card" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ top: 8, right: 24, left: 16, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#eef2f7" horizontal={false} />
          <XAxis type="number" stroke="#64748b" fontSize={12} allowDecimals={false} />
          <YAxis
            type="category"
            dataKey={dataKey}
            stroke="#64748b"
            fontSize={12}
            width={120}
            tickFormatter={formatTitle}
          />
          <Tooltip
            cursor={{ fill: 'rgba(59,130,246,0.08)' }}
            contentStyle={{ borderRadius: 6, border: '1px solid #e2e8f0', fontSize: 13 }}
          />
          <Bar dataKey="count" fill={ACCENT} radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

function RankedList({ items, nameKey }) {
  if (!items || items.length === 0) {
    return <div className="empty">No data yet.</div>
  }
  return (
    <div className="ranked-list">
      {items.map((item, i) => (
        <div className="ranked-row" key={`${item[nameKey]}-${i}`}>
          <div className="ranked-row-rank">#{i + 1}</div>
          <div className="ranked-row-name">{item[nameKey]}</div>
          <div className="ranked-row-count">{item.count}</div>
        </div>
      ))}
    </div>
  )
}

function Overview() {
  const navigate = useNavigate()
  const [overview, setOverview] = useState(null)
  const [sessions, setSessions] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([fetchOverview(), fetchSessions()])
      .then(([o, s]) => {
        setOverview(o)
        setSessions(s)
      })
      .catch(err => console.error(err))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return <div className="page"><div className="empty">Loading...</div></div>
  }

  if (!overview || overview.total_sessions === 0) {
    return (
      <div className="page">
        <header className="page-header">
          <div className="wordmark">DestinationIQ</div>
          <div className="wordmark-subtitle">Visitor Intelligence Dashboard</div>
        </header>
        <div className="empty">No sessions yet.</div>
      </div>
    )
  }

  const interestData = toSortedChartData(overview.interest_breakdown, 'interest')
  const intentData = toSortedChartData(overview.intent_breakdown, 'intent')
  const sentimentData = toSortedChartData(overview.sentiment_breakdown, 'sentiment')

  return (
    <div className="page">
      <header className="page-header">
        <div className="wordmark">DestinationIQ</div>
        <div className="wordmark-subtitle">Visitor Intelligence Dashboard</div>
      </header>

      <section>
        <div className="stat-grid">
          <StatCard title="Total Sessions" value={overview.total_sessions} />
          <StatCard title="Most Common Intent" value={formatTitle(topKey(overview.intent_breakdown))} />
          <StatCard title="Most Common Sentiment" value={formatTitle(topKey(overview.sentiment_breakdown))} />
          <StatCard title="Most Common Party" value={formatTitle(topKey(overview.party_breakdown))} />
        </div>
      </section>

      <section className="section">
        <SectionHeader title="Visitor Interests" subtitle="Topics mentioned across all conversations" />
        <HBarChart data={interestData} dataKey="interest" />
      </section>

      <section className="section">
        <SectionHeader title="Intent Breakdown" subtitle="Why visitors are engaging" />
        <HBarChart data={intentData} dataKey="intent" />
      </section>

      <section className="section">
        <SectionHeader title="Sentiment Breakdown" subtitle="Tone of conversations" />
        <HBarChart data={sentimentData} dataKey="sentiment" />
      </section>

      <section className="section">
        <SectionHeader title="Top Referenced Listings" subtitle="Venues, hotels, and events visitors asked about" />
        <RankedList items={overview.top_listings} nameKey="name" />
      </section>

      <section className="section">
        <SectionHeader title="Top Content Gaps" subtitle="Information visitors wanted but the assistant lacked" />
        <RankedList items={overview.top_content_gaps} nameKey="gap" />
      </section>

      <section className="section">
        <SectionHeader title="Recent Sessions" />
        <table className="session-table">
          <thead>
            <tr>
              <th>Session ID</th>
              <th>Intent</th>
              <th>Sentiment</th>
              <th>Party</th>
              <th>Processed At</th>
            </tr>
          </thead>
          <tbody>
            {(sessions || []).map(s => (
              <tr key={s.session_id} onClick={() => navigate(`/session/${s.session_id}`)}>
                <td className="session-id">{String(s.session_id).slice(0, 8)}</td>
                <td>{formatTitle(s.visitor_intent)}</td>
                <td>{formatTitle(s.sentiment)}</td>
                <td>{formatTitle(s.party_composition)}</td>
                <td>{formatDateTime(s.processed_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  )
}

export default Overview
