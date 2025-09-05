'use client';

import React from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { MapPin, Phone, Mail, Facebook, Twitter, Instagram, Youtube, Send } from 'lucide-react';

const Footer = () => {
  return (
    <footer className="pt-8 pb-4 border-t border-border bg-card text-card-foreground">
      <div className="container mx-auto px-4 max-w-7xl">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-8">
          {/* Company Info */}
          <div className="md:col-span-4">
            <h3 className="font-bold text-xl mb-4 text-foreground">OUTDOOR GEAR</h3>
            <p className="mb-4 max-w-[300px] text-sm text-muted-foreground">
              Providing premium outdoor equipment for adventurers since 2010. Quality gear for unforgettable experiences.
            </p>
            <div className="mb-4 space-y-3 text-muted-foreground">
              {[
                { icon: <MapPin className="h-4 w-4" />, text: '123 Adventure Way, Mountain View, CA 94043' },
                { icon: <Phone className="h-4 w-4" />, text: '+1 (800) 555-GEAR' },
                { icon: <Mail className="h-4 w-4" />, text: 'support@outdoorgear.com' },
              ].map((item, index) => (
                <div
                  key={index}
                  className="flex items-start"
                >
                  <div className="mr-2 mt-1 text-primary">
                    {item.icon}
                  </div>
                  <p className="text-sm">
                    {item.text}
                  </p>
                </div>
              ))}
            </div>
            <div className="flex space-x-2">
              {[
                { icon: <Facebook className="h-4 w-4" />, label: 'Facebook' },
                { icon: <Twitter className="h-4 w-4" />, label: 'Twitter' },
                { icon: <Instagram className="h-4 w-4" />, label: 'Instagram' },
                { icon: <Youtube className="h-4 w-4" />, label: 'YouTube' },
              ].map((item, index) => (
                <Button
                  key={index}
                  variant="ghost"
                  size="icon"
                  aria-label={item.label}
                  className="h-8 w-8 rounded-full text-muted-foreground hover:text-foreground hover:bg-accent"
                >
                  {item.icon}
                </Button>
              ))}
            </div>
          </div>

          {/* Quick Links */}
          <div className="md:col-span-2 col-span-1 sm:col-span-4">
            <h3 className="font-semibold text-base mb-4 text-foreground">Shop</h3>
            <div className="flex flex-col space-y-2">
              {['New Arrivals', 'Best Sellers', 'Hiking Gear', 'Camping', 'Climbing', 'Clothing', 'Footwear', 'Accessories'].map((item, index) => (
                <Link
                  key={index}
                  href="#"
                  className="text-sm transition-colors text-muted-foreground hover:text-foreground"
                >
                  {item}
                </Link>
              ))}
            </div>
          </div>

          {/* Support Links */}
          <div className="md:col-span-2 col-span-1 sm:col-span-4">
            <h3 className="font-semibold text-base mb-4 text-foreground">Support</h3>
            <div className="flex flex-col space-y-2">
              {['Contact Us', 'FAQs', 'Shipping & Returns', 'Store Locator', 'Gift Cards', 'Size Charts', 'Product Care', 'Warranty'].map((item, index) => (
                <Link
                  key={index}
                  href="#"
                  className="text-sm transition-colors text-muted-foreground hover:text-foreground"
                >
                  {item}
                </Link>
              ))}
            </div>
          </div>

          {/* Company Links */}
          <div className="md:col-span-2 col-span-1 sm:col-span-4">
            <h3 className="font-semibold text-base mb-4 text-foreground">Company</h3>
            <div className="flex flex-col space-y-2">
              {['About Us', 'Careers', 'Sustainability', 'Press', 'Affiliate Program', 'Terms of Service', 'Privacy Policy', 'Blog'].map((item, index) => (
                <Link
                  key={index}
                  href="#"
                  className="text-sm transition-colors text-muted-foreground hover:text-foreground"
                >
                  {item}
                </Link>
              ))}
            </div>
          </div>

          {/* Newsletter Signup */}
          <div className="md:col-span-2 col-span-1 sm:col-span-6 md:col-start-11">
            <h3 className="font-semibold text-base mb-4 text-foreground">Stay Updated</h3>
            <p className="mb-2 text-sm text-muted-foreground">
              Subscribe for exclusive offers and outdoor tips.
            </p>
            <div className="mb-3">
              <div className="relative mb-2">
                <Input
                  type="email"
                  placeholder="Your email"
                  className="pr-10 bg-background border-input text-foreground"
                />
                <Button 
                  variant="ghost" 
                  size="icon" 
                  className="absolute right-0 top-0 h-full text-muted-foreground hover:text-foreground"
                >
                  <Send className="h-4 w-4" />
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                We respect your privacy.
              </p>
            </div>
            <div>
              <Button
                variant="outline"
                size="sm"
                className="border border-input bg-background text-foreground hover:bg-accent hover:text-accent-foreground"
              >
                Download Our App
              </Button>
            </div>
          </div>
        </div>

        <div className="h-px my-6 bg-border"></div>

        <div className="flex flex-col sm:flex-row justify-between items-center">
          <p className="text-sm mb-2 sm:mb-0 text-muted-foreground">
            © {new Date().getFullYear()} Outdoor Gear. All rights reserved.
          </p>
          <div className="flex gap-4">
            {['Terms', 'Privacy', 'Cookies', 'Accessibility'].map((item, index) => (
              <Link
                key={index}
                href="#"
                className="text-sm transition-colors text-muted-foreground hover:text-foreground"
              >
                {item}
              </Link>
            ))}
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer; 