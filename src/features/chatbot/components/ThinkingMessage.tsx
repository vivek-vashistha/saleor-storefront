import React from "react";
import { Loader2 } from "lucide-react";

interface ThinkingMessageProps {
	thinking: string;
	toolCalls?: Array<{ name: string; status: string; data?: any }>;
}

export const ThinkingMessage: React.FC<ThinkingMessageProps> = ({ thinking, toolCalls = [] }) => {
	return (
		<div className="mb-2 flex justify-start">
			<div className="max-w-[80%] rounded-lg bg-gray-100 px-4 py-2 text-gray-800">
				<div className="flex items-center space-x-2">
					<Loader2 className="h-4 w-4 animate-spin text-blue-600" />
					<span className="text-sm font-medium text-blue-600">{thinking}</span>
				</div>

				{/* Tool Call Progress */}
				{toolCalls.length > 0 && (
					<div className="mt-2 space-y-1">
						{toolCalls.map((tool, index) => (
							<div key={index} className="flex items-center space-x-2 text-xs text-gray-600">
								<div
									className={`h-1.5 w-1.5 rounded-full ${
										tool.status === "completed"
											? "bg-green-500"
											: tool.status === "started"
												? "bg-yellow-500"
												: "bg-gray-400"
									}`}
								/>
								<span>{tool.name}</span>
								{tool.status === "started" && <span className="text-gray-500">...</span>}
								{tool.status === "completed" && <span className="text-green-600">✓</span>}
							</div>
						))}
					</div>
				)}
			</div>
		</div>
	);
};

export default ThinkingMessage;
