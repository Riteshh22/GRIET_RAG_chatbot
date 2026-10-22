import { motion } from 'framer-motion'
import {
  HiSearch,
  HiCog,
  HiDatabase,
  HiChip,
  HiDocumentText,
  HiChatAlt2,
  HiCheckCircle,
} from 'react-icons/hi'

const stages = [
  { name: 'Query', icon: HiSearch },
  { name: 'Embedding', icon: HiChip },
  { name: 'Dense Search', icon: HiDatabase },
  { name: 'BM25', icon: HiSearch },
  { name: 'Hybrid Merge', icon: HiCog },
  { name: 'Re-ranking', icon: HiChip },
  { name: 'LLM', icon: HiChatAlt2 },
  { name: 'Answer', icon: HiDocumentText },
]

export default function PipelineVisualization({ activeStages = [] }) {
  return (
    <div className="flex items-center gap-1 flex-wrap justify-center py-3">
      {stages.map((stage, i) => {
        const isActive = activeStages.includes(stage.name)
        const isComplete = activeStages.indexOf(stage.name) < activeStages.length - 1
        const Icon = stage.icon

        return (
          <div key={stage.name} className="flex items-center">
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.1 }}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-button text-xs font-semibold border-2 transition-all ${
                isComplete
                  ? 'bg-green-50 border-green-300 text-green-700'
                  : isActive
                  ? 'bg-orange-50 border-orange-400 text-orange-700 animate-pulse'
                  : 'bg-cream-50 border-cream-200 text-brown-300'
              }`}
            >
              {isComplete ? (
                <HiCheckCircle className="text-green-500 text-sm" />
              ) : (
                <Icon className={`text-sm ${isActive ? 'text-orange-500' : ''}`} />
              )}
              {stage.name}
            </motion.div>
            {i < stages.length - 1 && (
              <div className={`w-4 h-0.5 mx-1 ${isComplete ? 'bg-green-400' : 'bg-cream-200'}`} />
            )}
          </div>
        )
      })}
    </div>
  )
}
