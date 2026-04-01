import { QuickAction } from '../types'

const QUICK_ACTIONS: QuickAction[] = [
  { label: 'Indian Market', prompt: 'Give me an overview of Indian markets — NIFTY, SENSEX, and BANK NIFTY.', icon: '🇮🇳' },
  { label: 'Global Markets', prompt: 'Show me current status of major global indices.', icon: '🌍' },
  { label: 'IPO GMP', prompt: 'What are the current IPO GMP (Grey Market Premium) figures?', icon: '📋' },
  { label: 'Upcoming IPOs', prompt: 'List upcoming IPOs with price bands and dates.', icon: '🚀' },
  { label: 'Top Sectors', prompt: 'How are NIFTY sector indices performing today? NIFTY IT, FMCG, Pharma, Auto, Metal.', icon: '📊' },
  { label: 'Market Help', prompt: 'What can you help me with as TradeBot?', icon: '❓' },
]

interface Props {
  onAction: (prompt: string) => void
  disabled?: boolean
}

export default function QuickActions({ onAction, disabled }: Props) {
  return (
    <div className="flex flex-wrap gap-2 px-4 py-3 border-t border-surface-600">
      {QUICK_ACTIONS.map((action) => (
        <button
          key={action.label}
          onClick={() => onAction(action.prompt)}
          disabled={disabled}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium
            bg-surface-600 border border-surface-500 text-slate-300
            hover:border-accent-green/40 hover:text-accent-green hover:bg-surface-500
            disabled:opacity-40 disabled:cursor-not-allowed
            transition-all duration-150"
        >
          <span>{action.icon}</span>
          <span>{action.label}</span>
        </button>
      ))}
    </div>
  )
}
