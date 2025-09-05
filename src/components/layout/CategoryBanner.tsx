import React from 'react';
import { Button } from '@/components/ui/button';
import { ArrowRight } from 'lucide-react';
import Image from "next/image";

// Updated with larger, more impactful images
const categories = [
  {
    id: 1,
    title: 'Hiking & Camping',
    description: 'Essential gear for your outdoor adventures',
    image: 'https://images.unsplash.com/photo-1533873984035-25970ab07461?ixlib=rb-1.2.1&auto=format&fit=crop&w=1920&q=80'
  },
  {
    id: 2,
    title: 'Climbing',
    description: 'Equipment for scaling new heights',
    image: 'https://images.unsplash.com/photo-1522163182402-834f871fd851?ixlib=rb-1.2.1&auto=format&fit=crop&w=1920&q=80'
  },
  {
    id: 3,
    title: 'Snow Sports',
    description: 'Gear for winter adventures',
    image: 'https://images.unsplash.com/photo-1605540436563-5bca919ae766?ixlib=rb-1.2.1&auto=format&fit=crop&w=1920&q=80'
  },
  {
    id: 4,
    title: 'Water Activities',
    description: 'Equipment for lakes, rivers & oceans',
    image: 'https://images.unsplash.com/photo-1530053969600-caed2596d242?ixlib=rb-1.2.1&auto=format&fit=crop&w=1920&q=80'
  },
];

const CategoryBanner = () => {
  return (
    <div className="py-12 border-b border-border bg-background text-foreground">
      <div className="max-w-[1800px] px-4 sm:px-10 md:px-20 mx-auto">
        <div className="mb-10 text-center">
          <div className="uppercase font-semibold tracking-wider mb-2 text-sm text-primary">
            EXPLORE OUR COLLECTIONS
          </div>
          
          <h2
            className="font-bold mb-4 text-3xl md:text-4xl text-foreground"
          >
            Shop By Category
          </h2>
          
          <p className="max-w-[700px] mx-auto mb-6 text-lg text-muted-foreground">
            Discover premium gear for every outdoor activity, expertly curated for performance and durability
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-6">
          {categories.map((category) => (
            <div key={category.id}>
              <div className="relative h-[400px] overflow-hidden rounded-lg cursor-pointer border border-border transition-all duration-300 hover:-translate-y-2 group">
                <Image
                  src={category.image}
                  alt={category.title}
                  width={600}
                  height={400}
                  className="w-full h-full object-cover object-center transition-transform duration-500 group-hover:scale-105"
                />
                {/* Dark overlay for better contrast */}
                <div className="absolute inset-0 bg-black/40"></div>
                <div className="absolute bottom-0 left-0 right-0 p-6 z-10 bg-background">
                  <h3 className="font-bold text-xl mb-1 text-foreground">
                    {category.title}
                  </h3>
                  <p className="text-sm mb-4 text-muted-foreground">
                    {category.description}
                  </p>
                  <Button
                    variant="outline"
                    className="flex items-center space-x-1 border-input bg-background text-foreground hover:bg-accent hover:text-accent-foreground"
                  >
                    <span>Shop Now</span>
                    <ArrowRight className="h-4 w-4 ml-1" />
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default CategoryBanner; 