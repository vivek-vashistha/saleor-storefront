import { useEffect, useRef, useState, useCallback } from "react";
import { settings } from "@/config/settings";

export interface WebSocketMessage {
	type: string;
	[key: string]: any;
}

export interface WebSocketHookReturn {
	isConnected: boolean;
	sendMessage: (message: WebSocketMessage) => void;
	lastMessage: WebSocketMessage | null;
	connectionError: string | null;
	reconnect: () => void;
}

export const useWebSocket = (
	sessionId: string | null,
	onMessage?: (message: WebSocketMessage) => void,
): WebSocketHookReturn => {
	const [isConnected, setIsConnected] = useState(false);
	const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
	const [connectionError, setConnectionError] = useState<string | null>(null);
	const ws = useRef<WebSocket | null>(null);
	const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
	const reconnectAttempts = useRef(0);
	const maxReconnectAttempts = 3; // Reduced from 5 to prevent rapid cycling
	const reconnectDelay = 2000; // Increased from 1 second to 2 seconds
	const lastReconnectTime = useRef(0);
	const pingInterval = useRef<NodeJS.Timeout | null>(null);
	const PING_INTERVAL = 30000; // Ping every 30 seconds

	const connect = useCallback(() => {
		if (!sessionId) return;

		try {
			// Convert HTTP URL to WebSocket URL
			const wsUrl = settings.apiUrl.replace("http://", "ws://").replace("https://", "wss://");
			const wsEndpoint = `${wsUrl}/v1/sessions/${sessionId}/ws`;

			ws.current = new WebSocket(wsEndpoint);

			ws.current.onopen = () => {
				console.log("WebSocket connected");
				setIsConnected(true);
				setConnectionError(null);
				reconnectAttempts.current = 0;

				// Start ping interval to keep connection alive
				if (pingInterval.current) {
					clearInterval(pingInterval.current);
				}
				pingInterval.current = setInterval(() => {
					if (ws.current && ws.current.readyState === WebSocket.OPEN) {
						ws.current.send(JSON.stringify({ type: "ping" }));
					}
				}, PING_INTERVAL);
			};

			ws.current.onmessage = (event) => {
				try {
					const message: WebSocketMessage = JSON.parse(event.data);
					setLastMessage(message);
					onMessage?.(message);
				} catch (error) {
					console.error("Error parsing WebSocket message:", error);
				}
			};

			ws.current.onclose = (event) => {
				console.log("WebSocket disconnected:", event.code, event.reason);
				setIsConnected(false);

				// Only attempt to reconnect if not a normal closure and we haven't exceeded max attempts
				if (event.code !== 1000 && reconnectAttempts.current < maxReconnectAttempts) {
					const now = Date.now();
					const timeSinceLastReconnect = now - lastReconnectTime.current;

					// Prevent rapid reconnection attempts (minimum 5 seconds between attempts)
					if (timeSinceLastReconnect < 5000) {
						console.log("Too soon to reconnect, waiting...");
						return;
					}

					const delay = Math.min(reconnectDelay * Math.pow(1.5, reconnectAttempts.current), 10000); // Cap at 10 seconds
					console.log(`Attempting to reconnect in ${delay}ms (attempt ${reconnectAttempts.current + 1})`);

					lastReconnectTime.current = now;
					reconnectTimeoutRef.current = setTimeout(() => {
						reconnectAttempts.current++;
						connect();
					}, delay);
				} else if (reconnectAttempts.current >= maxReconnectAttempts) {
					setConnectionError("Failed to reconnect after multiple attempts");
				}
			};

			ws.current.onerror = (error) => {
				console.error("WebSocket error:", error);
				setConnectionError("WebSocket connection error");
			};
		} catch (error) {
			console.error("Error creating WebSocket connection:", error);
			setConnectionError("Failed to create WebSocket connection");
		}
	}, [sessionId, onMessage]);

	const disconnect = useCallback(() => {
		if (reconnectTimeoutRef.current) {
			clearTimeout(reconnectTimeoutRef.current);
			reconnectTimeoutRef.current = null;
		}

		if (pingInterval.current) {
			clearInterval(pingInterval.current);
			pingInterval.current = null;
		}

		if (ws.current) {
			ws.current.close(1000, "Manual disconnect");
			ws.current = null;
		}

		setIsConnected(false);
	}, []);

	const sendMessage = useCallback(
		(message: WebSocketMessage) => {
			if (!ws.current) {
				console.warn("WebSocket is not initialized. Cannot send message:", message);
				return;
			}

			if (ws.current.readyState === WebSocket.OPEN) {
				try {
					ws.current.send(JSON.stringify(message));
				} catch (error) {
					console.error("Error sending WebSocket message:", error);
					setConnectionError("Failed to send message");
				}
			} else if (ws.current.readyState === WebSocket.CONNECTING) {
				console.warn("WebSocket is still connecting. Message will be lost:", message);
			} else if (ws.current.readyState === WebSocket.CLOSING) {
				console.warn("WebSocket is closing. Message will be lost:", message);
			} else if (ws.current.readyState === WebSocket.CLOSED) {
				console.warn("WebSocket is closed. Attempting to reconnect...");
				// Trigger reconnection if the connection is closed
				if (reconnectAttempts.current < maxReconnectAttempts) {
					connect();
				}
			}
		},
		[connect],
	);

	const reconnect = useCallback(() => {
		disconnect();
		reconnectAttempts.current = 0;
		setConnectionError(null);
		connect();
	}, [disconnect, connect]);

	// Connect when sessionId changes
	useEffect(() => {
		if (sessionId) {
			connect();
		} else {
			disconnect();
		}

		return () => {
			disconnect();
		};
	}, [sessionId, connect, disconnect]);

	// Cleanup on unmount
	useEffect(() => {
		return () => {
			disconnect();
		};
	}, [disconnect]);

	return {
		isConnected,
		sendMessage,
		lastMessage,
		connectionError,
		reconnect,
	};
};
