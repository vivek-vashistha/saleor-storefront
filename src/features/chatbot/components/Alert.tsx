'use client';

import React, { useEffect, useState } from 'react';
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-react';
import { Alert as ShadcnAlert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { cn } from '@/lib/utils';
import { ChatAlertProps } from '@/features/chatbot/types';

const Alert: React.FC<ChatAlertProps> = ({
  children,
  severity = 'info',
  onClose,
  autoHideDuration = 6000,
  title,
}) => {
  const [open, setOpen] = useState(true);

  useEffect(() => {
    if (autoHideDuration > 0) {
      const timer = setTimeout(() => {
        setOpen(false);
        onClose?.();
      }, autoHideDuration);
      return () => clearTimeout(timer);
    }
  }, [autoHideDuration, onClose]);

  if (!open) return null;

  const severityClasses = {
    success: "border-accent bg-accent/10 text-accent-foreground",
    error: "border-destructive bg-destructive/10 text-destructive",
    info: "border-primary bg-primary/10 text-primary-foreground",
    warning: "border-warning bg-warning/10 text-warning-foreground",
  };

  const SeverityIcon = {
    success: CheckCircle,
    error: AlertCircle,
    info: Info,
    warning: AlertTriangle,
  }[severity];

  return (
    <ShadcnAlert className={cn(
      "animate-in fade-in slide-in-from-bottom-5 duration-300 shadow-lg",
      severityClasses[severity]
    )}>
      <div className="flex gap-3">
        <SeverityIcon className="h-5 w-5" />
        <div className="flex-1">
          {title && <AlertTitle>{title}</AlertTitle>}
          <AlertDescription>{children}</AlertDescription>
        </div>
        {onClose && (
          <button
            onClick={() => {
              setOpen(false);
              onClose();
            }}
            className="text-current opacity-70 hover:opacity-100 transition-opacity"
            aria-label="Close"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>
    </ShadcnAlert>
  );
};

export default Alert;
