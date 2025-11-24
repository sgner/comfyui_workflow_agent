import {
  AlertTriangle,
  Bot,
  Globe,
  Hammer,
  Loader2,
  Send,
  Sparkles,
  User
} from 'lucide-react'
import React, { useEffect, useRef } from 'react'

import { ChatMessage, Language, Sender } from '../types'
import { t } from '../utils/i18n'

interface ChatPanelProps {
  messages: ChatMessage[]
  input: string
  setInput: (val: string) => void
  onSend: () => void
  isProcessing: boolean
  onActionClick: (action: string) => void
  language: Language
}

const ChatPanel: React.FC<ChatPanelProps> = ({
  messages,
  input,
  setInput,
  onSend,
  isProcessing,
  onActionClick,
  language
}) => {
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      onSend()
    }
  }

  return (
    <div className="flex flex-col h-full bg-slate-900 border-r border-slate-700/50 relative">
      {/* Header */}
      <div className="p-4 border-b border-slate-700/50 bg-slate-900/50 backdrop-blur-sm flex-shrink-0">
        <div className="flex items-center gap-2">
          <div className="p-2 bg-indigo-600 rounded-lg">
            <Bot className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="font-semibold text-slate-100">
              {t(language, 'appName')}
            </h2>
            <p className="text-xs text-slate-400">
              {t(language, 'appSubtitle')}
            </p>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-4 space-y-6 min-h-0 custom-scrollbar"
      >
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center text-slate-500 space-y-4">
            <Sparkles className="w-12 h-12 opacity-20" />
            <p className="whitespace-pre-wrap max-w-xs">
              {t(language, 'welcome')}
            </p>
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex gap-3 ${msg.sender === Sender.USER ? 'flex-row-reverse' : 'flex-row'}`}
          >
            <div
              className={`
                            w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0
                            ${msg.sender === Sender.USER ? 'bg-slate-700' : 'bg-indigo-600'}
                        `}
            >
              {msg.sender === Sender.USER ? (
                <User size={16} />
              ) : (
                <Bot size={16} />
              )}
            </div>

            <div
              className={`flex flex-col max-w-[85%] ${msg.sender === Sender.USER ? 'items-end' : 'items-start'}`}
            >
              <div
                className={`
                                p-3 rounded-2xl text-sm leading-relaxed shadow-sm whitespace-pre-wrap
                                ${
                                  msg.sender === Sender.USER
                                    ? 'bg-slate-700 text-slate-100 rounded-tr-none'
                                    : 'bg-slate-800 text-slate-200 rounded-tl-none border border-slate-700/50'
                                }
                            `}
              >
                {msg.text}
              </div>

              {/* AI Metadata */}
              {msg.sender === Sender.AI && (
                <div className="mt-2 space-y-2 w-full">
                  {/* Grounding / Search Sources */}
                  {msg.metadata?.groundingSources &&
                    msg.metadata.groundingSources.length > 0 && (
                      <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-2">
                        <div className="flex items-center gap-1.5 text-[10px] text-slate-400 uppercase tracking-wider mb-1.5 font-semibold">
                          <Globe className="w-3 h-3" />
                          <span>{t(language, 'groundingSources')}</span>
                        </div>
                        <div className="flex flex-col gap-1">
                          {msg.metadata.groundingSources
                            .slice(0, 3)
                            .map((source, idx) => (
                              <a
                                key={idx}
                                href={source.uri}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-xs text-indigo-300 hover:text-indigo-200 hover:underline truncate block"
                              >
                                • {source.title}
                              </a>
                            ))}
                        </div>
                      </div>
                    )}

                  {/* Missing Nodes Warning */}
                  {msg.metadata?.missingNodes &&
                    msg.metadata.missingNodes.length > 0 && (
                      <div className="bg-amber-950/30 border border-amber-900/50 rounded-lg p-3 text-xs text-amber-200 flex gap-2 items-start">
                        <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                        <div>
                          <p className="font-semibold mb-1">
                            {t(language, 'missingNodes')}:
                          </p>
                          <ul className="list-disc list-inside opacity-80">
                            {msg.metadata.missingNodes.map((node, i) => (
                              <li key={i}>{node}</li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    )}

                  {/* Suggested Actions */}
                  {msg.metadata?.suggestedActions &&
                    msg.metadata.suggestedActions.length > 0 && (
                      <div className="flex flex-wrap gap-2 mt-2">
                        {msg.metadata.suggestedActions.map((action, i) => (
                          <button
                            key={i}
                            onClick={() => onActionClick(action)}
                            className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 border border-indigo-500/30 hover:border-indigo-500 text-indigo-300 text-xs rounded-full transition-colors flex items-center gap-1.5"
                          >
                            <Sparkles className="w-3 h-3" />
                            {action}
                          </button>
                        ))}
                      </div>
                    )}

                  {/* Update Indicator */}
                  {msg.metadata?.workflowUpdate && (
                    <div className="flex items-center gap-1.5 text-xs text-emerald-400 mt-1 pl-1">
                      <Hammer className="w-3 h-3" />
                      <span>{t(language, 'workflowUpdated')}</span>
                    </div>
                  )}
                </div>
              )}

              <span className="text-[10px] text-slate-500 mt-1 px-1">
                {msg.timestamp.toLocaleTimeString([], {
                  hour: '2-digit',
                  minute: '2-digit'
                })}
              </span>
            </div>
          </div>
        ))}

        {isProcessing && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center flex-shrink-0 animate-pulse">
              <Bot size={16} />
            </div>
            <div className="flex items-center gap-2 text-slate-400 text-sm p-3">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>{t(language, 'thinking')}</span>
            </div>
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="p-4 bg-slate-900 border-t border-slate-700/50 flex-shrink-0 z-10">
        <div className="relative flex items-end gap-2 bg-slate-800 p-2 rounded-xl border border-slate-700 focus-within:border-indigo-500 focus-within:ring-1 focus-within:ring-indigo-500/50 transition-all">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={t(language, 'inputPlaceholder')}
            className="w-full bg-transparent text-slate-200 text-sm placeholder-slate-500 resize-none focus:outline-none py-2 px-2 max-h-32 min-h-[44px] custom-scrollbar"
            rows={1}
            style={{ minHeight: '2.5rem' }}
          />
          <button
            onClick={onSend}
            disabled={!input.trim() || isProcessing}
            className={`
                            p-2 rounded-lg mb-0.5 transition-all flex-shrink-0
                            ${
                              !input.trim() || isProcessing
                                ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
                                : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-900/20'
                            }
                        `}
          >
            <Send size={18} />
          </button>
        </div>
        <p className="text-[10px] text-center text-slate-600 mt-2">
          {t(language, 'aiDisclaimer')}
        </p>
      </div>
    </div>
  )
}

export default ChatPanel
