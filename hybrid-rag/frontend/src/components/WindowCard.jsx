import { motion } from 'framer-motion'

export default function WindowCard({ title, children, className = '', headerRight }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className={`window-border bg-vintage-window overflow-hidden ${className}`}
    >
      <div className="window-header">
        <div className="flex items-center gap-2 mr-3">
          <div className="window-dot dot-red" />
          <div className="window-dot dot-yellow" />
          <div className="window-dot dot-green" />
        </div>
        <h3 className="font-display font-semibold text-sm text-brown-600 flex-1">{title}</h3>
        {headerRight}
      </div>
      <div className="p-5">{children}</div>
    </motion.div>
  )
}

export function StatCard({ label, value, icon: Icon, color = 'from-orange-500 to-orange-600', delay = 0 }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
      whileHover={{ y: -4, transition: { duration: 0.2 } }}
      className="window-border bg-vintage-window p-5 cursor-default"
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-semibold text-brown-300 uppercase tracking-wider mb-1">{label}</p>
          <p className="text-2xl font-display font-bold text-brown-700">{value}</p>
        </div>
        <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${color} flex items-center justify-center shadow-vintage`}>
          <Icon className="text-white text-lg" />
        </div>
      </div>
    </motion.div>
  )
}

export function MetricCard({ label, value, progress, color = '#E8820C', delay = 0 }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3, delay }}
      className="bg-vintage-window border-2 border-vintage-border rounded-card p-4"
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold text-brown-400 uppercase">{label}</span>
        <span className="text-sm font-bold text-brown-600">{value}</span>
      </div>
      {progress !== undefined && (
        <div className="w-full h-2 bg-cream-100 rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${progress * 100}%` }}
            transition={{ duration: 1, delay: delay + 0.3 }}
            className="h-full rounded-full"
            style={{ backgroundColor: color }}
          />
        </div>
      )}
    </motion.div>
  )
}
