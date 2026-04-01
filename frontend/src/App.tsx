import Header from './components/Header'
import ChatWindow from './components/ChatWindow'

export default function App() {
  return (
    <div className="min-h-screen bg-surface-900 flex items-center justify-center p-4">
      <div
        className="w-full bg-surface-800 border border-surface-600 rounded-2xl overflow-hidden flex flex-col shadow-2xl"
        style={{ maxWidth: '800px', height: 'calc(100vh - 2rem)', maxHeight: '900px' }}
      >
        <Header />
        <div className="flex-1 overflow-hidden">
          <ChatWindow />
        </div>
      </div>
    </div>
  )
}
