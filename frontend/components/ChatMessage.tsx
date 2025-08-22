'use client';

import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { Message } from '@/types';
import { Bot, User, Clock, FileText, Zap } from 'lucide-react';

interface ChatMessageProps {
  message: Message;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isUser = message.role === 'user';
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  return (
    <div className={`flex gap-4 mb-6 message-fade-in ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center">
          <Bot className="w-5 h-5 text-white" />
        </div>
      )}
      
      <div className={`max-w-[80%] ${isUser ? 'order-2' : ''}`}>
        <div
          className={`rounded-2xl px-4 py-3 ${
            isUser
              ? 'bg-blue-600 text-white ml-auto'
              : 'bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-sm'
          }`}
        >
          {isUser ? (
            <p className="text-sm sm:text-base">{message.content}</p>
          ) : (
            <div className="prose prose-sm max-w-none dark:prose-invert">
              <ReactMarkdown
                components={{
                  code: ({ children, ...props }) => (
                    <code
                      className="bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded text-sm"
                      {...props}
                    >
                      {children}
                    </code>
                  ),
                  pre: ({ children, ...props }) => (
                    <pre
                      className="bg-gray-100 dark:bg-gray-700 p-3 rounded-lg overflow-x-auto"
                      {...props}
                    >
                      {children}
                    </pre>
                  ),
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          )}
        </div>
        
        {/* Message metadata for assistant responses */}
        {!isUser && (message.sources || message.confidence !== undefined) && (
          <div className="mt-2 flex flex-wrap gap-2 text-xs text-gray-500 dark:text-gray-400">
            {message.confidence !== undefined && (
              <div className="flex items-center gap-1 bg-green-50 dark:bg-green-900/20 px-2 py-1 rounded-full">
                <Zap className="w-3 h-3" />
                <span>Confidence: {(message.confidence * 100).toFixed(1)}%</span>
              </div>
            )}
            
            {message.sources && message.sources.length > 0 && (
              <div className="flex items-center gap-1 bg-blue-50 dark:bg-blue-900/20 px-2 py-1 rounded-full">
                <FileText className="w-3 h-3" />
                <span>{message.sources.length} source{message.sources.length !== 1 ? 's' : ''}</span>
              </div>
            )}
            
            {isClient && (
              <div className="flex items-center gap-1 bg-gray-50 dark:bg-gray-800 px-2 py-1 rounded-full">
                <Clock className="w-3 h-3" />
                <span>{message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
              </div>
            )}
          </div>
        )}
        
        {/* Sources list */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="mt-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Sources:
            </h4>
            <div className="flex flex-wrap gap-2">
              {message.sources.map((source, index) => (
                <span
                  key={index}
                  className="text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 px-2 py-1 rounded-full"
                >
                  {source}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
      
      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-600 flex items-center justify-center order-1">
          <User className="w-5 h-5 text-white" />
        </div>
      )}
    </div>
  );
};