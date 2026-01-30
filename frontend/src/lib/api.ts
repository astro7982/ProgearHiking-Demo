import { getIdToken } from "./okta";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: Date;
  agent?: AgentInfo;
  toolCalls?: ToolCall[];
}

export interface AgentInfo {
  name: string;
  type: "salesforce" | "inventory" | "orchestrator";
  scopes: string[];
}

export interface ToolCall {
  id: string;
  name: string;
  status: "pending" | "running" | "completed" | "error";
  result?: unknown;
  duration?: number;
}

export interface UserAccess {
  salesforce: {
    connected: boolean;
    scopes: string[];
  };
  inventory: {
    authorized: boolean;
    scopes: string[];
  };
}

export interface ChatRequest {
  message: string;
  conversation_id?: string;
}

export interface ChatResponse {
  id: string;
  message: string;
  agent: AgentInfo;
  tool_calls: ToolCall[];
  conversation_id: string;
}

async function fetchWithAuth(
  endpoint: string,
  options: RequestInit = {}
): Promise<Response> {
  const idToken = await getIdToken();

  if (!idToken) {
    throw new Error("Not authenticated");
  }

  const headers = new Headers(options.headers);
  headers.set("Authorization", `Bearer ${idToken}`);
  headers.set("Content-Type", "application/json");

  return fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
  });
}

export async function sendChatMessage(
  request: ChatRequest
): Promise<ChatResponse> {
  const response = await fetchWithAuth("/api/chat", {
    method: "POST",
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to send message");
  }

  return response.json();
}

export async function getUserAccess(): Promise<UserAccess> {
  const response = await fetchWithAuth("/api/user/access");

  if (!response.ok) {
    throw new Error("Failed to get user access");
  }

  return response.json();
}

export async function connectSalesforce(): Promise<{ auth_url: string }> {
  const response = await fetchWithAuth("/api/salesforce/connect", {
    method: "POST",
  });

  if (!response.ok) {
    throw new Error("Failed to initiate Salesforce connection");
  }

  return response.json();
}

export async function disconnectSalesforce(): Promise<void> {
  const response = await fetchWithAuth("/api/salesforce/disconnect", {
    method: "POST",
  });

  if (!response.ok) {
    throw new Error("Failed to disconnect Salesforce");
  }
}

export async function getConversationHistory(
  conversationId: string
): Promise<ChatMessage[]> {
  const response = await fetchWithAuth(
    `/api/conversations/${conversationId}/messages`
  );

  if (!response.ok) {
    throw new Error("Failed to get conversation history");
  }

  return response.json();
}

export async function streamChat(
  request: ChatRequest,
  onChunk: (chunk: string) => void,
  onToolCall: (toolCall: ToolCall) => void,
  onComplete: (response: ChatResponse) => void,
  onError: (error: Error) => void
): Promise<void> {
  try {
    const idToken = await getIdToken();

    if (!idToken) {
      throw new Error("Not authenticated");
    }

    const response = await fetch(`${API_URL}/api/chat/stream`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${idToken}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to send message");
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) {
      throw new Error("No response body");
    }

    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();

      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const data = line.slice(6);
          if (data === "[DONE]") {
            continue;
          }

          try {
            const parsed = JSON.parse(data);

            if (parsed.type === "chunk") {
              onChunk(parsed.content);
            } else if (parsed.type === "tool_call") {
              onToolCall(parsed.tool_call);
            } else if (parsed.type === "complete") {
              onComplete(parsed.response);
            }
          } catch {
            // Ignore parse errors for partial chunks
          }
        }
      }
    }
  } catch (error) {
    onError(error instanceof Error ? error : new Error("Unknown error"));
  }
}
