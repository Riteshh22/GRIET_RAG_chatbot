import { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useParams, useNavigate } from 'react-router-dom';
import { HiPaperAirplane, HiStop, HiX, HiArrowLeft, HiInformationCircle } from 'react-icons/hi';
import ChatMessage from '../components/ChatMessage';
import { chatStream } from '../services/api';
import { useChatHistory } from '../hooks/useChatHistory';
import Sidebar from '../components/Sidebar';

export default function ChatPage() {
  const { id: conversationId } = useParams();
  const navigate = useNavigate();
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentSources, setCurrentSources] = useState([]);
  const [currentWebSources, setCurrentWebSources] = useState([]);
  const [answerSource, setAnswerSource] = useState('griet');
  const [confidence, setConfidence] = useState(0);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [showSourcePanel, setShowSourcePanel] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const abortControllerRef = useRef(null);

  const { conversations, createConversation, addMessageToConversation, updateConversation } = useChatHistory();

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  useEffect(() => {
    if (conversationId) {
      const conv = conversations.find(c => c.id === conversationId);
      if (conv) {
        setMessages(conv.messages || []);
      }
    } else {
      setMessages([]);
    }
  }, [conversationId, conversations]);

  const handleSubmit = useCallback(async (e) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;

    const userMessage = {
      role: 'user',
      content: input.trim(),
      timestamp: new Date().toISOString(),
    };

    const currentConvId = conversationId || createConversation();
    if (!conversationId) {
      navigate(`/chat/${currentConvId}`, { replace: true });
    }

    setMessages(prev => [...prev, userMessage]);
    addMessageToConversation(currentConvId, userMessage);
    setIsStreaming(true);
    setCurrentSources([]);
    setCurrentWebSources([]);
    setAnswerSource('griet');
    setConfidence(0);

    const query = input.trim();
    setInput('');

    abortControllerRef.current = new AbortController();

    try {
      await chatStream(
        { query, conversation_id: currentConvId },
        (token) => {
          if (abortControllerRef.current?.signal.aborted) return;
          setMessages(prev => {
            const msgs = [...prev];
            const lastMsg = msgs[msgs.length - 1];
            if (lastMsg?.role === 'assistant' && lastMsg.streaming) {
              lastMsg.content += token;
            } else {
              msgs.push({
                role: 'assistant',
                content: token,
                streaming: true,
                timestamp: new Date().toISOString(),
              });
            }
            return msgs;
          });
        },
        (sources) => {
          setCurrentSources(sources);
        },
        () => {
          setMessages(prev => {
            const msgs = [...prev];
            const lastMsg = msgs[msgs.length - 1];
            if (lastMsg?.role === 'assistant') {
              lastMsg.streaming = false;
              addMessageToConversation(currentConvId, lastMsg);
            }
            return msgs;
          });
          setIsStreaming(false);
        },
        (error) => {
          setMessages(prev => [
            ...prev,
            {
              role: 'assistant',
              content: `Error: ${error}`,
              streaming: false,
              timestamp: new Date().toISOString(),
            },
          ]);
          setIsStreaming(false);
        },
        (webSources) => {
          setCurrentWebSources(webSources);
        },
        (source) => {
          setAnswerSource(source);
        },
        (conf) => {
          setConfidence(conf);
        }
      );
    } catch (err) {
      if (!abortControllerRef.current?.signal.aborted) {
        setMessages(prev => [
          ...prev,
          {
            role: 'assistant',
            content: `Error: ${err.message}`,
            streaming: false,
            timestamp: new Date().toISOString(),
          },
        ]);
        setIsStreaming(false);
      }
    }
  }, [input, isStreaming, conversationId, navigate, createConversation, addMessageToConversation]);

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  }, [handleSubmit]);

  const stopGeneration = useCallback(() => {
    abortControllerRef.current?.abort();
    setIsStreaming(false);
  }, []);

  const handleNewChat = useCallback(() => {
    navigate('/chat');
  }, [navigate]);

  const exampleQuestions = [
    "Who is the HOD of CSE?",
    "What departments are available at GRIET?",
    "What are the admission requirements?",
    "Tell me about the CSE department",
    "What is the latest placement information?",
    "Show me information about GRIET clubs",
    "What are the hostel facilities?",
    "When are the semester exams?",
  ];

  return (
    <div className="flex h-screen bg-neutral-50">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      <main className="flex-1 flex flex-col lg:ml-0 min-w-0">
        <header className="sticky top-0 z-30 h-16 bg-white/80 backdrop-blur-md border-b border-neutral-200 flex items-center justify-between px-4 lg:px-6">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden p-2 rounded-xl hover:bg-neutral-100 text-neutral-600"
              aria-label="Open sidebar"
            >
              <HiArrowLeft className="text-xl" />
            </button>
            <button
              onClick={handleNewChat}
              className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-xl text-sm font-medium text-primary hover:bg-primary-light transition-colors"
            >
              <HiPaperAirplane className="text-lg" />
              New Chat
            </button>
          </div>

          <div className="flex items-center gap-2">
            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-xl bg-neutral-50">
              <HiInformationCircle className="text-neutral-400 text-lg" />
              <span className="text-sm text-neutral-600">GRIET RAG Chatbot</span>
            </div>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto p-4 lg:p-8">
          <div className="max-w-3xl mx-auto w-full space-y-6">
            {messages.length === 0 ? (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4 }}
                className="text-center py-16 lg:py-24"
              >
                <div className="w-16 h-16 rounded-2xl bg-primary-light flex items-center justify-center mx-auto mb-6">
                  <HiPaperAirplane className="text-primary text-2xl" />
                </div>
                <h1 className="text-2xl lg:text-3xl font-semibold text-neutral-900 mb-3">Ask me anything about GRIET</h1>
                <p className="text-neutral-500 mb-8 max-w-md mx-auto">
                  I can answer questions about departments, faculty, admissions, examinations, placements, events, clubs, infrastructure, and more using verified GRIET website information.
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-xl mx-auto text-left">
                  {exampleQuestions.map((question) => (
                    <button
                      key={question}
                      onClick={() => { setInput(question); handleSubmit({ preventDefault: () => {} }); }}
                      className="p-4 rounded-xl border border-neutral-200 bg-white hover:border-primary/50 hover:bg-primary/5 hover:shadow-subtle transition-all text-sm text-neutral-700 text-left"
                    >
                      {question}
                    </button>
                  ))}
                </div>
              </motion.div>
            ) : (
              <AnimatePresence mode="popLayout">
                {messages.map((msg, i) => (
                  <ChatMessage key={i} message={msg} />
                ))}
                <div ref={messagesEndRef} />
              </AnimatePresence>
            )}
          </div>
        </div>

        <div className="border-t border-neutral-200 bg-white/80 backdrop-blur-md p-4 lg:p-6">
          <form onSubmit={handleSubmit} className="max-w-3xl mx-auto">
            <div className="flex items-end gap-3">
              <div className="flex-1 relative">
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Ask about GRIET..."
                  rows={1}
                  className="input resize-none pr-12 max-h-48"
                  style={{ minHeight: '52px' }}
                  disabled={isStreaming}
                  aria-label="Chat input"
                />
              </div>
              {isStreaming ? (
                <button
                  type="button"
                  onClick={stopGeneration}
                  className="btn-danger p-3 rounded-xl flex-shrink-0"
                  aria-label="Stop generation"
                >
                  <HiStop className="text-lg" />
                </button>
              ) : (
                <button
                  type="submit"
                  disabled={!input.trim()}
                  className="btn-primary p-3 rounded-xl flex-shrink-0"
                  aria-label="Send message"
                >
                  <HiPaperAirplane className="text-lg" />
                </button>
              )}
            </div>
            <p className="text-xs text-neutral-400 text-center mt-2">
              Press Enter to send, Shift+Enter for new line
            </p>
          </form>
        </div>
      </main>

      <AnimatePresence>
        {(currentSources.length > 0 || currentWebSources.length > 0) && showSourcePanel && (
          <motion.div
            initial={{ opacity: 0, x: 300 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 300 }}
            transition={{ duration: 0.25 }}
            className="fixed right-0 top-16 bottom-0 w-96 bg-white border-l border-neutral-200 z-40 lg:relative lg:static lg:border-0 lg:w-auto lg:h-auto lg:shadow-none lg:bg-transparent"
          >
            <div className="flex flex-col h-full">
              <div className="flex items-center justify-between p-4 border-b border-neutral-200">
                <h2 className="font-semibold text-neutral-900">Sources</h2>
                <button
                  onClick={() => setShowSourcePanel(false)}
                  className="p-2 rounded-xl hover:bg-neutral-100 text-neutral-500 lg:hidden"
                >
                  <HiX className="text-xl" />
                </button>
              </div>
              <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {currentSources.map((source, i) => (
                  <div key={source.id || i} className="source-card">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="source-badge source-badge-griet">GRIET</span>
                      <span className="text-xs font-mono text-neutral-400">{(source.similarity_score * 100).toFixed(0)}%</span>
                    </div>
                    <p className="font-medium text-neutral-900 text-sm mb-1">{source.document_name}</p>
                    <p className="text-xs text-neutral-500 mb-2">Page {source.page_number}</p>
                    <p className="text-sm text-neutral-600 line-clamp-3">{source.content}</p>
                    {source.source_url && (
                      <a href={source.source_url} target="_blank" rel="noopener noreferrer" className="text-xs text-primary hover:underline mt-2 inline-block">
                        View on GRIET website →
                      </a>
                    )}
                  </div>
                ))}
                {currentWebSources.map((source, i) => (
                  <div key={source.url || i} className="source-card border-amber-100 bg-amber-50">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="source-badge source-badge-web">Web</span>
                    </div>
                    <p className="font-medium text-neutral-900 text-sm mb-1">{source.title}</p>
                    <p className="text-sm text-neutral-600 line-clamp-3">{source.snippet}</p>
                    {source.url && (
                      <a href={source.url} target="_blank" rel="noopener noreferrer" className="text-xs text-amber-700 hover:underline mt-2 inline-block">
                        View source →
                      </a>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}