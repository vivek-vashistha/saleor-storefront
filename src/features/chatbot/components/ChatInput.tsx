import React, { useState, useRef, useEffect, useCallback } from "react";
import { SendIcon } from "./ChatIcons";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";

// Define Product interface
interface Product {
	id: string;
	name: string;
}

// Custom hook for debouncing values with improved typing
const useDebounce = <T,>(value: T, delay: number): T => {
	const [debouncedValue, setDebouncedValue] = useState<T>(value);

	useEffect(() => {
		const handler = setTimeout(() => {
			setDebouncedValue(value);
		}, delay);

		return () => {
			clearTimeout(handler);
		};
	}, [value, delay]);

	return debouncedValue;
};

interface ChatInputProps {
	isLoading: boolean;
	onSendMessage: (message: string, productIds?: string[]) => void;
	products: Product[];
}

// Interface for tracking tagged products
interface TaggedProduct {
	id: string;
	name: string;
}

export const ChatInput: React.FC<ChatInputProps> = ({ isLoading, onSendMessage, products }) => {
	// Core state
	const [inputText, setInputText] = useState<string>("");
	const [taggedProducts, setTaggedProducts] = useState<TaggedProduct[]>([]);
	const [cursorPosition, setCursorPosition] = useState<number>(0);

	// Suggestion state
	const [isTagging, setIsTagging] = useState<boolean>(false);
	const [tagStartIndex, setTagStartIndex] = useState<number>(0);
	const [tagText, setTagText] = useState<string>("");
	const [suggestions, setSuggestions] = useState<Product[]>([]);
	const [selectedSuggestionIndex, setSelectedSuggestionIndex] = useState<number>(-1);

	// Refs
	const inputRef = useRef<HTMLInputElement>(null);
	const suggestionsRef = useRef<HTMLDivElement>(null);

	// Debounced values
	const debouncedInput = useDebounce(inputText, 150);
	const debouncedCursorPosition = useDebounce(cursorPosition, 150);

	// Detect @ symbol for tagging
	useEffect(() => {
		if (!debouncedInput) {
			setIsTagging(false);
			setSuggestions([]);
			return;
		}

		// Look for @ symbol that might start a tag
		const lastAtSymbolIndex = debouncedInput.lastIndexOf("@", debouncedCursorPosition - 1);

		if (lastAtSymbolIndex >= 0) {
			const isValidTagStart =
				lastAtSymbolIndex === 0 ||
				debouncedInput[lastAtSymbolIndex - 1] === " " ||
				debouncedInput[lastAtSymbolIndex - 1] === "\n";

			const isValidCursorPos = debouncedCursorPosition > lastAtSymbolIndex;

			if (isValidTagStart && isValidCursorPos) {
				const potentialTag = debouncedInput.substring(lastAtSymbolIndex + 1, debouncedCursorPosition);

				// Only activate tagging if no spaces in the tag (which would end it)
				if (!potentialTag.includes(" ") && !potentialTag.includes("\n")) {
					setIsTagging(true);
					setTagStartIndex(lastAtSymbolIndex);
					setTagText(potentialTag);

					// Filter suggestions
					if (potentialTag.length > 0) {
						const filtered = products
							.filter((product) => product.name.toLowerCase().includes(potentialTag.toLowerCase()))
							.sort((a, b) => {
								// Prioritize exact matches and starts-with matches
								const aStart = a.name.toLowerCase().startsWith(potentialTag.toLowerCase());
								const bStart = b.name.toLowerCase().startsWith(potentialTag.toLowerCase());

								if (aStart && !bStart) return -1;
								if (!aStart && bStart) return 1;

								return a.name.length - b.name.length;
							})
							.slice(0, 5);

						setSuggestions(filtered);
						setSelectedSuggestionIndex(filtered.length > 0 ? 0 : -1);
						return;
					}
				}
			}
		}

		// If we get here, we're not in a valid tagging state
		setIsTagging(false);
		setSuggestions([]);
	}, [debouncedInput, debouncedCursorPosition, products]);

	// Handle input changes
	const handleInputChange = useCallback(
		(e: React.ChangeEvent<HTMLInputElement>) => {
			const newText = e.target.value;
			const cursorPos = e.target.selectionStart || 0;

			setInputText(newText);
			setCursorPosition(cursorPos);

			// If no tagged products, nothing to check
			if (taggedProducts.length === 0) return;

			// Check if any product names have been modified/removed
			taggedProducts.forEach((taggedProduct) => {
				// If the product name no longer exists in the input text (or is partial), remove the tag
				if (!newText.includes(taggedProduct.name)) {
					setTaggedProducts((prev) => prev.filter((tag) => tag.id !== taggedProduct.id));
				}
			});
		},
		[taggedProducts],
	);

	// Handle cursor position updates
	const handleSelectionChange = useCallback(() => {
		if (inputRef.current) {
			setCursorPosition(inputRef.current.selectionStart || 0);
		}
	}, []);

	// Apply a product tag when selected
	const applyTag = useCallback(
		(product: Product) => {
			if (!isTagging) return;

			// Calculate text before and after the tag
			const beforeTag = inputText.substring(0, tagStartIndex);
			const afterTag = inputText.substring(tagStartIndex + tagText.length + 1); // +1 for @ symbol

			// Add to tagged products
			setTaggedProducts((prev) => [...prev, { id: product.id, name: product.name }]);

			// Replace @tag with product name in the input
			const newText = beforeTag + product.name + " " + afterTag;
			setInputText(newText);

			// Set cursor position after the product name and space
			const newCursorPos = tagStartIndex + product.name.length + 1; // +1 for space
			setCursorPosition(newCursorPos);

			// Focus input and set cursor
			setTimeout(() => {
				if (inputRef.current) {
					inputRef.current.focus();
					inputRef.current.setSelectionRange(newCursorPos, newCursorPos);
				}
			}, 0);

			// Reset tagging state
			setIsTagging(false);
			setSuggestions([]);
		},
		[inputText, isTagging, tagStartIndex, tagText],
	);

	// Remove a tagged product
	const removeTag = useCallback(
		(tagId: string) => {
			// Find the product to remove
			const productToRemove = taggedProducts.find((tag) => tag.id === tagId);

			if (productToRemove) {
				// Remove the product name from the input text
				const newText = inputText.replace(new RegExp(`\\b${productToRemove.name}\\b`, "g"), "");

				// Clean up multiple spaces that might be left
				const cleanedText = newText.replace(/\s+/g, " ").trim();

				setInputText(cleanedText);
			}

			// Remove the tag
			setTaggedProducts((prev) => prev.filter((tag) => tag.id !== tagId));
		},
		[inputText, taggedProducts],
	);

	// Send the message
	const handleSendMessage = useCallback(() => {
		if (!inputText.trim() && taggedProducts.length === 0) return;

		// Get tagged product IDs
		const productIds = taggedProducts.map((tag) => tag.id);

		// Send message
		onSendMessage(inputText, productIds.length > 0 ? productIds : undefined);

		// Reset state
		setInputText("");
		setTaggedProducts([]);
		setIsTagging(false);
		setSuggestions([]);
	}, [inputText, onSendMessage, taggedProducts]);

	// Handle keyboard events
	const handleKeyDown = useCallback(
		(e: React.KeyboardEvent<HTMLInputElement>) => {
			// Special handling for backspace when cursor is at the end of a product name
			if (e.key === "Backspace" && taggedProducts.length > 0) {
				const curPos = inputRef.current?.selectionStart || 0;

				// Check if cursor is at the end of any tagged product name
				taggedProducts.forEach((taggedProduct) => {
					const productNameEndPos = inputText.indexOf(taggedProduct.name) + taggedProduct.name.length;

					// If cursor is just after a product name
					if (curPos === productNameEndPos) {
						e.preventDefault(); // Prevent default backspace behavior

						// Remove the product name from text
						const productNameStartPos = inputText.indexOf(taggedProduct.name);
						const newText =
							inputText.substring(0, productNameStartPos) + inputText.substring(productNameEndPos);

						// Clean up multiple spaces
						const cleanedText = newText.replace(/\s+/g, " ");

						setInputText(cleanedText);

						// Remove the tag
						setTaggedProducts((prev) => prev.filter((tag) => tag.id !== taggedProduct.id));

						// Set cursor position
						setTimeout(() => {
							if (inputRef.current) {
								const newCurPos = productNameStartPos;
								inputRef.current.setSelectionRange(newCurPos, newCurPos);
								setCursorPosition(newCurPos);
							}
						}, 0);

						return;
					}
				});
			}

			// If suggestions are active, handle selection
			if (isTagging && suggestions.length > 0) {
				switch (e.key) {
					case "ArrowDown":
						e.preventDefault();
						setSelectedSuggestionIndex((prev) => (prev < suggestions.length - 1 ? prev + 1 : 0));
						break;

					case "ArrowUp":
						e.preventDefault();
						setSelectedSuggestionIndex((prev) => (prev > 0 ? prev - 1 : suggestions.length - 1));
						break;

					case "Enter":
						e.preventDefault();
						if (selectedSuggestionIndex >= 0) {
							applyTag(suggestions[selectedSuggestionIndex]);
						} else {
							handleSendMessage();
						}
						break;

					case "Escape":
						e.preventDefault();
						setIsTagging(false);
						setSuggestions([]);
						break;

					case "Tab":
						e.preventDefault();
						if (selectedSuggestionIndex >= 0) {
							applyTag(suggestions[selectedSuggestionIndex]);
						} else if (suggestions.length > 0) {
							applyTag(suggestions[0]);
						}
						break;
				}
			} else if (e.key === "Enter" && !e.shiftKey) {
				e.preventDefault();
				handleSendMessage();
			}
		},
		[isTagging, suggestions, selectedSuggestionIndex, applyTag, handleSendMessage, inputText, taggedProducts],
	);

	// Add selection event listeners
	useEffect(() => {
		const input = inputRef.current;
		if (input) {
			input.addEventListener("click", handleSelectionChange);
			input.addEventListener("keyup", handleSelectionChange);
			input.addEventListener("select", handleSelectionChange);

			return () => {
				input.removeEventListener("click", handleSelectionChange);
				input.removeEventListener("keyup", handleSelectionChange);
				input.removeEventListener("select", handleSelectionChange);
			};
		}
	}, [handleSelectionChange]);

	// Handle clicks outside suggestion box
	useEffect(() => {
		const handleClickOutside = (e: MouseEvent) => {
			if (
				suggestionsRef.current &&
				!suggestionsRef.current.contains(e.target as Node) &&
				inputRef.current &&
				!inputRef.current.contains(e.target as Node)
			) {
				setIsTagging(false);
				setSuggestions([]);
			}
		};

		document.addEventListener("mousedown", handleClickOutside);
		return () => {
			document.removeEventListener("mousedown", handleClickOutside);
		};
	}, []);

	return (
		<div className="flex flex-col gap-2">
			{/* Product tags */}
			{taggedProducts.length > 0 && (
				<div className="mb-2 flex flex-wrap gap-1.5">
					{taggedProducts.map((tag) => (
						<Badge
							key={tag.id}
							variant="default"
							className="flex items-center gap-1 px-2 py-0.5 text-sm font-medium"
						>
							{tag.name}
							<button
								className="ml-1 rounded-full p-0.5 transition-colors hover:bg-muted"
								onClick={() => removeTag(tag.id)}
								aria-label={`Remove ${tag.name} tag`}
							>
								<svg
									xmlns="http://www.w3.org/2000/svg"
									width="14"
									height="14"
									viewBox="0 0 24 24"
									fill="none"
									stroke="currentColor"
									strokeWidth="2"
									strokeLinecap="round"
									strokeLinejoin="round"
								>
									<line x1="18" y1="6" x2="6" y2="18"></line>
									<line x1="6" y1="6" x2="18" y2="18"></line>
								</svg>
							</button>
						</Badge>
					))}
				</div>
			)}

			<div className="relative flex items-center gap-2">
				{/* Simple input field */}
				<Input
					ref={inputRef}
					className="flex-1 border border-[#E2E8F0] pr-10 font-sans text-base"
					placeholder="Ask me about products (vitamins, supplements, beauty, grocery)... (type @ to tag products)"
					value={inputText}
					onChange={handleInputChange}
					onKeyDown={handleKeyDown}
					disabled={isLoading}
					aria-label="Type your message"
					autoComplete="off"
				/>

				{/* Send button */}
				<Button
					onClick={handleSendMessage}
					disabled={isLoading || (!inputText.trim() && taggedProducts.length === 0)}
					size="icon"
					className="bg-[#0F172A] text-white transition-colors hover:bg-[#0F172A]/90"
					aria-label="Send message"
				>
					<SendIcon />
				</Button>

				{/* Product suggestions dropdown */}
				{isTagging && suggestions.length > 0 && (
					<div
						ref={suggestionsRef}
						className="absolute bottom-full left-0 right-14 z-50 mb-1 overflow-hidden rounded-md border border-border bg-background shadow-lg"
						role="listbox"
						aria-label="Product suggestions"
					>
						<div className="border-b border-border px-3 py-1.5 text-xs font-semibold text-muted-foreground">
							Product Suggestions
						</div>

						<div className="max-h-[200px] overflow-y-auto">
							{suggestions.map((product, index) => (
								<div
									key={`${product.id}-${index}`}
									className={cn(
										"hover:bg-muted/60 cursor-pointer px-3 py-2 text-sm transition-colors",
										selectedSuggestionIndex === index ? "bg-primary/10 font-medium" : "",
									)}
									role="option"
									aria-selected={selectedSuggestionIndex === index}
									onClick={() => applyTag(product)}
									onMouseEnter={() => setSelectedSuggestionIndex(index)}
								>
									{product.name}
								</div>
							))}
						</div>
					</div>
				)}
			</div>
		</div>
	);
};
