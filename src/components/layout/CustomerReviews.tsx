'use client';

import React from 'react';
import { Star, Quote } from 'lucide-react';
import Image from "next/image";
import { Review } from '@/types';

// Sample reviews
const reviews: Review[] = [
  {
    id: 1,
    author: 'NY Times Wirecutter',
    rating: 5,
    review: "The Adventure Backpack Pro sets a new standard for outdoor gear. Its durability and smart organization make it our top pick for hiking and travel.",
    logo: "https://placehold.co/200x100/ffffff/000000?text=NY+Times",
    badge: "Editor's Choice",
    date: "February 2025",
    productImage: 'https://images.unsplash.com/photo-1551632811-561732d1e306?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80'
  },
  {
    id: 2,
    author: 'Outdoor Gear Lab',
    rating: 4.8,
    review: "The All-Weather Jacket excels in harsh conditions. Water-resistant, breathable, and surprisingly lightweight - it's earned our highest recommendation.",
    logo: "https://placehold.co/200x100/ffffff/000000?text=Outdoor+Gear+Lab",
    badge: "Top Rated",
    date: "January 2025",
    productImage: 'https://images.unsplash.com/photo-1605540436563-5bca919ae766?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80'
  },
  {
    id: 3,
    author: 'Backpacker Magazine',
    rating: 4.9,
    review: "Camping Tent Ultra redefines what we expect from a 4-season tent. Setup is intuitive, and it handles wind and rain with remarkable stability.",
    logo: "https://placehold.co/200x100/ffffff/000000?text=Backpacker+Magazine",
    badge: "Best in Test",
    date: "March 2025",
    productImage: 'https://images.unsplash.com/photo-1537225228614-56cc3556d7ed?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80'
  }
];

const ReviewCard = ({ review }: { review: Review }) => {
  // Generate stars for rating
  const renderRating = (rating: number) => {
    const stars = [];
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating % 1 !== 0;
    
    for (let i = 0; i < 5; i++) {
      if (i < fullStars) {
        stars.push(<Star key={i} className="h-4 w-4 fill-current text-primary" />);
      } else if (i === fullStars && hasHalfStar) {
        stars.push(<Star key={i} className="h-4 w-4 fill-current text-primary" />);
      } else {
        stars.push(<Star key={i} className="h-4 w-4 opacity-30 text-muted-foreground" />);
      }
    }
    
    return stars;
  };

  return (
    <div className="h-full">
      <div className="h-full flex flex-col relative overflow-visible border border-border rounded-xl shadow-md transition-all duration-300 hover:-translate-y-2 bg-card text-card-foreground">
        <div className="h-[200px] rounded-t-xl relative overflow-hidden">
          {/* Background image */}
          <div 
            className="absolute inset-0 z-0"
            style={{
              backgroundImage: `url(${review.productImage})`,
              backgroundSize: 'cover',
              backgroundPosition: 'center'
            }}
          />
          
          {/* Dark overlay for better readability */}
          <div className="absolute inset-0 bg-black/30 z-[1]"></div>
          
          <Image
            src={review.logo} 
            alt={review.author} 
            width={150}
            height={40}
            className="h-10 max-w-[150px] object-contain filter invert opacity-90 absolute top-5 left-5 z-10"
          />
          
          <div className="absolute top-3 right-3 font-bold text-xs py-0.5 px-4 rounded shadow-md z-10 bg-primary text-primary-foreground">
            {review.badge}
          </div>
        </div>
        
        <div className="p-6 flex-grow flex flex-col">
          <div className="relative mb-4">
            <div className="absolute -top-3 -left-3">
              <Quote className="w-8 h-8 opacity-30 text-muted-foreground" />
            </div>
            <h3 className="font-bold text-lg mb-2 text-foreground">
              {review.author}
            </h3>
          </div>

          <div className="flex items-center mb-4">
            <div className="flex mr-2">
              {renderRating(review.rating)}
            </div>
            <span className="text-sm font-semibold ml-1 text-foreground">
              {review.rating.toFixed(1)}
            </span>
          </div>

          <p className="mb-auto italic leading-relaxed text-[1.05rem] tracking-wide text-foreground">
            &quot;{review.review}&quot;
          </p>

          <div className="my-4 h-px bg-border"></div>

          <span className="block text-right text-xs mt-2 font-medium text-muted-foreground">
            {review.date}
          </span>
        </div>
      </div>
    </div>
  );
};

const CustomerReviews = () => {
  return (
    <section className="py-10 relative border-t border-border bg-background text-foreground">
      {/* Background grid pattern */}
      <div 
        className="absolute inset-0 opacity-[0.03] pointer-events-none bg-grid-pattern"
        aria-hidden="true"
      ></div>
      
      <div className="max-w-[1800px] mx-auto px-4 sm:px-10 md:px-20 relative z-10">
        <div className="text-center mb-16">
          <div className="uppercase font-semibold tracking-wider mb-2 text-sm text-primary">
            TRUSTED BY EXPERTS
          </div>
          
          <h2 className="font-extrabold mb-4 text-3xl md:text-4xl leading-tight text-foreground">
            Expert Reviews
          </h2>
          
          <p className="max-w-[700px] mx-auto mb-10 text-lg leading-relaxed text-muted-foreground">
            Our products are consistently recognized by leading outdoor gear experts and publications
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {reviews.map((review) => (
            <ReviewCard key={review.id} review={review} />
          ))}
        </div>
      </div>
    </section>
  );
};

export default CustomerReviews; 