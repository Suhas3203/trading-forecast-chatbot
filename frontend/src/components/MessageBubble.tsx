import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Message } from '../types'
import { TrendingUp, User } from 'lucide-react'

interface Props {
  message: Message
}

function TypingIndicator() {
  return (
    <div className="flex items-center gap-1.5 px-1 py-2">
      <span className="w-2 h-2 rounded-full bg-slate-400 typing-dot" />
      <span className="w-2 h-2 rounded-full bg-slate-400 typing-dot" />
      <span className="w-2 h-2 rounded-full bg-slate-400 typing-dot" />
    </div>
  )
}

export default function MessageBubble({ message }: Props) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'} items-start`}>
      {/* Avatar */}
      <div
        className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center mt-0.5 ${
          isUser
            ? 'bg-accent-blue/20 border border-accent-blue/40'
            : 'bg-accent-green/10 border border-accent-green/30'
        }`}
      >
        {isUser ? (
          <User size={14} className="text-accent-blue" />
        ) : (
          <TrendingUp size={14} className="text-accent-green" />
        )}
      </div>

      {/* Bubble */}
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
          isUser
            ? 'bg-accent-blue/20 border border-accent-blue/20 text-slate-100 rounded-tr-sm'
            : 'bg-surface-600 border border-surface-500 text-slate-200 rounded-tl-sm'
        }`}
      >
        {message.isLoading ? (
          <TypingIndicator />
        ) : isUser ? (
          <p className="whitespace-pre-wrap">{message.content}</p>
        ) : (
          <div className="prose-trading">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  )
}
