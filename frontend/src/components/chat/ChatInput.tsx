"use client";

import React, { useState, useRef, useEffect } from "react";
import { Send, Paperclip, Mic, Sparkles } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

const SUGGESTIONS = [
  "Show me the top 5 sales opportunities",
  "What's our current inventory for hiking boots?",
  "Find customers who purchased backpacks last month",
  "Check stock levels for camping tents",
  "Update inventory: Add 50 units of Trail Runner Pro",
  "What are my pending leads?",
];

export function ChatInput({
  onSend,
  disabled = false,
  placeholder = "Ask about sales, customers, or inventory...",
}: ChatInputProps) {
  const [message, setMessage] = useState("");
  const [showSuggestions, setShowSuggestions] = useState(true);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(
        textareaRef.current.scrollHeight,
        200
      )}px`;
    }
  }, [message]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSend(message.trim());
      setMessage("");
      setShowSuggestions(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setMessage(suggestion);
    setShowSuggestions(false);
    textareaRef.current?.focus();
  };

  return (
    <div className="space-y-3">
      {/* Quick Suggestions */}
      <AnimatePresence>
        {showSuggestions && !message && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            className="flex flex-wrap gap-2"
          >
            {SUGGESTIONS.slice(0, 4).map((suggestion, index) => (
              <motion.button
                key={suggestion}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.05 }}
                onClick={() => handleSuggestionClick(suggestion)}
                className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-white border border-stone-200 rounded-full hover:bg-forest-50 hover:border-forest-300 transition-all duration-200 text-stone-600 hover:text-forest-700"
              >
                <Sparkles className="h-3 w-3" />
                {suggestion.length > 40
                  ? suggestion.slice(0, 40) + "..."
                  : suggestion}
              </motion.button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Input Area */}
      <form onSubmit={handleSubmit} className="relative">
        <div
          className={cn(
            "flex items-end gap-2 p-2 bg-white border-2 rounded-2xl transition-all duration-200 shadow-lg",
            disabled
              ? "border-stone-200 opacity-75"
              : "border-stone-200 focus-within:border-forest-400 focus-within:ring-4 focus-within:ring-forest-100"
          )}
        >
          {/* Attachment Button */}
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="shrink-0 h-9 w-9 text-stone-400 hover:text-stone-600"
            disabled={disabled}
          >
            <Paperclip className="h-5 w-5" />
          </Button>

          {/* Textarea */}
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled}
            rows={1}
            className="flex-1 resize-none bg-transparent border-0 focus:ring-0 focus:outline-none text-stone-800 placeholder:text-stone-400 py-2 px-1 text-base max-h-[200px]"
          />

          {/* Voice Button */}
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="shrink-0 h-9 w-9 text-stone-400 hover:text-stone-600"
            disabled={disabled}
          >
            <Mic className="h-5 w-5" />
          </Button>

          {/* Send Button */}
          <Button
            type="submit"
            size="icon"
            className={cn(
              "shrink-0 h-10 w-10 rounded-xl transition-all duration-200",
              message.trim()
                ? "bg-forest-600 hover:bg-forest-700 text-white shadow-md"
                : "bg-stone-100 text-stone-400 cursor-not-allowed"
            )}
            disabled={!message.trim() || disabled}
          >
            <Send className="h-5 w-5" />
          </Button>
        </div>

        {/* Character Counter */}
        {message.length > 0 && (
          <div className="absolute -bottom-5 right-2 text-xs text-stone-400">
            {message.length}/2000
          </div>
        )}
      </form>
    </div>
  );
}
