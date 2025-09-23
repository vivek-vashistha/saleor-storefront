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
	const maxReconnectAttempts = 5;
	const reconnectDelay = 1000; // Start with 1 second

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

				// Attempt to reconnect if not a normal closure
				if (event.code !== 1000 && reconnectAttempts.current < maxReconnectAttempts) {
					const delay = reconnectDelay * Math.pow(2, reconnectAttempts.current);
					console.log(`Attempting to reconnect in ${delay}ms (attempt ${reconnectAttempts.current + 1})`);

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

		if (ws.current) {
			ws.current.close(1000, "Manual disconnect");
			ws.current = null;
		}

		setIsConnected(false);
	}, []);

	const sendMessage = useCallback((message: WebSocketMessage) => {
		if (ws.current && ws.current.readyState === WebSocket.OPEN) {
			ws.current.send(JSON.stringify(message));
		} else {
			console.warn("WebSocket is not connected. Cannot send message:", message);
		}
	}, []);

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
