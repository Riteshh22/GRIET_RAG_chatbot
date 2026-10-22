import { Outlet, useLocation } from 'react-router-dom'
import Sidebar from './Sidebar'
import { motion, AnimatePresence } from 'framer-motion'

export default function Layout() {
  const location = useLocation()

  return (
    <div className="flex h-screen bg-vintage-bg overflow-hidden">
      <Sidebar />
      <main className="flex-1 ml-[260px] overflow-y-auto">
        <AnimatePresence mode="wait">
          <motion.div
            key={location.pathname}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            transition={{ duration: 0.25 }}
            className="min-h-screen p-6"
          >
            <Outlet />
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  )
}
