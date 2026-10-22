import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import Layout from './components/Layout'
import ChatPage from './pages/ChatPage'

export default function App() {
  return (
    <Router>
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: '#FFFFFF',
            color: '#171717',
            border: '1px solid #E5E5E5',
            borderRadius: '12px',
            fontFamily: 'Inter, sans-serif',
            boxShadow: '0 4px 16px rgba(0, 0, 0, 0.08)',
          },
          duration: 4000,
        }}
      />
      <Routes>
        <Route path="/" element={<Navigate to="/chat" replace />} />
        <Route element={<Layout />}>
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/chat/:id" element={<ChatPage />} />
        </Route>
      </Routes>
    </Router>
  )
}