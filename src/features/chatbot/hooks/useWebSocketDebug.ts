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
	debugLog: string[];
}

export const useWebSocketDebug = (
	sessionId: string | null,
	onMessage?: (message: WebSocketMessage) => void,
): WebSocketHookReturn => {
	const [isConnected, setIsConnected] = useState(false);
	const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
	const [connectionError, setConnectionError] = useState<string | null>(null);
	const [debugLog, setDebugLog] = useState<string[]>([]);
	const ws = useRef<WebSocket | null>(null);
	const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
	const reconnectAttempts = useRef(0);
	const maxReconnectAttempts = 5;
	const reconnectDelay = 1000; // Start with 1 second

	const addDebugLog = useCallback((message: string) => {
		const timestamp = new Date().toLocaleTimeString();
		const logMessage = `[${timestamp}] ${message}`;
		setDebugLog((prev) => [...prev, logMessage]);
		console.log(`[WebSocket Debug] ${logMessage}`);
	}, []);

	const connect = useCallback(() => {
		if (!sessionId) {
			addDebugLog("No session ID provided");
			return;
		}

		try {
			// Convert HTTP URL to WebSocket URL
			const wsUrl = settings.apiUrl.replace("http://", "ws://").replace("https://", "wss://");
			const wsEndpoint = `${wsUrl}/v1/sessions/${sessionId}/ws`;

			addDebugLog(`Attempting to connect to: ${wsEndpoint}`);
			ws.current = new WebSocket(wsEndpoint);

			ws.current.onopen = () => {
				addDebugLog("WebSocket connection opened");
				console.log("🔌 WebSocket connection opened");
				setIsConnected(true);
				setConnectionError(null);
				reconnectAttempts.current = 0;
			};

			ws.current.onmessage = (event) => {
				addDebugLog(`Received message: ${event.data}`);
				try {
					const message: WebSocketMessage = JSON.parse(event.data);
					setLastMessage(message);
					onMessage?.(message);
				} catch (error) {
					addDebugLog(`Error parsing message: ${error}`);
					console.error("Error parsing WebSocket message:", error);
				}
			};

			ws.current.onclose = (event) => {
				addDebugLog(`WebSocket closed: ${event.code} - ${event.reason}`);
				setIsConnected(false);

				// Attempt to reconnect if not a normal closure
				if (event.code !== 1000 && reconnectAttempts.current < maxReconnectAttempts) {
					const delay = reconnectDelay * Math.pow(2, reconnectAttempts.current);
					addDebugLog(`Attempting to reconnect in ${delay}ms (attempt ${reconnectAttempts.current + 1})`);

					reconnectTimeoutRef.current = setTimeout(() => {
						reconnectAttempts.current++;
						connect();
					}, delay);
				} else if (reconnectAttempts.current >= maxReconnectAttempts) {
					setConnectionError("Failed to reconnect after multiple attempts");
					addDebugLog("Max reconnection attempts reached");
				}
			};

			ws.current.onerror = (error) => {
				addDebugLog(`WebSocket error: ${error}`);
				console.error("WebSocket error:", error);
				setConnectionError("WebSocket connection error");
			};
		} catch (error) {
			addDebugLog(`Connection error: ${error}`);
			console.error("Error creating WebSocket connection:", error);
			setConnectionError("Failed to create WebSocket connection");
		}
	}, [sessionId, onMessage, addDebugLog]);

	const disconnect = useCallback(() => {
		addDebugLog("Disconnecting WebSocket");
		if (reconnectTimeoutRef.current) {
			clearTimeout(reconnectTimeoutRef.current);
			reconnectTimeoutRef.current = null;
		}

		if (ws.current) {
			ws.current.close(1000, "Manual disconnect");
			ws.current = null;
		}

		setIsConnected(false);
	}, [addDebugLog]);

	const sendMessage = useCallback(
		(message: WebSocketMessage) => {
			if (ws.current && ws.current.readyState === WebSocket.OPEN) {
				const messageStr = JSON.stringify(message);
				addDebugLog(`Sending message: ${messageStr}`);
				ws.current.send(messageStr);
			} else {
				addDebugLog("WebSocket is not connected. Cannot send message");
				console.warn("WebSocket is not connected. Cannot send message:", message);
			}
		},
		[addDebugLog],
	);

	const reconnect = useCallback(() => {
		addDebugLog("Manual reconnect requested");
		disconnect();
		reconnectAttempts.current = 0;
		setConnectionError(null);
		connect();
	}, [disconnect, connect, addDebugLog]);

	// Connect when sessionId changes
	useEffect(() => {
		if (sessionId) {
			addDebugLog(`Session ID changed to: ${sessionId}`);
			connect();
		} else {
			addDebugLog("No session ID, disconnecting");
			disconnect();
		}

		return () => {
			disconnect();
		};
	}, [sessionId, connect, disconnect, addDebugLog]);

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
		debugLog,
	};
};
