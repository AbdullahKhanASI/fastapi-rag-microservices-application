# RAG Chatbot Frontend

A modern React/Next.js frontend for the RAG (Retrieval-Augmented Generation) chatbot system.

## Features

- 💬 **Interactive Chat Interface**: Beautiful chat UI with message streaming
- 📁 **File Upload**: Drag-and-drop document upload with support for PDF, TXT, DOCX
- 🎯 **Source Attribution**: See which documents were used to answer your questions
- 🌓 **Dark Mode Support**: Automatic dark/light theme detection
- 📱 **Responsive Design**: Works on desktop, tablet, and mobile
- ⚡ **Real-time Updates**: Live connection status and typing indicators
- 🔍 **Sample Questions**: Quick-start with pre-made example questions

## Tech Stack

- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling
- **Lucide React** - Beautiful icons
- **Axios** - API communication
- **React Markdown** - Formatted message rendering

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Backend services running on localhost:8000

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at http://localhost:3000

### Environment Variables

Create a `.env.local` file:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Project Structure

```
frontend/
├── app/                    # Next.js App Router
│   ├── globals.css        # Global styles
│   ├── layout.tsx         # Root layout
│   └── page.tsx           # Chat page
├── components/            # React components
│   ├── ChatMessage.tsx    # Message display
│   ├── ChatInput.tsx      # Message input
│   ├── TypingIndicator.tsx # Loading state
│   └── FileUpload.tsx     # File upload modal
├── lib/                   # Utilities
│   └── api.ts            # API client
├── types/                 # TypeScript definitions
│   └── index.ts          # Shared types
└── public/               # Static assets
```

## API Integration

The frontend communicates with the FastAPI backend through:

- `POST /chat` - Send messages and get AI responses
- `GET /files` - List uploaded documents  
- `POST /upload` - Upload new documents
- `GET /health/all` - Check backend status

## Development

```bash
# Development server
npm run dev

# Production build
npm run build

# Start production server
npm start

# Lint code
npm run lint
```

## Features in Detail

### Chat Interface
- Real-time message exchange
- Message history with timestamps
- Source document citations
- Confidence scores for AI responses

### File Management
- Drag-and-drop upload
- Multiple file format support
- Upload progress and status
- Document count display

### Responsive Design
- Mobile-first approach
- Touch-friendly interface
- Adaptive layouts
- Dark mode support

## Contributing

1. Follow TypeScript best practices
2. Use Tailwind CSS for styling
3. Add proper error handling
4. Update types when changing APIs
5. Test on multiple devices