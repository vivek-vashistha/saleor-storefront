import React from 'react';
import { Button } from '@/components/ui/button';
import { Heart, ShoppingCart, Truck, ArrowRight } from 'lucide-react';
import Rating from "@/components/ui/Rating";
import Image from "next/image";
import { FeaturedProduct } from '@/types';

// Sample products - in a real app, these would come from an API or CMS
const products: FeaturedProduct[] = [
  {
    id: 1,
    name: 'Adventure Backpack Pro',
    price: 129.99,
    rating: 4.5,
    image: 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80',
    category: 'Gear',
    isNew: true,
    discount: 15,
    freeShipping: true
  },
  {
    id: 2,
    name: 'Hiking Boots Elite',
    price: 189.99,
    rating: 4.8,
    image: 'https://images.unsplash.com/photo-1551107696-a4b0c5a0d9a2?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80',
    category: 'Footwear',
    isNew: false,
    discount: null,
    freeShipping: true
  },
  {
    id: 3,
    name: 'All-Weather Jacket',
    price: 249.99,
    rating: 4.7,
    image: 'https://images.unsplash.com/photo-1519211975560-4ca611f5a72a?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80',
    category: 'Clothing',
    isNew: true,
    discount: 10,
    freeShipping: false
  },
  {
    id: 4,
    name: 'Camping Tent Ultra',
    price: 299.99,
    rating: 4.6,
    image: 'https://images.unsplash.com/photo-1537225228614-56cc3556d7ed?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80',
    category: 'Gear',
    isNew: false,
    discount: null,
    freeShipping: true
  }
];

const ProductPrice = ({ price, discount }: { price: number; discount: number | null }) => {
  const discountedPrice = discount 
    ? (price - (price * discount / 100)).toFixed(2) 
    : null;

  return (
    <div className="flex items-baseline mt-4">
      {discount ? (
        <>
          <span className="text-2xl font-extrabold text-foreground">
            ${discountedPrice}
          </span>
          <span className="ml-2 line-through font-medium text-sm text-muted-foreground">
            ${price}
          </span>
        </>
      ) : (
        <span className="text-2xl font-extrabold text-foreground">
          ${price}
        </span>
      )}
    </div>
  );
};

const ProductCard = ({ product }: { product: FeaturedProduct }) => {
  return (
    <div className="h-full">
      <div className="h-full flex flex-col border border-border rounded-2xl overflow-hidden shadow-md transition-all duration-300 hover:shadow-lg hover:-translate-y-2 bg-card text-card-foreground">
        <div className="relative">
          <div className="overflow-hidden">
            <Image
              src={product.image}
              alt={product.name}
              width={600}
              height={300}
              className="h-[300px] w-full object-cover transition-transform duration-500 hover:scale-105"
            />
          </div>
          
          {/* Badges */}
          <div className="absolute top-4 left-4 flex flex-col gap-2">
            {product.isNew && (
              <div className="font-bold text-xs py-1 px-2 rounded shadow-md bg-primary text-primary-foreground">
                NEW
              </div>
            )}
            
            {product.discount && (
              <div className="font-bold text-xs py-1 px-2 rounded shadow-md bg-destructive text-destructive-foreground">
                -{product.discount}%
              </div>
            )}
          </div>
          
          {/* Favorite button */}
          <Button
            variant="secondary"
            size="icon"
            className="absolute top-4 right-4 w-8 h-8 rounded-full flex items-center justify-center shadow-sm hover:scale-110 bg-secondary text-secondary-foreground"
          >
            <Heart className="h-4 w-4" />
          </Button>
          
          {/* Free shipping badge */}
          {product.freeShipping && (
            <div className="absolute bottom-4 left-4 flex items-center text-xs font-semibold rounded px-2 py-1 shadow-sm bg-secondary text-secondary-foreground">
              <Truck className="h-3 w-3 mr-1" />
              <span>Free Shipping</span>
            </div>
          )}
        </div>
        
        <div className="flex-grow p-5">
          <div className="uppercase font-semibold tracking-wider text-xs text-muted-foreground">
            {product.category}
          </div>
          
          <h2 className="font-bold text-xl mt-2 mb-2 leading-snug text-foreground">
            {product.name}
          </h2>
          
          <div className="flex items-center mb-4">
            <div className="mr-2">
              <Rating value={product.rating} precision={0.1} />
            </div>
            <span className="text-sm text-muted-foreground">
              ({product.rating})
            </span>
          </div>
          
          <ProductPrice price={product.price} discount={product.discount} />
        </div>
        
        <div className="px-5 pb-5">
          <Button
            className="w-full py-2 font-semibold rounded-lg shadow-sm bg-primary text-primary-foreground hover:bg-primary/90"
          >
            <ShoppingCart className="h-5 w-5 mr-2" />
            Add to Cart
          </Button>
        </div>
      </div>
    </div>
  );
};

export function FeaturedProducts() {
  return (
    <section className="relative py-20 overflow-hidden bg-background text-foreground">
      {/* Background decoration */}
      <div 
        className="absolute inset-0 opacity-[0.03] pointer-events-none bg-grid-pattern"
        aria-hidden="true"
      ></div>
      
      <div className="container px-4 mx-auto">
        <div className="text-center mb-16">
          <span className="inline-block py-1 px-3 rounded-full text-xs font-medium tracking-wider bg-primary/10 text-primary mb-4">
            FEATURED PRODUCTS
          </span>
          <h2 className="text-4xl font-extrabold mb-6 text-foreground">
            Shop Our Most Popular Items
          </h2>
          <div className="w-24 h-1 bg-border mx-auto rounded-full"></div>
          <p className="mt-6 max-w-2xl mx-auto text-lg text-muted-foreground">
            Discover our hand-selected range of premium products that have been loved by our customers.
          </p>
        </div>
        
        {/* <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
          {products.map((product) => (
            <ProductCard key={product.id} product={product} />
          ))}
        </div> */}
        
        {/* <div className="text-center mt-16">
          <Button className="font-semibold px-8 py-6 bg-primary text-primary-foreground hover:bg-primary/90" size="lg">
            View All Products
            <ArrowRight className="ml-2 h-5 w-5" />
          </Button>
        </div> */}
      </div>
    </section>
  );
}

export default FeaturedProducts; 