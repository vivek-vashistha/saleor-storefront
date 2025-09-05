import {useCallback, useState} from 'react';
import {Message, Product, ProductBundle} from '@/features/chatbot/types';
import {initializeSession, deleteSession, sendMessage} from '@/features/chatbot/api';
import { useUser } from '@/context/UserContext';

interface UseChatSessionProps {
  onMaximize?: () => void;
  isMaximized?: boolean;
}

export const useChatSession = ({ onMaximize, isMaximized }: UseChatSessionProps = {}) => {
  const { user } = useUser();
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([{
    type: 'bot',
    content: "Hi there! I'm your outdoor gear advisor. Tell me about your planned activities, experience level, and any specific needs, and I'll recommend the perfect gear for your adventure.",
    timestamp: new Date().toISOString(),
  }]);
  const [isLoading, setIsLoading] = useState(false);
  const [bundles, setBundles] = useState<ProductBundle[]>([]);
  const [recommendedProducts, setRecommendedProducts] = useState<Product[]>([]);
  const [messageType, setMessageType] = useState<'product_bundle_recommendation' | 'product_recommendation'>('product_bundle_recommendation');
  const [productMessageTimestamp, setProductMessageTimestamp] = useState<string | null>(null);
  const [userHasSentMessage, setUserHasSentMessage] = useState(false);

  // Function to process bot messages from API response
  const processBotMessages = useCallback((responseMessages: Array<{type: string; content: string | string[]; recommended_products?: Product[]; bundle_id?: string; recommended_bundles?: ProductBundle[]}>) => {
    responseMessages.forEach((message) => {
      const currentTimestamp = new Date().toISOString();

      if (message.type === 'ai') {
        // Concatenate all content items if it's an array
        let messageContent: string;
        if (Array.isArray(message.content)) {
          messageContent = message.content.join('\n');
        } else {
          messageContent = message.content;
        }

        const botMessage: Message = {
          type: 'bot',
          content: messageContent,
          timestamp: currentTimestamp,
        };
        setMessages(prev => [...prev, botMessage]);
      }

      if (message.type === 'product_bundle_recommendation' && message.recommended_bundles && message.recommended_bundles.length > 0) {
        // Set the message type
        setMessageType('product_bundle_recommendation');
        
        // Store bundles
        setBundles(message.recommended_bundles);
        
        // Auto-maximize the chat window
        if (onMaximize && !isMaximized) {
          onMaximize();
        }

        setProductMessageTimestamp(currentTimestamp);

        // Handle content that might be an array
        let messageContent: string;
        if (typeof message.content === 'string') {
          messageContent = message.content;
        } else if (Array.isArray(message.content) && message.content.length > 0) {
          messageContent = message.content.join('\n');
        } else {
          messageContent = 'Here are some recommended bundles for you:';
        }

        const botMessage: Message = {
          type: 'bot',
          content: messageContent,
          timestamp: currentTimestamp,
          isProductBundleRecommendation: true,
          recommendedBundles: message.recommended_bundles
        };
        setMessages(prev => [...prev, botMessage]);
      }

      if (message.type === 'product_recommendation' && message.recommended_products && message.recommended_products.length > 0) {
        // Set the message type
        setMessageType('product_recommendation');
        
        // Store products
        setRecommendedProducts(message.recommended_products);
        
        // Auto-maximize the chat window
        if (onMaximize && !isMaximized) {
          onMaximize();
        }

        setProductMessageTimestamp(currentTimestamp);

        // Handle content that might be an array
        let messageContent: string;
        if (typeof message.content === 'string') {
          messageContent = message.content;
        } else if (Array.isArray(message.content) && message.content.length > 0) {
          messageContent = message.content.join('\n');
        } else {
          messageContent = 'Here are some recommended products for you:';
        }

        const botMessage: Message = {
          type: 'bot',
          content: messageContent,
          timestamp: currentTimestamp,
          isProductRecommendation: true,
          recommendedProducts: message.recommended_products,
        };
        setMessages(prev => [...prev, botMessage]);
      }
    });
  }, [isMaximized, onMaximize]);

  // Function to initialize chat session
  const initializeSessionFn = useCallback(async () => {
    if (conversationId) return; // Don't initialize if we already have a session

    try {
      setIsLoading(true);

      // Initialize the session using the API function
      // const sessionResponse = await initializeSession();
      const sessionResponse = await initializeSession(user?.id || 'vivek_001');

      if (sessionResponse.id) {
        console.log("Conversation ID: " + sessionResponse.id);
        setConversationId(sessionResponse.id);
      } else {
        throw new Error("Failed to get conversation ID");
      }
    } catch (error) {
      console.error('Error initializing session:', error);
    } finally {
      setIsLoading(false);
    }
  }, [conversationId]);

  // Function to delete the session if user hasn't sent any messages
  const deleteSessionIfUnused = useCallback(async () => {
    if (conversationId && !userHasSentMessage) {
      try {
        await deleteSession(conversationId);
        console.log(`Deleted unused session: ${conversationId}`);
      } catch (error) {
        console.error('Error deleting session:', error);
      } finally {
        setConversationId(null);
      }
    }
  }, [conversationId, userHasSentMessage]);

  // Function to send a message
  const sendMessageFn = useCallback(async (messageContent: string, productIds?: string[]) => {
    if (!messageContent.trim()) return;

    // Add user message to state
    const userMessage: Message = {
      type: 'user',
      content: messageContent,
      timestamp: new Date().toISOString(),
      referencedProductIds: productIds
    };
    setMessages((prev) => [...prev, userMessage]);
    setUserHasSentMessage(true);

    // If no conversation exists yet, initialize and send in one go
    if (!conversationId) {
      try {
        setIsLoading(true);

        // Step 1: Initialize the session using the API function
        const sessionResponse = await initializeSession(user?.id || 'vivek_001');
        // const sessionResponse = await initializeSession();

        let sessionId = null;
        if (sessionResponse.id) {
          console.log("Conversation ID: " + sessionResponse.id);
          sessionId = sessionResponse.id;
          setConversationId(sessionId);
        } else {
          throw new Error("Failed to get conversation ID");
        }

        // Step 2: Send the user's message using the API function
        const messageResponse = await sendMessage(
          sessionId,
          messageContent,
          // '1',
          user?.id || 'vivek_001',
          productIds || [] // Include product IDs in API call
        );

        // Process the response messages
        processBotMessages(messageResponse.messages);

      } catch (error) {
        console.error('Error:', error);
        const errorMessage = error instanceof Error ? error.message : 'Sorry, an error occurred while processing your request.';
        const currentTimestamp = new Date().toISOString();

        const botMessage: Message = {
          type: 'bot',
          content: errorMessage,
          timestamp: currentTimestamp,
          isError: true
        };
        setMessages(prev => [...prev, botMessage]);
      } finally {
        setIsLoading(false);
      }
    } else {
      // Otherwise, just send the message to the existing conversation
      setIsLoading(true);
      try {
        // Send the message using the API function
        const response = await sendMessage(
          conversationId,
          messageContent,
          // '1',
          user?.id || 'vivek_001',
          productIds || [] // Include product IDs in API call
        );

        // Process the response messages
        processBotMessages(response.messages);

      } catch (error) {
        console.error('Error:', error);
        const errorMessage = error instanceof Error ? error.message : 'Sorry, an error occurred while processing your request.';
        const currentTimestamp = new Date().toISOString();

        const botMessage: Message = {
          type: 'bot',
          content: errorMessage,
          timestamp: currentTimestamp,
          isError: true
        };
        setMessages(prev => [...prev, botMessage]);
      } finally {
        setIsLoading(false);
      }
    }
  }, [conversationId, processBotMessages]);

  // Get products data based on the message type
  const getProductsData = () => {
    if (messageType === 'product_recommendation') {
      return recommendedProducts;
    } 
    // For bundle recommendations, flatten all products from all bundles
    return bundles.flatMap(bundle => bundle.products || []);
  };

  return {
    messages,
    isLoading,
    allBundles: messageType === 'product_recommendation' 
      ? [{ bundle_id: 'recommendations', products: recommendedProducts }] 
      : bundles,
    products: recommendedProducts,
    messageType,
    productMessageTimestamp,
    userHasSentMessage,
    conversationId,
    sendMessage: sendMessageFn,
    initializeSession: initializeSessionFn,
    deleteSessionIfUnused,
    // Expose product objects for suggestions
    productSuggestions: getProductsData()
      .filter(product => product.name)
      .map(product => ({
        id: product.product_id.toString(),
        name: product.name
      }))
  };
};

export default useChatSession;