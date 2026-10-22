import { useState } from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  HiHome,
  HiChatAlt2,
  HiPlus,
  HiArrowLeft,
  HiClock,
  HiX,
  HiTrash,
} from 'react-icons/hi';
import { useChatHistory } from '../hooks/useChatHistory';

export default function Sidebar({ isOpen, onClose }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { conversations, deleteConversation, clearAllConversations } = useChatHistory();
  const [hoveredId, setHoveredId] = useState(null);
  const [showClearConfirm, setShowClearConfirm] = useState(false);

  const handleNewChat = () => {
    navigate('/chat');
    if (window.innerWidth < 768) onClose();
  };

  const handleConversationClick = (id) => {
    navigate(`/chat/${id}`);
    if (window.innerWidth < 768) onClose();
  };

  return (
    <>
      {window.innerWidth < 768 && isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black/20 z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={`fixed left-0 top-0 h-full w-72 bg-white border-r border-neutral-200 flex flex-col z-50 lg:translate-x-0 transition-transform duration-300 ease-in-out ${
          window.innerWidth < 768 ? (isOpen ? 'translate-x-0' : '-translate-x-full') : 'translate-x-0'
        }`}
      >
        <div className="flex items-center justify-between h-16 px-4 border-b border-neutral-200">
          <NavLink to="/chat" onClick={() => window.innerWidth < 768 && onClose()} className="flex items-center gap-2">
            <div className="w-9 h-9 rounded-xl bg-primary flex items-center justify-center">
              <HiChatAlt2 className="text-white text-lg" />
            </div>
            <span className="font-semibold text-lg text-neutral-900">GRIET Chat</span>
          </NavLink>
          <button
            onClick={onClose}
            className="lg:hidden p-2 rounded-xl hover:bg-neutral-100 text-neutral-500"
            aria-label="Close sidebar"
          >
            <HiX className="text-xl" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-3 space-y-1">
          <button
            onClick={handleNewChat}
            className="w-full sidebar-item justify-center text-primary font-semibold hover:bg-primary-light"
          >
            <HiPlus className="text-lg" />
            <span>New Chat</span>
          </button>

          {conversations.length > 0 && (
            <>
              <div className="px-3 py-2">
                <p className="text-xs font-semibold text-neutral-400 uppercase tracking-wider">Recent Chats</p>
              </div>
              <AnimatePresence mode="popLayout">
                {conversations.map((conv, index) => (
                  <motion.div
                    key={conv.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 20 }}
                    transition={{ duration: 0.2, delay: index * 0.03 }}
                    className="relative group"
                  >
                    <button
                      onClick={() => handleConversationClick(conv.id)}
                      className={`w-full sidebar-item ${location.pathname === `/chat/${conv.id}` ? 'sidebar-item-active' : ''}`}
                    >
                      <HiChatAlt2 className="text-lg flex-shrink-0" />
                      <span className="truncate flex-1 text-left">{conv.title}</span>
                      <span className="text-xs text-neutral-400 flex-shrink-0">{conv.updatedAt}</span>
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteConversation(conv.id);
                      }}
                      className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded-lg text-neutral-400 hover:text-red-500 hover:bg-red-50 opacity-0 group-hover:opacity-100 transition-all"
                      aria-label="Delete conversation"
                    >
                      <HiTrash className="text-sm" />
                    </button>
                  </motion.div>
                ))}
              </AnimatePresence>

              {conversations.length > 0 && (
                <button
                  onClick={() => setShowClearConfirm(true)}
                  className="w-full sidebar-item justify-center text-red-500 hover:bg-red-50"
                >
                  <HiClock className="text-lg" />
                  <span>Clear All History</span>
                </button>
              )}
            </>
          )}

          {conversations.length === 0 && (
            <div className="text-center py-10 text-neutral-400">
              <HiClock className="text-3xl mx-auto mb-3 opacity-50" />
              <p className="text-sm">No conversations yet</p>
              <p className="text-xs mt-1">Start a new chat to begin</p>
            </div>
          )}
        </div>

        <div className="p-3 border-t border-neutral-200">
          <div className="flex items-center gap-3 px-3 py-2 rounded-xl bg-neutral-50">
            <div className="w-2 h-2 rounded-full bg-green-500" />
            <span className="text-sm font-medium text-neutral-600">Ready</span>
          </div>
        </div>
      </aside>

      <AnimatePresence>
        {showClearConfirm && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
            onClick={() => setShowClearConfirm(false)}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="bg-white rounded-2xl p-6 w-full max-w-md shadow-xl"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-lg font-semibold text-neutral-900 mb-2">Clear All Conversations?</h3>
              <p className="text-neutral-600 mb-6">This will permanently delete all your chat history. This action cannot be undone.</p>
              <div className="flex gap-3 justify-end">
                <button
                  onClick={() => setShowClearConfirm(false)}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button
                  onClick={() => {
                    clearAllConversations();
                    setShowClearConfirm(false);
                  }}
                  className="btn-danger"
                >
                  Clear All
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}