'use client';

import React, {memo, useState} from 'react';
import {Button} from '@/components/ui/button';
import {AddShoppingCartIcon} from './ChatIcons';
import Alert from './Alert';
import {useCart} from '@/features/cart/context';
import { useParams, useRouter } from "next/navigation";
import {BundleCarousel} from "./BundleCarousel";
import {Product, ProductPanelProps} from '@/features/chatbot/types';
import {ArrowLeft, ArrowRight} from 'lucide-react';

const ProductPanel: React.FC<ProductPanelProps> = ({allBundles = [], messageType = 'product_bundle_recommendation'}) => {
    const {addToCart} = useCart();
    const params = useParams<{ channel?: string }>();
    const router = useRouter();

    const resolveChannel = () => {
        const fromParams = params?.channel;
        if (fromParams) return fromParams;
        if (typeof window !== 'undefined') {
            const seg = window.location.pathname.split('/')[1];
            if (seg) return seg;
        }
        // default switched to channel-ind (was default-channel)
        // return "default-channel";
        return "channel-ind";
    };
    const [openSnackbar, setOpenSnackbar] = useState(false);
    const [selectedBundleIndex, setSelectedBundleIndex] = useState(0);

    // Determine if we have multiple bundles
    const hasMultipleBundles = allBundles.length > 1;

    // Use the selected bundle from allBundles
    const currentBundle = allBundles.length > 0 ? allBundles[selectedBundleIndex] : null;

    const handleAddAllToCart = async () => {
        try {
            const channel = resolveChannel();
            console.log("[Chat:AddAllToCart] channel", channel);
            if (!currentBundle?.products || currentBundle.products.length === 0) return;

            const tasks = currentBundle.products.filter(Boolean).map((product) => async () => {
                try {
                    console.log("[Chat:AddAllToCart] request", { name: product!.name, channel });
                    const res = await fetch("/api/cart/add", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ name: product!.name, channel }),
                    });
                    const data: any = await res.json().catch(() => ({} as any));
                    console.log("[Chat:AddAllToCart] response", { name: product!.name, status: res.status, data });
                    const success = res.ok && data?.success;
                    if (success) {
                        // Update local cart immediately for responsive count updates
                        addToCart({
                            product_id: product!.product_id,
                            name: product!.name,
                            price: product!.price,
                            image_url: product!.image_url,
                            quantity: 1,
                        });
                        // Ask Next.js to refresh server components (navbar count)
                        try { router.refresh(); } catch {}
                    }
                    return { product, success } as const;
                } catch (e) {
                    console.warn("[Chat:AddAllToCart] failed", { name: product!.name, error: e });
                    return { product, success: false } as const;
                }
            });

            const runWithConcurrency = async <T,>(fns: Array<() => Promise<T>>, limit = 5) => {
                const results: T[] = [];
                let cursor = 0;
                const workers = new Array(Math.min(limit, fns.length)).fill(0).map(async () => {
                    while (cursor < fns.length) {
                        const i = cursor++;
                        results[i] = await fns[i]!();
                    }
                });
                await Promise.all(workers);
                return results;
            };

            await runWithConcurrency(tasks, 5);

            setOpenSnackbar(true);
        } catch (error) {
            console.error("Error adding products to cart:", error);
        }
    };

    const handleAddToCart = async (product: Product) => {
        try {
            const channel = resolveChannel();
            console.log("[Chat:AddToCart] channel", channel);
            if (product) {
                console.log("[Chat:AddToCart] request", { name: product.name, channel });
                const res = await fetch("/api/cart/add", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ name: product.name, channel }),
                });
                const data: any = await res.json().catch(() => ({} as any));
                console.log("[Chat:AddToCart] response", { status: res.status, data });
                if (!res.ok || !data?.success) {
                    const msg = (data && (data as any).error) || (data && (data as any).errors && (data as any).errors[0]?.message) || "Failed to add to Saleor cart";
                    throw new Error(msg);
                }
                addToCart({
                    product_id: product.product_id,
                    name: product.name,
                    price: product.price,
                    image_url: product.image_url,
                    quantity: 1
                });
                try { router.refresh(); } catch {}
                setOpenSnackbar(true);
                setTimeout(() => setOpenSnackbar(false), 3000);
            }
        } catch (error) {
            console.error("[Chat:AddToCart] error", error);
        }
    };

    const handlePreviousBundle = () => {
        setSelectedBundleIndex((prev) => (prev === 0 ? allBundles.length - 1 : prev - 1));
    };

    const handleNextBundle = () => {
        setSelectedBundleIndex((prev) => (prev === allBundles.length - 1 ? 0 : prev + 1));
    };

    if (!currentBundle || !currentBundle.products || currentBundle.products.length === 0) {
        return null;
    }

    const isProductRecommendations = messageType === 'product_recommendation';
    const panelTitle = isProductRecommendations ? 'RECOMMENDATIONS' : 'BUNDLE';

    return (
        <div className="h-full flex flex-col  rounded-r-xl overflow-auto relative">
            <header className="p-4 bg-header-foreground flex justify-between items-center border-b border-border sticky top-0 z-30">
                <div className="flex items-center gap-2">
                    <h2 className="text-lg font-semibold">{panelTitle}</h2>
                    {hasMultipleBundles && !isProductRecommendations && (
                        <>
                            <span className="text-sm font-medium px-2 py-0.5 bg-background rounded-md">
                                {selectedBundleIndex + 1} of {allBundles.length}
                            </span>
                            {/* Previous bundle button */}
                            <Button
                                variant="ghost"
                                size="icon"
                                className="h-8 w-8 rounded-md border border-border bg-foreground text-background hover:bg-primary/90 hover:text-background/90 ml-2"
                                onClick={handlePreviousBundle}
                                title="Previous Bundle"
                            >
                                <ArrowLeft className="h-4 w-4"/>
                            </Button>
                            {/* Next bundle button */}
                            <Button
                                variant="ghost"
                                size="icon"
                                className="h-8 w-8 rounded-md border border-border bg-foreground text-background hover:bg-primary/90 hover:text-background/90"
                                onClick={handleNextBundle}
                                title="Next Bundle"
                            >
                                <ArrowRight className="h-4 w-4"/>
                            </Button>
                        </>
                    )}
                </div>

                <div className="flex items-center gap-2">
                    {currentBundle.products && currentBundle.products.length > 0 && (
                        <Button
                            variant="default"
                            size="sm"
                            className="bg-primary hover:bg-primary/90 font-semibold text-base h-10 px-6"
                            onClick={handleAddAllToCart}
                        >
                            <AddShoppingCartIcon/>
                            <span>{isProductRecommendations ? "Add all to Cart" : "Add all bundles to Cart"}</span>
                        </Button>
                    )}
                </div>
            </header>
            <div className="flex-1 p-4">
            <BundleCarousel
                        isBundledProducts={!isProductRecommendations}
                        products={currentBundle.products}
                        onAddToCart={handleAddToCart}
                    />
                
            </div>

            

            {/* Success notification */}
            {openSnackbar && (
                <div className="fixed bottom-4 right-4 z-[1500]">
                    <Alert severity="success" onClose={() => setOpenSnackbar(false)}>
                        Item added to cart
                    </Alert>
                </div>
            )}
        </div>
    )
};

// Create a memoized version
export const MemoizedProductPanel = memo(ProductPanel);

export default ProductPanel;