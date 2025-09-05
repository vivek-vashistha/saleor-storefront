"use client";

import { type ReactNode } from "react";
import { CopilotKit } from "@copilotkit/react-core"; // Correct import!
import "@copilotkit/react-ui/styles.css";
import { ChatPopup } from "../components/CopilotPopup";

const runtimeUrl =
	process.env.NEXT_PUBLIC_COPILOTKIT_RUNTIME_URL || "http://localhost:8000/v1/chat/completions";

export function ClientProviders({ children }: { children: ReactNode }) {
	return (
		<CopilotKit runtimeUrl={runtimeUrl} showDevConsole={true}>
			{children}
			<ChatPopup />
		</CopilotKit>
	);
}
