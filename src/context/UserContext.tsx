"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { useCurrentUser } from "@/hooks/useCurrentUser";

interface User {
	id: string;
	name: string;
	email?: string;
}

interface UserContextType {
	user: User | null;
	setUser: (user: User | null) => void;
	isAuthenticated: boolean;
	login: (userData: User) => void;
	logout: () => void;
	resetMemory: () => Promise<void>;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

export function UserProvider({ children }: { children: React.ReactNode }) {
	const [user, setUser] = useState<User | null>(null);
	const { user: saleorUser, loading: saleorLoading } = useCurrentUser();

	// Update user when Saleor user data changes
	useEffect(() => {
		if (saleorUser && !saleorLoading) {
			// Convert Saleor user to our User format
			const displayName = saleorUser.firstName
				? `${saleorUser.firstName}${saleorUser.lastName ? ` ${saleorUser.lastName}` : ""}`
				: saleorUser.email || "User";

			const userData: User = {
				id: saleorUser.id,
				name: displayName,
				email: saleorUser.email,
			};

			setUser(userData);
			localStorage.setItem("user", JSON.stringify(userData));
		} else if (!saleorUser && !saleorLoading) {
			// No authenticated user, check for stored user or set to null (visitor)
			const storedUser = localStorage.getItem("user");
			if (storedUser) {
				try {
					const parsedUser = JSON.parse(storedUser) as User;
					setUser(parsedUser);
				} catch (error) {
					console.error("Failed to parse stored user:", error);
					setUser(null);
				}
			} else {
				// No user data available - user is a visitor
				setUser(null);
			}
		}
	}, [saleorUser, saleorLoading]);

	const login = (userData: User) => {
		setUser(userData);
		localStorage.setItem("user", JSON.stringify(userData));
	};

	const logout = () => {
		setUser(null);
		localStorage.removeItem("user");
	};

	const resetMemory = async () => {
		if (!user) {
			console.log("No user logged in - nothing to reset");
			return;
		}

		try {
			const { resetUserMemory } = await import("@/features/chatbot/api/sessionApi");
			await resetUserMemory(user.id);

			// Show success feedback (could be enhanced with toast notifications)
			console.log("User memory reset successfully");

			// Force a page reload to ensure all sessions are fresh
			// This is necessary because the current active session still has the old profile
			alert("Memory reset successfully! The page will reload to ensure all sessions are fresh.");
			window.location.reload();
		} catch (error) {
			console.error("Failed to reset user memory:", error);
			throw error;
		}
	};

	const value: UserContextType = {
		user,
		setUser,
		isAuthenticated: !!user,
		login,
		logout,
		resetMemory,
	};

	return <UserContext.Provider value={value}>{children}</UserContext.Provider>;
}

export function useUser() {
	const context = useContext(UserContext);
	if (context === undefined) {
		throw new Error("useUser must be used within a UserProvider");
	}
	return context;
}
