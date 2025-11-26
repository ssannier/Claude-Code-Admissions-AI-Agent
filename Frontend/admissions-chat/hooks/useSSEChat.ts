"use client";

import { useState, useCallback, useRef } from "react";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

export interface SSEEvent {
  response?: string;        // Streaming text chunk
  thinking?: string;        // Tool usage indicator
  tool_result?: string;     // Tool execution result
  final_result?: string;    // Complete response
  error?: string;           // Error message
}

interface UseSSEChatOptions {
  agentProxyUrl: string;
  sessionId: string;
  phoneNumber?: string;
  studentName?: string;
}

export function useSSEChat({
  agentProxyUrl,
  sessionId,
  phoneNumber,
  studentName,
}: UseSSEChatOptions) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentResponse, setCurrentResponse] = useState("");
  const [toolStatus, setToolStatus] = useState<string | null>(null);

  const eventSourceRef = useRef<EventSource | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(
    async (prompt: string) => {
      // Add user message
      const userMessage: ChatMessage = {
        role: "user",
        content: prompt,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, userMessage]);
      setIsStreaming(true);
      setError(null);
      setCurrentResponse("");
      setToolStatus(null);

      try {
        // Create abort controller
        abortControllerRef.current = new AbortController();

        // Send request to Agent Proxy
        const response = await fetch(agentProxyUrl, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Accept: "text/event-stream",
          },
          body: JSON.stringify({
            prompt,
            session_id: sessionId,
            phone_number: phoneNumber,
            student_name: studentName,
          }),
          signal: abortControllerRef.current.signal,
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        // Check if response is SSE
        const contentType = response.headers.get("content-type");
        if (!contentType?.includes("text/event-stream")) {
          throw new Error("Expected SSE response but got: " + contentType);
        }

        // Process SSE stream
        const reader = response.body?.getReader();
        const decoder = new TextDecoder();

        if (!reader) {
          throw new Error("No response body");
        }

        let accumulatedText = "";

        while (true) {
          const { done, value } = await reader.read();

          if (done) {
            break;
          }

          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split("\n");

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              const data = line.substring(6);

              try {
                const event: SSEEvent = JSON.parse(data);

                // Handle response chunks (streaming text)
                if (event.response) {
                  accumulatedText += event.response;
                  setCurrentResponse(accumulatedText);
                }

                // Handle thinking indicators (tool usage)
                if (event.thinking) {
                  setToolStatus(event.thinking);
                  // Don't add to accumulated text, just show as status
                }

                // Handle tool results
                if (event.tool_result) {
                  setToolStatus("Tool execution completed");
                  // Clear tool status after a moment
                  setTimeout(() => setToolStatus(null), 2000);
                }

                // Handle final result (completion)
                if (event.final_result) {
                  const assistantMessage: ChatMessage = {
                    role: "assistant",
                    content: event.final_result,
                    timestamp: new Date(),
                  };
                  setMessages((prev) => [...prev, assistantMessage]);
                  setCurrentResponse("");
                  setToolStatus(null);
                }

                // Handle errors
                if (event.error) {
                  throw new Error(event.error);
                }
              } catch (parseError) {
                console.warn("Failed to parse SSE event:", data, parseError);
              }
            }
          }
        }
      } catch (err) {
        if (err instanceof Error) {
          if (err.name === "AbortError") {
            console.log("Request aborted");
          } else {
            console.error("Chat error:", err);
            setError(err.message || "Failed to communicate with agent");
          }
        }
      } finally {
        setIsStreaming(false);
        abortControllerRef.current = null;
      }
    },
    [agentProxyUrl, sessionId, phoneNumber, studentName]
  );

  const cancelStream = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }
    setIsStreaming(false);
  }, []);

  return {
    messages,
    isStreaming,
    error,
    currentResponse,
    toolStatus,
    sendMessage,
    cancelStream,
  };
}
