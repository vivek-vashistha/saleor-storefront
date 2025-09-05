'use client';

import React from 'react';
import { Product } from '@/features/chatbot/types';
import { ProductCard } from '@/features/chatbot/components';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Package } from 'lucide-react';

interface ProductRecommendationsGridProps {
  products: Product[];
  onAddToCart: (product: Product) => void;
}

export const ProductRecommendationsGrid = ({
  products,
  onAddToCart,
}: ProductRecommendationsGridProps) => {
  if (!products || products.length === 0) {
    return null;
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header with styling */}
      <div className="flex justify-between items-center mb-4">
        <div className="flex items-center gap-2">
          <Package className="h-5 w-5 text-primary"/>
          <h3 className="text-base font-medium text-foreground">Recommended Products</h3>
        </div>
        <span className="text-xs px-2 py-1 bg-muted rounded-md font-medium">
          {products.length} items
        </span>
      </div>

      {/* Scrollable content area */}
      <div className="flex-grow mb-4">
        <div className="bg-card rounded-xl border border-border shadow-sm p-4">
          <ScrollArea className="h-[calc(100vh-420px)]">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5 pb-4">
              {products.map((product, index) => (
                <div key={`${product.product_id || index}`}
                     className="transform transition-all duration-200 hover:scale-[1.02]">
                  <ProductCard
                    product={product}
                    onAddToCart={onAddToCart}
                  />
                </div>
              ))}
            </div>
          </ScrollArea>
        </div>
      </div>
    </div>
  );
};

export default ProductRecommendationsGrid; 