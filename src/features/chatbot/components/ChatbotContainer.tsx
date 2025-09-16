"use client"

import React, { useEffect, useRef, useState } from 'react';
import { Button } from "@/components/ui/button";
import {
  X as CloseIcon,
  Maximize2 as OpenIcon,
  Minimize2 as CloseFullscreenIcon,
} from "lucide-react";
import Image from 'next/image';
import { cn } from '@/lib/utils';
import { useChatControls } from '@/context/ChatControlsContext';
import ChatMessages from './ChatMessages';
import ChatInput from './ChatInput';
import UserDisplay from './UserDisplay';
import useChatSession from '../hooks/useChatSession';
import { MemoizedProductPanel } from './ProductPanel';

const ChatbotContainer: React.FC = () => {
  const { isOpen, isMaximized, toggleChatSize, openChat, closeChat } = useChatControls();
  const [isAnimating, setIsAnimating] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const sheetContentRef = useRef<HTMLDivElement>(null);

  const {
    messages,
    isLoading,
    allBundles,
    messageType,
    productMessageTimestamp,
    userHasSentMessage,
    conversationId,
    sendMessage,
    initializeSession,
    deleteSessionIfUnused,
    productSuggestions
  } = useChatSession({
    onMaximize: () => {
      if (!isMaximized) {
        setIsAnimating(true);
        setTimeout(() => {
          toggleChatSize();
          setTimeout(() => {
            setIsAnimating(false);
          }, 850);
        }, 150);
      }
    },
    isMaximized
  });

  const hasProductBundles = allBundles.length > 0;

  // scroll to bottom
  const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  useEffect(scrollToBottom, [messages]);

  // manage session lifecycle
  useEffect(() => {
    if (isOpen && !conversationId) initializeSession();
    if (!isOpen && conversationId && !userHasSentMessage) deleteSessionIfUnused();
  }, [isOpen, conversationId, userHasSentMessage, initializeSession, deleteSessionIfUnused]);

  // reset overflow hack
  useEffect(() => {
    document.body.style.overflow = '';
    return () => { document.body.style.overflow = ''; }
  }, []);

  const handleToggleChatSize = () => {
    setIsAnimating(true);
    setTimeout(() => {
      toggleChatSize();
      setTimeout(() => setIsAnimating(false), 850);
    }, 150);
  };

  return (
    <>
      
      {/* Launcher: badge (when closed) + button, aligned together */}
      <div className="fixed bottom-4 right-4 z-[1300] flex items-center gap-2">
        {!isOpen && (
          <div className="bg-[#176142] text-white px-2 py-1.5 rounded-full shadow-md max-w-[180px] flex items-center gap-2">
            <p className="text-xs font-medium font-sans">Need help with gear?</p>
          </div>
        )}
        <Button
          onClick={isOpen ? closeChat : openChat}
          // className={`rounded-full flex items-center justify-center text-white shadow-lg w-14 h-14 ${
          className={`rounded-full flex items-center justify-center text-white shadow-lg ${
            isOpen ? 'w-12 h-12' : 'w-16 h-16'
          } ${
            isOpen
              ? 'bg-[#64748B] hover:bg-[#64748B]'
              : 'bg-gradient-to-r from-[#75C566] to-[#01814E] hover:opacity-90'
          }`}
          aria-label={isOpen ? "Close chat" : "Open chat"}
          aria-expanded={isOpen}
          aria-controls="chatbot-panel"
        >
          {isOpen
            ? <CloseIcon className="h-6 w-6" />
            : <Image src="/message.svg" alt="Chat" width={24} height={24} />
          }
        </Button>
      </div>

      {isOpen && (
        <div
          id="chatbot-panel"
          role="dialog"
          aria-modal="true"
          aria-labelledby="chatbot-title"
          className={cn(
            "fixed z-[1300]",
            isMaximized
              ? "top-20 right-4 h-auto"
              : "bottom-20 right-4 w-[90vw] sm:w-[300px] md:w-[500px]"
          )}
          style={{
            transition: isAnimating
              ? 'all 0.8s cubic-bezier(0.34,1.56,0.64,1)'
              : 'all 0.3s ease',
          }}
        >
          <div
            className={cn(
              "h-full flex flex-col overflow-hidden shadow-lg bg-background border border-border",
              isMaximized ? "rounded-2xl" : "rounded-xl"
            )}
            style={{
              transition: isAnimating
                ? 'all 0.8s cubic-bezier(0.34,1.56,0.64,1)'
                : 'all 0.3s ease',
              height: isMaximized ? 'calc(100vh - 6rem)' : '600px',
              width: isMaximized ? '97vw' : 'auto',
              right: '4rem',
            }}
            ref={sheetContentRef}
          >
            {/* ─── MAIN CONTENT ─────────────────────────── */}
            <div className="flex overflow-hidden h-full">
              
              {/* ── LEFT PANE (chat + header + input) ─────── */}
              <div
                className={
                  isMaximized && hasProductBundles
                    ? "flex-none w-2/5 flex flex-col h-full"
                    : "flex-1 flex flex-col h-full"
                }
              >
                {/* header now lives inside left pane */}
                {isMaximized ? (
                  <div className="flex flex-col border-b border-border flex-none">
                    <div className="flex justify-between items-center p-3">
                      <div className="flex items-center space-x-1">
                        <Button
                          variant="default"
                          size="icon"
                          onClick={closeChat}
                          className="bg-transparent text-[#020617] hover:bg-white/10"
                          aria-label="Close chat"
                        >
                          <CloseIcon className="h-5 w-5" />
                        </Button>
                        <Button
                          variant="default"
                          size="icon"
                          onClick={handleToggleChatSize}
                          className="bg-transparent text-[#020617] hover:bg-white/10"
                          aria-label="Minimize chat"
                        >
                          <CloseFullscreenIcon className="h-5 w-5" />
                        </Button>
                      </div>
                    </div>
                    <UserDisplay />
                  </div>
                ) : (
                  <div className="flex flex-col border-b border-border flex-none">
                    <header className="p-3 bg-[#E2E8F0] flex justify-between items-center">
                      <div className="flex items-center space-x-1">
                        <Button
                          variant="default"
                          size="icon"
                          onClick={closeChat}
                          className="bg-transparent text-[#020617] hover:bg-white/10"
                          aria-label="Close chat"
                        >
                          <CloseIcon className="h-5 w-5" />
                        </Button>
                        <Button
                          variant="default"
                          size="icon"
                          onClick={handleToggleChatSize}
                          className="bg-transparent text-[#020617] hover:bg-white/10"
                          aria-label="Maximize chat"
                        >
                          <OpenIcon className="h-5 w-5" />
                        </Button>
                      </div>
                      <h6
                        id="chatbot-title"
                        className="font-sans font-semibold text-lg text-[#020617]"
                      >
                        OUTDOOR GEAR ADVISOR
                      </h6>
                    </header>
                    <UserDisplay />
                  </div>
                )}

                {/* messages scroll */}
                <ChatMessages
                  messages={messages}
                  isLoading={isLoading}
                  productMessageTimestamp={productMessageTimestamp}
                  messagesEndRef={messagesEndRef as React.RefObject<HTMLDivElement>}
                  className="flex-1 overflow-y-auto"
                />

                {/* input at bottom */}
                <div className="p-3 border-t border-border bg-white flex-none">
                  <ChatInput
                    isLoading={isLoading}
                    onSendMessage={sendMessage}
                    products={productSuggestions}
                  />
                </div>
              </div>

              {/* ── RIGHT PANE (product bundles) ────────── */}
              {isMaximized && hasProductBundles && (
                <div
                  className="flex-none w-3/5 border-l border-border flex flex-col overflow-hidden bg-[#F5F5F5]"
                  aria-label="Product recommendations"
                >
                  <MemoizedProductPanel
                    allBundles={allBundles}
                    messageType={messageType}
                  />
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* typing indicator styles */}
      <style jsx global>{`
        .typing-indicator {
          display: flex;
          align-items: center;
        }
        .typing-indicator span {
          height: 8px;
          width: 8px;
          background-color: currentColor;
          border-radius: 50%;
          margin: 0 2px;
          opacity: 0.6;
          display: inline-block;
          animation: typing 1.4s infinite ease-in-out both;
        }
        .typing-indicator span:nth-child(1) { animation-delay: 0s; }
        .typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
        .typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes typing {
          0% { transform: scale(1); }
          50% { transform: scale(1.5); }
          100% { transform: scale(1); }
        }
      `}</style>
    </>
  );
};

export default ChatbotContainer;