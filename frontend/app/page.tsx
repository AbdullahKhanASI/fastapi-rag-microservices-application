'use client';

import dynamic from 'next/dynamic';
import { Suspense } from 'react';

// Dynamically import the ChatPage component with no SSR
const ChatPage = dynamic(() => import('@/components/ChatPage'), {
  ssr: false,
  loading: () => (
    <div className="flex flex-col h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-blue-900">
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Loading RAG Chatbot...</p>
        </div>
      </div>
    </div>
  ),
});

export default function Page() {
  return (
    <Suspense fallback={
      <div className="flex flex-col h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-blue-900">
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-gray-600 dark:text-gray-400">Initializing...</p>
          </div>
        </div>
      </div>
    }>
      <ChatPage />
    </Suspense>
  );
}