import React from "react";

interface WebSocketStatusProps {
	isConnected: boolean;
	currentThinking?: string | null;
	toolCalls?: Array<{ name: string; status: string; data?: any }>;
	connectionError?: string | null;
	onReconnect?: () => void;
}

export const WebSocketStatus: React.FC<WebSocketStatusProps> = ({
	isConnected,
	currentThinking,
	toolCalls = [],
	connectionError,
	onReconnect,
}) => {
	const getStatusDot = () => {
		if (isConnected) {
			return <div className="h-2 w-2 rounded-full bg-green-500" />;
		}
		// Grey dot when not connected
		return <div className="h-2 w-2 rounded-full bg-gray-400" />;
	};

	return (
		<div className="flex items-center space-x-2">
			{getStatusDot()}
			{connectionError && onReconnect && (
				<button onClick={onReconnect} className="text-xs text-blue-500 underline hover:text-blue-700">
					Reconnect
				</button>
			)}

			{/* Connection Error Details */}
			{connectionError && <div className="rounded bg-red-50 p-2 text-xs text-red-500">{connectionError}</div>}
		</div>
	);
};
