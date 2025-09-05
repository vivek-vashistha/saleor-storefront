// Bundle carousel component
import React from "react";
import { Button } from "@/components/ui/button";
import { ProductCard } from "@/features/chatbot/components";
import { useChatControls } from "@/context/ChatControlsContext";
import { useCartControls } from "@/features/cart/context";
import { Product } from "@/features/chatbot/types";
import { Check, ShoppingCart } from "lucide-react";

export const BundleCarousel = ({
  products,
  onAddToCart,
  isBundledProducts = true,
}: {
  products: Product[];
  onAddToCart: (product: Product) => void;
  isBundledProducts?: boolean;
}) => {
  // Get chat control functions
  const { closeChat } = useChatControls();
  // Get cart control functions
  const { openCart } = useCartControls();

  // Calculate total bundle price for all products
  const calculateBundlePrice = () => {
    return products.reduce((total, product) => total + (product.price || 0), 0);
  };

  const bundlePrice = calculateBundlePrice();
  const discount = bundlePrice * 0.1; // Example 10% bundle discount
  const finalPrice = bundlePrice - discount;

  const handleAddEntireBundleToCart = () => {
    // Add all products to cart
    products.forEach((product) => {
      onAddToCart(product);
    });

    // Close the chat completely
    closeChat();

    // Open the cart
    setTimeout(() => {
      openCart();
    }, 300); // Small delay for better UX
  };

  return (
   <div className="flex flex-col h-full">
      {/* Scrollable content area with fixed height */}
      <div className="flex-1 min-h-0">
        <div className="h-full overflow-y-auto px-4 py-2">
          <div className="grid grid-cols-1 gap-3">
            {products.map((product, index) => (
              <div
                key={`${product.product_id || index}`}
                className="transform transition-all duration-200 hover:scale-[1.01]"
              >
                <ProductCard product={product} onAddToCart={onAddToCart} />
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Fixed Bundle summary */}
      {bundlePrice > 0 && (
        <div className="bg-background border-t border-border z-10 sticky bottom-0 shadow-[0_-2px_6px_rgba(0,0,0,0.05)]">
          <div className="max-w-screen-xl mx-auto px-4 py-1">
            {/* Price summary and benefits in a grid layout */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-2">
              {/* Left column: Price Summary */}
              <div className="py-1">
                <h4 className="font-medium text-base mb-1.5">Price Summary</h4>
                <div className="flex justify-between text-sm text-foreground">
                  <span>Subtotal ({products.length} items)</span>
                  <span>${bundlePrice.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-sm text-green-600 dark:text-green-500 font-medium my-1">
                  <span>Bundle Discount (10%)</span>
                  <span>-${discount.toFixed(2)}</span>
                </div>
                <div className="pt-1 border-t border-dashed border-border flex justify-between font-semibold text-foreground text-base">
                  <span>Total</span>
                  <span className="text-xl">${finalPrice.toFixed(2)}</span>
                </div>
              </div>

              {/* Right column: Benefits */}
              <div className="py-1 flex flex-col items-end">
                <h4 className="font-medium text-base mb-1 w-full text-right">Benefits</h4>
                <div className="grid grid-cols-[1fr_auto] gap-x-3 gap-y-1.5 items-center">
                  <span className="text-sm text-right text-foreground">
                    Free shipping
                  </span>
                  <div className="border border-black rounded-full p-1">
                    <Check className="h-4 w-4 text-foreground" />
                  </div>

                  <span className="text-sm text-right text-foreground">
                    30-day guarantee
                  </span>
                  <div className="border border-black rounded-full p-1">
                    <Check className="h-4 w-4 text-foreground" />
                  </div>

                  <span className="text-sm text-right text-foreground">
                    Save ${discount.toFixed(2)}
                  </span>
                  <div className="border border-black rounded-full p-1">
                    <Check className="h-4 w-4 text-foreground" />
                  </div>
                </div>
              </div>
            </div>

            {/* Call to action button */}
            <div className="flex items-center justify-center gap-4 bg-primary/10 p-2 rounded-lg mt-2">
              <p className="text-base font-semibold text-primary whitespace-nowrap">
                Save ${discount.toFixed(2)} with this bundle
              </p>
              <Button
                className="bg-primary hover:bg-primary/90 font-semibold text-base h-10 px-6"
                onClick={handleAddEntireBundleToCart}
              >
                <ShoppingCart className="h-4 w-4" />
                {isBundledProducts ? "Add Bundle to Cart" : "Add all to Cart"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default BundleCarousel;