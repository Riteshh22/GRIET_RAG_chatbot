import { motion } from 'framer-motion'
import {
  HiDocumentText,
  HiChip,
  HiDatabase,
  HiCog,
  HiClock,
  HiLightningBolt,
  HiChartBar,
  HiCheckCircle,
} from 'react-icons/hi'
import WindowCard, { StatCard } from '../components/WindowCard'
import { MetricCard } from '../components/WindowCard'
import LoadingSkeleton from '../components/LoadingSkeleton'
import { useSystemInfo, useSystemHealth, useDocuments, useEvaluation } from '../hooks/useData'

export default function Dashboard() {
  const { info, loading } = useSystemInfo()
  const { health } = useSystemHealth()
  const { documents } = useDocuments()
  const { metrics } = useEvaluation()

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-4 gap-4 mb-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="window-border bg-vintage-window p-5 animate-pulse">
              <div className="h-3 bg-cream-200 rounded w-20 mb-2" />
              <div className="h-7 bg-cream-200 rounded w-12" />
            </div>
          ))}
        </div>
        <LoadingSkeleton rows={4} />
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-2"
      >
        <h1 className="font-display text-3xl font-bold text-brown-800">Dashboard</h1>
        <p className="text-brown-400 mt-1">System overview and performance metrics</p>
      </motion.div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Documents Indexed"
          value={info?.total_documents || 0}
          icon={HiDocumentText}
          delay={0}
        />
        <StatCard
          label="Total Chunks"
          value={info?.total_chunks || 0}
          icon={HiChip}
          color="from-brown-400 to-brown-500"
          delay={0.1}
        />
        <StatCard
          label="Embedding Model"
          value="BGE"
          icon={HiDatabase}
          color="from-green-500 to-green-600"
          delay={0.2}
        />
        <StatCard
          label="Vector Database"
          value="Qdrant"
          icon={HiCog}
          color="from-blue-500 to-blue-600"
          delay={0.3}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard
          label="LLM"
          value="Qwen3"
          icon={HiLightningBolt}
          color="from-purple-500 to-purple-600"
          delay={0.4}
        />
        <StatCard
          label="Avg Retrieval"
          value={health?.avg_latency ? `${health.avg_latency.toFixed(1)}s` : '—'}
          icon={HiClock}
          color="from-cyan-500 to-cyan-600"
          delay={0.5}
        />
        <StatCard
          label="Re-ranker"
          value={info?.reranker_enabled ? 'Active' : 'Off'}
          icon={HiCheckCircle}
          color={info?.reranker_enabled ? 'from-green-500 to-green-600' : 'from-gray-400 to-gray-500'}
          delay={0.6}
        />
      </div>

      {/* System Status + Recent */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <WindowCard title="System Status">
          <div className="space-y-3">
            <StatusRow
              label="Ollama"
              status={info?.ollama_status === 'connected'}
              detail={info?.ollama_status === 'connected' ? info?.llm_model : 'Disconnected'}
            />
            <StatusRow
              label="Qdrant"
              status={info?.vector_db_status === 'connected'}
              detail={info?.vector_db_status === 'connected' ? `Collection: ${info?.qdrant_collection}` : 'Disconnected'}
            />
            <StatusRow
              label="Embedding Model"
              status={true}
              detail={info?.embedding_model}
            />
            <StatusRow
              label="CPU Usage"
              status={true}
              detail={health ? `${health.cpu_usage}%` : 'N/A'}
            />
            <StatusRow
              label="RAM Usage"
              status={true}
              detail={health ? `${health.ram_usage}% of ${health.ram_total}GB` : 'N/A'}
            />
            <StatusRow
              label="Vector DB Size"
              status={true}
              detail={`${health?.index_size || 0} vectors`}
            />
          </div>
        </WindowCard>

        <WindowCard title="Configuration">
          <div className="space-y-3">
            <ConfigRow label="Chunk Size" value={info?.chunk_size || 512} />
            <ConfigRow label="Chunk Overlap" value={info?.chunk_overlap || 64} />
            <ConfigRow label="Top K" value={info?.top_k || 5} />
            <ConfigRow label="Hybrid Alpha" value={info?.hybrid_alpha || 0.7} />
            <ConfigRow label="Embedding Dimension" value={info?.embedding_dimension || 384} />
            <ConfigRow label="Reranker Model" value={info?.reranker_model || 'BAAI/bge-reranker-base'} />
          </div>
        </WindowCard>
      </div>

      {/* Evaluation Quick View */}
      {metrics && (
        <WindowCard title="Evaluation Metrics Overview">
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            <MetricCard label="Faithfulness" value={`${(metrics.generation.faithfulness * 100).toFixed(0)}%`} progress={metrics.generation.faithfulness} delay={0} />
            <MetricCard label="Relevancy" value={`${(metrics.generation.answer_relevancy * 100).toFixed(0)}%`} progress={metrics.generation.answer_relevancy} color="#6BCB77" delay={0.1} />
            <MetricCard label="Context Prec." value={`${(metrics.retrieval.context_precision * 100).toFixed(0)}%`} progress={metrics.retrieval.context_precision} color="#4A90D9" delay={0.2} />
            <MetricCard label="Context Recall" value={`${(metrics.retrieval.context_recall * 100).toFixed(0)}%`} progress={metrics.retrieval.context_recall} color="#9B59B6" delay={0.3} />
            <MetricCard label="NDCG" value={`${(metrics.retrieval.ndcg * 100).toFixed(0)}%`} progress={metrics.retrieval.ndcg} color="#E74C3C" delay={0.4} />
            <MetricCard label="Hit Rate" value={`${(metrics.retrieval.hit_rate * 100).toFixed(0)}%`} progress={metrics.retrieval.hit_rate} color="#F39C12" delay={0.5} />
          </div>
        </WindowCard>
      )}

      {/* Recent Documents */}
      <WindowCard title="Recent Documents">
        {documents.length === 0 ? (
          <p className="text-brown-300 text-sm text-center py-6">No documents uploaded yet</p>
        ) : (
          <div className="space-y-2">
            {documents.slice(0, 5).map((doc) => (
              <div
                key={doc.id}
                className="flex items-center justify-between p-3 bg-cream-50 rounded-card border border-cream-200"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-orange-400 to-orange-500 flex items-center justify-center">
                    <HiDocumentText className="text-white text-sm" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-brown-600">{doc.filename}</p>
                    <p className="text-xs text-brown-300">{doc.chunks} chunks · {doc.pages} pages</p>
                  </div>
                </div>
                <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                  doc.status === 'indexed'
                    ? 'bg-green-50 text-green-600 border border-green-200'
                    : doc.status === 'processing'
                    ? 'bg-yellow-50 text-yellow-600 border border-yellow-200'
                    : 'bg-red-50 text-red-600 border border-red-200'
                }`}>
                  {doc.status}
                </span>
              </div>
            ))}
          </div>
        )}
      </WindowCard>
    </div>
  )
}

function StatusRow({ label, status, detail }) {
  return (
    <div className="flex items-center justify-between p-3 bg-cream-50 rounded-card border border-cream-200">
      <div className="flex items-center gap-2">
        <div className={`w-2.5 h-2.5 rounded-full ${status ? 'bg-green-500' : 'bg-red-500'}`} />
        <span className="text-sm font-semibold text-brown-600">{label}</span>
      </div>
      <span className="text-xs text-brown-400 font-mono">{detail}</span>
    </div>
  )
}

function ConfigRow({ label, value }) {
  return (
    <div className="flex items-center justify-between p-3 bg-cream-50 rounded-card border border-cream-200">
      <span className="text-sm font-semibold text-brown-600">{label}</span>
      <span className="text-sm font-mono text-brown-400">{value}</span>
    </div>
  )
}
