export const WEBSOCKET_CONFIG = {
	// WebSocket connection settings
	RECONNECT_ATTEMPTS: 5,
	RECONNECT_DELAY: 1000,
	PING_INTERVAL: 30000, // 30 seconds

	// Message streaming settings
	CHUNK_SIZE: 50,
	STREAMING_DELAY: 50, // milliseconds

	// Tool call display settings
	TOOL_CALL_TIMEOUT: 30000, // 30 seconds

	// Connection health check
	HEALTH_CHECK_INTERVAL: 10000, // 10 seconds
};

export const WEBSOCKET_MESSAGE_TYPES = {
	// Client to server
	PING: "ping",
	MESSAGE: "message",

	// Server to client
	PONG: "pong",
	CONNECTION_ESTABLISHED: "connection_established",
	THINKING_UPDATE: "thinking_update",
	TOOL_CALL_UPDATE: "tool_call_update",
	MESSAGE_CHUNK: "message_chunk",
	PRODUCT_RECOMMENDATIONS: "product_recommendations",
	ERROR: "error",
} as const;

export type WebSocketMessageType = (typeof WEBSOCKET_MESSAGE_TYPES)[keyof typeof WEBSOCKET_MESSAGE_TYPES];
