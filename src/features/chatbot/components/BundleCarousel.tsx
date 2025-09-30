// Bundle carousel component
import React from "react";
import { Check, ShoppingCart } from "lucide-react";
import { ProductCard } from "./ProductCard";
import { Button } from "@/components/ui/button";
import { useChatControls } from "@/context/ChatControlsContext";
import { useCartControls } from "@/features/cart/context";
import { type Product } from "@/features/chatbot/types";

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
		<div className="flex h-full flex-col">
			{/* Scrollable content area with fixed height */}
			<div className="min-h-0 flex-1">
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
				<div className="sticky bottom-0 z-10 border-t border-border bg-background shadow-[0_-2px_6px_rgba(0,0,0,0.05)]">
					<div className="mx-auto max-w-screen-xl px-4 py-1">
						{/* Price summary and benefits in a grid layout */}
						<div className="grid grid-cols-1 gap-2 lg:grid-cols-2">
							{/* Left column: Price Summary */}
							<div className="py-1">
								<h4 className="mb-1.5 text-base font-medium">Price Summary</h4>
                                <div className="flex justify-between text-sm text-foreground">
									<span>Subtotal ({products.length} items)</span>
									{/* <span>${bundlePrice.toFixed(2)}</span> */}
                                    <span>₹{bundlePrice.toFixed(2)}</span>
								</div>
								<div className="my-1 flex justify-between text-sm font-medium text-green-600 dark:text-green-500">
									<span>Bundle Discount (10%)</span>
                                    <span>-₹{discount.toFixed(2)}</span>
								</div>
								<div className="flex justify-between border-t border-dashed border-border pt-1 text-base font-semibold text-foreground">
									<span>Total</span>
                                    <span className="text-xl">₹{finalPrice.toFixed(2)}</span>
								</div>
							</div>

							{/* Right column: Benefits */}
							<div className="flex flex-col items-end py-1">
								<h4 className="mb-1 w-full text-right text-base font-medium">Benefits</h4>
								<div className="grid grid-cols-[1fr_auto] items-center gap-x-3 gap-y-1.5">
									<span className="text-right text-sm text-foreground">Free shipping</span>
									<div className="rounded-full border border-black p-1">
										<Check className="h-4 w-4 text-foreground" />
									</div>

									<span className="text-right text-sm text-foreground">30-day guarantee</span>
									<div className="rounded-full border border-black p-1">
										<Check className="h-4 w-4 text-foreground" />
									</div>

                                <span className="text-right text-sm text-foreground">Save ₹{discount.toFixed(2)}</span>
									<div className="rounded-full border border-black p-1">
										<Check className="h-4 w-4 text-foreground" />
									</div>
								</div>
							</div>
						</div>

						{/* Call to action button */}
						<div className="bg-primary/10 mt-2 flex items-center justify-center gap-4 rounded-lg p-2">
                            <p className="whitespace-nowrap text-base font-semibold text-primary">
                                Save ₹{discount.toFixed(2)} with this bundle
							</p>
							<Button
								className="hover:bg-primary/90 h-10 bg-primary px-6 text-base font-semibold"
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
