'use client';

import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Tag, Bell, Check, Send } from 'lucide-react';

import { Button } from '@/components/ui/button';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';

// Define form schema with validation
const formSchema = z.object({
  email: z.string().email({ message: 'Please enter a valid email address' }),
});

type FormValues = z.infer<typeof formSchema>;

const Newsletter = () => {
  const [subscribed, setSubscribed] = useState(false);

  // Initialize form with react-hook-form and zod validation
  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      email: '',
    },
  });

  const onSubmit = (values: FormValues) => {
    // In a real app, you would send this to your backend
    console.log('Subscribing email:', values.email);
    setSubscribed(true);
    form.reset();
  };

  return (
    <div className="py-10 relative border-t border-border">
      {/* Background image */}
      <div 
        className="absolute inset-0 z-0" 
        style={{
          backgroundImage: `url('https://images.unsplash.com/photo-1504280390367-361c6d9f38f4?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80')`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundAttachment: 'fixed',
        }}
      />
      
      {/* Dark overlay for readability */}
      <div className="absolute inset-0 bg-black/60 z-0"></div>
      
      {/* Decorative pattern */}
      <div 
        className="absolute inset-0 pointer-events-none opacity-10 z-[1]" 
        style={{
          backgroundImage: 'radial-gradient(circle, white 1px, transparent 1px)',
          backgroundSize: '30px 30px'
        }}
      />
      
      <div className="max-w-[1800px] mx-auto px-4 sm:px-10 md:px-20 relative z-10">
        <div className="p-6 md:p-10 rounded-3xl border border-border shadow-md relative overflow-hidden bg-background text-foreground">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-10 items-center">
            <div>
              <div className="uppercase font-semibold tracking-wider mb-2 text-sm text-primary">
                STAY CONNECTED
              </div>
              
              <h2 className="font-extrabold mb-4 text-3xl md:text-4xl leading-tight text-foreground">
                Join Our Adventure Community
              </h2>
              
              <p className="mb-8 text-lg leading-relaxed text-muted-foreground">
                Subscribe to our newsletter and be the first to know about exclusive deals, new gear releases, and expert outdoor tips.
              </p>
              
              <div className="h-px mb-8 bg-border"></div>
              
              <div className="space-y-4 mb-6">
                {[
                  { icon: <Tag className="h-5 w-5 text-primary" />, text: 'Exclusive subscriber discounts and early access to sales' },
                  { icon: <Bell className="h-5 w-5 text-primary" />, text: 'New product alerts and seasonal gear guides' },
                  { icon: <Check className="h-5 w-5 text-primary" />, text: 'Expert gear recommendations and adventure planning tips' },
                ].map((item, index) => (
                  <div
                    key={index}
                    className="flex items-center"
                  >
                    <div className="mr-3 p-2 rounded-full bg-primary/10">
                      {item.icon}
                    </div>
                    <p className="font-medium text-foreground">
                      {item.text}
                    </p>
                  </div>
                ))}
              </div>
            </div>
            
            <div>
              <div className="p-6 md:p-8 rounded-xl border border-border shadow-md relative overflow-hidden bg-card text-card-foreground">
                {!subscribed ? (
                  <>
                    <h3 className="font-bold text-2xl mb-6 text-foreground">
                      Sign Up for Our Newsletter
                    </h3>
                    
                    <Form {...form}>
                      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                        <FormField
                          control={form.control}
                          name="email"
                          render={({ field }) => (
                            <FormItem>
                              <FormControl>
                                <Input
                                  type="email"
                                  placeholder="Your email address"
                                  className="py-6 px-4 rounded-lg bg-background border-input text-foreground"
                                  {...field}
                                />
                              </FormControl>
                              <FormMessage className="text-sm text-destructive" />
                            </FormItem>
                          )}
                        />
                        
                        <div className="space-y-2">
                          <Button 
                            type="submit"
                            className="w-full py-6 font-semibold rounded-lg shadow-md flex items-center justify-center bg-primary text-primary-foreground hover:bg-primary/90"
                          >
                            <span>Subscribe Now</span>
                            <Send className="h-5 w-5 ml-2" />
                          </Button>
                          
                          <p className="text-xs text-center text-muted-foreground">
                            We respect your privacy. Unsubscribe at any time.
                          </p>
                        </div>
                      </form>
                    </Form>
                    
                    <div className="mt-6 p-4 rounded-lg border border-border bg-background">
                      <p className="text-sm text-muted-foreground">
                        <strong className="text-foreground">Join 25,000+</strong> outdoor enthusiasts already receiving our weekly newsletter!
                      </p>
                    </div>
                  </>
                ) : (
                  <div className="text-center py-8">
                    <div className="mx-auto mb-4 p-4 rounded-full w-20 h-20 flex items-center justify-center bg-primary/10">
                      <Check className="h-8 w-8 text-primary" />
                    </div>
                    
                    <h3 className="font-bold text-2xl mb-2 text-foreground">
                      Thank You For Subscribing!
                    </h3>
                    
                    <p className="mb-6 text-muted-foreground">
                      You&apos;ve successfully joined our adventure community. Get ready for exclusive offers, tips, and outdoor inspiration.
                    </p>
                    
                    <Button
                      onClick={() => setSubscribed(false)}
                      variant="outline"
                      className="border border-input bg-background text-foreground hover:bg-accent hover:text-accent-foreground"
                    >
                      Subscribe Another Email
                    </Button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Newsletter;