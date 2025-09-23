import { Star, Tag, CreditCard, Gift } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

export default function RewardsBar() {
	return (
		<Card className="relative z-10 w-full rounded-none bg-white shadow-sm">
			<CardContent
				// className="max-w-screen-2xl w-full px-4 md:px-15"
				className=" pl-15 w-full"
			>
				<div
					className="grid w-full items-center gap-x-6 md:gap-x-10"
					style={{ gridTemplateColumns: "auto 1fr" }}
				>
					{/* OUTDOOR REWARDS - Now in grid */}
					<div className="flex flex-col items-center gap-2 text-center sm:flex-row sm:text-left">
						<Star className="size-6 flex-shrink-0 text-foreground" />
						<span className="text-xl font-bold uppercase tracking-wide text-foreground md:text-2xl">
							GRAB Rewards
						</span>
					</div>

					<div className="pl-25 grid w-full grid-cols-3 gap-x-10 md:gap-x-10">
						{/* Members save… */}
						<div className="flex flex-col items-center gap-2 pr-10 text-center text-sm text-muted-foreground sm:flex-row sm:text-left">
							<Tag className="size-6 flex-shrink-0 text-foreground" />
							<span className="text-base md:text-lg">Members save 20% on all full‑price items</span>
						</div>

						{/* Earn 5% back… */}
						<div className="flex flex-col items-center gap-2 pr-10 text-center text-sm text-muted-foreground sm:flex-row sm:text-left">
							<CreditCard className="size-6 flex-shrink-0 text-foreground" />
							<span className="text-base md:text-lg">Earn 5% back on purchases with our credit card</span>
						</div>

						{/* Free shipping… */}
						<div className="flex flex-col items-center gap-2 pr-10 text-center text-sm text-muted-foreground sm:flex-row sm:text-left">
							<Gift className="size-6 flex-shrink-0 text-foreground" />
							<span className="text-base md:text-lg">Free shipping on orders over $50</span>
						</div>
					</div>
				</div>
			</CardContent>
		</Card>
	);
}
