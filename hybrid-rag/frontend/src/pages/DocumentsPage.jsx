import { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useDropzone } from 'react-dropzone'
import {
  HiUpload,
  HiDocumentText,
  HiTrash,
  HiRefresh,
  HiSearch,
  HiCheckCircle,
  HiExclamationCircle,
  HiClock,
  HiX,
} from 'react-icons/hi'
import WindowCard from '../components/WindowCard'
import { TableSkeleton } from '../components/LoadingSkeleton'
import { useDocuments } from '../hooks/useData'
import { uploadDocument, deleteDocument, reindexDocument } from '../services/api'
import toast from 'react-hot-toast'

export default function DocumentsPage() {
  const { documents, loading, refresh } = useDocuments()
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [searchQuery, setSearchQuery] = useState('')

  const onDrop = useCallback(async (acceptedFiles) => {
    if (acceptedFiles.length === 0) return

    for (const file of acceptedFiles) {
      setUploading(true)
      setUploadProgress(0)
      try {
        await uploadDocument(file, (progress) => setUploadProgress(progress))
        toast.success(`${file.name} uploaded and indexed successfully`)
      } catch (err) {
        toast.error(`Failed to upload ${file.name}: ${err.message}`)
      }
    }
    setUploading(false)
    setUploadProgress(0)
    refresh()
  }, [refresh])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
      'text/csv': ['.csv'],
      'text/markdown': ['.md'],
    },
    maxSize: 50 * 1024 * 1024,
  })

  const handleDelete = async (docId, filename) => {
    if (!window.confirm(`Delete "${filename}"? This will remove all indexed chunks.`)) return
    try {
      await deleteDocument(docId)
      toast.success('Document deleted')
      refresh()
    } catch (err) {
      toast.error(err.message)
    }
  }

  const handleReindex = async (docId) => {
    try {
      toast.loading('Re-indexing document...')
      await reindexDocument(docId)
      toast.dismiss()
      toast.success('Document re-indexed successfully')
      refresh()
    } catch (err) {
      toast.dismiss()
      toast.error(err.message)
    }
  }

  const filteredDocs = documents.filter((d) =>
    d.filename.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="font-display text-3xl font-bold text-brown-800">Document Manager</h1>
        <p className="text-brown-400 mt-1">Upload, manage, and index your documents</p>
      </motion.div>

      {/* Upload Area */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <div
          {...getRootProps()}
          className={`window-border bg-vintage-window p-8 text-center cursor-pointer transition-all ${
            isDragActive ? 'border-orange-400 bg-orange-50' : 'hover:border-orange-300'
          }`}
        >
          <input {...getInputProps()} />
          <div className="flex flex-col items-center">
            {uploading ? (
              <div className="w-full max-w-md">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-orange-500 to-orange-600 flex items-center justify-center mx-auto mb-4 animate-pulse">
                  <HiUpload className="text-white text-2xl" />
                </div>
                <p className="text-sm font-semibold text-brown-600 mb-3">Uploading and indexing...</p>
                <div className="w-full h-3 bg-cream-100 rounded-full overflow-hidden">
                  <motion.div
                    className="h-full bg-gradient-to-r from-orange-500 to-orange-600 rounded-full"
                    animate={{ width: `${uploadProgress}%` }}
                  />
                </div>
                <p className="text-xs text-brown-400 mt-2">{uploadProgress}%</p>
              </div>
            ) : (
              <>
                <div className="w-16 h-16 rounded-2xl bg-cream-100 border-2 border-dashed border-vintage-border flex items-center justify-center mx-auto mb-4">
                  <HiUpload className="text-brown-300 text-2xl" />
                </div>
                <p className="text-sm font-semibold text-brown-600 mb-1">
                  {isDragActive ? 'Drop your files here' : 'Drag & drop files here'}
                </p>
                <p className="text-xs text-brown-400 mb-3">or click to browse</p>
                <div className="flex flex-wrap justify-center gap-2">
                  {['PDF', 'DOCX', 'TXT', 'CSV', 'Markdown'].map((type) => (
                    <span key={type} className="px-3 py-1 bg-cream-100 rounded-button text-xs font-semibold text-brown-400 border border-cream-200">
                      {type}
                    </span>
                  ))}
                </div>
              </>
            )}
          </div>
        </div>
      </motion.div>

      {/* Search + Table */}
      <WindowCard title={`Uploaded Documents (${filteredDocs.length})`}>
        <div className="mb-4">
          <div className="relative">
            <HiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-brown-300" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search documents..."
              className="w-full pl-10 pr-4 py-2.5 bg-cream-50 border-2 border-cream-200 rounded-button text-sm text-brown-600 placeholder:text-brown-300 focus:outline-none focus:border-orange-400 transition-colors"
            />
          </div>
        </div>

        {loading ? (
          <TableSkeleton rows={5} />
        ) : filteredDocs.length === 0 ? (
          <div className="text-center py-10">
            <HiDocumentText className="text-4xl text-brown-200 mx-auto mb-3" />
            <p className="text-sm text-brown-300">
              {searchQuery ? 'No documents match your search' : 'No documents uploaded yet'}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b-2 border-cream-200">
                  <th className="text-left py-3 px-4 text-xs font-bold text-brown-400 uppercase tracking-wider">File Name</th>
                  <th className="text-left py-3 px-4 text-xs font-bold text-brown-400 uppercase tracking-wider">Pages</th>
                  <th className="text-left py-3 px-4 text-xs font-bold text-brown-400 uppercase tracking-wider">Chunks</th>
                  <th className="text-left py-3 px-4 text-xs font-bold text-brown-400 uppercase tracking-wider">Status</th>
                  <th className="text-left py-3 px-4 text-xs font-bold text-brown-400 uppercase tracking-wider">Uploaded</th>
                  <th className="text-right py-3 px-4 text-xs font-bold text-brown-400 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody>
                <AnimatePresence>
                  {filteredDocs.map((doc) => (
                    <motion.tr
                      key={doc.id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="border-b border-cream-100 hover:bg-cream-50 transition-colors"
                    >
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-orange-400 to-orange-500 flex items-center justify-center flex-shrink-0">
                            <HiDocumentText className="text-white text-sm" />
                          </div>
                          <span className="text-sm font-semibold text-brown-600 truncate max-w-[200px]">{doc.filename}</span>
                        </div>
                      </td>
                      <td className="py-3 px-4 text-sm text-brown-500">{doc.pages}</td>
                      <td className="py-3 px-4 text-sm text-brown-500">{doc.chunks}</td>
                      <td className="py-3 px-4">
                        <StatusBadge status={doc.status} />
                      </td>
                      <td className="py-3 px-4 text-xs text-brown-400">
                        {doc.upload_time ? new Date(doc.upload_time).toLocaleDateString() : '—'}
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => handleReindex(doc.id)}
                            className="p-1.5 rounded-lg hover:bg-cream-100 text-brown-300 hover:text-orange-500 transition-colors"
                            title="Re-index"
                          >
                            <HiRefresh className="text-sm" />
                          </button>
                          <button
                            onClick={() => handleDelete(doc.id, doc.filename)}
                            className="p-1.5 rounded-lg hover:bg-red-50 text-brown-300 hover:text-red-500 transition-colors"
                            title="Delete"
                          >
                            <HiTrash className="text-sm" />
                          </button>
                        </div>
                      </td>
                    </motion.tr>
                  ))}
                </AnimatePresence>
              </tbody>
            </table>
          </div>
        )}
      </WindowCard>
    </div>
  )
}

function StatusBadge({ status }) {
  const config = {
    indexed: { icon: HiCheckCircle, color: 'bg-green-50 text-green-600 border-green-200', label: 'Indexed' },
    processing: { icon: HiClock, color: 'bg-yellow-50 text-yellow-600 border-yellow-200', label: 'Processing' },
    uploading: { icon: HiClock, color: 'bg-blue-50 text-blue-600 border-blue-200', label: 'Uploading' },
    failed: { icon: HiExclamationCircle, color: 'bg-red-50 text-red-600 border-red-200', label: 'Failed' },
  }

  const { icon: Icon, color, label } = config[status] || config.failed

  return (
    <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold border ${color}`}>
      <Icon className="text-xs" />
      {label}
    </span>
  )
}
