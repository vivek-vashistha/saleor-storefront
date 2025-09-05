'use client';

import React, {useEffect, useRef, useState} from 'react';
import ReactMarkdown from 'react-markdown';
import {cn} from '@/lib/utils';
import {Card} from '@/components/ui/card';
import {MessageBubbleProps} from '@/features/chatbot/types';
import {getRecommendationStrategy} from './RecommendationStrategies';
import {createMarkdownComponents} from './MarkdownComponents';

const MessageBubble: React.FC<MessageBubbleProps> = ({ 
  message,
}) => {
  // Track whether the full message has been displayed
  const [isFullyTyped, setIsFullyTyped] = useState(message.type !== 'bot');
  // Track the current displayed message text
  const [displayedText, setDisplayedText] = useState('');
  // Simple toggle for showing the typing cursor
  const [showCursor, setShowCursor] = useState(message.type === 'bot');

  // Store animation-related variables in refs to avoid re-renders
  const animationRef = useRef({
    fullContent: message.content || '',
    currentIndex: 0,
    intervalId: null as NodeJS.Timeout | null,
    typingSpeed: 2, // milliseconds between characters (faster animation)
    isAnimating: false
  });

  // Get markdown components for this message
  const markdownComponents = createMarkdownComponents(message);

  useEffect(() => {
    // Only animate bot messages
    if (message.type === 'bot') {
      const anim = animationRef.current;
      anim.fullContent = message.content || '';
      anim.currentIndex = 0;
      anim.isAnimating = true;

      // Start with empty text
      setDisplayedText('');
      setShowCursor(true);
      setIsFullyTyped(false);

      // Use a recursive function for more precise timing control
      const typeNextCharacter = () => {
        const anim = animationRef.current;

        if (anim.currentIndex < anim.fullContent.length) {
          // Add next character
          setDisplayedText(anim.fullContent.substring(0, anim.currentIndex + 1));
          anim.currentIndex++;

          // Schedule next character
          anim.intervalId = setTimeout(typeNextCharacter, anim.typingSpeed);
        } else {
          // Done typing
          anim.isAnimating = false;
          setShowCursor(false);
          setIsFullyTyped(true);
        }
      };

      // Start the typing animation immediately
      typeNextCharacter();

      // Cleanup function
      return () => {
        if (anim.intervalId) {
          clearTimeout(anim.intervalId);
        }
      };
    } else {
      // For user messages, show full text immediately
      setDisplayedText(message.content || '');
      setShowCursor(false);
      setIsFullyTyped(true);
    }
  }, [message.type, message.content]);

  // Get the appropriate rendering strategy for this message
  const renderRecommendationPreview = () => {
    const strategy = getRecommendationStrategy(message);
    return strategy(message);
  };

  return (
    <div className={cn(
      "flex mb-2 animate-in fade-in slide-in-from-bottom-5 duration-300",
      message.type === 'user' ? "justify-end" : "justify-start"
    )}>
      <Card className={cn(
        "p-3 max-w-[80%] w-auto shadow-md",
        message.type === 'user' 
          ? "bg-[#151D1F] text-white rounded-[20px_20px_0_20px] font-geist" 
          : "bg-[#F1F5F966] text-[#002A1A] rounded-[20px_20px_20px_0] border border-[#E2E8F0] font-geist"
      )}>
        {message.type === 'user' ? (
          <p className="font-normal">{message.content}</p>
        ) : (
          <div>
            {/* When typing is in progress */}
            {message.type === 'bot' && (
              <div className="markdown-content">
                {!isFullyTyped ? (
                  <>
                    <ReactMarkdown components={markdownComponents}>
                      {displayedText}
                    </ReactMarkdown>
                    {showCursor && <span className="ml-0.5 animate-pulse">|</span>}
                  </>
                ) : (
                  <ReactMarkdown components={markdownComponents}>
                    {message.content}
                  </ReactMarkdown>
                )}
              </div>
            )}

            {/* Product/Bundle Information - show when recommendations are available */}
            {isFullyTyped && (message.isProductBundleRecommendation || message.isProductRecommendation) && (
              <div className="rounded-lg p-3 mt-3 border border-border">
                {renderRecommendationPreview()}
              </div>
            )}
          </div>
        )}
      </Card>
    </div>
  );
};

export default React.memo(MessageBubble, (prevProps, nextProps) => {
  // Custom comparison function to prevent unnecessary re-renders
  return prevProps.message.timestamp === nextProps.message.timestamp && 
         prevProps.message.content === nextProps.message.content;
}); 
