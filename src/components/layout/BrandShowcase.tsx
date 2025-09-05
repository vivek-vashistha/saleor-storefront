import React from 'react';
import { Badge } from '@/components/ui/badge';
import { CheckCircle, ShieldCheck } from 'lucide-react';
import Image from "next/image";
import { Brand } from '@/types';

// Brand logos using remote images instead of local ones
const brands: Brand[] = [
  {
    id: 1,
    name: 'Patagonia',
    logo: 'https://upload.wikimedia.org/wikipedia/commons/2/2a/Patagonia_%28Unternehmen%29_logo.svg',
    description: 'Sustainable outdoor clothing and gear'
  },
  {
    id: 2,
    name: 'The North Face',
    logo: 'https://upload.wikimedia.org/wikipedia/commons/e/e1/The_North_Face.png',
    description: 'Performance apparel for extreme conditions'
  },
  {
    id: 3,
    name: 'Columbia',
    logo: 'https://upload.wikimedia.org/wikipedia/commons/c/c2/Columbia_Sportswear_Co_logo.svg',
    description: 'Innovative technology for outdoor enthusiasts'
  },
  {
    id: 4,
    name: 'Salomon',
    logo: 'https://upload.wikimedia.org/wikipedia/commons/9/9b/Salomon_logo_2022.svg',
    description: 'Premium trail running and hiking equipment'
  },
  {
    id: 5,
    name: 'Osprey',
    logo: 'https://upload.wikimedia.org/wikipedia/commons/d/dd/Osprey_logo.png',
    description: 'High-quality backpacks and travel gear'
  },
  {
    id: 6,
    name: 'Black Diamond',
    logo: 'https://upload.wikimedia.org/wikipedia/commons/d/d2/Black_Diamond_logo.png',
    description: 'Climbing, skiing and mountain gear'
  },
];

const BrandCard = ({ brand }: { brand: Brand }) => (
  <div className="w-full">
    <div className="p-6 flex flex-col items-center justify-center min-h-[220px] border border-border rounded-xl shadow-md transition-all duration-300 hover:shadow-lg hover:-translate-y-2 bg-card text-card-foreground">
      <Image
        src={brand.logo}
        alt={brand.name}
        width={200}
        height={80}
        className="max-w-[80%] h-[80px] object-contain mb-4 transition-all duration-300 hover:scale-105"
      />
      <p className="text-center mt-2 italic text-sm text-muted-foreground">
        {brand.description}
      </p>
    </div>
  </div>
);

const BrandShowcase = () => {
  return (
    <section className="py-16 border-t border-b border-border relative bg-background text-foreground">
      {/* Background grid pattern */}
      <div 
        className="absolute inset-0 opacity-[0.03] pointer-events-none bg-grid-pattern"
        aria-hidden="true"
      ></div>
      
      <div className="container max-w-[1800px] mx-auto px-4 sm:px-6 md:px-10 relative z-10">
        <header className="mb-4 text-center">
          <div className="mb-1 font-semibold tracking-[0.15em] uppercase text-sm text-primary">
            PREMIUM PARTNERSHIPS
          </div>
          <h3 className="font-extrabold mb-2 text-2xl md:text-4xl leading-tight text-foreground">
            Trusted by the Best Brands
          </h3>
          <p className="max-w-[700px] mx-auto mb-6 text-lg leading-relaxed font-light text-muted-foreground">
            We partner with the world&apos;s leading outdoor brands to bring you the highest quality gear, 
            ensuring your adventures are equipped with reliable and innovative products
          </p>
          <div className="flex justify-center items-center gap-2 mb-10">
            <Badge variant="outline" className="px-4 py-1.5 text-xs font-medium border-primary/30 bg-primary text-primary-foreground flex items-center">
              <ShieldCheck className="h-3.5 w-3.5 mr-1" />
              Authorized Retailer
            </Badge>
            <Badge variant="outline" className="px-4 py-1.5 text-xs font-medium border-primary/30 bg-primary text-primary-foreground flex items-center">
              <CheckCircle className="h-3.5 w-3.5 mr-1" />
              100% Authentic Guarantee
            </Badge>
          </div>
        </header>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-8 justify-center">
          {brands.map((brand) => (
            <BrandCard key={brand.id} brand={brand} />
          ))}
        </div>
      </div>
    </section>
  );
};

export default BrandShowcase; 