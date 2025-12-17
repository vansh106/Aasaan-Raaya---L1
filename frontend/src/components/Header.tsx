import { Bot } from 'lucide-react'

export default function Header() {
  return (
    <header className="bg-gray-800/50 backdrop-blur-sm border-b border-gray-700">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-primary-600 rounded-lg">
            <Bot className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">ERP AI Assistant</h1>
            <p className="text-sm text-gray-400">Intelligent ERP Data Query Agent</p>
          </div>
        </div>
      </div>
    </header>
  )
}


