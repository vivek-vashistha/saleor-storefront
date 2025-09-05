import React from 'react';
import { Button } from "@/components/ui/button";
import { CloseIcon, OpenInFullIcon, CloseFullscreenIcon } from './ChatIcons';

interface ChatHeaderProps {
  isMaximized: boolean;
  onToggleSize: () => void;
  onClose: () => void;
}

const ChatHeader: React.FC<ChatHeaderProps> = ({
  isMaximized,
  onToggleSize,
  onClose
}) => {
  return (
    <header className="p-3 bg-muted text-muted-foreground flex justify-between items-center border-b border-border">
      <h6 id="chatbot-title" className="font-semibold text-lg">Outdoor Gear Assistant</h6>
      <div className="flex items-center">
        <Button
          variant="default"
          size="icon"
          onClick={onToggleSize}
          className="mr-1 bg-primary text-primary-foreground hover:bg-primary/90"
          aria-label={isMaximized ? "Minimize chat" : "Maximize chat"}
        >
          {isMaximized ? <CloseFullscreenIcon /> : <OpenInFullIcon />}
        </Button>
        <Button 
          variant="default" 
          size="icon" 
          onClick={onClose}
          className="bg-primary text-primary-foreground hover:bg-primary/90"
          aria-label="Close chat"
        >
          <CloseIcon />
        </Button>
      </div>
    </header>
  );
};

export default ChatHeader; 