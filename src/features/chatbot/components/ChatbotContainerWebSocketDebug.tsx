"use client";

import React, { useEffect, useRef, useState } from "react";
import Image from "next/image";
import { X as CloseIcon, Maximize2 as OpenIcon, Minimize2 as CloseFullscreenIcon } from "lucide-react";

import { useChatSessionWebSocketDebug } from "../hooks/useChatSessionWebSocketDebug";
import { ChatInput } from "./ChatInput";
import ChatMessages from "./ChatMessages";
import { MemoizedProductPanel } from "./ProductPanel";
import { UserDisplay } from "./UserDisplay";
import { WebSocketStatus } from "./WebSocketStatus";
import { StreamingMessage } from "./StreamingMessage";
import { cn } from "@/lib/utils";
import { useChatControls } from "@/context/ChatControlsContext";
import { Button } from "@/components/ui/button";

export const ChatbotContainerWebSocketDebug: React.FC = () => {
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
		debugLog,
	} = useChatSessionWebSocketDebug({
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

	// Implement sliding window for performance (only show last 50 messages)
	const MESSAGE_WINDOW_SIZE = 50;
	const visibleMessages = enhancedMessages.slice(-MESSAGE_WINDOW_SIZE);

	return (
		<>
			{/* Launcher: badge (when closed) + button, aligned together */}
			<div className="fixed bottom-4 right-4 z-[1300] flex items-center gap-2">
				{!isOpen && (
					<div className="flex max-w-[180px] items-center gap-2 rounded-full bg-[#176142] px-2 py-1.5 text-white shadow-md">
						<p className="font-sans text-xs font-medium">Need help?</p>
					</div>
				)}
				<Button
					onClick={isOpen ? closeChat : openChat}
					className={`flex items-center justify-center rounded-full text-white shadow-lg ${
						isOpen ? "h-12 w-12" : "h-16 w-16"
					} ${
						isOpen
							? "bg-[#64748B] hover:bg-[#64748B]"
							: "bg-gradient-to-r from-[#75C566] to-[#01814E] hover:opacity-90"
					}`}
					aria-label={isOpen ? "Close chat" : "Open chat"}
					aria-expanded={isOpen}
					aria-controls="chatbot-panel"
				>
					{isOpen ? (
						<CloseIcon className="h-6 w-6" />
					) : (
						<Image src="/message.svg" alt="Chat" width={24} height={24} />
					)}
				</Button>
			</div>

			{isOpen && (
				<div
					id="chatbot-panel"
					role="dialog"
					aria-modal="true"
					aria-labelledby="chatbot-title"
					className={cn(
						"fixed z-[1300]",
						isMaximized ? "right-4 top-20 h-auto" : "bottom-20 right-4 w-[90vw] sm:w-[300px] md:w-[500px]",
					)}
					style={{
						transition: isAnimating ? "all 0.8s cubic-bezier(0.34,1.56,0.64,1)" : "all 0.3s ease",
					}}
				>
					<div
						className={cn(
							"flex h-full flex-col overflow-hidden border border-border bg-background shadow-lg",
							isMaximized ? "rounded-2xl" : "rounded-xl",
						)}
						style={{
							transition: isAnimating ? "all 0.8s cubic-bezier(0.34,1.56,0.64,1)" : "all 0.3s ease",
							height: isMaximized ? "calc(100vh - 6rem)" : "600px",
							width: isMaximized ? "97vw" : "auto",
							right: "4rem",
						}}
						ref={sheetContentRef}
					>
						{/* ─── MAIN CONTENT ─────────────────────────── */}
						<div className="flex h-full overflow-hidden">
							{/* ── LEFT PANE (chat + header + input) ─────── */}
							<div
								className={
									isMaximized && hasProductBundles
										? "flex h-full w-2/5 flex-none flex-col"
										: "flex h-full flex-1 flex-col"
								}
							>
								{/* header now lives inside left pane */}
								{isMaximized ? (
									<div className="flex flex-none flex-col border-b border-border">
										<div className="flex items-center justify-between p-3">
											<div className="flex items-center space-x-1">
												<Button
													variant="default"
													size="icon"
													onClick={closeChat}
													className="bg-transparent text-[#020617] hover:bg-white/10"
													aria-label="Close chat"
												>
													<CloseIcon className="h-5 w-5" />
												</Button>
												<Button
													variant="default"
													size="icon"
													onClick={handleToggleChatSize}
													className="bg-transparent text-[#020617] hover:bg-white/10"
													aria-label="Minimize chat"
												>
													<CloseFullscreenIcon className="h-5 w-5" />
												</Button>
											</div>
											{/* WebSocket Status in maximized view */}
											<div className="flex items-center space-x-2">
												<span className="font-sans text-sm font-medium text-[#020617]">
													I-HERB SUPPLEMENTS ADVISOR
												</span>
												<WebSocketStatus
													isConnected={isWebSocketConnected}
													currentThinking={currentThinking}
													toolCalls={toolCalls}
													connectionError={connectionError}
													onReconnect={reconnect}
												/>
											</div>
										</div>
										<UserDisplay />
									</div>
								) : (
									<div className="flex flex-none flex-col border-b border-border">
										<header className="flex items-center justify-between bg-[#E2E8F0] p-3">
											<div className="flex items-center space-x-1">
												<Button
													variant="default"
													size="icon"
													onClick={closeChat}
													className="bg-transparent text-[#020617] hover:bg-white/10"
													aria-label="Close chat"
												>
													<CloseIcon className="h-5 w-5" />
												</Button>
												<Button
													variant="default"
													size="icon"
													onClick={handleToggleChatSize}
													className="bg-transparent text-[#020617] hover:bg-white/10"
													aria-label="Maximize chat"
												>
													<OpenIcon className="h-5 w-5" />
												</Button>
											</div>
											<div className="flex items-center space-x-2">
												<h6 id="chatbot-title" className="font-sans text-lg font-semibold text-[#020617]">
													I-HERB SUPPLEMENTS ADVISOR
												</h6>
												<WebSocketStatus
													isConnected={isWebSocketConnected}
													currentThinking={currentThinking}
													toolCalls={toolCalls}
													connectionError={connectionError}
													onReconnect={reconnect}
												/>
											</div>
										</header>
										<UserDisplay />
									</div>
								)}

								{/* messages scroll */}
								<ChatMessages
									messages={visibleMessages}
									isLoading={isLoading}
									productMessageTimestamp={productMessageTimestamp}
									messagesEndRef={messagesEndRef as React.RefObject<HTMLDivElement>}
									className="flex-1 overflow-y-auto"
								/>

								{/* input at bottom */}
								<div className="flex-none border-t border-border bg-white p-3">
									<ChatInput
										isLoading={isLoading}
										onSendMessage={sendMessage}
										products={productSuggestions}
									/>
								</div>
							</div>

							{/* ── RIGHT PANE (product bundles) ────────── */}
							{isMaximized && hasProductBundles && (
								<div
									className="flex w-3/5 flex-none flex-col overflow-hidden border-l border-border bg-[#F5F5F5]"
									aria-label="Product recommendations"
								>
									<MemoizedProductPanel allBundles={allBundles} messageType={messageType} />
								</div>
							)}
						</div>
					</div>
				</div>
			)}

			{/* typing indicator styles */}
			<style jsx global>{`
				.typing-indicator {
					display: flex;
					align-items: center;
				}
				.typing-indicator span {
					height: 8px;
					width: 8px;
					background-color: currentColor;
					border-radius: 50%;
					margin: 0 2px;
					opacity: 0.6;
					display: inline-block;
					animation: typing 1.4s infinite ease-in-out both;
				}
				.typing-indicator span:nth-child(1) {
					animation-delay: 0s;
				}
				.typing-indicator span:nth-child(2) {
					animation-delay: 0.2s;
				}
				.typing-indicator span:nth-child(3) {
					animation-delay: 0.4s;
				}
				@keyframes typing {
					0% {
						transform: scale(1);
					}
					50% {
						transform: scale(1.5);
					}
					100% {
						transform: scale(1);
					}
				}
			`}</style>
		</>
	);
};
