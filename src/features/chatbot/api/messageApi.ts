import { getApiClient } from "./client";
import { type Product, type ProductBundle } from "@/features/chatbot/types";

// Define the response message structure
interface ApiResponseMessage {
	type: string;
	content: string | string[];
	recommended_products?: Product[];
	bundle_id?: string;
	recommended_bundles?: ProductBundle[];
}

// Define the message response structure
interface MessageResponse {
	messages: ApiResponseMessage[];
	[key: string]: unknown;
}

/**
 * Send a message to an existing chat session
 * @param sessionId - The session ID
 * @param content - The message content
 * @param userId - The user ID
 * @param referencedProductIds - Optional product IDs referenced in the message
 * @returns The message response with AI messages
 */
export const sendMessage = async (
	sessionId: string,
	content: string,
	userId: string = "vivek_001",
	referencedProductIds: string[] = [],
): Promise<MessageResponse> => {
	const apiClient = getApiClient();
	const response = await apiClient.post<MessageResponse>(`/v1/sessions/${sessionId}/message`, {
		content,
		user_id: userId,
		referenced_product_ids: referencedProductIds,
	});

	return response.data;
};
