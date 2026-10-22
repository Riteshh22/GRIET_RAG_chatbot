import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { HiChip, HiSearch, HiDatabase, HiCog, HiDocumentText, HiCheckCircle } from 'react-icons/hi'

const floatingCards = [
  { text: 'Embedding Generated', icon: HiChip, x: '10%', y: '20%', delay: 0, color: 'from-orange-400 to-orange-500' },
  { text: 'Dense Search Complete', icon: HiSearch, x: '75%', y: '15%', delay: 0.5, color: 'from-brown-300 to-brown-400' },
  { text: 'BM25 Retrieved', icon: HiDatabase, x: '85%', y: '55%', delay: 1, color: 'from-orange-500 to-orange-600' },
  { text: 'Re-ranking Finished', icon: HiCog, x: '5%', y: '60%', delay: 1.5, color: 'from-brown-400 to-brown-500' },
  { text: 'Answer Generated', icon: HiDocumentText, x: '70%', y: '80%', delay: 2, color: 'from-orange-400 to-orange-600' },
  { text: 'Citation Verified', icon: HiCheckCircle, x: '15%', y: '85%', delay: 2.5, color: 'from-green-400 to-green-500' },
]

export default function LandingPage() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-vintage-bg overflow-hidden relative">
      {/* Floating background cards */}
      {floatingCards.map((card, i) => {
        const Icon = card.icon
        return (
          <motion.div
            key={i}
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{
              opacity: [0, 0.6, 0.6, 0],
              scale: [0.5, 1, 1, 0.8],
              y: [0, -20, 0],
            }}
            transition={{
              duration: 4,
              delay: card.delay,
              repeat: Infinity,
              repeatDelay: 2,
            }}
            className="fixed z-0 pointer-events-none"
            style={{ left: card.x, top: card.y }}
          >
            <div className={`glass-dark rounded-card px-4 py-3 flex items-center gap-2 shadow-vintage`}>
              <div className={`w-7 h-7 rounded-lg bg-gradient-to-br ${card.color} flex items-center justify-center`}>
                <Icon className="text-white text-xs" />
              </div>
              <span className="text-xs font-semibold text-brown-500 whitespace-nowrap">{card.text}</span>
            </div>
          </motion.div>
        )
      })}

      {/* Pixel grid background */}
      <div className="absolute inset-0 opacity-[0.03]" style={{
        backgroundImage: 'radial-gradient(circle, #4A370B 1px, transparent 1px)',
        backgroundSize: '24px 24px',
      }} />

      <div className="relative z-10 flex flex-col items-center justify-center min-h-screen px-6">
        {/* Logo */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="mb-8"
        >
          <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-orange-500 to-orange-600 flex items-center justify-center shadow-vintage-lg mx-auto mb-6">
            <HiChip className="text-white text-3xl" />
          </div>
        </motion.div>

        {/* Title */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="text-center mb-8"
        >
          <h1 className="font-display text-5xl md:text-7xl font-bold text-brown-800 mb-4 tracking-tight">
            Enterprise Hybrid
            <br />
            <span className="gradient-text">RAG Platform</span>
          </h1>
          <p className="text-lg md:text-xl text-brown-400 max-w-2xl mx-auto font-medium leading-relaxed">
            Grounded AI answers powered by Hybrid Search,
            <br className="hidden md:block" />
            Re-ranking and Citation Verification.
          </p>
        </motion.div>

        {/* Pipeline display */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.4 }}
          className="window-border bg-vintage-window p-6 mb-10 max-w-xl w-full"
        >
          <div className="flex items-center gap-2 mb-4">
            <div className="window-dot dot-red" />
            <div className="window-dot dot-yellow" />
            <div className="window-dot dot-green" />
            <span className="text-xs font-semibold text-brown-300 ml-2">Pipeline Architecture</span>
          </div>
          <div className="space-y-2">
            {['Document Upload', 'Text Extraction & Chunking', 'BGE Embedding Generation', 'Qdrant Vector Storage', 'Hybrid Dense + BM25 Search', 'Cross-Encoder Re-ranking', 'Qwen3 Answer Generation', 'Citation-Verified Output'].map((step, i) => (
              <motion.div
                key={step}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.6 + i * 0.1 }}
                className="flex items-center gap-3"
              >
                <div className="w-6 h-6 rounded-full bg-gradient-to-br from-orange-500 to-orange-600 flex items-center justify-center text-white text-xs font-bold shadow-sm">
                  {i + 1}
                </div>
                <span className="text-sm text-brown-600 font-medium">{step}</span>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Buttons */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.8 }}
          className="flex items-center gap-4"
        >
          <motion.button
            whileHover={{ scale: 1.03, y: -2 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => navigate('/dashboard')}
            className="px-8 py-4 bg-gradient-to-r from-orange-500 to-orange-600 text-white font-display font-bold rounded-button shadow-vintage-hover text-lg"
          >
            Launch Workspace
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.03, y: -2 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => navigate('/architecture')}
            className="px-8 py-4 bg-vintage-window border-2 border-vintage-border text-brown-600 font-display font-bold rounded-button shadow-vintage text-lg hover:bg-cream-100 transition-colors"
          >
            View Architecture
          </motion.button>
        </motion.div>

        {/* Tech badges */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.2 }}
          className="mt-12 flex flex-wrap justify-center gap-3"
        >
          {['React', 'FastAPI', 'Qwen3', 'BGE', 'Qdrant', 'BM25', 'Re-ranking'].map((tech) => (
            <span
              key={tech}
              className="px-3 py-1.5 bg-vintage-window border border-vintage-border rounded-button text-xs font-semibold text-brown-400"
            >
              {tech}
            </span>
          ))}
        </motion.div>
      </div>
    </div>
  )
}
