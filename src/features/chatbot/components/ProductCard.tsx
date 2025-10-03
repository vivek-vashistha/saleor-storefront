// Product card component for carousel view
import React, { useState } from "react";
import { Card } from "@/components/ui/card";
import Rating from "@/components/ui/Rating";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ShoppingCart } from "lucide-react";
import Image from "next/image";
import { Product } from "@/features/chatbot/types";

export const ProductCard = ({
  product,
  onAddToCart,
}: {
  product: Product;
  onAddToCart: (product: Product) => void;
}) => {
  const [imageError, setImageError] = useState(false);
  console.log("Product ", product)

  return (
    <Card className="w-full bg-background rounded-lg border border-border shadow-sm flex flex-row p-2">
      <div className="w-32 md:w-40 h-32 md:h-40 flex-shrink-0 relative">
        <Image
          src={product.image_url}
          alt={product.name}
          fill
          className="object-cover"
          sizes="(max-width: 768px) 8rem, 10rem"
          onError={(e) => {
            if (!imageError) {
              setImageError(true);
              e.currentTarget.src = "https://placehold.co/400x400?text=No+Image";
            }
          }}
        />
      </div>

      <div className="flex-1 flex flex-col px-3">
        <div className="space-y-2">
          <h3 className="font-semibold text-foreground text-lg line-clamp-2">
            {product.name}
          </h3>
          <div className="flex items-center gap-2 flex-wrap">
            <div className="uppercase text-xs font-semibold text-foreground">
              {product.category || "UNCATEGORIZED"}
            </div>
            {product.best_for && product.best_for.length > 0 && (
              <>
                <span className="text-muted-foreground">|</span>
                <span className="text-xs text-foreground">Best for:</span>
                <div className="flex flex-wrap gap-1">
                  {product.best_for.map((tag: string, index: number) => (
                    <Badge
                      key={index}
                      variant="outline"
                      className="border-foreground/20 text-foreground text-xs"
                    >
                      {tag.trim().replace(/,/g, "")}
                    </Badge>
                  ))}
                </div>
              </>
            )}
          </div>
        </div>
        <p className="text-sm text-muted-foreground line-clamp-2 my-2">
          {product.description || "No description available for this product."}
        </p>

        <div className="flex items-center justify-between mt-auto pt-2">
          <div className="text-lg font-bold text-foreground">
            {/* Use INR symbol for channel-ind by default */}
            {/* ${product.price?.toFixed(2) || "0.00"} */}
            ₹{product.price?.toFixed(2) || "0.00"}
          </div>
          <div className="flex items-center">
            <div className="flex items-center mr-3">
              <Rating value={product.review_score || 4} precision={0.5} />
              <span className="text-sm text-muted-foreground ml-1">
                ({product.review_score?.toFixed(1) || "4.0"})
              </span>
            </div>
            <Button
              onClick={() => onAddToCart(product)}
              className="bg-primary text-primary-foreground hover:bg-primary/90"
              size="sm"
            >
              <ShoppingCart className="h-4 w-4 mr-1" />
              Add to Cart
            </Button>
          </div>
        </div>
      </div>
    </Card>
  );
};

export default ProductCard;