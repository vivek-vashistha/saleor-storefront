"use client"

import dynamic from 'next/dynamic';

// Dynamically import the chatbot with no SSR to avoid hydration issues
const ChatbotContainer = dynamic(
  () => import('@/features/chatbot/components/ChatbotContainer'),
  { ssr: false }
);

export default function ClientChatbotWrapper() {
  return <ChatbotContainer />;
}