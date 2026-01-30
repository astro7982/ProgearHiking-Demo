"use client";

import React from "react";
import { motion } from "framer-motion";
import ReactMarkdown from "react-markdown";
import {
  Mountain,
  User,
  Cloud,
  Package,
  CheckCircle2,
  Loader2,
  AlertCircle,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import type { ChatMessage as ChatMessageType, ToolCall } from "@/lib/api";

interface ChatMessageProps {
  message: ChatMessageType;
  isLatest?: boolean;
}

function ToolCallItem({ toolCall }: { toolCall: ToolCall }) {
  const [expanded, setExpanded] = React.useState(false);

  const statusIcon = {
    pending: <Loader2 className="h-3 w-3 animate-spin text-stone-400" />,
    running: <Loader2 className="h-3 w-3 animate-spin text-summit-500" />,
    completed: <CheckCircle2 className="h-3 w-3 text-forest-500" />,
    error: <AlertCircle className="h-3 w-3 text-red-500" />,
  };

  const statusColors = {
    pending: "bg-stone-100 border-stone-200",
    running: "bg-summit-50 border-summit-200",
    completed: "bg-forest-50 border-forest-200",
    error: "bg-red-50 border-red-200",
  };

  return (
    <div
      className={cn(
        "rounded-lg border p-3 transition-all duration-200",
        statusColors[toolCall.status]
      )}
    >
      <div
        className="flex items-center justify-between cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-2">
          {statusIcon[toolCall.status]}
          <span className="text-sm font-medium text-stone-700">
            {toolCall.name}
          </span>
          {toolCall.duration && (
            <span className="text-xs text-stone-500">
              {toolCall.duration}ms
            </span>
          )}
        </div>
        {toolCall.result !== undefined && (
          <button className="text-stone-400 hover:text-stone-600">
            {expanded ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </button>
        )}
      </div>
      {expanded && toolCall.result !== undefined && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: "auto", opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          className="mt-2 pt-2 border-t border-stone-200"
        >
          <pre className="text-xs text-stone-600 overflow-auto max-h-40 rounded bg-white/50 p-2">
            {JSON.stringify(toolCall.result, null, 2)}
          </pre>
        </motion.div>
      )}
    </div>
  );
}

export function ChatMessage({ message, isLatest = false }: ChatMessageProps) {
  const isUser = message.role === "user";
  const isAssistant = message.role === "assistant";

  const agentIcon = {
    salesforce: <Cloud className="h-4 w-4" />,
    inventory: <Package className="h-4 w-4" />,
    orchestrator: <Mountain className="h-4 w-4" />,
  };

  const agentColors = {
    salesforce: "from-blue-500 to-blue-600",
    inventory: "from-forest-500 to-forest-600",
    orchestrator: "from-stone-600 to-stone-700",
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={cn(
        "flex gap-4 py-4",
        isUser ? "flex-row-reverse" : "flex-row"
      )}
    >
      {/* Avatar */}
      <Avatar
        className={cn(
          "h-9 w-9 shrink-0 shadow-md",
          isAssistant &&
            message.agent &&
            `bg-gradient-to-br ${agentColors[message.agent.type]}`
        )}
      >
        <AvatarFallback
          className={cn(
            isUser
              ? "bg-forest-600 text-white"
              : message.agent
              ? `bg-gradient-to-br ${agentColors[message.agent.type]} text-white`
              : "bg-stone-600 text-white"
          )}
        >
          {isUser ? (
            <User className="h-4 w-4" />
          ) : message.agent ? (
            agentIcon[message.agent.type]
          ) : (
            <Mountain className="h-4 w-4" />
          )}
        </AvatarFallback>
      </Avatar>

      {/* Message Content */}
      <div
        className={cn(
          "flex flex-col gap-2 max-w-[80%]",
          isUser ? "items-end" : "items-start"
        )}
      >
        {/* Agent Badge */}
        {isAssistant && message.agent && (
          <div className="flex items-center gap-2">
            <Badge
              variant={
                message.agent.type === "salesforce" ? "salesforce" : "inventory"
              }
              icon={agentIcon[message.agent.type]}
            >
              {message.agent.name}
            </Badge>
            {message.agent.scopes.length > 0 && (
              <div className="flex gap-1">
                {message.agent.scopes.slice(0, 2).map((scope) => (
                  <Badge key={scope} variant="outline" className="text-[10px]">
                    {scope}
                  </Badge>
                ))}
                {message.agent.scopes.length > 2 && (
                  <Badge variant="outline" className="text-[10px]">
                    +{message.agent.scopes.length - 2}
                  </Badge>
                )}
              </div>
            )}
          </div>
        )}

        {/* Message Bubble */}
        <div
          className={cn(
            "rounded-2xl px-4 py-3 shadow-sm",
            isUser
              ? "bg-forest-600 text-white rounded-tr-md"
              : "bg-white border border-stone-200 text-stone-800 rounded-tl-md"
          )}
        >
          <div
            className={cn(
              "prose prose-sm max-w-none",
              isUser && "prose-invert"
            )}
          >
            <ReactMarkdown
              components={{
                p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                ul: ({ children }) => (
                  <ul className="list-disc pl-4 mb-2">{children}</ul>
                ),
                ol: ({ children }) => (
                  <ol className="list-decimal pl-4 mb-2">{children}</ol>
                ),
                code: ({ children }) => (
                  <code
                    className={cn(
                      "px-1 py-0.5 rounded text-sm",
                      isUser ? "bg-white/20" : "bg-stone-100"
                    )}
                  >
                    {children}
                  </code>
                ),
                strong: ({ children }) => (
                  <strong className="font-semibold">{children}</strong>
                ),
              }}
            >
              {message.content}
            </ReactMarkdown>
          </div>
        </div>

        {/* Tool Calls */}
        {message.toolCalls && message.toolCalls.length > 0 && (
          <div className="flex flex-col gap-2 w-full mt-1">
            {message.toolCalls.map((toolCall) => (
              <ToolCallItem key={toolCall.id} toolCall={toolCall} />
            ))}
          </div>
        )}

        {/* Timestamp */}
        <span className="text-xs text-stone-400">
          {new Date(message.timestamp).toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </span>
      </div>
    </motion.div>
  );
}
