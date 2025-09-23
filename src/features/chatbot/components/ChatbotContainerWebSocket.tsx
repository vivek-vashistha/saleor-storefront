"use client";

import React, { useEffect, useRef, useState } from "react";
import Image from "next/image";
import { X as CloseIcon, Maximize2 as OpenIcon, Minimize2 as CloseFullscreenIcon } from "lucide-react";

import { useChatSessionWebSocket } from "../hooks/useChatSessionWebSocket";
import { ChatInput } from "./ChatInput";
import ChatMessages from "./ChatMessages";
import { MemoizedProductPanel } from "./ProductPanel";
import { UserDisplay } from "./UserDisplay";
import { WebSocketStatus } from "./WebSocketStatus";
import { StreamingMessage } from "./StreamingMessage";
import { cn } from "@/lib/utils";
import { useChatControls } from "@/context/ChatControlsContext";
import { Button } from "@/components/ui/button";

export const ChatbotContainerWebSocket: React.FC = () => {
	const { isOpen, isMaximized, toggleChatSize, openChat, closeChat } = useChatControls();
	const [isAnimating, setIsAnimating] = useState(false);
	const messagesEndRef = useRef<HTMLDivElement>(null);
	const sheetContentRef = useRef<HTMLDivElement>(null);

	const {
		messages,
		isLoading,
		allBundles,
		messageType,
		productMessageTimestamp,
		userHasSentMessage,
		conversationId,
		sendMessage,
		initializeSession,
		deleteSessionIfUnused,
		productSuggestions,
		// WebSocket specific
		isWebSocketConnected,
		currentThinking,
		toolCalls,
		streamingMessage,
		isStreaming,
		connectionError,
		reconnect,
	} = useChatSessionWebSocket({
		onMaximize: () => {
			if (!isMaximized) {
				setIsAnimating(true);
				setTimeout(() => {
					toggleChatSize();
					setTimeout(() => {
						setIsAnimating(false);
					}, 850);
				}, 150);
			}
		},
		isMaximized,
	});

	const hasProductBundles = allBundles.length > 0;

	// scroll to bottom
	const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
	useEffect(scrollToBottom, [messages, streamingMessage]);

	// manage session lifecycle
	useEffect(() => {
		if (isOpen && !conversationId) void initializeSession();
		if (!isOpen && conversationId && !userHasSentMessage) void deleteSessionIfUnused();
	}, [isOpen, conversationId, userHasSentMessage, initializeSession, deleteSessionIfUnused]);

	// reset overflow hack
	useEffect(() => {
		document.body.style.overflow = "";
		return () => {
			document.body.style.overflow = "";
		};
	}, []);

	const handleToggleChatSize = () => {
		setIsAnimating(true);
		toggleChatSize();
		setTimeout(() => {
			setIsAnimating(false);
		}, 850);
	};

	const handleCloseChat = () => {
		setIsAnimating(true);
		closeChat();
		setTimeout(() => {
			setIsAnimating(false);
		}, 300);
	};

	// Enhanced messages with streaming support
	const enhancedMessages = [...messages];
	if (streamingMessage && isStreaming) {
		enhancedMessages.push({
			type: "bot",
			content: streamingMessage,
			timestamp: new Date().toISOString(),
			isStreaming: true,
		});
	}

	return (
		<div className="fixed bottom-4 right-4 z-50">
			{!isOpen ? (
				<Button
					onClick={openChat}
					className="h-14 w-14 rounded-full bg-blue-600 shadow-lg transition-all duration-300 hover:scale-105 hover:bg-blue-700"
					size="icon"
				>
					<Image src="/clover-icon.svg" alt="Chat" width={24} height={24} className="text-white" />
				</Button>
			) : (
				<div
					className={cn(
						"rounded-lg border border-gray-200 bg-white shadow-2xl transition-all duration-500 ease-in-out",
						isMaximized ? "h-[90vh] w-[90vw] max-w-6xl" : "h-[600px] max-h-[80vh] w-96",
						isAnimating && "scale-95 transform opacity-90",
					)}
				>
					{/* Header */}
					<div className="flex items-center justify-between rounded-t-lg border-b border-gray-200 bg-gradient-to-r from-blue-600 to-blue-700 p-4 text-white">
						<div className="flex items-center space-x-3">
							<Image src="/clover-icon.svg" alt="Chat" width={24} height={24} className="text-white" />
							<div>
								<h3 className="text-lg font-semibold">AI Assistant</h3>
								<WebSocketStatus
									isConnected={isWebSocketConnected}
									currentThinking={currentThinking}
									toolCalls={toolCalls}
									connectionError={connectionError}
									onReconnect={reconnect}
								/>
							</div>
						</div>
						<div className="flex items-center space-x-2">
							<Button
								onClick={handleToggleChatSize}
								variant="ghost"
								size="icon"
								className="text-white hover:bg-white/20"
							>
								{isMaximized ? <CloseFullscreenIcon className="h-4 w-4" /> : <OpenIcon className="h-4 w-4" />}
							</Button>
							<Button
								onClick={handleCloseChat}
								variant="ghost"
								size="icon"
								className="text-white hover:bg-white/20"
							>
								<CloseIcon className="h-4 w-4" />
							</Button>
						</div>
					</div>

					{/* User Display */}
					<div className="border-b border-gray-100 p-3">
						<UserDisplay />
					</div>

					{/* Messages Container */}
					<div
						ref={sheetContentRef}
						className="flex-1 space-y-4 overflow-y-auto p-4"
						style={{ height: isMaximized ? "calc(90vh - 200px)" : "400px" }}
					>
						{enhancedMessages.length === 0 ? (
							<div className="py-8 text-center text-gray-500">
								<p className="text-lg font-medium">Welcome! 👋</p>
								<p className="mt-2 text-sm">
									I'm here to help you find the perfect products. What are you looking for today?
								</p>
							</div>
						) : (
							enhancedMessages.map((message, index) => (
								<div key={index} className="flex flex-col space-y-2">
									{message.type === "user" ? (
										<div className="flex justify-end">
											<div className="max-w-[80%] rounded-lg bg-blue-600 px-4 py-2 text-white">
												<p className="text-sm">{message.content}</p>
											</div>
										</div>
									) : (
										<div className="flex justify-start">
											<div className="max-w-[80%] rounded-lg bg-gray-100 px-4 py-2 text-gray-800">
												{message.isStreaming ? (
													<StreamingMessage content={message.content} isStreaming={isStreaming} />
												) : (
													<p className="whitespace-pre-wrap text-sm">{message.content}</p>
												)}
												{message.isError && <p className="mt-1 text-xs text-red-500">⚠️ Error occurred</p>}
											</div>
										</div>
									)}
								</div>
							))
						)}

						{/* Loading indicator */}
						{isLoading && !isStreaming && (
							<div className="flex justify-start">
								<div className="rounded-lg bg-gray-100 px-4 py-2 text-gray-800">
									<div className="flex items-center space-x-2">
										<div className="h-4 w-4 animate-spin rounded-full border-b-2 border-blue-600"></div>
										<span className="text-sm">Thinking...</span>
									</div>
								</div>
							</div>
						)}

						<div ref={messagesEndRef} />
					</div>

					{/* Product Panel */}
					{hasProductBundles && (
						<div className="border-t border-gray-200">
							<MemoizedProductPanel
								bundles={allBundles}
								messageType={messageType}
								timestamp={productMessageTimestamp}
							/>
						</div>
					)}

					{/* Product Suggestions */}
					{productSuggestions.length > 0 && (
						<div className="border-t border-gray-200 p-4">
							<h4 className="mb-2 font-medium text-gray-800">Recommended Products</h4>
							<div className="grid grid-cols-1 gap-2">
								{productSuggestions.slice(0, 3).map((product, index) => (
									<div key={index} className="rounded bg-gray-50 p-2 text-sm text-gray-600">
										{product.name}
									</div>
								))}
							</div>
						</div>
					)}

					{/* Input */}
					<div className="border-t border-gray-200 p-4">
						<ChatInput isLoading={isLoading} onSendMessage={sendMessage} products={productSuggestions} />
					</div>
				</div>
			)}
		</div>
	);
};
