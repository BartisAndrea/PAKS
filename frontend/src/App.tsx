import { useState } from 'react'

function App() {
  const [activeTab, setActiveTab] = useState<'chat' | 'documents' | 'search'>('chat')

  return (
    <div className="min-h-screen bg-gray-950 text-white flex">
      <div className="w-64 bg-gray-900 border-r border-gray-800 flex flex-col p-4">
        <h1 className="text-xl font-bold text-purple-400 mb-8">🧠 PAKS</h1>
        
        <nav className="flex flex-col gap-2">
          <button
            onClick={() => setActiveTab('chat')}
            className={`text-left px-4 py-3 rounded-lg transition-colors ${
              activeTab === 'chat' 
                ? 'bg-purple-600 text-white' 
                : 'text-gray-400 hover:bg-gray-800'
            }`}
          >
            💬 Chat
          </button>
          <button
            onClick={() => setActiveTab('documents')}
            className={`text-left px-4 py-3 rounded-lg transition-colors ${
              activeTab === 'documents' 
                ? 'bg-purple-600 text-white' 
                : 'text-gray-400 hover:bg-gray-800'
            }`}
          >
            📄 Dokumentumok
          </button>
          <button
            onClick={() => setActiveTab('search')}
            className={`text-left px-4 py-3 rounded-lg transition-colors ${
              activeTab === 'search' 
                ? 'bg-purple-600 text-white' 
                : 'text-gray-400 hover:bg-gray-800'
            }`}
          >
            🔍 Keresés
          </button>
        </nav>
      </div>

      <div className="flex-1 flex flex-col">
        <header className="bg-gray-900 border-b border-gray-800 px-6 py-4">
          <h2 className="text-lg font-semibold">
            {activeTab === 'chat' && '💬 AI Chat'}
            {activeTab === 'documents' && '📄 Dokumentumok'}
            {activeTab === 'search' && '🔍 Keresés'}
          </h2>
        </header>

        <main className="flex-1 p-6">
          {activeTab === 'chat' && <div className="text-gray-400">Chat hamarosan...</div>}
          {activeTab === 'documents' && <div className="text-gray-400">Dokumentumok hamarosan...</div>}
          {activeTab === 'search' && <div className="text-gray-400">Keresés hamarosan...</div>}
        </main>
      </div>
    </div>
  )
}

export default App