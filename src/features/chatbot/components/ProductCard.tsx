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
	console.log("Product ", product);

	return (
		<Card className="flex w-full flex-row rounded-lg border border-border bg-background p-2 shadow-sm">
			<div className="relative h-32 w-32 flex-shrink-0 md:h-40 md:w-40">
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

			<div className="flex flex-1 flex-col px-3">
				<div className="space-y-2">
					<h3 className="line-clamp-2 text-lg font-semibold text-foreground">{product.name}</h3>
					<div className="flex flex-wrap items-center gap-2">
						<div className="text-xs font-semibold uppercase text-foreground">
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
											className="border-foreground/20 text-xs text-foreground"
										>
											{tag.trim().replace(/,/g, "")}
										</Badge>
									))}
								</div>
							</>
						)}
					</div>
				</div>
				<p className="my-2 line-clamp-2 text-sm text-muted-foreground">
					{product.description || "No description available for this product."}
				</p>

				<div className="mt-auto flex items-center justify-between pt-2">
					<div className="text-lg font-bold text-foreground">
						{/* Use INR symbol for channel-ind by default */}
						{/* ${product.price?.toFixed(2) || "0.00"} */}₹{product.price?.toFixed(2) || "0.00"}
					</div>
					<div className="flex items-center">
						<div className="mr-3 flex items-center">
							<Rating value={product.review_score || 4} precision={0.5} />
							<span className="ml-1 text-sm text-muted-foreground">
								({product.review_score?.toFixed(1) || "4.0"})
							</span>
						</div>
						<Button
							onClick={() => onAddToCart(product)}
							className="hover:bg-primary/90 bg-primary text-primary-foreground"
							size="sm"
						>
							<ShoppingCart className="mr-1 h-4 w-4" />
							Add to Cart
						</Button>
					</div>
				</div>
			</div>
		</Card>
	);
};

export default ProductCard;
