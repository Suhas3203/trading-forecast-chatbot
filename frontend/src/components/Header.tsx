import { TrendingUp } from 'lucide-react'

export default function Header() {
  return (
    <header className="flex items-center gap-3 px-5 py-4 border-b border-surface-600 bg-surface-800">
      <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-accent-green/10 border border-accent-green/30">
        <TrendingUp size={20} className="text-accent-green" />
      </div>
      <div>
        <h1 className="text-white font-semibold text-lg leading-tight">TradeBot</h1>
        <p className="text-slate-400 text-xs">Indian & Global Market Intelligence</p>
      </div>
      <div className="ml-auto flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-accent-green animate-pulse" />
        <span className="text-xs text-slate-400">Live</span>
      </div>
    </header>
  )
}
