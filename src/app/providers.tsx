"use client";

import { type ReactNode } from "react";
import { ChatControlsProvider } from "@/context/ChatControlsContext";
import { UserProvider } from "@/context/UserContext";
import { CartControlsProvider } from "@/features/cart/context/CartControlsContext";
import { CartProvider } from "@/features/cart/context/CartContext";

export function ClientProviders({ children }: { children: ReactNode }) {
	return (
		<UserProvider>
			<CartProvider>
				<CartControlsProvider>
					<ChatControlsProvider>
						{children}
					</ChatControlsProvider>
				</CartControlsProvider>
			</CartProvider>
		</UserProvider>
	);
}
