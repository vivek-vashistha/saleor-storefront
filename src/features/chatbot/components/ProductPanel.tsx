'use client';

import React, {memo, useState} from 'react';
import {Button} from '@/components/ui/button';
import {AddShoppingCartIcon} from './ChatIcons';
import Alert from './Alert';
import {useCart} from '@/features/cart/context';
import {BundleCarousel} from "./BundleCarousel";
import {Product, ProductPanelProps} from '@/features/chatbot/types';
import {ArrowLeft, ArrowRight} from 'lucide-react';

const ProductPanel: React.FC<ProductPanelProps> = ({allBundles = [], messageType = 'product_bundle_recommendation'}) => {
    const {addToCart} = useCart();
    const [openSnackbar, setOpenSnackbar] = useState(false);
    const [selectedBundleIndex, setSelectedBundleIndex] = useState(0);

    // Determine if we have multiple bundles
    const hasMultipleBundles = allBundles.length > 1;

    // Use the selected bundle from allBundles
    const currentBundle = allBundles.length > 0 ? allBundles[selectedBundleIndex] : null;

    const handleAddAllToCart = () => {
        try {
            if (currentBundle?.products && currentBundle.products.length > 0) {
                currentBundle.products.forEach(product => {
                    if (product) {
                        addToCart({
                            product_id: product.product_id,
                            name: product.name,
                            price: product.price,
                            image_url: product.image_url,
                            quantity: 1
                        });
                    }
                });
                setOpenSnackbar(true);
            }
        } catch (error) {
            console.error("Error adding products to cart:", error);
        }
    };

    const handleAddToCart = (product: Product) => {
        try {
            if (product) {
                addToCart({
                    product_id: product.product_id,
                    name: product.name,
                    price: product.price,
                    image_url: product.image_url,
                    quantity: 1
                });

                // Show success message
                setOpenSnackbar(true);
                setTimeout(() => setOpenSnackbar(false), 3000);
            }
        } catch (error) {
            console.error("Error adding product to cart:", error);
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