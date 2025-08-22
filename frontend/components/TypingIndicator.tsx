'use client';

import React from 'react';
import { Bot } from 'lucide-react';

export const TypingIndicator: React.FC = () => {
  return (
    <div className="flex gap-4 mb-6 justify-start message-fade-in">
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center">
        <Bot className="w-5 h-5 text-white" />
      </div>
      
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-sm rounded-2xl px-4 py-3">
        <div className="flex items-center gap-1">
          <span className="text-sm text-gray-600 dark:text-gray-300">AI is thinking</span>
          <div className="flex gap-1 ml-2">
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse delay-75"></div>
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse delay-150"></div>
          </div>
        </div>
      </div>
    </div>
  );
};