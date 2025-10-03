"use client";

import React, { useState } from "react";
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { AddShoppingCartIcon } from "./ChatIcons";
import Rating from "@/components/ui/Rating";
import Alert from "./Alert";
import { useCart } from "@/features/cart/context";
import { useParams, useRouter } from "next/navigation";
import { Badge } from "@/components/ui/badge";
import Image from "next/image";

interface ProductProps {
	product: {
		product_id?: string | number;
		name: string;
		description: string;
		price: number;
		image_url: string;
		category?: string;
		review_score: number;
		best_for?: string[];
	};
}

const ProductRecommendation: React.FC<ProductProps> = ({ product }) => {
	const { addToCart } = useCart();
	const params = useParams<{ channel?: string }>();
	const router = useRouter();

	const resolveChannel = () => {
		// Prefer route param; fallback to first path segment; default switched to "channel-ind" (was "default-channel")
		const fromParams = params?.channel;
		if (fromParams) return fromParams;
		if (typeof window !== "undefined") {
			const seg = window.location.pathname.split("/")[1];
			if (seg) return seg;
		}
		// return "default-channel";
		return "channel-ind";
	};
	const [openSnackbar, setOpenSnackbar] = useState(false);
	const [imageError, setImageError] = useState(false);

	const handleAddToCart = async () => {
		try {
			const channel = resolveChannel();
			console.log("[Chat:AddToCart] channel", channel);
			// Call server route to search Saleor by name and add to checkout
			console.log("[Chat:AddToCart] request", { name: product.name, channel });
			const res = await fetch("/api/cart/add", {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({ name: product.name, channel }),
			});
			const data: any = await res.json().catch(() => ({}) as any);
			console.log("[Chat:AddToCart] response", { status: res.status, data });
			if (!res.ok || !data?.success) {
				const msg =
					(data && (data as any).error) ||
					(data && (data as any).errors && (data as any).errors[0]?.message) ||
					"Failed to add to Saleor cart";
				throw new Error(msg);
			}
			// Optionally also mirror to local cart for the drawer UX
			const productId =
				typeof product.product_id === "string"
					? parseInt(product.product_id, 10)
					: (product.product_id as number) || Math.floor(Math.random() * 1000000);
			addToCart({
				product_id: productId,
				name: product.name,
				price: product.price,
				image_url: product.image_url,
				quantity: 1,
			});
			// Refresh server components (e.g., server navbar cart count)
			try {
				router.refresh();
			} catch {}
			setOpenSnackbar(true);
		} catch (e) {
			console.error("[Chat:AddToCart] error", e);
			setOpenSnackbar(true);
		}
	};

	return (
		<>
			<Card className="h-full overflow-hidden bg-card text-card-foreground shadow-md transition-transform duration-200 hover:scale-[1.02]">
				<div className="h-[160px] w-full overflow-hidden">
					<Image
						src={product.image_url}
						alt={product.name}
						width={400}
						height={160}
						onError={(e) => {
							if (!imageError) {
								setImageError(true);
								e.currentTarget.src =
									"data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iIzMzMyIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMjAiIGZpbGw9IiNlMGUwZTAiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj5JbWFnZSBub3QgZm91bmQ8L3RleHQ+PC9zdmc+";
							}
						}}
						className="h-full w-full object-cover"
					/>
				</div>

				<CardHeader className="p-2 pb-1">
					<div className="text-xs font-medium uppercase tracking-wider text-primary">
						{product.category || "Uncategorized"}
					</div>
					<h6 className="line-clamp-1 text-base font-semibold text-card-foreground">{product.name}</h6>
				</CardHeader>

				<CardContent className="flex-1 overflow-auto p-2 pt-0">
					<p className="mb-1 line-clamp-3 h-[4.5em] overflow-hidden text-sm text-card-foreground">
						{product.description}
					</p>
					<div className="mb-1 flex items-center gap-1">
						<Rating value={product.review_score} precision={0.1} />
						<p className="text-sm text-muted-foreground">({product.review_score.toFixed(1)})</p>
					</div>
					{product.best_for && (
						<div className="text-sm text-card-foreground">
							<span className="text-muted-foreground">Best For:</span>
							<div className="mt-1 flex flex-wrap gap-1">
								{product.best_for.map((tag, index) => (
									<Badge key={index} variant="outline" className="bg-primary/10 text-xs text-primary">
										{tag.trim().replace(/,/g, "")}
									</Badge>
								))}
							</div>
						</div>
					)}
				</CardContent>

				<CardFooter className="flex flex-col justify-between gap-1 border-t border-border p-2 pt-0 sm:flex-row sm:items-center">
					<p className="text-lg font-bold text-primary">
						{resolveChannel() === "channel-ind" ? "₹" : "$"}
						{product.price.toFixed(2)}
					</p>
					<Button
						onClick={handleAddToCart}
						className="flex w-full items-center justify-center sm:w-[140px]"
						size="sm"
					>
						<AddShoppingCartIcon />
						<span className="ml-1">Add to Cart</span>
					</Button>
				</CardFooter>
			</Card>

			{openSnackbar && (
				<div className="fixed bottom-4 right-4 z-[1500]">
					<Alert severity="success" onClose={() => setOpenSnackbar(false)}>
						{product.name} added to cart!
					</Alert>
				</div>
			)}
		</>
	);
};

export default React.memo(ProductRecommendation);
