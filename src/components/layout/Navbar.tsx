"use client";

import * as React from "react";
import Link from "next/link";
import { Menu, Search, Heart, User } from "lucide-react";

import {
  NavigationMenu,
  NavigationMenuList,
  NavigationMenuItem,
  NavigationMenuLink,
} from "@/components/ui/navigation-menu";
import {
  Sheet,
  SheetTrigger,
  SheetContent,
  SheetClose,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Cart } from "@/features/cart/components";
import { cn } from "@/lib/utils";
import { useUser } from "@/context/UserContext";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";

const navItems = [
  { label: "New Arrivals", href: "#" },
  { label: "Gear", href: "#" },
  { label: "Clothing", href: "#" },
  { label: "Footwear", href: "#" },
  { label: "Sale", href: "#" },
];

export default function Navbar() {
  const { user } = useUser();
  const [isMobile, setIsMobile] = React.useState(false);
  React.useEffect(() => {
    const onResize = () => setIsMobile(window.innerWidth < 768);
    onResize();
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  return (
    <header className="fixed inset-x-0 top-0 z-50">
      <div className="flex h-16 items-center bg-white px-4 md:px-6 border-b border-border/30">
        {/* ═════════════ LEFT CLUSTER ═════════════ */}
        <div className="flex items-center gap-5">
          {/* ── mobile burger ── */}
          {isMobile && (
            <Sheet>
              <SheetTrigger asChild>
                <Button variant="ghost" size="icon" aria-label="Open menu">
                  <Menu className="size-5" />
                </Button>
              </SheetTrigger>

              <SheetContent side="left" className="w-64 p-0">
                <nav className="flex h-full flex-col">
                  {navItems.map((item) => (
                    <SheetClose asChild key={item.label}>
                      <Link
                        href={item.href}
                        className="block w-full px-6 py-4 text-lg font-medium hover:bg-muted"
                      >
                        {item.label}
                      </Link>
                    </SheetClose>
                  ))}
                </nav>
              </SheetContent>
            </Sheet>
          )}

          {/* ── logo ── */}
          <Link href="/" className="flex items-center gap-3">
          <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 16 16"
              fill="currentColor"
              className="h-10 w-10 shrink-0 text-primary"
            >
              <path
                fillRule="evenodd"
                d="M7.022 1.566a1.13 1.13 0 0 1 1.96 0l6.857 11.667c.457.778-.092 1.767-.98 1.767H1.144c-.889 0-1.437-.99-.98-1.767z"
              />
            </svg>
            {/* ── stacked word-mark ── */}
            <span className="flex flex-col leading-none text-primary">
              {/* 26 px ≈ 1.625 rem */}
              <span className="font-[Phudu] text-[1.325rem] font-extrabold uppercase tracking-wide leading-none">
                Adventure
              </span>
              {/* pull “STORE” up by 2 px to kiss-fit the two lines */}
              <span className="-mt-[2px] font-[Phudu] text-[1.325rem] font-extrabold uppercase tracking-wide leading-none">
                Store
              </span>
            </span>
          </Link>

          {/* ── desktop nav ── */}
          {/* {!isMobile && (
            <NavigationMenu>
              <NavigationMenuList>
                {navItems.map((item) => (
                  <NavigationMenuItem key={item.label}>
                    <NavigationMenuLink asChild>
                      <Link
                        href={item.href}
                        className={cn(
                          "px-3 py-2 text-sm font-medium transition-colors",
                          "hover:text-foreground/80 focus:text-foreground"
                        )}
                      >
                        {item.label}
                      </Link>
                    </NavigationMenuLink>
                  </NavigationMenuItem>
                ))}
              </NavigationMenuList>
            </NavigationMenu>
          )} */}
          {!isMobile && (
            <NavigationMenu
              /** ➊ give the list a left-margin so it clears the logo */
              className="ml-14"
            >
              <NavigationMenuList
                /** ➋ space links out evenly */
                className="space-x-10"
              >
                {navItems.map((item) => (
                  <NavigationMenuItem key={item.label}>
                    <NavigationMenuLink asChild>
                      <Link
                        href={item.href}
                        className={cn(
                          /* keep the old padding for click target */
                          "px-3 py-2 text-sm font-medium transition-colors",
                          "hover:text-foreground/80 focus:text-foreground"
                        )}
                      >
                        {item.label}
                      </Link>
                    </NavigationMenuLink>
                  </NavigationMenuItem>
                ))}
              </NavigationMenuList>
            </NavigationMenu>
          )}
        </div>

        {/* ═════════════ RIGHT CLUSTER ═════════════ */}
        <div className="ml-auto flex items-center gap-2">
          {/* search (hidden below md) */}
          <div className="relative hidden md:block">
            <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search products…"
              className="w-64 pl-10"
              type="text"
            />
          </div>

          {/* wishlist */}
          <Button variant="ghost" size="icon" className="relative">
            <Heart className="size-5" />
            <span className="absolute -right-1 -top-1 flex size-4 items-center justify-center rounded-full bg-primary text-[10px] font-bold leading-none text-primary-foreground">
              0
            </span>
          </Button>

          {/* cart */}
          <Cart />

          {/* account */}
          {user ? (
            <Link href="/profile">
              <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-50 rounded-full border border-blue-200 hover:bg-blue-100 transition-colors cursor-pointer">
                <Avatar className="h-6 w-6">
                  <AvatarFallback className="text-xs bg-blue-100 text-blue-800">
                    {user.name.charAt(0).toUpperCase()}
                  </AvatarFallback>
                </Avatar>
                <span className="text-sm font-medium text-blue-900">
                  {user.name}
                </span>
                <Badge variant="outline" className="text-xs border-blue-300 text-blue-700">
                  AI Memory
                </Badge>
              </div>
            </Link>
          ) : (
            <Button variant="ghost" size="icon">
              <User className="size-5" />
            </Button>
          )}
        </div>
      </div>
    </header>
  );
}