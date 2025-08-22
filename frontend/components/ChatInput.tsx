'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2 } from 'lucide-react';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  isLoading: boolean;
  placeholder?: string;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage,
  isLoading,
  placeholder = "Ask me anything about your documents...",
}) => {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !isLoading) {
      onSendMessage(message.trim());
      setMessage('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    }
  }, [message]);

  return (
    <form onSubmit={handleSubmit} className="flex gap-3 items-end">
      <div className="flex-1 relative">
        <textarea
          ref={textareaRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={isLoading}
          rows={1}
          className={`
            w-full px-4 py-3 pr-12 rounded-2xl border border-gray-200 dark:border-gray-700
            bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100
            focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
            resize-none transition-all duration-200
            ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}
          `}
          style={{ minHeight: '48px', maxHeight: '120px' }}
        />
        
        {/* Character count hint */}
        {message.length > 500 && (
          <div className="absolute -top-6 right-0 text-xs text-gray-500">
            {message.length}/1000
          </div>
        )}
      </div>
      
      <button
        type="submit"
        disabled={!message.trim() || isLoading}
        className={`
          p-3 rounded-2xl transition-all duration-200 flex items-center justify-center
          ${
            message.trim() && !isLoading
              ? 'bg-blue-600 hover:bg-blue-700 text-white shadow-lg hover:shadow-xl'
              : 'bg-gray-200 dark:bg-gray-700 text-gray-400 dark:text-gray-500 cursor-not-allowed'
          }
        `}
      >
        {isLoading ? (
          <Loader2 className="w-5 h-5 animate-spin" />
        ) : (
          <Send className="w-5 h-5" />
        )}
      </button>
    </form>
  );
};