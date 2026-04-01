import { useState, useRef, useEffect, KeyboardEvent } from 'react'
import { Send, RotateCcw } from 'lucide-react'
import { Message } from '../types'
import { sendChat } from '../api/chat'
import MessageBubble from './MessageBubble'
import QuickActions from './QuickActions'

const WELCOME_MESSAGE: Message = {
  id: 'welcome',
  role: 'assistant',
  content: `Welcome to **TradeBot** 👋

I'm your market intelligence assistant. Ask me about:
- 📈 **Indian indices** — NIFTY 50, SENSEX, BANK NIFTY, sector indices
- 🌍 **Global markets** — S&P 500, NASDAQ, Dow Jones, FTSE, Nikkei
- 📋 **IPO GMP** — Grey Market Premium for upcoming IPOs
- 🔍 **Stock analysis** — price, technicals, forecast for any NSE/BSE stock
- 📊 **Trading forecasts** — RSI, SMA, support/resistance

Use the quick action buttons below or type your question!`,
  timestamp: new Date(),
}

function generateId() {
  return Math.random().toString(36).slice(2, 11)
}

export default function ChatWindow() {
  const [messages, setMessages] = useState<Message[]>([WELCOME_MESSAGE])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async (text?: string) => {
    const content = (text || input).trim()
    if (!content || isLoading) return

    const userMessage: Message = {
      id: generateId(),
      role: 'user',
      content,
      timestamp: new Date(),
    }

    const loadingMessage: Message = {
      id: 'loading',
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isLoading: true,
    }

    const updatedMessages = [...messages, userMessage]
    setMessages([...updatedMessages, loadingMessage])
    setInput('')
    setIsLoading(true)

    // Resize textarea back to single line
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }

    try {
      const reply = await sendChat(updatedMessages.filter((m) => m.id !== 'welcome'))
      setMessages([
        ...updatedMessages,
        {
          id: generateId(),
          role: 'assistant',
          content: reply,
          timestamp: new Date(),
        },
      ])
    } catch (err) {
      const code = err instanceof Error ? err.message : ''
      const content =
        code === 'rate_limit'
          ? "I'm receiving too many requests right now. Please wait a few seconds and try again."
          : code === 'backend_down'
          ? 'Cannot reach the backend server. Make sure it is running on port 8000.'
          : `Something went wrong: **${code}**`
      setMessages([
        ...updatedMessages,
        {
          id: generateId(),
          role: 'assistant',
          content,
          timestamp: new Date(),
        },
      ])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleTextareaInput = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 120) + 'px'
    }
  }

  const handleReset = () => {
    setMessages([WELCOME_MESSAGE])
    setInput('')
  }

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-5">
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Quick Actions */}
      <QuickActions onAction={handleSend} disabled={isLoading} />

      {/* Input */}
      <div className="px-4 pb-4 pt-2">
        <div className="flex items-end gap-2 bg-surface-600 border border-surface-500 rounded-2xl px-4 py-3 focus-within:border-accent-green/40 transition-colors">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onInput={handleTextareaInput}
            onKeyDown={handleKeyDown}
            placeholder="Ask about NIFTY, a stock, IPO GMP..."
            disabled={isLoading}
            rows={1}
            className="flex-1 bg-transparent text-slate-200 placeholder-slate-500 text-sm resize-none outline-none leading-relaxed disabled:opacity-50"
            style={{ maxHeight: '120px' }}
          />
          <div className="flex items-center gap-1.5 pb-0.5">
            <button
              onClick={handleReset}
              title="Clear chat"
              className="p-1.5 rounded-lg text-slate-500 hover:text-slate-300 hover:bg-surface-500 transition-colors"
            >
              <RotateCcw size={15} />
            </button>
            <button
              onClick={() => handleSend()}
              disabled={!input.trim() || isLoading}
              className="p-1.5 rounded-lg bg-accent-green text-surface-900 hover:bg-accent-green/90 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
            >
              <Send size={15} />
            </button>
          </div>
        </div>
        <p className="text-center text-xs text-slate-600 mt-2">
          For informational purposes only. Not financial advice.
        </p>
      </div>
    </div>
  )
}
