"use client";

import Image from "next/image";
import { ArrowRight, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
// import { Card } from "@/components/ui/card";
// import { Badge } from "@/components/ui/badge";

export default function Hero() {
  return (
    // <section className="relative h-[70vh] w-full overflow-hidden md:h-[90vh]">
    <section className="relative mt-15 h-[69vh] w-full overflow-hidden md:h-[84vh]">
      <div className="flex h-full">
        {/* left panel */}
        <div className="flex flex-1 items-center bg-[#0f1619] text-white">
          <div className="mx-auto max-w-xl px-4 sm:px-8 md:px-14 " >
            <span className="inline-flex items-center gap-2 rounded-full bg-white px-4 py-1 text-sm font-semibold uppercase tracking-wide text-primary">
              <Image
                src="/clover-icon.png"
                alt="Clover icon"
                width={16}
                height={16}
                className="size-4"
                priority
              />
              New Spring Collection
            </span>

            {/* <h1 className="mt-1 font-[Phudu] text-3xl font-extrabold uppercase leading-tight tracking-tight sm:text-4xl md:text-6xl"> */}
            <h1 className="mt-4 font-[Phudu] text-3xl font-extrabold uppercase tracking-tight
             leading-[0.9]            /* <── 90 % line-height */
             sm:text-4xl  sm:leading-[0.9]
             md:text-6xl  md:leading-[0.9]">
              Gear Up For Your Next Adventure
            </h1>

            <p className="mt-3 max-w-md text-base text-white/80 md:text-lg">
              Discover premium outdoor equipment for every expedition, from
              mountain peaks to forest trails. Quality gear for unforgettable
              adventures.
            </p>

            <div className="mt-6 flex flex-wrap gap-4">
              {/* █████  PRIMARY – gradient green  █████ */}
              <Button
                size="lg"
                className="gap-2 rounded-[16px] px-6 py-4 font-bold uppercase tracking-wide text-white
                          bg-gradient-to-r from-[#01814E] to-[#75C566] hover:opacity-90"
              >
                Shop All Gear
                <ArrowRight className="size-5" />
              </Button>

              {/* █████  SECONDARY – frosted outline  █████ */}
              <Button
                // "ghost" keeps the radial-ring & focus styles from shadcn - we just override colours
                variant="ghost"
                size="lg"
                className="gap-2 rounded-[16px] px-6 py-4 font-bold uppercase tracking-wide
                          border border-white bg-white/25 backdrop-blur-lg text-white
                          hover:bg-white/30"
              >
                Explore Activities
                <Search className="size-5" />
              </Button>
            </div>
          </div>
        </div>

        {/* right panel */}
        <div className="relative flex-1">
          <Image
            src="https://images.unsplash.com/photo-1470770841072-f978cf4d019e?auto=format&fit=crop&w=1200&q=80"
            alt="Hikers climbing lush forest stairs"
            fill
            priority
            className="object-cover"
          />
        </div>
      </div>
    </section>
  );
}
