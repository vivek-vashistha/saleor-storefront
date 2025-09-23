import React, { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";

interface StreamingMessageProps {
	content: string;
	isStreaming: boolean;
	onComplete?: () => void;
}

export const StreamingMessage: React.FC<StreamingMessageProps> = ({ content, isStreaming, onComplete }) => {
	const [displayedContent, setDisplayedContent] = useState("");
	const [currentIndex, setCurrentIndex] = useState(0);

	useEffect(() => {
		if (content && currentIndex < content.length) {
			const timer = setTimeout(() => {
				setDisplayedContent((prev) => prev + content[currentIndex]);
				setCurrentIndex((prev) => prev + 1);
			}, 20); // Adjust speed as needed

			return () => clearTimeout(timer);
		} else if (content && currentIndex >= content.length && isStreaming) {
			// Streaming is complete
			onComplete?.();
		}
	}, [content, currentIndex, isStreaming, onComplete]);

	// Reset when content changes
	useEffect(() => {
		setDisplayedContent("");
		setCurrentIndex(0);
	}, [content]);

	return (
		<div className="flex items-start space-x-2">
			<div className="flex-1">
				<div className="whitespace-pre-wrap text-gray-800">
					{displayedContent}
					{isStreaming && <span className="ml-1 inline-block h-4 w-2 animate-pulse bg-gray-400" />}
				</div>
			</div>
			{isStreaming && <Loader2 className="mt-1 h-4 w-4 flex-shrink-0 animate-spin text-gray-400" />}
		</div>
	);
};
