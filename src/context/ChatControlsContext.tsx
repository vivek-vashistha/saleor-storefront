'use client';

import React, { createContext, useContext, useState, useCallback } from 'react';

type ChatControlsContextType = {
  isMaximized: boolean;
  isOpen: boolean;
  minimizeChat: () => void;
  maximizeChat: () => void;
  toggleChatSize: () => void;
  openChat: () => void;
  closeChat: () => void;
};

const ChatControlsContext = createContext<ChatControlsContextType | undefined>(undefined);

export function ChatControlsProvider({ children }: { children: React.ReactNode }) {
  const [isMaximized, setIsMaximized] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  
  const minimizeChat = useCallback(() => {
    setIsMaximized(false);
  }, []);
  
  const maximizeChat = useCallback(() => {
    setIsMaximized(true);
  }, []);
  
  const toggleChatSize = useCallback(() => {
    setIsMaximized(prev => !prev);
  }, []);
  
  const openChat = useCallback(() => {
    setIsOpen(true);
  }, []);
  
  const closeChat = useCallback(() => {
    setIsOpen(false);
  }, []);

  return (
    <ChatControlsContext.Provider
      value={{
        isMaximized,
        isOpen,
        minimizeChat,
        maximizeChat,
        toggleChatSize,
        openChat,
        closeChat,
      }}
    >
      {children}
    </ChatControlsContext.Provider>
  );
}

export function useChatControls() {
  const context = useContext(ChatControlsContext);
  if (context === undefined) {
    throw new Error('useChatControls must be used within a ChatControlsProvider');
  }
  return context;
} 