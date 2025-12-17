export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  selectedApis?: any[]
  rawData?: any[]
  isError?: boolean
}

export interface ChatRequest {
  query: string
  context?: Array<{ role: string; content: string }>
}

export interface ChatResponse {
  success: boolean
  response: string
  selected_apis?: any[]
  raw_data?: any[]
  error?: string
}


