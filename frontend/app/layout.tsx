import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'RAG Chatbot - AI-Powered Document Q&A',
  description: 'Ask questions about your documents using advanced AI and retrieval-augmented generation.',
  keywords: 'AI, RAG, chatbot, document search, LLM, artificial intelligence',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="h-full">
      <body className={`${inter.className} h-full bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-blue-900`}>
        <div className="min-h-full">
          {children}
        </div>
      </body>
    </html>
  )
}