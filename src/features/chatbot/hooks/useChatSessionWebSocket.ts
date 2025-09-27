import { useState, useCallback, useEffect, useRef } from "react";
import { initializeSession } from "../api/sessionApi";
import { sendMessage as sendMessageApi } from "../api/messageApi";
import { type Message } from "../types/Message";
import { useWebSocket, type WebSocketMessage } from "./useWebSocket";
import { useUser } from "@/context/UserContext";

interface UseChatSessionWebSocketProps {
	onMaximize?: () => void;
	isMaximized?: boolean;
}

export const useChatSessionWebSocket = ({ onMaximize, isMaximized }: UseChatSessionWebSocketProps = {}) => {
	const { user } = useUser();
	const hasPersonalizedMessage = useRef(false);

	// Session state
	const [conversationId, setConversationId] = useState<string | null>(null);
	const [messages, setMessages] = useState<Message[]>([
		{
			type: "bot",
			content:
				"Hi there! I'm your product advisor. Tell me about your health goals, concerns, or the vitamins, supplements, sports nutrition, beauty or grocery items you're looking for, and I'll recommend the best options.",
			timestamp: new Date().toISOString(),
		},
	]);
	const [isLoading, setIsLoading] = useState(false);
	const [userHasSentMessage, setUserHasSentMessage] = useState(false);

	// Update the initial message when user data becomes available
	useEffect(() => {
		if (user?.name && !hasPersonalizedMessage.current) {
			const personalizedMessage = `Hi ${user.name}! I'm your product advisor. Tell me about your health goals, concerns, or the vitamins, supplements, sports nutrition, beauty or grocery items you're looking for, and I'll recommend the best options.`;

			setMessages([
				{
					type: "bot",
					content: personalizedMessage,
					timestamp: new Date().toISOString(),
				},
			]);
			hasPersonalizedMessage.current = true;
		}
	}, [user?.name]);

	// WebSocket state
	const [isWebSocketConnected, setIsWebSocketConnected] = useState(false);
	const [currentThinking, setCurrentThinking] = useState<string | null>(null);
	const [toolCalls, setToolCalls] = useState<Array<{ name: string; status: string; data?: any }>>([]);
	const [streamingMessage, setStreamingMessage] = useState<string>("");
	const [isStreaming, setIsStreaming] = useState(false);

	// Use ref to track accumulated chunks to avoid race conditions
	const accumulatedChunksRef = useRef<string>("");

	// Product-related state
	const [allBundles, setAllBundles] = useState<any[]>([]);
	const [productSuggestions, setProductSuggestions] = useState<any[]>([]);
	const [messageType, setMessageType] = useState<"product_bundle_recommendation" | "product_recommendation">(
		"product_bundle_recommendation",
	);
	const [productMessageTimestamp, setProductMessageTimestamp] = useState<number | null>(null);

	// WebSocket message handler
	const handleWebSocketMessage = useCallback(
		(message: WebSocketMessage) => {
			console.log("WebSocket message received:", message);

			switch (message.type) {
				case "connection_established":
					setIsWebSocketConnected(true);
					console.log("WebSocket connection established for session:", message.session_id);
					break;

				case "thinking_update":
					setCurrentThinking(message.thinking);
					break;

				case "tool_call_update":
					const toolCall = {
						name: message.tool_name,
						status: message.status,
						data: message.data,
					};

					setToolCalls((prev) => {
						const existing = prev.find((tc) => tc.name === toolCall.name);
						if (existing) {
							return prev.map((tc) => (tc.name === toolCall.name ? toolCall : tc));
						} else {
							return [...prev, toolCall];
						}
					});
					break;

				case "message_chunk":
					console.log("🔍 Frontend: Received message_chunk:", {
						chunk: message.chunk,
						is_final: message.is_final,
						current_streaming: streamingMessage,
						accumulated_ref: accumulatedChunksRef.current,
						chunk_length: message.chunk?.length || 0,
					});

					if (message.is_final) {
						// Final chunk - handle both string and array content
						const currentTimestamp = new Date().toISOString();

						if (Array.isArray(message.chunk)) {
							// Create separate messages for each chunk item
							message.chunk.forEach((chunkItem, index) => {
								const botMessage: Message = {
									type: "bot",
									content: chunkItem,
									timestamp: new Date(Date.now() + index * 100).toISOString(), // Slight delay between messages
								};
								setMessages((prev) => [...prev, botMessage]);
							});
						} else {
							// Single string chunk - create one message with ALL accumulated content
							// Use the ref to get the complete accumulated content
							const completeContent = accumulatedChunksRef.current + message.chunk;
							console.log("🔍 Frontend: Final chunk processing:", {
								accumulated_ref: accumulatedChunksRef.current,
								final_chunk: message.chunk,
								complete_content: completeContent,
								complete_length: completeContent.length,
							});

							const botMessage: Message = {
								type: "bot",
								content: completeContent,
								timestamp: currentTimestamp,
							};
							setMessages((prev) => [...prev, botMessage]);
						}

						// Reset streaming state and ref
						setStreamingMessage("");
						accumulatedChunksRef.current = "";
						setIsStreaming(false);
						setCurrentThinking(null);
						setToolCalls([]);
					} else {
						// Intermediate chunk - accumulate using ref to avoid race conditions
						console.log("🔍 Frontend: Intermediate chunk:", {
							chunk: message.chunk,
							previous_accumulated: accumulatedChunksRef.current,
							new_accumulated: accumulatedChunksRef.current + message.chunk,
						});

						// Update both ref and state
						accumulatedChunksRef.current += message.chunk;
						setStreamingMessage(accumulatedChunksRef.current);

						if (!isStreaming) {
							setIsStreaming(true);
						}
					}
					break;

				case "product_recommendations":
					setProductSuggestions(message.products || []);
					setMessageType("product_recommendation");
					setProductMessageTimestamp(Date.now());
					break;

				case "error":
					console.error("WebSocket error:", message.error);
					const errorMessage: Message = {
						type: "bot",
						content: `Error: ${message.error}`,
						timestamp: new Date().toISOString(),
						isError: true,
					};
					setMessages((prev) => [...prev, errorMessage]);
					setCurrentThinking(null);
					setToolCalls([]);
					setIsStreaming(false);
					break;

				case "pong":
					// Handle ping/pong for connection health
					break;

				default:
					console.warn("Unknown WebSocket message type:", message.type);
			}
		},
		[streamingMessage, isStreaming],
	);

	// WebSocket hook
	const {
		isConnected,
		sendMessage: sendWebSocketMessage,
		connectionError,
		reconnect,
	} = useWebSocket(conversationId, handleWebSocketMessage);

	// Initialize session
	const initializeSessionFn = useCallback(async () => {
		try {
			const sessionResponse = await initializeSession(user?.id || "vivek_001");
			if (sessionResponse.id) {
				setConversationId(sessionResponse.id);
				console.log("Session initialized:", sessionResponse.id);
			}
		} catch (error) {
			console.error("Error initializing session:", error);
		}
	}, [user?.id]);

	// Delete session if unused
	const deleteSessionIfUnused = useCallback(async () => {
		if (conversationId && !userHasSentMessage) {
			try {
				// You would implement session deletion here
				console.log("Deleting unused session:", conversationId);
				setConversationId(null);
				setMessages([]);
				setAllBundles([]);
				setProductSuggestions([]);
			} catch (error) {
				console.error("Error deleting session:", error);
			}
		}
	}, [conversationId, userHasSentMessage]);

	// Send message function
	const sendMessageFn = useCallback(
		async (messageContent: string, productIds?: string[]) => {
			if (!messageContent.trim()) return;

			const currentTimestamp = new Date().toISOString();
			const userMessage: Message = {
				type: "user",
				content: messageContent,
				timestamp: currentTimestamp,
			};

			setMessages((prev) => [...prev, userMessage]);
			setUserHasSentMessage(true);

			// If no conversation exists yet, initialize and send in one go
			if (!conversationId) {
				try {
					setIsLoading(true);
					const sessionResponse = await initializeSession(user?.id || "vivek_001");

					if (sessionResponse.id) {
						setConversationId(sessionResponse.id);
						// Wait for WebSocket connection
						await new Promise((resolve) => {
							const checkConnection = () => {
								if (isConnected) {
									resolve(true);
								} else {
									setTimeout(checkConnection, 100);
								}
							};
							checkConnection();
						});

						// Send message via WebSocket
						sendWebSocketMessage({
							type: "message",
							content: messageContent,
							user_id: user?.id || "vivek_001",
							referenced_product_ids: productIds || [],
						});
					}
				} catch (error) {
					console.error("Error:", error);
					const errorMessage: Message = {
						type: "bot",
						content: error instanceof Error ? error.message : "Sorry, an error occurred.",
						timestamp: new Date().toISOString(),
						isError: true,
					};
					setMessages((prev) => [...prev, errorMessage]);
				} finally {
					setIsLoading(false);
				}
			} else {
				// Send message via WebSocket
				if (isConnected) {
					sendWebSocketMessage({
						type: "message",
						content: messageContent,
						user_id: user?.id || "vivek_001",
						referenced_product_ids: productIds || [],
					});
				} else {
					// Fallback to HTTP API if WebSocket is not connected
					try {
						setIsLoading(true);
						const messageResponse = await sendMessageApi(
							conversationId,
							messageContent,
							user?.id || "vivek_001",
							productIds || [],
						);

						// Process the response messages
						const botMessages = messageResponse.messages || [];
						const newMessages: Message[] = botMessages.map((msg: any) => ({
							type: "bot",
							content: msg.content || "",
							timestamp: new Date().toISOString(),
						}));

						setMessages((prev) => [...prev, ...newMessages]);
					} catch (error) {
						console.error("Error sending message:", error);
						const errorMessage: Message = {
							type: "bot",
							content: "Sorry, an error occurred while processing your request.",
							timestamp: new Date().toISOString(),
							isError: true,
						};
						setMessages((prev) => [...prev, errorMessage]);
					} finally {
						setIsLoading(false);
					}
				}
			}
		},
		[conversationId, user?.id, isConnected, sendWebSocketMessage],
	);

	// Update connection status
	useEffect(() => {
		setIsWebSocketConnected(isConnected);
	}, [isConnected]);

	// Handle connection errors
	useEffect(() => {
		if (connectionError) {
			console.error("WebSocket connection error:", connectionError);
		}
	}, [connectionError]);

	// Get products data based on the message type (matching original logic)
	const getProductsData = () => {
		if (messageType === "product_recommendation") {
			return productSuggestions;
		}
		// For bundle recommendations, flatten all products from all bundles
		return allBundles.flatMap((bundle) => bundle.products || []);
	};

	return {
		// Session state
		conversationId,
		messages,
		isLoading: isLoading || isStreaming,
		userHasSentMessage,

		// WebSocket state
		isWebSocketConnected,
		currentThinking,
		toolCalls,
		streamingMessage,
		isStreaming,
		connectionError,

		// Product state (matching original structure)
		allBundles:
			messageType === "product_recommendation"
				? [{ bundle_id: "recommendations", products: productSuggestions }]
				: allBundles,
		products: productSuggestions,
		messageType,
		productMessageTimestamp,
		productSuggestions: getProductsData()
			.filter((product) => product.name)
			.map((product) => ({
				id: product.product_id?.toString() || product.id,
				name: product.name,
			})),

		// Actions
		sendMessage: sendMessageFn,
		initializeSession: initializeSessionFn,
		deleteSessionIfUnused,
		reconnect,

		// Legacy compatibility
		hasProductBundles: allBundles.length > 0,
	};
};
