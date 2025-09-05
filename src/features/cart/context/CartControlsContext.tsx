'use client';

import React, { createContext, useContext, useState, useCallback } from 'react';

type CartControlsContextType = {
  isCartOpen: boolean;
  openCart: () => void;
  closeCart: () => void;
  toggleCart: () => void;
};

const CartControlsContext = createContext<CartControlsContextType | undefined>(undefined);

export function CartControlsProvider({ children }: { children: React.ReactNode }) {
  const [isCartOpen, setIsCartOpen] = useState(false);
  
  const openCart = useCallback(() => {
    setIsCartOpen(true);
  }, []);
  
  const closeCart = useCallback(() => {
    setIsCartOpen(false);
  }, []);
  
  const toggleCart = useCallback(() => {
    setIsCartOpen(prev => !prev);
  }, []);

  return (
    <CartControlsContext.Provider
      value={{
        isCartOpen,
        openCart,
        closeCart,
        toggleCart,
      }}
    >
      {children}
    </CartControlsContext.Provider>
  );
}

export function useCartControls() {
  const context = useContext(CartControlsContext);
  if (context === undefined) {
    throw new Error('useCartControls must be used within a CartControlsProvider');
  }
  return context;
}