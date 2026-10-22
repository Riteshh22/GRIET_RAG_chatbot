import axios from 'axios'

const API_BASE = '/api'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 120000,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.detail || error.message || 'An error occurred'
    return Promise.reject(new Error(message))
  }
)

export const uploadDocument = async (file, onProgress) => {
  const formData = new FormData()
  formData.append('file', file)
  return api.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (e) => {
      if (onProgress && e.total) {
        onProgress(Math.round((e.loaded * 100) / e.total))
      }
    },
  })
}

export const sendChatMessage = async (data) => {
  return api.post('/chat', data)
}

export const chatStream = async (data, onToken, onSources, onDone, onError, onWebSources, onAnswerSource, onConfidence) => {
  try {
    const response = await fetch(`${API_BASE}/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })

    const reader = response.body.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const payload = JSON.parse(line.slice(6))
            if (payload.type === 'token') onToken(payload.content)
            if (payload.type === 'sources') onSources(payload.sources)
            if (payload.type === 'web_sources') onWebSources(payload.web_sources)
            if (payload.type === 'answer_source') onAnswerSource(payload.answer_source)
            if (payload.type === 'confidence') onConfidence(payload.confidence)
            if (payload.type === 'done') onDone()
            if (payload.type === 'error') onError(payload.message)
          } catch { /* skip parse errors */ }
        }
      }
    }
  } catch (err) {
    onError(err.message)
  }
}

export const searchDocuments = async (query, topK = 5, sourceType = null) => {
  return api.post('/search', { query, top_k: topK, source_type: sourceType })
}

export const listDocuments = async () => {
  return api.get('/list-documents')
}

export const deleteDocument = async (docId) => {
  return api.delete(`/delete/${docId}`)
}

export const reindexDocument = async (docId) => {
  return api.post(`/reindex/${docId}`)
}

export const getSystemInfo = async () => {
  return api.get('/system-info')
}

export const getSystemHealth = async () => {
  return api.get('/system-health')
}

export const getEvaluationMetrics = async () => {
  return api.get('/evaluation/metrics')
}

export const getSearchHistory = async () => {
  return api.get('/search-history')
}

export const crawlGriet = async (maxPages = null, incremental = false) => {
  return api.post('/crawl', { max_pages: maxPages, incremental })
}

export const getCrawlStatus = async () => {
  return api.get('/crawl/status')
}

export default api