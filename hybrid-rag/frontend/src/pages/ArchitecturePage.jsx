import { useState } from 'react'
import { motion } from 'framer-motion'
import {
  HiChip,
  HiDatabase,
  HiSearch,
  HiCog,
  HiDocumentText,
  HiChatAlt2,
  HiLightningBolt,
  HiServer,
} from 'react-icons/hi'

const archNodes = [
  { id: 'react', label: 'React Frontend', desc: 'Vite + Tailwind + Framer Motion', icon: HiChip, color: 'from-blue-400 to-blue-600', x: 50, y: 10 },
  { id: 'fastapi', label: 'FastAPI Backend', desc: 'Python REST + Streaming', icon: HiServer, color: 'from-green-400 to-green-600', x: 50, y: 25 },
  { id: 'langchain', label: 'LangChain', desc: 'Document Loaders + Text Splitter', icon: HiCog, color: 'from-purple-400 to-purple-600', x: 20, y: 40 },
  { id: 'embedding', label: 'BGE Embeddings', desc: 'BAAI/bge-small-en-v1.5', icon: HiChip, color: 'from-orange-400 to-orange-600', x: 80, y: 40 },
  { id: 'qdrant', label: 'Qdrant', desc: 'Vector Database', icon: HiDatabase, color: 'from-cyan-400 to-cyan-600', x: 80, y: 58 },
  { id: 'bm25', label: 'BM25', desc: 'Sparse Retrieval', icon: HiSearch, color: 'from-yellow-400 to-yellow-600', x: 20, y: 58 },
  { id: 'hybrid', label: 'Hybrid Retriever', desc: 'Dense + Sparse Fusion', icon: HiSearch, color: 'from-pink-400 to-pink-600', x: 50, y: 72 },
  { id: 'reranker', label: 'Cross-Encoder', desc: 'BAAI/bge-reranker-base', icon: HiCog, color: 'from-red-400 to-red-600', x: 50, y: 85 },
  { id: 'qwen', label: 'Qwen3:8B', desc: 'Ollama LLM', icon: HiLightningBolt, color: 'from-violet-400 to-violet-600', x: 80, y: 85 },
]

const connections = [
  ['react', 'fastapi'],
  ['fastapi', 'langchain'],
  ['fastapi', 'embedding'],
  ['langchain', 'qdrant'],
  ['langchain', 'bm25'],
  ['qdrant', 'hybrid'],
  ['bm25', 'hybrid'],
  ['hybrid', 'reranker'],
  ['reranker', 'qwen'],
]

