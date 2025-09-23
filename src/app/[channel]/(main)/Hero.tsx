"use client";

import Image from "next/image";
import { ArrowRight, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
// import { Card } from "@/components/ui/card";
// import { Badge } from "@/components/ui/badge";

export function Hero() {
	return (
		// <section className="relative h-[70vh] w-full overflow-hidden md:h-[90vh]">
		<section className="mt-15 relative h-[69vh] w-full overflow-hidden md:h-[84vh]">
			<div className="flex h-full">
				{/* left panel */}
				<div className="flex flex-1 items-center bg-[#0f1619] text-white">
					<div className="mx-auto max-w-xl px-4 sm:px-8 md:px-14 ">
						<span className="inline-flex items-center gap-2 rounded-full bg-white px-4 py-1 text-sm font-semibold uppercase tracking-wide text-primary">
							<Image
								src="/clover-icon.png"
								alt="iHerb icon"
								width={16}
								height={16}
								className="size-4"
								priority
							/>
							Natural Health & Wellness
						</span>

						{/* <h1 className="mt-1 font-[Phudu] text-3xl font-extrabold uppercase leading-tight tracking-tight sm:text-4xl md:text-6xl"> */}
						<h1
							className="/* <── 90 % line-height */
             mt-4            font-[Phudu] text-3xl font-extrabold uppercase leading-[0.9] tracking-tight
             sm:text-4xl  sm:leading-[0.9]
             md:text-6xl  md:leading-[0.9]"
						>
							Nourish Your Health Journey
						</h1>

						<p className="mt-3 max-w-md text-base text-white/80 md:text-lg">
							Discover premium vitamins, supplements, and natural health products to support your wellness
							journey. Quality nutrition for a healthier life.
						</p>

						<div className="mt-6 flex flex-wrap gap-4">
							{/* █████  PRIMARY – gradient green  █████ */}
							<Button
								size="lg"
								className="gap-2 rounded-[16px] bg-gradient-to-r from-[#01814E] to-[#75C566] px-6 py-4 font-bold
                          uppercase tracking-wide text-white hover:opacity-90"
							>
								Shop Vitamins & Supplements
								<ArrowRight className="size-5" />
							</Button>

							{/* █████  SECONDARY – frosted outline  █████ */}
							<Button
								// "ghost" keeps the radial-ring & focus styles from shadcn - we just override colours
								variant="ghost"
								size="lg"
								className="gap-2 rounded-[16px] border border-white bg-white/25 px-6 py-4
                          font-bold uppercase tracking-wide text-white backdrop-blur-lg
                          hover:bg-white/30"
							>
								Browse Health Categories
								<Search className="size-5" />
							</Button>
						</div>
					</div>
				</div>

				{/* right panel */}
				<div className="relative flex-1">
					<Image
						src="https://images.unsplash.com/photo-1562751362-404243c2eea3?q=80&w=3087&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D"
						alt="Healthy lifestyle with vitamins and supplements"
						fill
						priority
						className="object-cover"
					/>
				</div>
			</div>
		</section>
	);
}
