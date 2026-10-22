import { useState } from 'react';
import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { HiOutlineClipboardCopy, HiCheck, HiLink, HiGlobeAlt } from 'react-icons/hi';

const codeTheme = {
  ...oneDark,
  'pre[class*="language-"]': {
    ...oneDark['pre[class*="language-"]'],
    borderRadius: '8px',
    padding: '16px',
  },
};

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <button onClick={copy} className="p-1.5 rounded-lg hover:bg-neutral-200 transition-colors" title="Copy code" aria-label="Copy code">
      {copied ? <HiCheck className="text-green-500 w-4 h-4" /> : <HiOutlineClipboardCopy className="text-neutral-400 w-4 h-4" />}
    </button>
  );
}

export default function ChatMessage({ message }) {
  const isUser = message.role === 'user';

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}
    >
      <div className={isUser ? 'message-user' : 'message-assistant'}>
        {isUser ? (
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
        ) : (
          <div className="text-sm leading-relaxed">
            <ReactMarkdown
              components={{
                code({ node, inline, className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || '');
                  if (!inline && match) {
                    return (
                      <div className="my-3 relative group">
                        <div className="absolute top-2 right-2 z-10 opacity-0 group-hover:opacity-100 transition-opacity">
                          <CopyButton text={String(children)} />
                        </div>
                        <SyntaxHighlighter
                          language={match[1]}
                          style={codeTheme}
                          className="rounded-xl border border-neutral-200 text-sm"
                        >
                          {String(children).replace(/\n$/, '')}
                        </SyntaxHighlighter>
                      </div>
                    );
                  }
                  return (
                    <code className="bg-neutral-100 px-1.5 py-0.5 rounded text-xs font-mono text-primary" {...props}>
                      {children}
                    </code>
                  );
                },
                p: ({ children }) => <p className="mb-3 last:mb-0">{children}</p>,
                ul: ({ children }) => <ul className="list-disc list-inside mb-3 space-y-1">{children}</ul>,
                ol: ({ children }) => <ol className="list-decimal list-inside mb-3 space-y-1">{children}</ol>,
                strong: ({ children }) => <strong className="font-semibold text-neutral-900">{children}</strong>,
                h1: ({ children }) => <h1 className="text-xl font-bold text-neutral-900 mb-2 mt-4">{children}</h1>,
                h2: ({ children }) => <h2 className="text-lg font-bold text-neutral-900 mb-2 mt-4">{children}</h2>,
                h3: ({ children }) => <h3 className="text-base font-semibold text-neutral-900 mb-1 mt-3">{children}</h3>,
                blockquote: ({ children }) => (
                  <blockquote className="border-l-4 border-primary pl-4 italic text-neutral-600 my-4">{children}</blockquote>
                ),
                a: ({ href, children }) => (
                  <a href={href} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline flex items-center gap-1">
                    {children}
                    <HiLink className="text-xs" />
                  </a>
                ),
              }}
            >
              {message.content}
            </ReactMarkdown>
            {message.streaming && (
              <motion.span
                animate={{ opacity: [1, 0] }}
                transition={{ repeat: Infinity, duration: 0.8 }}
                className="inline-block w-1.5 h-4 bg-primary ml-0.5 align-middle"
              />
            )}
            {(message.sources && message.sources.length > 0) || (message.web_sources && message.web_sources.length > 0) ? (
              <div className="mt-4 pt-3 border-t border-neutral-100">
                <p className="text-xs font-medium text-neutral-500 mb-2 flex items-center gap-1">
                  Sources
                  {message.answer_source === 'griet' && <span className="source-badge source-badge-griet">GRIET</span>}
                  {message.answer_source === 'web' && <span className="source-badge source-badge-web">Web</span>}
                  {message.answer_source === 'hybrid' && (
                    <>
                      <span className="source-badge source-badge-griet">GRIET</span>
                      <span className="source-badge source-badge-web">Web</span>
                    </>
                  )}
                </p>
                <div className="space-y-2">
                  {message.sources?.map((source, i) => (
                    <SourceCard key={source.id || i} source={source} index={i} type="griet" />
                  ))}
                  {message.web_sources?.map((source, i) => (
                    <WebSourceCard key={source.url || i} source={source} index={i} />
                  ))}
                </div>
              </div>
            ) : null}
          </div>
        )}
      </div>
    </motion.div>
  );
}

function SourceCard({ source, index, type }) {
  const [expanded, setExpanded] = useState(false);
  const hasUrl = source.source_url || (source.metadata && source.metadata.source_url);
  const url = hasUrl || source.metadata?.source_url;
  const pageType = source.page_type || source.metadata?.page_type;
  const department = source.department || source.metadata?.department;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2, delay: index * 0.05 }}
      className="source-card"
    >
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-primary-light flex items-center justify-center">
          <HiLink className="text-primary text-sm" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-medium text-neutral-900 truncate">{source.document_name}</span>
            {source.similarity_score > 0 && (
              <span className="text-xs font-mono text-neutral-400 bg-neutral-100 px-2 py-0.5 rounded">
                {(source.similarity_score * 100).toFixed(0)}%
              </span>
            )}
          </div>
          <div className="flex items-center gap-2 text-xs text-neutral-500 mb-2 flex-wrap">
            {pageType && <span className="bg-neutral-100 px-2 py-0.5 rounded-full">{pageType}</span>}
            {department && <span className="bg-neutral-100 px-2 py-0.5 rounded-full">{department}</span>}
            <span>Page {source.page_number || 'N/A'}</span>
          </div>
          <p className="text-sm text-neutral-600 line-clamp-3">{source.content}</p>
          {url && (
            <a
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-xs text-primary hover:underline mt-2"
            >
              <HiGlobeAlt className="text-xs" />
              View on GRIET website
            </a>
          )}
        </div>
      </div>
    </motion.div>
  );
}

function WebSourceCard({ source, index }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2, delay: index * 0.05 }}
      className="source-card border-amber-100 bg-amber-50"
    >
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-amber-100 flex items-center justify-center">
          <HiGlobeAlt className="text-amber-600 text-sm" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-medium text-neutral-900 truncate">{source.title}</span>
            <span className="text-xs font-medium text-amber-700 bg-amber-100 px-2 py-0.5 rounded">Web</span>
          </div>
          <p className="text-sm text-neutral-600 line-clamp-3">{source.snippet || source.content}</p>
          {source.url && (
            <a
              href={source.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-xs text-amber-700 hover:underline mt-2"
            >
              <HiLink className="text-xs" />
              View source
            </a>
          )}
        </div>
      </div>
    </motion.div>
  );
}