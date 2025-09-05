import { 
  MessageSquare, 
  X, 
  Maximize, 
  Minimize,
  Send, 
  ShoppingCart, 
  Plus 
} from "lucide-react";

export const ChatIcon = () => <MessageSquare className="w-6 h-6 text-white" strokeWidth={2.5} />;
export const CloseIcon = () => <X className="w-6 h-6 text-white" strokeWidth={2.5} />;
export const OpenInFullIcon = () => <Maximize className="w-6 h-6 text-white" strokeWidth={2.5} />;
export const CloseFullscreenIcon = () => <Minimize className="w-6 h-6 text-white" strokeWidth={2.5} />;
export const SendIcon = () => <Send className="w-5 h-5 text-white" strokeWidth={2.5} />;
export const AddShoppingCartIcon = () => <ShoppingCart className="w-4 h-4 text-white" strokeWidth={2.5} />;
export const PlusIcon = () => <Plus className="w-4 h-4 text-white" strokeWidth={2.5} />;