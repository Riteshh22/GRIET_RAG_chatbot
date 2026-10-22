import { useState, useCallback, useRef } from 'react'
import { chatStream } from '../services/api'

export function useChat() {
  const [messages, setMessages] = useState([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [currentSources, setCurrentSources] = useState([])
  const [conversationId, setConversationId] = useState(null)
  const abortRef = useRef(false)

  const sendMessage = useCallback(async (query) => {
    if (!query.trim() || isStreaming) return

    const userMessage = {
      role: 'user',
      content: query,
      timestamp: new Date().toISOString(),
    }

    setMessages((prev) => [...prev, userMessage])
    setIsStreaming(true)
    setCurrentSources([])
    abortRef.current = false

    let answerContent = ''

    await chatStream(
      { query, conversation_id: conversationId },
      (token) => {
        if (abortRef.current) return
        answerContent += token
        setMessages((prev) => {
          const msgs = [...prev]
          const lastMsg = msgs[msgs.length - 1]
          if (lastMsg?.role === 'assistant' && lastMsg.streaming) {
            lastMsg.content = answerContent
          } else {
            msgs.push({
              role: 'assistant',
              content: answerContent,
              streaming: true,
              timestamp: new Date().toISOString(),
            })
          }
          return [...msgs]
        })
      },
      (sources) => {
        setCurrentSources(sources)
      },
      () => {
        setMessages((prev) => {
          const msgs = [...prev]
          const lastMsg = msgs[msgs.length - 1]
          if (lastMsg?.role === 'assistant') {
            lastMsg.streaming = false
          }
          return [...msgs]
        })
        setIsStreaming(false)
      },
      (error) => {
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: `Error: ${error}`,
            streaming: false,
            timestamp: new Date().toISOString(),
          },
        ])
        setIsStreaming(false)
      }
    )
  }, [conversationId, isStreaming])

  const clearConversation = useCallback(() => {
    setMessages([])
    setCurrentSources([])
    setConversationId(null)
  }, [])

  const stopGeneration = useCallback(() => {
    abortRef.current = true
    setIsStreaming(false)
  }, [])

  return {
    messages,
    isStreaming,
    currentSources,
    sendMessage,
    clearConversation,
    stopGeneration,
  }
}
