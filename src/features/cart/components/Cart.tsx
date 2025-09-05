'use client';

import React from 'react';
import { useCart, useCartControls } from '@/features/cart/context';
import { Button } from '@/components/ui/button';
import { Minus, Plus, ShoppingCart, Trash2 } from 'lucide-react';
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/components/ui/sheet';
import Image from "next/image";
import type { CartItem, CartItemProps } from '@/features/cart/types';

const CartBadge = ({ count }: { count: number }) => (
  count > 0 ? (
    <span className="absolute -top-1 -right-1 text-xs font-bold rounded-full h-5 w-5 flex items-center justify-center border-2 border-input bg-background text-foreground">
      {count}
    </span>
  ) : null
);

const EmptyCartMessage = () => (
  <div className="flex flex-col items-center justify-center h-full space-y-4 text-foreground">
    <div className="text-4xl text-muted-foreground">
      <ShoppingCart className="h-16 w-16" />
    </div>
    <p>Your cart is empty</p>
    <Button 
      variant="outline"
      onClick={() => window.location.href = '/products'}
      className="px-4 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90"
    >
      Browse Products
    </Button>
  </div>
);

const CartItem = ({ item, onUpdateQuantity, onRemove }: CartItemProps) => (
  <li className="py-4 text-foreground">
    <div className="flex gap-4 w-full">
      {/* Product Image */}
      <Image
        src={item.image_url}
        alt={item.name}
        width={80}
        height={80}
        className="w-20 h-20 rounded object-cover border border-input"
        onError={(e) => {
          const target = e.target as HTMLImageElement;
          if (!target.getAttribute('data-error')) {
            target.setAttribute('data-error', 'true');
            target.src = 'https://placehold.co/80x80?text=No+Image';
          }
        }}
      />
      
      <div className="flex-1">
        <h3 className="font-medium mb-1 text-foreground">
          {item.name}
        </h3>
        <p className="text-sm mb-2 text-muted-foreground">
          ${item.price.toFixed(2)}
        </p>
        
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="icon"
            className="w-8 h-8 flex items-center justify-center rounded border-input text-foreground"
            onClick={() => onUpdateQuantity(item.product_id, item.quantity - 1)}
            disabled={item.quantity <= 1}
          >
            <Minus className="h-3 w-3" />
          </Button>
          
          <span className="min-w-[20px] text-center text-foreground">
            {item.quantity}
          </span>
          
          <Button
            variant="outline"
            size="icon"
            className="w-8 h-8 flex items-center justify-center rounded border-input text-foreground"
            onClick={() => onUpdateQuantity(item.product_id, item.quantity + 1)}
          >
            <Plus className="h-3 w-3" />
          </Button>
          
          <Button
            variant="ghost"
            size="icon"
            className="ml-2 p-1 rounded text-destructive hover:bg-destructive/10 hover:text-destructive"
            onClick={() => onRemove(item.product_id)}
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  </li>
);

const CartFooter = ({ total }: { total: number }) => (
  <div className="p-4 border-t border-border bg-card">
    <div className="flex justify-between mb-4 text-foreground">
      <span>Subtotal:</span>
      <span className="font-bold">
        ${total.toFixed(2)}
      </span>
    </div>
    <Button className="w-full py-4 font-medium rounded-lg bg-primary text-primary-foreground hover:bg-primary/90">
      Proceed to Checkout
    </Button>
  </div>
);

export default function Cart() {
  const { isCartOpen, openCart, closeCart } = useCartControls();
  const { cartItems, removeFromCart, updateQuantity, getCartTotal, getCartCount } = useCart();

  return (
    <>
      <Button
        variant="ghost"
        size="icon"
        onClick={openCart}
        className="relative text-foreground"
      >
        <ShoppingCart className="h-5 w-5" />
        <CartBadge count={getCartCount()} />
      </Button>

      <Sheet open={isCartOpen} onOpenChange={closeCart}>
        <SheetContent 
          className="w-full sm:max-w-md p-0 overflow-hidden bg-background border-l border-border">
          <div className="flex flex-col h-full">
            <SheetHeader className="p-4 border-b border-border">
              <SheetTitle className="text-lg font-semibold text-foreground">
                Shopping Cart ({getCartCount()} items)
              </SheetTitle>
            </SheetHeader>

            <div className="flex-1 overflow-y-auto p-4 bg-background">
              {cartItems.length === 0 ? (
                <EmptyCartMessage />
              ) : (
                <ul className="divide-y divide-border">
                  {cartItems.map((item) => (
                    <CartItem 
                      key={item.product_id} 
                      item={item} 
                      onUpdateQuantity={updateQuantity}
                      onRemove={removeFromCart}
                    />
                  ))}
                </ul>
              )}
            </div>

            {cartItems.length > 0 && (
              <CartFooter total={getCartTotal()} />
            )}
          </div>
        </SheetContent>
      </Sheet>
    </>
  );
}