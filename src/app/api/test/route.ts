import { type NextRequest } from "next/server";

export async function GET() {
	return new Response("Test endpoint working!", { status: 200 });
}

export async function POST(req: NextRequest) {
	const body = await req.json();
	return new Response(JSON.stringify({ message: "Test POST working!", body }), {
		status: 200,
		headers: { "Content-Type": "application/json" },
	});
}
