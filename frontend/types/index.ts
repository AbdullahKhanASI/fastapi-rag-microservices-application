export interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
  sources?: string[];
  confidence?: number;
  isStreaming?: boolean;
}

export interface ChatRequest {
  message: string;
  conversation_history: Array<{
    human: string;
    assistant: string;
  }>;
  retrieval_params?: {
    top_k: number;
    threshold: number;
  };
  generation_params?: {
    max_tokens: number;
    temperature: number;
  };
}

export interface ChatResponse {
  response: string;
  sources: string[];
  confidence: number;
  retrieved_docs: Array<{
    chunk_id: string;
    content: string;
    score: number;
    source_file: string;
  }>;
  enhanced_query?: {
    enhanced_query: string;
    intent: string;
    confidence: number;
  };
  token_usage?: {
    total_tokens: number;
    prompt_tokens: number;
    completion_tokens: number;
  };
}

export interface DocumentFile {
  file_id: string;
  file_name: string;
  chunks_count: number;
  status: string;
  message: string;
}

export interface ApiError {
  detail: string;
  status?: number;
}