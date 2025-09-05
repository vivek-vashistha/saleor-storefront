'use client';

import React, { useState } from 'react';
import { useUser } from '@/context/UserContext';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ConfirmationDialog } from '@/components/ui/confirmation-dialog';
import { Trash2 } from 'lucide-react';

const UserDisplay: React.FC = () => {
  const { user, resetMemory } = useUser();
  const [showResetDialog, setShowResetDialog] = useState(false);
  const [isResetting, setIsResetting] = useState(false);

  const handleResetMemory = async () => {
    setIsResetting(true);
    try {
      await resetMemory();
      setShowResetDialog(false);
      // The resetMemory function will handle the page reload
      // No need for additional alert here
    } catch (error) {
      console.error('Failed to reset memory:', error);
      alert('Failed to reset memory. Please try again.');
    } finally {
      setIsResetting(false);
    }
  };

  if (!user) return null;

  return (
    <>
      <div className="flex items-center justify-between px-3 py-2 bg-gray-50 border-b border-border">
        <div className="flex items-center gap-2">
          <Avatar className="h-6 w-6">
            <AvatarImage src="" alt={user.name} />
            <AvatarFallback className="text-xs bg-blue-100 text-blue-800">
              {user.name.charAt(0).toUpperCase()}
            </AvatarFallback>
          </Avatar>
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-gray-700">
              {user.name}
            </span>
            <Badge variant="secondary" className="text-xs">
              Memory Enabled
            </Badge>
          </div>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setShowResetDialog(true)}
          className="h-6 w-6 p-0 text-gray-500 hover:text-red-600"
          title="Reset AI Memory"
        >
          <Trash2 className="h-3 w-3" />
        </Button>
      </div>

      {/* Reset Memory Confirmation Dialog */}
      <ConfirmationDialog
        open={showResetDialog}
        onOpenChange={setShowResetDialog}
        title="Reset AI Memory"
        description="Are you sure you want to reset your AI memory? This will permanently delete all your saved preferences and conversation history."
        confirmText="Reset Memory"
        cancelText="Cancel"
        variant="destructive"
        onConfirm={handleResetMemory}
        loading={isResetting}
      />
    </>
  );
};

export default UserDisplay;