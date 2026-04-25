import { Routes, Route } from 'react-router-dom'
import Overview from './pages/Overview.jsx'
import SessionDetail from './pages/SessionDetail.jsx'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Overview />} />
      <Route path="/session/:session_id" element={<SessionDetail />} />
    </Routes>
  )
}

export default App
