import { motion } from 'framer-motion'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts'
import { HiChartBar, HiLightBulb, HiTrendingUp } from 'react-icons/hi'
import WindowCard, { MetricCard } from '../components/WindowCard'
import { useEvaluation } from '../hooks/useData'

export default function EvaluationPage() {
  const { metrics, loading } = useEvaluation()

  if (loading || !metrics) {
    return (
      <div className="max-w-6xl mx-auto">
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-cream-200 rounded w-48" />
          <div className="h-64 bg-cream-100 rounded-window" />
        </div>
      </div>
    )
  }

  const retrievalData = [
    { metric: 'Precision@K', value: (metrics.retrieval.precision_at_k * 100).toFixed(0) },
    { metric: 'Recall@K', value: (metrics.retrieval.recall_at_k * 100).toFixed(0) },
    { metric: 'MRR', value: (metrics.retrieval.mrr * 100).toFixed(0) },
    { metric: 'MAP', value: (metrics.retrieval.map_score * 100).toFixed(0) },
    { metric: 'NDCG', value: (metrics.retrieval.ndcg * 100).toFixed(0) },
    { metric: 'Hit Rate', value: (metrics.retrieval.hit_rate * 100).toFixed(0) },
  ]

  const generationData = [
    { metric: 'Faithfulness', value: (metrics.generation.faithfulness * 100).toFixed(0) },
    { metric: 'Relevancy', value: (metrics.generation.answer_relevancy * 100).toFixed(0) },
    { metric: 'Correctness', value: (metrics.generation.answer_correctness * 100).toFixed(0) },
    { metric: 'Semantic Sim.', value: (metrics.generation.semantic_similarity * 100).toFixed(0) },
  ]

  const radarData = [
    { subject: 'Precision', A: metrics.retrieval.precision_at_k * 100, fullMark: 100 },
    { subject: 'Recall', A: metrics.retrieval.recall_at_k * 100, fullMark: 100 },
    { subject: 'Faithfulness', A: metrics.generation.faithfulness * 100, fullMark: 100 },
    { subject: 'Relevancy', A: metrics.generation.answer_relevancy * 100, fullMark: 100 },
    { subject: 'NDCG', A: metrics.retrieval.ndcg * 100, fullMark: 100 },
    { subject: 'Hit Rate', A: metrics.retrieval.hit_rate * 100, fullMark: 100 },
  ]

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="font-display text-3xl font-bold text-brown-800">Evaluation Dashboard</h1>
        <p className="text-brown-400 mt-1">RAG pipeline performance metrics using RAGAS</p>
      </motion.div>

      {/* Retrieval Metrics */}
      <WindowCard title="Retrieval Metrics">
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
          <MetricCard label="Precision@K" value={`${(metrics.retrieval.precision_at_k * 100).toFixed(0)}%`} progress={metrics.retrieval.precision_at_k} delay={0} />
          <MetricCard label="Recall@K" value={`${(metrics.retrieval.recall_at_k * 100).toFixed(0)}%`} progress={metrics.retrieval.recall_at_k} color="#6BCB77" delay={0.1} />
          <MetricCard label="MRR" value={`${(metrics.retrieval.mrr * 100).toFixed(0)}%`} progress={metrics.retrieval.mrr} color="#4A90D9" delay={0.2} />
          <MetricCard label="MAP" value={`${(metrics.retrieval.map_score * 100).toFixed(0)}%`} progress={metrics.retrieval.map_score} color="#9B59B6" delay={0.3} />
          <MetricCard label="NDCG" value={`${(metrics.retrieval.ndcg * 100).toFixed(0)}%`} progress={metrics.retrieval.ndcg} color="#E74C3C" delay={0.4} />
          <MetricCard label="Hit Rate" value={`${(metrics.retrieval.hit_rate * 100).toFixed(0)}%`} progress={metrics.retrieval.hit_rate} color="#F39C12" delay={0.5} />
        </div>

        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={retrievalData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#EDD9B5" />
              <XAxis dataKey="metric" tick={{ fontSize: 12, fill: '#8B6914' }} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 12, fill: '#8B6914' }} />
              <Tooltip
                contentStyle={{
                  background: '#FDF8F0',
                  border: '2px solid #D4B896',
                  borderRadius: '8px',
                }}
              />
              <Bar dataKey="value" fill="#E8820C" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </WindowCard>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Generation Metrics */}
        <WindowCard title="Generation Metrics (RAGAS)">
          <div className="space-y-3 mb-6">
            <MetricCard label="Faithfulness" value={`${(metrics.generation.faithfulness * 100).toFixed(0)}%`} progress={metrics.generation.faithfulness} delay={0} />
            <MetricCard label="Answer Relevancy" value={`${(metrics.generation.answer_relevancy * 100).toFixed(0)}%`} progress={metrics.generation.answer_relevancy} color="#6BCB77" delay={0.1} />
            <MetricCard label="Answer Correctness" value={`${(metrics.generation.answer_correctness * 100).toFixed(0)}%`} progress={metrics.generation.answer_correctness} color="#4A90D9" delay={0.2} />
            <MetricCard label="Semantic Similarity" value={`${(metrics.generation.semantic_similarity * 100).toFixed(0)}%`} progress={metrics.generation.semantic_similarity} color="#9B59B6" delay={0.3} />
          </div>

          <div className="space-y-2">
            {Object.entries(metrics.generation).map(([key, val]) => (
              <div key={key} className="flex items-center justify-between p-2 bg-cream-50 rounded border border-cream-200">
                <span className="text-xs font-semibold text-brown-500 capitalize">{key.replace(/_/g, ' ')}</span>
                <span className="text-xs font-mono text-brown-400">{val.toFixed(3)}</span>
              </div>
            ))}
          </div>
        </WindowCard>

        {/* Radar Chart */}
        <WindowCard title="Overall Performance">
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={radarData}>
                <PolarGrid stroke="#EDD9B5" />
                <PolarAngleAxis dataKey="subject" tick={{ fontSize: 11, fill: '#8B6914' }} />
                <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fontSize: 10, fill: '#B8956C' }} />
                <Radar name="Score" dataKey="A" stroke="#E8820C" fill="#E8820C" fillOpacity={0.3} strokeWidth={2} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </WindowCard>
      </div>

      {/* Context Metrics */}
      <WindowCard title="Context Quality">
        <div className="grid grid-cols-3 gap-4">
          <MetricCard label="Context Precision" value={`${(metrics.retrieval.context_precision * 100).toFixed(0)}%`} progress={metrics.retrieval.context_precision} color="#4A90D9" delay={0} />
          <MetricCard label="Context Recall" value={`${(metrics.retrieval.context_recall * 100).toFixed(0)}%`} progress={metrics.retrieval.context_recall} color="#6BCB77" delay={0.1} />
          <MetricCard label="Context Relevancy" value={`${(metrics.retrieval.context_relevancy * 100).toFixed(0)}%`} progress={metrics.retrieval.context_relevancy} color="#9B59B6" delay={0.2} />
        </div>
      </WindowCard>
    </div>
  )
}
