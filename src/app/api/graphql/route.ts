import { type NextRequest, NextResponse } from "next/server";
import { getServerAuthClient } from "@/app/config";
import { CurrentUserDocument } from "@/gql/graphql";

export async function POST(request: NextRequest) {
	try {
		const { query, variables } = await request.json();

		// For now, we'll handle the CurrentUser query specifically
		// In a full implementation, you'd want a more generic GraphQL handler
		if (query.includes("CurrentUser") || query.includes("me {")) {
			const authClient = await getServerAuthClient();

			const response = await authClient.fetchWithAuth(process.env.NEXT_PUBLIC_SALEOR_API_URL!, {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
				},
				body: JSON.stringify({
					query: CurrentUserDocument.toString(),
					variables,
				}),
			});

			if (!response.ok) {
				return NextResponse.json({ errors: [{ message: "Authentication required" }] }, { status: 401 });
			}

			const data = await response.json();
			return NextResponse.json(data);
		}

		return NextResponse.json({ errors: [{ message: "Unsupported query" }] }, { status: 400 });
	} catch (error) {
		console.error("GraphQL API error:", error);
		return NextResponse.json({ errors: [{ message: "Internal server error" }] }, { status: 500 });
	}
}
