export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  isLoading?: boolean
}

export interface QuickAction {
  label: string
  prompt: string
  icon: string
}
