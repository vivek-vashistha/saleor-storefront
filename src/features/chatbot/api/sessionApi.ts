import { getApiClient } from './client';

interface SessionResponse {
  id: string;
  [key: string]: unknown;
}

// Cart summary payload sent during session initialization
export interface CartSummaryItem {
  id: string | null;
  quantity: number;
  productName: string;
  productSlug: string;
  variantId: string;
  variantName: string;
  currency: string;
  unitPrice: number;
  totalPrice: number;
  image: string | null;
}

export interface CartSummary {
  checkoutId: string | null;
  items: CartSummaryItem[];
  lineCount: number;
  currency: string;
}

/**
 * Initialize a new chat session
 * @param userId - The user ID
 * @param initialContent - The initial message content
 * @param cartSummary - Optional cart summary to provide shopping context
 * @returns The session response with ID
 */
export const initializeSession = async (
  userId: string = 'vivek_001',
  initialContent: string = "Hi, there!",
  cartSummary?: CartSummary,
): Promise<SessionResponse> => {
  const apiClient = getApiClient();
  const response = await apiClient.post<SessionResponse>('/v1/sessions', {
    user_id: userId,
    content: initialContent,
    // Provide cart context to backend if available
    ...(cartSummary ? { cart_summary: cartSummary } : {}),
  });

  return response.data;
};

/**
 * Delete an existing chat session
 * @param sessionId - The session ID to delete
 */
export const deleteSession = async (sessionId: string): Promise<void> => {
  const apiClient = getApiClient();
  await apiClient.delete(`/v1/sessions/${sessionId}`);
};

/**
 * Reset user memory by clearing all user profile data
 * @param userId - The user ID whose memory should be reset
 */
export const resetUserMemory = async (userId: string): Promise<void> => {
  const apiClient = getApiClient();
  await apiClient.delete(`/v1/users/${userId}/memory`);
};