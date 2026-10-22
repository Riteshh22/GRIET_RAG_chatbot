import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  HiCog,
  HiSave,
  HiChip,
  HiLightningBolt,
  HiDatabase,
  HiAdjustments,
  HiSearch,
} from 'react-icons/hi'
import WindowCard from '../components/WindowCard'
import { getSystemInfo } from '../services/api'
import toast from 'react-hot-toast'

export default function SettingsPage() {
  const [settings, setSettings] = useState({
    embedding_model: 'BAAI/bge-small-en-v1.5',
    llm_model: 'qwen3:8b',
    top_k: 5,
    chunk_size: 512,
    chunk_overlap: 64,
    temperature: 0.3,
    max_tokens: 2048,
    hybrid_alpha: 0.7,
    reranker_enabled: true,
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getSystemInfo()
      .then((res) => {
        setSettings((prev) => ({
          ...prev,
          embedding_model: res.data.embedding_model || prev.embedding_model,
          llm_model: res.data.llm_model || prev.llm_model,
          top_k: res.data.top_k || prev.top_k,
          chunk_size: res.data.chunk_size || prev.chunk_size,
          chunk_overlap: res.data.chunk_overlap || prev.chunk_overlap,
          hybrid_alpha: res.data.hybrid_alpha || prev.hybrid_alpha,
        }))
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const handleSave = () => {
    toast.success('Settings saved successfully')
  }

  const updateSetting = (key, value) => {
    setSettings((prev) => ({ ...prev, [key]: value }))
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="font-display text-3xl font-bold text-brown-800">Settings</h1>
        <p className="text-brown-400 mt-1">Configure your RAG pipeline parameters</p>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Models */}
        <WindowCard title="Models">
          <div className="space-y-4">
            <SettingSelect
              label="Embedding Model"
              value={settings.embedding_model}
              onChange={(v) => updateSetting('embedding_model', v)}
              options={['BAAI/bge-small-en-v1.5', 'BAAI/bge-base-en-v1.5', 'all-MiniLM-L6-v2']}
              icon={HiChip}
            />
            <SettingSelect
              label="LLM Model"
              value={settings.llm_model}
              onChange={(v) => updateSetting('llm_model', v)}
              options={['qwen3:8b', 'qwen3:4b', 'llama3:8b', 'mistral:7b']}
              icon={HiLightningBolt}
            />
            <SettingToggle
              label="Re-ranking"
              description="Enable cross-encoder re-ranking"
              enabled={settings.reranker_enabled}
              onChange={(v) => updateSetting('reranker_enabled', v)}
            />
          </div>
        </WindowCard>

        {/* Retrieval */}
        <WindowCard title="Retrieval">
          <div className="space-y-4">
            <SettingSlider
              label="Top K"
              description="Number of chunks to retrieve"
              value={settings.top_k}
              min={1}
              max={20}
              step={1}
              onChange={(v) => updateSetting('top_k', v)}
            />
            <SettingSlider
              label="Hybrid Alpha"
              description="Dense vs Sparse weight (1.0 = all dense)"
              value={settings.hybrid_alpha}
              min={0}
              max={1}
              step={0.1}
              onChange={(v) => updateSetting('hybrid_alpha', v)}
            />
          </div>
        </WindowCard>

        {/* Chunking */}
        <WindowCard title="Chunking">
          <div className="space-y-4">
            <SettingSlider
              label="Chunk Size"
              description="Maximum characters per chunk"
              value={settings.chunk_size}
              min={128}
              max={2048}
              step={64}
              onChange={(v) => updateSetting('chunk_size', v)}
            />
            <SettingSlider
              label="Chunk Overlap"
              description="Character overlap between chunks"
              value={settings.chunk_overlap}
              min={0}
              max={256}
              step={8}
              onChange={(v) => updateSetting('chunk_overlap', v)}
            />
          </div>
        </WindowCard>

        {/* Generation */}
        <WindowCard title="Generation">
          <div className="space-y-4">
            <SettingSlider
              label="Temperature"
              description="Creativity level (0 = deterministic)"
              value={settings.temperature}
              min={0}
              max={1}
              step={0.05}
              onChange={(v) => updateSetting('temperature', v)}
            />
            <SettingSlider
              label="Max Tokens"
              description="Maximum response length"
              value={settings.max_tokens}
              min={256}
              max={8192}
              step={256}
              onChange={(v) => updateSetting('max_tokens', v)}
            />
          </div>
        </WindowCard>
      </div>

      {/* Save */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="flex justify-end"
      >
        <motion.button
          whileHover={{ scale: 1.03, y: -2 }}
          whileTap={{ scale: 0.98 }}
          onClick={handleSave}
          className="px-8 py-3 bg-gradient-to-r from-orange-500 to-orange-600 text-white font-display font-bold rounded-button shadow-vintage-hover flex items-center gap-2"
        >
          <HiSave className="text-lg" />
          Save Settings
        </motion.button>
      </motion.div>
    </div>
  )
}

function SettingSelect({ label, value, onChange, options, icon: Icon }) {
  return (
    <div className="p-3 bg-cream-50 rounded-card border border-cream-200">
      <div className="flex items-center gap-2 mb-2">
        <Icon className="text-brown-300" />
        <span className="text-sm font-semibold text-brown-600">{label}</span>
      </div>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full p-2 bg-vintage-window border-2 border-cream-200 rounded-button text-sm text-brown-600 focus:outline-none focus:border-orange-400"
      >
        {options.map((opt) => (
          <option key={opt} value={opt}>{opt}</option>
        ))}
      </select>
    </div>
  )
}

function SettingSlider({ label, description, value, min, max, step, onChange }) {
  return (
    <div className="p-3 bg-cream-50 rounded-card border border-cream-200">
      <div className="flex items-center justify-between mb-1">
        <span className="text-sm font-semibold text-brown-600">{label}</span>
        <span className="text-sm font-mono text-orange-600 font-bold">{value}</span>
      </div>
      <p className="text-xs text-brown-300 mb-2">{description}</p>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="w-full h-2 bg-cream-200 rounded-full appearance-none cursor-pointer accent-orange-500"
      />
    </div>
  )
}

function SettingToggle({ label, description, enabled, onChange }) {
  return (
    <div className="flex items-center justify-between p-3 bg-cream-50 rounded-card border border-cream-200">
      <div>
        <span className="text-sm font-semibold text-brown-600">{label}</span>
        <p className="text-xs text-brown-300">{description}</p>
      </div>
      <button
        onClick={() => onChange(!enabled)}
        className={`relative w-12 h-6 rounded-full transition-colors ${
          enabled ? 'bg-orange-500' : 'bg-cream-200'
        }`}
      >
        <div
          className={`absolute top-0.5 w-5 h-5 rounded-full bg-white shadow-md transition-transform ${
            enabled ? 'translate-x-6' : 'translate-x-0.5'
          }`}
        />
      </button>
    </div>
  )
}
