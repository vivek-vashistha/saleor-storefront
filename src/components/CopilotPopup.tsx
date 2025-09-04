"use client";

import { CopilotPopup } from "@copilotkit/react-ui";
import { useCopilotAction } from "@copilotkit/react-core";

export function ChatPopup() {
	useCopilotAction({
		name: "sendMessage",
		description: "Send a message to backend session",
		parameters: [
			{ name: "sessionId", type: "string" },
			{ name: "message", type: "string" },
		],
		handler: async ({ sessionId, message }) => {
			await fetch(`http://localhost:8000/v1/sessions/${sessionId}/message`, {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({ message }),
			});
		},
	});

	return (
		<>
			<CopilotPopup instructions="You are a helpful shopping assistant for the Saleor storefront. Help users with product searches, recommendations, and general shopping questions." />
		</>
	);
}
