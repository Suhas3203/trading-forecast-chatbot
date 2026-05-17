import { Message } from '../types'

const API_BASE = import.meta.env.VITE_API_URL ?? ''

export async function sendChat(messages: Message[]): Promise<string> {
  const payload = {
    messages: messages
      .filter((m) => !m.isLoading)
      .map((m) => ({ role: m.role, content: m.content })),
  }

  const response = await fetch(`${API_BASE}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: '' }))
    const detail = error.detail || ''
    if (response.status === 429) throw new Error('rate_limit')
    if (response.status === 0 || response.status >= 502)  throw new Error('backend_down')
    throw new Error(detail || `Server error ${response.status}`)
  }

  const data = await response.json()
  return data.reply
}
