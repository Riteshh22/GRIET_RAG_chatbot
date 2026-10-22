import { useState, useEffect, useCallback } from 'react'
import { getSystemInfo, getSystemHealth, getEvaluationMetrics, listDocuments } from '../services/api'

export function useSystemInfo() {
  const [info, setInfo] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchInfo = useCallback(async () => {
    try {
      setLoading(true)
      const res = await getSystemInfo()
      setInfo(res.data)
      setError(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchInfo()
    const interval = setInterval(fetchInfo, 30000)
    return () => clearInterval(interval)
  }, [fetchInfo])

  return { info, loading, error, refresh: fetchInfo }
}

export function useSystemHealth() {
  const [health, setHealth] = useState(null)
  const [loading, setLoading] = useState(true)

  const fetchHealth = useCallback(async () => {
    try {
      const res = await getSystemHealth()
      setHealth(res.data)
    } catch {
      setHealth(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchHealth()
    const interval = setInterval(fetchHealth, 5000)
    return () => clearInterval(interval)
  }, [fetchHealth])

  return { health, loading, refresh: fetchHealth }
}

export function useDocuments() {
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(true)

  const fetchDocs = useCallback(async () => {
    try {
      setLoading(true)
      const res = await listDocuments()
      setDocuments(res.data.documents || [])
    } catch {
      setDocuments([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchDocs()
  }, [fetchDocs])

  return { documents, loading, refresh: fetchDocs }
}

export function useEvaluation() {
  const [metrics, setMetrics] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getEvaluationMetrics()
      .then((res) => setMetrics(res.data))
      .catch(() => setMetrics(null))
      .finally(() => setLoading(false))
  }, [])

  return { metrics, loading }
}
