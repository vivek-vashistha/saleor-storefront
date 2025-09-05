/**
 * Interface for chat message structure
 */
export interface Message {
  type: 'user' | 'bot';
  content: string;
  timestamp: string;
  isProductBundleRecommendation?: boolean;
  isProductRecommendation?: boolean;
  isError?: boolean;
  recommendedBundles?: ProductBundle[];
  recommendedProducts?: Product[];
  referencedProductIds?: string[]; // Product IDs referenced in the message
}

/**
 * Interface for product recommendation data
 */
export interface Product {
  product_id: number;
  name: string;
  price: number;
  image_url: string;
  category?: string;
  description?: string;
  review_score?: number;
  best_for?: string[];
  [key: string]: unknown;
}

/**
 * Interface for product bundle
 */
export interface ProductBundle {
  bundle_id: string;
  products: Product[];
}

/**
 * Props for MessageBubble component
 */
export interface MessageBubbleProps {
  message: Message;
  productMessageTimestamp?: string | null;
}

/**
 * Props for ProductPanel component
 */
export interface ProductPanelProps {
  allBundles?: ProductBundle[];
  messageType?: 'product_bundle_recommendation' | 'product_recommendation';
}

/**
 * Props for chat alert component
 */
export interface ChatAlertProps {
  severity: 'success' | 'info' | 'warning' | 'error';
  children: React.ReactNode;
  onClose?: () => void;
  autoHideDuration?: number;
  title?: string;
}