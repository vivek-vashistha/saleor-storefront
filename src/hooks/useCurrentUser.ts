"use client";

import { useState, useEffect } from "react";
import { CurrentUserDocument } from "@/gql/graphql";

interface User {
	id: string;
	firstName?: string;
	lastName?: string;
	email?: string;
}

interface UseCurrentUserResult {
	user: User | null;
	loading: boolean;
	error: string | null;
}

export function useCurrentUser(): UseCurrentUserResult {
	const [user, setUser] = useState<User | null>(null);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);

	useEffect(() => {
		const fetchUser = async () => {
			try {
				setLoading(true);
				setError(null);

				// Use the same GraphQL endpoint as the server-side code
				const response = await fetch("/api/graphql", {
					method: "POST",
					headers: {
						"Content-Type": "application/json",
					},
					body: JSON.stringify({
						query: CurrentUserDocument.toString(),
					}),
					credentials: "include", // Include cookies for authentication
				});

				if (!response.ok) {
					throw new Error(`HTTP error! status: ${response.status}`);
				}

				const result = await response.json();

				if (result.errors) {
					// User is not authenticated
					setUser(null);
				} else if (result.data?.me) {
					const saleorUser = result.data.me;
					setUser({
						id: saleorUser.id,
						firstName: saleorUser.firstName,
						lastName: saleorUser.lastName,
						email: saleorUser.email,
					});
				} else {
					setUser(null);
				}
			} catch (err) {
				console.error("Failed to fetch user:", err);
				setError(err instanceof Error ? err.message : "Failed to fetch user");
				setUser(null);
			} finally {
				setLoading(false);
			}
		};

		fetchUser();
	}, []);

	return { user, loading, error };
}
