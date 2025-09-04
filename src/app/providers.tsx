"use client";

import { type ReactNode } from "react";
import { CopilotKit } from "@copilotkit/react-core"; // Correct import!
import "@copilotkit/react-ui/styles.css";
import { ChatPopup } from "../components/CopilotPopup";

const runtimeUrl = process.env.NEXT_PUBLIC_COPILOTKIT_RUNTIME_URL;

export function ClientProviders({ children }: { children: ReactNode }) {
	return (
		// <CopilotKit runtimeUrl="http://localhost:8000">
		<CopilotKit
			// Some package versions still type this prop loosely; it *is* required at runtime.
			// eslint-disable-next-line @typescript-eslint/ban-ts-comment
			// @ts-ignore
			runtimeUrl={runtimeUrl}
			agent="shopAgent"
			showDevConsole={false}
		>
			{children}
			<ChatPopup />
		</CopilotKit>
	);
}
