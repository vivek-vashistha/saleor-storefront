'use client';

import React from 'react';
import { Star } from 'lucide-react';
import { cn } from '@/lib/utils';

interface RatingProps {
  value: number;
  precision?: number;
  className?: string;
}

const Rating: React.FC<RatingProps> = ({ 
  value, 
  precision = 0.5, 
  className 
}) => {
  const totalStars = 5;
  const roundedValue = Math.round(value / precision) * precision;
  
  return (
    <div className={cn("flex items-center", className)}>
      {[...Array(totalStars)].map((_, index) => {
        const starValue = index + 1;
        
        // Calculate fill percentage for partial stars
        let fillPercentage = 0;
        if (roundedValue >= starValue) {
          fillPercentage = 100; // Full star
        } else if (roundedValue > index) {
          // Partial star - calculate exact percentage
          fillPercentage = Math.min(100, Math.max(0, (roundedValue - index) * 100));
        }
        
        return (
          <span key={index} className="relative inline-block w-4 h-4">
            {/* Background star (light fill) */}
            <Star 
              className="w-4 h-4 absolute text-muted-foreground stroke-muted-foreground fill-muted-foreground/10"
            />
            
            {/* Filled portion of star */}
            {fillPercentage > 0 && (
              <div 
                className="absolute overflow-hidden h-full" 
                style={{ width: `${fillPercentage}%` }}
              >
                <Star 
                  className="w-4 h-4 text-muted-foreground fill-muted-foreground"
                />
              </div>
            )}
          </span>
        );
      })}
    </div>
  );
};

export default Rating;