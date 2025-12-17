import { User, Bot, Database, AlertCircle } from 'lucide-react'
import { Message as MessageType } from '../types'

interface MessageProps {
  message: MessageType
}

export default function Message({ message }: MessageProps) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} animate-fade-in`}>
      <div className={`flex max-w-[80%] ${isUser ? 'flex-row-reverse' : 'flex-row'} gap-3`}>
        {/* Avatar */}
        <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
          isUser ? 'bg-primary-600' : message.isError ? 'bg-red-600' : 'bg-gray-700'
        }`}>
          {isUser ? (
            <User className="w-5 h-5 text-white" />
          ) : message.isError ? (
            <AlertCircle className="w-5 h-5 text-white" />
          ) : (
            <Bot className="w-5 h-5 text-white" />
          )}
        </div>

        {/* Message Content */}
        <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
          <div className={`rounded-lg px-4 py-3 ${
            isUser 
              ? 'bg-primary-600 text-white' 
              : message.isError
                ? 'bg-red-900/20 border border-red-500/50 text-red-300'
                : 'bg-gray-800/50 border border-gray-700 text-gray-200'
          }`}>
            <p className="whitespace-pre-wrap break-words">{message.content}</p>

            {/* Display selected APIs if available */}
            {message.selectedApis && message.selectedApis.length > 0 && (
              <div className="mt-3 pt-3 border-t border-gray-700">
                <div className="flex items-center text-xs text-gray-400 mb-2">
                  <Database className="w-3 h-3 mr-1" />
                  APIs Used:
                </div>
                <div className="space-y-1">
                  {message.selectedApis.map((api: any, idx: number) => (
                    <div key={idx} className="text-xs bg-gray-900/50 rounded px-2 py-1">
                      <span className="text-primary-400 font-mono">{api.api_id}</span>
                      {api.reasoning && (
                        <p className="text-gray-500 mt-0.5">{api.reasoning}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Timestamp */}
          <span className="text-xs text-gray-500 mt-1">
            {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>
      </div>
    </div>
  )
}


