/**
 * Interface for brand data
 */
export interface Brand {
  id: number;
  name: string;
  logo: string;
  description: string;
}

/**
 * Interface for customer review data
 */
export interface Review {
  id: number;
  author: string;
  rating: number;
  review: string;
  logo: string;
  badge: string;
  date: string;
  productImage: string;
}

/**
 * Interface for featured product data
 */
export interface FeaturedProduct {
  id: number;
  name: string;
  price: number;
  rating: number;
  image: string;
  category: string;
  isNew: boolean;
  discount: number | null;
  freeShipping: boolean;
}

