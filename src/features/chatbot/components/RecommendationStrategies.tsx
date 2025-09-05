'use client';

import React from 'react';
import Image from 'next/image';
import { Message } from '@/features/chatbot/types';

// Strategy interface (implicit in TypeScript)
export type RecommendationRenderer = (message: Message) => React.ReactNode | null;

// Product recommendation strategy
export const renderProductRecommendation: RecommendationRenderer = (message) => {
  if (!message.isProductRecommendation || !message.recommendedProducts || message.recommendedProducts.length === 0) {
    return null;
  }

  const firstProduct = message.recommendedProducts[0];
  const productCount = message.recommendedProducts.length;
  
  return (
    <div className="relative mt-2 flex items-center">
      <div className="flex items-center">
        {/* Product image */}
        <div className="relative h-20 w-20 mr-3">
          <div className="absolute z-30 top-0 left-0 h-20 w-20 bg-muted-background rounded-md border border-border overflow-hidden shadow-sm">
            {firstProduct.image_url && (
              <Image 
                src={firstProduct.image_url} 
                alt={firstProduct.name || 'Product'} 
                fill 
                className="object-cover" 
              />
            )}
          </div>
          
          {/* Dummy stacked cards for multiple products */}
          {productCount > 1 && (
            <>
              <div className="absolute z-20 top-1 left-1 h-20 w-20 bg-muted rounded-md border border-border shadow-sm" />
              {productCount > 2 && (
                <div className="absolute z-10 top-2 left-2 h-20 w-20 bg-muted/80 rounded-md border border-border shadow-sm" />
              )}
            </>
          )}
        </div>
        
        {/* Text describing the products */}
        <div>
          <p className="text-sm font-medium text-primary">
            {productCount} Product{productCount > 1 ? 's' : ''} Found
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            Recommended just for your needs
          </p>
        </div>
      </div>
    </div>
  );
};

// Bundle recommendation strategy
export const renderBundleRecommendation: RecommendationRenderer = (message) => {
  if (!message.isProductBundleRecommendation || !message.recommendedBundles || message.recommendedBundles.length === 0) {
    return null;
  }

  // Get the first bundle's first product for displaying
  const firstBundle = message.recommendedBundles[0];
  const firstProduct = firstBundle?.products && firstBundle.products.length > 0 
    ? firstBundle.products[0] 
    : null;

  if (!firstProduct) return null;

  // Number of bundles available
  const bundleCount = message.recommendedBundles.length;

  return (
    <div className="relative mt-2 flex items-center bg-amber-50">
      <div className="flex items-center">
        {/* Stack representation */}
        <div className="relative h-20 w-20 mr-3">
          {/* First product image on top */}
          <div className="absolute z-30 top-0 left-0 h-20 w-20 bg-background rounded-md border border-border overflow-hidden shadow-sm">
            {firstProduct.image_url && (
              <Image 
                src={firstProduct.image_url} 
                alt={firstProduct.name || 'Product'} 
                fill 
                className="object-cover" 
              />
            )}
          </div>

          {/* Dummy stacked cards (only rendered if there's more than one bundle) */}
          {bundleCount > 1 && (
            <>
              {/* Second card (slightly offset) */}
              <div className="absolute z-20 top-1 left-1 h-20 w-20 bg-muted rounded-md border border-border shadow-sm" />

              {/* Third card (more offset) - only show if there are 3+ bundles */}
              {bundleCount > 2 && (
                <div className="absolute z-10 top-2 left-2 h-20 w-20 bg-muted/80 rounded-md border border-border shadow-sm" />
              )}
            </>
          )}
        </div>

        {/* Text describing the bundles */}
        <div>
          <p className="text-sm font-medium text-primary">
            {bundleCount > 1 
              ? `${bundleCount} Bundle Options`
              : `1 Bundle Option`}
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            We&apos;ve curated these options just for you!
          </p>
        </div>
      </div>
    </div>
  );
};

// Strategy selector
export const getRecommendationStrategy = (message: Message): RecommendationRenderer => {
  if (message.isProductRecommendation) {
    return renderProductRecommendation;
  }
  if (message.isProductBundleRecommendation) {
    return renderBundleRecommendation;
  }
  
  // Default strategy returns null
  return () => null;
}; 