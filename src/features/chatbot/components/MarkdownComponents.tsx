'use client';

import React from 'react';
import {cn} from '@/lib/utils';
import {Message} from '@/features/chatbot/types';

// Function to create markdown components based on message
export const createMarkdownComponents = (message: Message) => {
  const isRecommendation = message.isProductBundleRecommendation || message.isProductRecommendation;
  
  return {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    p: ({children, ...props}: React.PropsWithChildren<any>) => (
      <p className={cn(
        "my-2", 
        isRecommendation ? "text-muted-foreground" : ""
      )} {...props}>
        {children}
      </p>
    ),
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    strong: ({children, ...props}: React.PropsWithChildren<any>) => (
      <strong className="font-semibold text-primary" {...props}>{children}</strong>
    ),
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    h1: ({children, ...props}: React.PropsWithChildren<any>) => (
      <h1 className="my-3 text-primary text-xl font-semibold" {...props}>{children}</h1>
    ),
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    h2: ({children, ...props}: React.PropsWithChildren<any>) => (
      <h2 className="my-3 text-primary text-lg font-semibold" {...props}>{children}</h2>
    ),
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    li: ({children, ...props}: React.PropsWithChildren<any>) => (
      <li className={cn(
        "my-1", 
        isRecommendation ? "text-muted-foreground" : ""
      )} {...props}>
        {children}
      </li>
    ),
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    ul: ({children, ...props}: React.PropsWithChildren<any>) => (
      <ul className={cn(
        "ml-5 pl-0", 
        isRecommendation ? "text-muted-foreground" : ""
      )} {...props}>
        {children}
      </ul>
    ),
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    ol: ({children, ...props}: React.PropsWithChildren<any>) => (
      <ol className={cn(
        "ml-5 pl-0", 
        isRecommendation ? "text-muted-foreground" : ""
      )} {...props}>
        {children}
      </ol>
    ),
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    code: ({children, ...props}: React.PropsWithChildren<any>) => (
      <code className="bg-muted text-primary px-1 py-0.5 rounded" {...props}>{children}</code>
    )
  };
}; 