import { motion } from 'framer-motion'

export default function LoadingSkeleton({ rows = 3, className = '' }) {
  return (
    <div className={`space-y-3 ${className}`}>
      {Array.from({ length: rows }).map((_, i) => (
        <motion.div
          key={i}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: i * 0.1 }}
          className="animate-pulse"
        >
          <div className="h-4 bg-cream-200 rounded w-3/4 mb-2" />
          <div className="h-3 bg-cream-100 rounded w-full mb-1" />
          <div className="h-3 bg-cream-100 rounded w-5/6" />
        </motion.div>
      ))}
    </div>
  )
}

export function CardSkeleton() {
  return (
    <div className="window-border bg-vintage-window p-5 animate-pulse">
      <div className="flex items-start justify-between">
        <div className="space-y-2">
          <div className="h-3 bg-cream-200 rounded w-24" />
          <div className="h-7 bg-cream-200 rounded w-16" />
        </div>
        <div className="w-10 h-10 bg-cream-200 rounded-xl" />
      </div>
    </div>
  )
}

export function TableSkeleton({ rows = 5 }) {
  return (
    <div className="space-y-2">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex items-center gap-4 p-4 animate-pulse">
          <div className="h-4 bg-cream-200 rounded w-40" />
          <div className="h-4 bg-cream-100 rounded w-16" />
          <div className="h-4 bg-cream-100 rounded w-16" />
          <div className="h-4 bg-cream-100 rounded w-24" />
        </div>
      ))}
    </div>
  )
}
