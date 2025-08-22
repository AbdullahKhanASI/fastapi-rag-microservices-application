'use client';

import React, { useState, useEffect, useRef, useId } from 'react';
import { ChatMessage } from '@/components/ChatMessage';
import { ChatInput } from '@/components/ChatInput';
import { TypingIndicator } from '@/components/TypingIndicator';
import { FileUpload } from '@/components/FileUpload';
import { chatApi } from '@/lib/api';
import { Message, DocumentFile, ChatRequest } from '@/types';
import { 
  Upload, 
  FileText, 
  Bot, 
  Sparkles, 
  RefreshCw,
  AlertCircle,
  CheckCircle,
  Activity
} from 'lucide-react';

// This will be replaced with a proper component-scoped ID generator

const SAMPLE_QUESTIONS = [
  "How does low-rank adaptation work for fine-tuning large language models?",
  "What are the key capabilities of frontier AI models in 2025?",
  "Compare parameter efficient tuning methods",
  "Which AI models should I use for text generation tasks?"
];

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isFileUploadOpen, setIsFileUploadOpen] = useState(false);
  const [documents, setDocuments] = useState<DocumentFile[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'checking'>('checking');
  const [mounted, setMounted] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const baseId = useId();
  const messageIdRef = useRef(0);

  // Ensure component is mounted on client
  useEffect(() => {
    setMounted(true);
  }, []);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Check backend connection and load documents on mount (only on client)
  useEffect(() => {
    if (mounted) {
      checkBackendConnection();
      loadDocuments();
    }
  }, [mounted]);

  const checkBackendConnection = async () => {
    setConnectionStatus('checking');
    try {
      await chatApi.getHealthStatus();
      setConnectionStatus('connected');
    } catch (error) {
      setConnectionStatus('disconnected');
    }
  };

  const loadDocuments = async () => {
    try {
      const response = await chatApi.getFiles();
      // Handle both array response and {files: []} object response
      const docs = Array.isArray(response) ? response : (response.files || []);
      const documentFiles = docs.map((filename: string): DocumentFile => ({
        file_id: filename, // Use filename as ID for existing files
        file_name: filename,
        chunks_count: 0, // We don't know chunk count from files endpoint
        status: 'processed',
        message: 'Previously uploaded file'
      }));
      setDocuments(documentFiles);
    } catch (error) {
      console.error('Failed to load documents:', error);
      setDocuments([]); // Ensure documents is always an array
    }
  };

  const generateMessageId = () => {
    return `${baseId}-msg-${++messageIdRef.current}`;
  };

  const handleSendMessage = async (content: string) => {
    const userMessage: Message = {
      id: generateMessageId(),
      content,
      role: 'user',
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // Prepare conversation history
      const conversationHistory = messages
        .slice(-4) // Last 2 exchanges (4 messages)
        .reduce((acc, msg, index, arr) => {
          if (msg.role === 'user' && arr[index + 1]?.role === 'assistant') {
            acc.push({
              human: msg.content,
              assistant: arr[index + 1].content,
            });
          }
          return acc;
        }, [] as Array<{ human: string; assistant: string }>);

      const chatRequest: ChatRequest = {
        message: content,
        conversation_history: conversationHistory,
        retrieval_params: {
          top_k: 5,
          threshold: 0.6,
        },
        generation_params: {
          max_tokens: 500,
          temperature: 0.7,
        },
      };

      const response = await chatApi.sendMessage(chatRequest);
      
      const assistantMessage: Message = {
        id: generateMessageId(),
        content: response.response,
        role: 'assistant',
        timestamp: new Date(),
        sources: response.sources,
        confidence: response.confidence,
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error: any) {
      const errorMessage: Message = {
        id: generateMessageId(),
        content: `I apologize, but I encountered an error while processing your request: ${error.detail || 'Unknown error'}. Please try again or check if the backend services are running.`,
        role: 'assistant',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSampleQuestion = (question: string) => {
    handleSendMessage(question);
  };

  const handleFileUploaded = (file: DocumentFile) => {
    setDocuments(prev => {
      // Ensure prev is always an array
      const currentDocs = Array.isArray(prev) ? prev : [];
      return [...currentDocs, file];
    });
  };

  const ConnectionIndicator = () => (
    <div className="flex items-center gap-2 text-xs">
      {connectionStatus === 'connected' ? (
        <>
          <CheckCircle className="w-3 h-3 text-green-500" />
          <span className="text-green-600">Backend Connected</span>
        </>
      ) : connectionStatus === 'disconnected' ? (
        <>
          <AlertCircle className="w-3 h-3 text-red-500" />
          <span className="text-red-600">Backend Disconnected</span>
          <button
            onClick={checkBackendConnection}
            className="ml-1 text-blue-600 hover:text-blue-800"
          >
            <RefreshCw className="w-3 h-3" />
          </button>
        </>
      ) : (
        <>
          <Activity className="w-3 h-3 text-yellow-500 animate-pulse" />
          <span className="text-yellow-600">Checking Connection...</span>
        </>
      )}
    </div>
  );

  // Don't render anything until mounted on client
  if (!mounted) {
    return null;
  }

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-blue-900">
      {/* Header */}
      <header className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm border-b border-gray-200 dark:border-gray-700 px-4 py-3">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
              <Bot className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                RAG Chatbot
              </h1>
              <p className="text-xs text-gray-600 dark:text-gray-400">
                AI-powered document Q&A
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <ConnectionIndicator />
            <div className="flex items-center gap-2 text-xs text-gray-600 dark:text-gray-400">
              <FileText className="w-3 h-3" />
              <span>{documents.length} documents</span>
            </div>
            <button
              onClick={() => setIsFileUploadOpen(true)}
              className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded-lg text-sm flex items-center gap-2 transition-colors"
            >
              <Upload className="w-4 h-4" />
              Upload
            </button>
          </div>
        </div>
      </header>

      {/* Chat Messages */}
      <div className="flex-1 overflow-hidden">
        <div className="h-full overflow-y-auto px-4 py-6">
          <div className="max-w-4xl mx-auto">
            {messages.length === 0 ? (
              /* Welcome Screen */
              <div className="text-center py-12">
                <div className="w-16 h-16 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-6">
                  <Sparkles className="w-8 h-8 text-white" />
                </div>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-3">
                  Welcome to RAG Chatbot
                </h2>
                <p className="text-gray-600 dark:text-gray-400 mb-8 max-w-md mx-auto">
                  Ask questions about your uploaded documents and get AI-powered answers with source citations.
                </p>
                
                {documents.length > 0 ? (
                  <div className="space-y-4">
                    <h3 className="text-lg font-medium text-gray-800 dark:text-gray-200">
                      Try these sample questions:
                    </h3>
                    <div className="grid gap-3 max-w-2xl mx-auto">
                      {SAMPLE_QUESTIONS.map((question, index) => (
                        <button
                          key={index}
                          onClick={() => handleSampleQuestion(question)}
                          className="p-4 text-left bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl hover:border-blue-300 dark:hover:border-blue-600 hover:shadow-lg transition-all duration-200"
                        >
                          <p className="text-sm text-gray-700 dark:text-gray-300">{question}</p>
                        </button>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-6 max-w-md mx-auto">
                    <FileText className="w-8 h-8 text-blue-600 mx-auto mb-3" />
                    <p className="text-blue-800 dark:text-blue-300 text-sm">
                      Upload some documents first to start asking questions about them.
                    </p>
                    <button
                      onClick={() => setIsFileUploadOpen(true)}
                      className="mt-3 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm transition-colors"
                    >
                      Upload Documents
                    </button>
                  </div>
                )}
              </div>
            ) : (
              /* Chat Messages */
              <div className="space-y-6">
                {messages.map((message) => (
                  <ChatMessage key={message.id} message={message} />
                ))}
                {isLoading && <TypingIndicator />}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Chat Input */}
      <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm border-t border-gray-200 dark:border-gray-700 px-4 py-4">
        <div className="max-w-4xl mx-auto">
          <ChatInput
            onSendMessage={handleSendMessage}
            isLoading={isLoading}
            placeholder={
              documents.length > 0
                ? "Ask me anything about your documents..."
                : "Upload some documents first, then ask questions about them..."
            }
          />
        </div>
      </div>

      {/* File Upload Modal */}
      <FileUpload
        isOpen={isFileUploadOpen}
        onClose={() => setIsFileUploadOpen(false)}
        onFileUploaded={handleFileUploaded}
      />
    </div>
  );
}