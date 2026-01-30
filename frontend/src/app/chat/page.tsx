"use client";

import React, { useEffect, useState, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  Mountain,
  Cloud,
  Package,
  RefreshCw,
  Trash2,
  Plus,
  MessageSquare,
  History,
  Settings,
  HelpCircle,
  Loader2,
  CheckCircle2,
  AlertTriangle,
  Link as LinkIcon,
  Unlink,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Header } from "@/components/layout/Header";
import { ChatMessage } from "@/components/chat/ChatMessage";
import { ChatInput } from "@/components/chat/ChatInput";
import {
  getOktaAuth,
  getUserInfo,
  signOut,
  type UserInfo,
} from "@/lib/okta";
import {
  sendChatMessage,
  getUserAccess,
  connectSalesforce,
  streamChat,
  type ChatMessage as ChatMessageType,
  type UserAccess,
  type ToolCall,
  type AgentInfo,
} from "@/lib/api";

export default function ChatPage() {
  const router = useRouter();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [user, setUser] = useState<UserInfo | null>(null);
  const [access, setAccess] = useState<UserAccess | null>(null);
  const [messages, setMessages] = useState<ChatMessageType[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [connectingService, setConnectingService] = useState<string | null>(null);

  // Check authentication
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const oktaAuth = getOktaAuth();
        const authenticated = await oktaAuth.isAuthenticated();

        if (!authenticated) {
          router.push("/");
          return;
        }

        const userInfo = await getUserInfo();
        setUser(userInfo);

        // Fetch user access
        try {
          const userAccess = await getUserAccess();
          setAccess(userAccess);
        } catch (err) {
          console.error("Failed to fetch user access:", err);
          // Set default access
          setAccess({
            salesforce: { connected: false, scopes: [] },
            inventory: { authorized: true, scopes: ["inventory:read", "inventory:write"] },
          });
        }
      } catch (error) {
        console.error("Auth check failed:", error);
        router.push("/");
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, [router]);

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSignOut = async () => {
    try {
      await signOut();
    } catch (error) {
      console.error("Sign out failed:", error);
    }
  };

  const handleSendMessage = useCallback(
    async (content: string) => {
      // Add user message
      const userMessage: ChatMessageType = {
        id: `user-${Date.now()}`,
        role: "user",
        content,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, userMessage]);
      setIsTyping(true);

      try {
        // For demo purposes, simulate a response
        // In production, this would use streamChat or sendChatMessage
        await new Promise((resolve) => setTimeout(resolve, 1500));

        // Simulate agent response based on message content
        let agentType: "salesforce" | "inventory" = "inventory";
        let agentName = "Inventory Agent";
        let scopes: string[] = ["inventory:read"];
        let responseContent = "";
        let toolCalls: ToolCall[] = [];

        const lowerContent = content.toLowerCase();

        if (
          lowerContent.includes("sales") ||
          lowerContent.includes("lead") ||
          lowerContent.includes("opportunity") ||
          lowerContent.includes("customer") ||
          lowerContent.includes("account") ||
          lowerContent.includes("contact")
        ) {
          agentType = "salesforce";
          agentName = "Salesforce Agent";
          scopes = ["sales:read", "customer:read"];

          if (lowerContent.includes("lead")) {
            toolCalls = [
              {
                id: "tc-1",
                name: "salesforce.get_leads",
                status: "completed",
                duration: 234,
                result: {
                  leads: [
                    { name: "John Smith", company: "Alpine Adventures", status: "New" },
                    { name: "Sarah Johnson", company: "Peak Performance", status: "Contacted" },
                  ],
                },
              },
            ];
            responseContent = `I found **2 active leads** in your pipeline:\n\n1. **John Smith** from Alpine Adventures (New)\n2. **Sarah Johnson** from Peak Performance (Contacted)\n\nWould you like me to provide more details on any of these leads?`;
          } else if (lowerContent.includes("opportunity")) {
            toolCalls = [
              {
                id: "tc-1",
                name: "salesforce.get_opportunities",
                status: "completed",
                duration: 312,
                result: {
                  opportunities: [
                    { name: "Enterprise Deal - Mountain Corp", amount: 45000, stage: "Negotiation" },
                    { name: "Retail Partnership - TrailBlaze", amount: 28000, stage: "Proposal" },
                  ],
                },
              },
            ];
            responseContent = `Here are your **top sales opportunities**:\n\n| Opportunity | Amount | Stage |\n|-------------|--------|-------|\n| Enterprise Deal - Mountain Corp | $45,000 | Negotiation |\n| Retail Partnership - TrailBlaze | $28,000 | Proposal |\n\nTotal pipeline value: **$73,000**`;
          } else {
            toolCalls = [
              {
                id: "tc-1",
                name: "salesforce.search_accounts",
                status: "completed",
                duration: 189,
                result: { accounts_found: 3 },
              },
            ];
            responseContent = `I found **3 customer accounts** matching your query. Would you like me to show details for any specific customer?`;
          }
        } else if (
          lowerContent.includes("inventory") ||
          lowerContent.includes("stock") ||
          lowerContent.includes("product") ||
          lowerContent.includes("boot") ||
          lowerContent.includes("tent") ||
          lowerContent.includes("backpack")
        ) {
          if (lowerContent.includes("update") || lowerContent.includes("add")) {
            scopes = ["inventory:read", "inventory:write"];
            toolCalls = [
              {
                id: "tc-1",
                name: "inventory.update_stock",
                status: "completed",
                duration: 156,
                result: { updated: true, new_quantity: 150 },
              },
            ];
            responseContent = `I've **updated the inventory** successfully. The new stock level has been recorded.\n\nWould you like me to set up a low-stock alert for this item?`;
          } else {
            toolCalls = [
              {
                id: "tc-1",
                name: "inventory.check_stock",
                status: "completed",
                duration: 98,
                result: {
                  products: [
                    { name: "Trail Runner Pro", sku: "TRP-001", quantity: 45, status: "In Stock" },
                    { name: "Summit Hiking Boot", sku: "SHB-002", quantity: 12, status: "Low Stock" },
                    { name: "Alpine Tent 4P", sku: "AT4-003", quantity: 28, status: "In Stock" },
                  ],
                },
              },
            ];
            responseContent = `Here's the current **inventory status**:\n\n| Product | SKU | Qty | Status |\n|---------|-----|-----|--------|\n| Trail Runner Pro | TRP-001 | 45 | In Stock |\n| Summit Hiking Boot | SHB-002 | 12 | Low Stock |\n| Alpine Tent 4P | AT4-003 | 28 | In Stock |\n\n⚠️ **Alert**: Summit Hiking Boot is running low. Consider reordering.`;
          }
        } else {
          // Default response
          responseContent = `I can help you with:\n\n**Salesforce** (Sales & Customers)\n- View and manage leads\n- Track opportunities\n- Search customer accounts\n- View contact information\n\n**Inventory**\n- Check stock levels\n- Update inventory quantities\n- Set low-stock alerts\n- View product catalog\n\nWhat would you like to know?`;
        }

        const assistantMessage: ChatMessageType = {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          content: responseContent,
          timestamp: new Date(),
          agent: {
            name: agentName,
            type: agentType,
            scopes,
          },
          toolCalls,
        };

        setMessages((prev) => [...prev, assistantMessage]);
      } catch (error) {
        console.error("Failed to send message:", error);
        // Add error message
        setMessages((prev) => [
          ...prev,
          {
            id: `error-${Date.now()}`,
            role: "assistant",
            content:
              "Sorry, I encountered an error processing your request. Please try again.",
            timestamp: new Date(),
          },
        ]);
      } finally {
        setIsTyping(false);
      }
    },
    [conversationId]
  );

  const handleConnectSalesforce = async () => {
    setConnectingService("salesforce");
    try {
      const { auth_url } = await connectSalesforce();
      window.location.href = auth_url;
    } catch (error) {
      console.error("Failed to connect Salesforce:", error);
    } finally {
      setConnectingService(null);
    }
  };

  const handleNewConversation = () => {
    setMessages([]);
    setConversationId(null);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-stone-50 to-forest-50">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-10 w-10 text-forest-600 animate-spin" />
          <p className="text-stone-500">Loading your workspace...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-stone-50 flex flex-col">
      <Header user={user} access={access} onSignOut={handleSignOut} />

      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <AnimatePresence>
          {sidebarOpen && (
            <motion.aside
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: 280, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              className="border-r bg-white flex flex-col overflow-hidden"
            >
              {/* New Chat Button */}
              <div className="p-4 border-b">
                <Button
                  onClick={handleNewConversation}
                  className="w-full justify-start gap-2"
                  variant="outline"
                >
                  <Plus className="h-4 w-4" />
                  New Conversation
                </Button>
              </div>

              {/* Agent Status */}
              <div className="p-4 border-b">
                <h3 className="text-xs font-semibold text-stone-500 uppercase tracking-wider mb-3">
                  Agent Status
                </h3>
                <div className="space-y-2">
                  {/* Salesforce Agent */}
                  <div
                    className={cn(
                      "flex items-center justify-between p-3 rounded-lg border transition-colors",
                      access?.salesforce.connected
                        ? "bg-blue-50 border-blue-200"
                        : "bg-stone-50 border-stone-200"
                    )}
                  >
                    <div className="flex items-center gap-2">
                      <div
                        className={cn(
                          "h-8 w-8 rounded-lg flex items-center justify-center",
                          access?.salesforce.connected
                            ? "bg-blue-500"
                            : "bg-stone-300"
                        )}
                      >
                        <Cloud className="h-4 w-4 text-white" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-stone-800">
                          Salesforce
                        </p>
                        <p className="text-xs text-stone-500">
                          {access?.salesforce.connected
                            ? "Connected"
                            : "Not connected"}
                        </p>
                      </div>
                    </div>
                    {!access?.salesforce.connected && (
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={handleConnectSalesforce}
                        disabled={connectingService === "salesforce"}
                        className="h-7 px-2"
                      >
                        {connectingService === "salesforce" ? (
                          <Loader2 className="h-3 w-3 animate-spin" />
                        ) : (
                          <LinkIcon className="h-3 w-3" />
                        )}
                      </Button>
                    )}
                  </div>

                  {/* Inventory Agent */}
                  <div
                    className={cn(
                      "flex items-center justify-between p-3 rounded-lg border transition-colors",
                      access?.inventory.authorized
                        ? "bg-forest-50 border-forest-200"
                        : "bg-stone-50 border-stone-200"
                    )}
                  >
                    <div className="flex items-center gap-2">
                      <div
                        className={cn(
                          "h-8 w-8 rounded-lg flex items-center justify-center",
                          access?.inventory.authorized
                            ? "bg-forest-500"
                            : "bg-stone-300"
                        )}
                      >
                        <Package className="h-4 w-4 text-white" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-stone-800">
                          Inventory
                        </p>
                        <p className="text-xs text-stone-500">
                          {access?.inventory.authorized
                            ? "Authorized"
                            : "No access"}
                        </p>
                      </div>
                    </div>
                    {access?.inventory.authorized && (
                      <CheckCircle2 className="h-4 w-4 text-forest-500" />
                    )}
                  </div>
                </div>
              </div>

              {/* Scopes Info */}
              {access && (
                <div className="p-4 border-b">
                  <h3 className="text-xs font-semibold text-stone-500 uppercase tracking-wider mb-3">
                    Your Permissions
                  </h3>
                  <div className="flex flex-wrap gap-1">
                    {access.inventory.scopes.map((scope) => (
                      <Badge
                        key={scope}
                        variant="inventory"
                        className="text-[10px]"
                      >
                        {scope}
                      </Badge>
                    ))}
                    {access.salesforce.scopes.map((scope) => (
                      <Badge
                        key={scope}
                        variant="salesforce"
                        className="text-[10px]"
                      >
                        {scope}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {/* Recent Conversations */}
              <div className="flex-1 overflow-auto p-4">
                <h3 className="text-xs font-semibold text-stone-500 uppercase tracking-wider mb-3">
                  Recent
                </h3>
                <div className="space-y-1">
                  {[
                    "Inventory check for hiking boots",
                    "Q4 sales pipeline review",
                    "Customer account lookup",
                  ].map((title, i) => (
                    <button
                      key={i}
                      className="w-full text-left px-3 py-2 rounded-lg text-sm text-stone-600 hover:bg-stone-100 transition-colors truncate"
                    >
                      <MessageSquare className="h-3 w-3 inline-block mr-2 text-stone-400" />
                      {title}
                    </button>
                  ))}
                </div>
              </div>

              {/* Footer */}
              <div className="p-4 border-t">
                <div className="flex items-center gap-2">
                  <Button variant="ghost" size="sm" className="flex-1">
                    <Settings className="h-4 w-4 mr-1" />
                    Settings
                  </Button>
                  <Button variant="ghost" size="sm" className="flex-1">
                    <HelpCircle className="h-4 w-4 mr-1" />
                    Help
                  </Button>
                </div>
              </div>
            </motion.aside>
          )}
        </AnimatePresence>

        {/* Main Chat Area */}
        <main className="flex-1 flex flex-col overflow-hidden">
          {/* Messages */}
          <div className="flex-1 overflow-auto px-4 py-6">
            <div className="max-w-3xl mx-auto">
              {messages.length === 0 ? (
                <div className="text-center py-12">
                  <div className="h-16 w-16 rounded-2xl bg-gradient-to-br from-forest-500 to-forest-700 flex items-center justify-center mx-auto mb-6 shadow-xl">
                    <Mountain className="h-9 w-9 text-white" />
                  </div>
                  <h2 className="text-2xl font-bold text-stone-800 mb-2">
                    Welcome to ProGear AI
                  </h2>
                  <p className="text-stone-500 mb-8 max-w-md mx-auto">
                    I can help you manage your Salesforce CRM and inventory.
                    What would you like to know?
                  </p>

                  {/* Quick Actions */}
                  <div className="grid sm:grid-cols-2 gap-4 max-w-lg mx-auto">
                    <Card
                      className="cursor-pointer hover:shadow-md transition-shadow border-2 border-transparent hover:border-blue-200"
                      onClick={() =>
                        handleSendMessage("Show me the top sales opportunities")
                      }
                    >
                      <CardContent className="p-4 flex items-start gap-3">
                        <div className="h-10 w-10 rounded-lg bg-blue-100 flex items-center justify-center shrink-0">
                          <Cloud className="h-5 w-5 text-blue-600" />
                        </div>
                        <div className="text-left">
                          <p className="font-medium text-stone-800">
                            Sales Pipeline
                          </p>
                          <p className="text-xs text-stone-500">
                            View opportunities & leads
                          </p>
                        </div>
                      </CardContent>
                    </Card>
                    <Card
                      className="cursor-pointer hover:shadow-md transition-shadow border-2 border-transparent hover:border-forest-200"
                      onClick={() =>
                        handleSendMessage("Check current inventory levels")
                      }
                    >
                      <CardContent className="p-4 flex items-start gap-3">
                        <div className="h-10 w-10 rounded-lg bg-forest-100 flex items-center justify-center shrink-0">
                          <Package className="h-5 w-5 text-forest-600" />
                        </div>
                        <div className="text-left">
                          <p className="font-medium text-stone-800">
                            Inventory Status
                          </p>
                          <p className="text-xs text-stone-500">
                            Check stock & alerts
                          </p>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </div>
              ) : (
                <div className="space-y-2">
                  {messages.map((message, index) => (
                    <ChatMessage
                      key={message.id}
                      message={message}
                      isLatest={index === messages.length - 1}
                    />
                  ))}

                  {/* Typing Indicator */}
                  {isTyping && (
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="flex items-center gap-3 py-4"
                    >
                      <Avatar className="h-9 w-9 bg-gradient-to-br from-stone-500 to-stone-600">
                        <AvatarFallback className="bg-gradient-to-br from-stone-500 to-stone-600 text-white">
                          <Mountain className="h-4 w-4" />
                        </AvatarFallback>
                      </Avatar>
                      <div className="flex items-center gap-1 px-4 py-3 rounded-2xl bg-white border border-stone-200">
                        <div className="typing-indicator flex gap-1">
                          <span className="h-2 w-2 rounded-full bg-stone-400"></span>
                          <span className="h-2 w-2 rounded-full bg-stone-400"></span>
                          <span className="h-2 w-2 rounded-full bg-stone-400"></span>
                        </div>
                      </div>
                    </motion.div>
                  )}

                  <div ref={messagesEndRef} />
                </div>
              )}
            </div>
          </div>

          {/* Input Area */}
          <div className="border-t bg-white/80 backdrop-blur-lg p-4">
            <div className="max-w-3xl mx-auto">
              <ChatInput onSend={handleSendMessage} disabled={isTyping} />
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
