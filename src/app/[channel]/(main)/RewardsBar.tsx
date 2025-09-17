import { Star, Tag, CreditCard, Gift } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";


export default function RewardsBar() {
  return (
    <Card 
      className="relative z-10 w-full bg-white shadow-sm rounded-none"
    >
      <CardContent
        // className="max-w-screen-2xl w-full px-4 md:px-15" 
        className=" w-full pl-15" 
      >
        <div className="grid w-full gap-x-6 md:gap-x-10 items-center" style={{ gridTemplateColumns: "auto 1fr" }}>
          {/* OUTDOOR REWARDS - Now in grid */}
          <div className="flex flex-col sm:flex-row items-center gap-2 text-center sm:text-left">
            <Star className="size-6 text-foreground flex-shrink-0" />
            <span className="text-xl md:text-2xl font-bold uppercase tracking-wide text-foreground">
              Outdoor Rewards
            </span>
          </div>

          <div className="grid grid-cols-3 gap-x-10 md:gap-x-10 pl-25 w-full">
            {/* Members save… */}
            <div className="flex flex-col sm:flex-row items-center gap-2 text-center sm:text-left text-sm text-muted-foreground pr-10">
              <Tag className="size-6 text-foreground flex-shrink-0" />
              <span className="text-base md:text-lg">
                Members save 20% on all full‑price items
              </span>
            </div>

            {/* Earn 5% back… */}
            <div className="flex flex-col sm:flex-row items-center gap-2 text-center sm:text-left text-sm text-muted-foreground pr-10">
              <CreditCard className="size-6 text-foreground flex-shrink-0" />
              <span className="text-base md:text-lg">
                Earn 5% back on purchases with our credit card
              </span>
            </div>

            {/* Free shipping… */}
            <div className="flex flex-col sm:flex-row items-center gap-2 text-center sm:text-left text-sm text-muted-foreground pr-10">
              <Gift className="size-6 text-foreground flex-shrink-0" />
              <span className="text-base md:text-lg">
                Free shipping on orders over $50
              </span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}