export default function ArchitecturePage() {
  const [hoveredNode, setHoveredNode] = useState(null)

  const techStack = {
    frontend: ['React', 'Vite', 'Tailwind CSS', 'Framer Motion', 'Recharts'],
    backend: ['FastAPI', 'Python', 'Pydantic', 'Uvicorn'],
    llm: ['Ollama', 'Qwen3:8B'],
    embeddings: ['BAAI/bge-small-en-v1.5', 'Sentence Transformers'],
    database: ['Qdrant'],
    retrieval: ['Dense Search', 'BM25', 'RRF Fusion'],
    reranking: ['BAAI/bge-reranker-base', 'Cross-Encoder'],
    evaluation: ['RAGAS', 'Precision@K', 'NDCG', 'Faithfulness'],
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="font-display text-3xl font-bold text-brown-800">Architecture</h1>
        <p className="text-brown-400 mt-1">System design and technology stack</p>
      </motion.div>

      {/* Architecture Diagram */}
      <motion.div
        initial={{ opacity: 0, scale: 0.98 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.1 }}
        className="window-border bg-vintage-window p-6"
      >
        <div className="flex items-center gap-2 mb-4">
          <div className="window-dot dot-red" />
          <div className="window-dot dot-yellow" />
          <div className="window-dot dot-green" />
          <span className="text-xs font-semibold text-brown-300 ml-2">System Architecture</span>
        </div>

        <div className="relative bg-cream-50 rounded-card border border-cream-200" style={{ height: '500px' }}>
          {/* Connection lines */}
          <svg className="absolute inset-0 w-full h-full pointer-events-none">
            {connections.map(([fromId, toId], i) => {
              const from = archNodes.find((n) => n.id === fromId)
              const to = archNodes.find((n) => n.id === toId)
              if (!from || !to) return null
              const x1 = `${from.x}%`
              const y1 = `${from.y + 4}%`
              const x2 = `${to.x}%`
              const y2 = `${to.y - 2}%`
              return (
                <line
                  key={i}
                  x1={x1} y1={y1} x2={x2} y2={y2}
                  stroke={hoveredNode === fromId || hoveredNode === toId ? '#E8820C' : '#D4B896'}
                  strokeWidth="2"
                  strokeDasharray="6,4"
                  className="transition-all duration-300"
                />
              )
            })}
          </svg>

          {/* Nodes */}
          {archNodes.map((node) => {
            const Icon = node.icon
            const isHovered = hoveredNode === node.id
            return (
              <motion.div
                key={node.id}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.2 + Math.random() * 0.3 }}
                whileHover={{ scale: 1.08, zIndex: 10 }}
                onMouseEnter={() => setHoveredNode(node.id)}
                onMouseLeave={() => setHoveredNode(null)}
                className="absolute -translate-x-1/2 -translate-y-1/2 cursor-default"
                style={{ left: `${node.x}%`, top: `${node.y}%` }}
              >
                <div className={`bg-vintage-window border-2 ${isHovered ? 'border-orange-400 shadow-vintage-hover' : 'border-vintage-border shadow-vintage'} rounded-card px-4 py-3 text-center transition-all duration-300 min-w-[120px]`}>
                  <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${node.color} flex items-center justify-center mx-auto mb-1.5`}>
                    <Icon className="text-white text-sm" />
                  </div>
                  <p className="text-xs font-bold text-brown-700">{node.label}</p>
                  <p className="text-[10px] text-brown-300 mt-0.5">{node.desc}</p>
                </div>
              </motion.div>
            )
          })}
        </div>
      </motion.div>

      {/* Tech Stack */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {Object.entries(techStack).map(([category, items], i) => (
          <motion.div
            key={category}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 * i }}
            className="window-border bg-vintage-window p-4"
          >
            <h3 className="font-display font-bold text-sm text-brown-700 capitalize mb-3">{category}</h3>
            <div className="space-y-1.5">
              {items.map((item) => (
                <div key={item} className="flex items-center gap-2 px-2 py-1.5 bg-cream-50 rounded-lg border border-cream-200">
                  <div className="w-1.5 h-1.5 rounded-full bg-orange-500" />
                  <span className="text-xs font-medium text-brown-500">{item}</span>
                </div>
              ))}
            </div>
          </motion.div>
        ))}
      </div>

      {/* Features */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="window-border bg-vintage-window p-6"
      >
        <h2 className="font-display text-lg font-bold text-brown-700 mb-4">Implemented Features</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          {[
            'Hybrid Search',
            'Citation Verification',
            'Streaming Response',
            'Multi-document Upload',
            'Conversation Memory',
            'Search History',
            'Re-ranking',
            'Source Highlighting',
            'Pipeline Visualization',
            'Retrieval Evaluation',
            'Generation Evaluation',
            'System Health',
            'Responsive Design',
            'Keyboard Shortcuts',
          ].map((feature) => (
            <div key={feature} className="flex items-center gap-2 px-3 py-2 bg-cream-50 rounded-card border border-cream-200">
              <div className="w-4 h-4 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0">
                <span className="text-green-600 text-xs">✓</span>
              </div>
              <span className="text-xs font-medium text-brown-600">{feature}</span>
            </div>
          ))}
        </div>
      </motion.div>
    </div>
  )
}
