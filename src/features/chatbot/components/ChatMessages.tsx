import React from 'react';
import { cn } from '@/lib/utils';
import MessageBubble from './MessageBubble';
import { Message } from '@/features/chatbot/types';

interface ChatMessagesProps {
  messages: Message[];
  productMessageTimestamp: string | null;
  isLoading: boolean;
  messagesEndRef: React.RefObject<HTMLDivElement>;
  className?: string;
}

const ChatMessages: React.FC<ChatMessagesProps> = ({
  messages,
  productMessageTimestamp,
  isLoading,
  messagesEndRef,
  className
}) => {
  return (
    <div className={cn("flex-1 overflow-y-auto p-4", className)} 
      role="log"
      aria-live="polite"
      aria-atomic="false"
      aria-relevant="additions"
    >
      <div className="flex flex-col">
        {/* Message bubbles */}
        {messages.map((message, index) => (
          <MessageBubble 
            key={`${message.timestamp}-${index}`} 
            message={message} 
            productMessageTimestamp={productMessageTimestamp}
          />
        ))}

        {/* Loading indicator */}
        {isLoading && (
          <div className="flex justify-start mb-2">
            <div className="p-3 rounded-[20px_20px_20px_0] flex items-center">
              <div className="typing-indicator" aria-label="Assistant is typing">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}

        {/* Auto-scroll reference */}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
};

export default ChatMessages; 
