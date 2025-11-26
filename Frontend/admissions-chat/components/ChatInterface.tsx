"use client";

import { useState, useRef, useEffect } from "react";
import { useSSEChat } from "@/hooks/useSSEChat";

interface ChatInterfaceProps {
  sessionData: {
    phoneNumber: string;
    studentName: string;
    sessionId: string;
  };
  onBack: () => void;
}

export default function ChatInterface({ sessionData, onBack }: ChatInterfaceProps) {
  const [inputValue, setInputValue] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const agentProxyUrl = process.env.NEXT_PUBLIC_AGENT_PROXY_URL || "http://localhost:3002";

  const { messages, isStreaming, error, currentResponse, toolStatus, sendMessage } = useSSEChat({
    agentProxyUrl,
    sessionId: sessionData.sessionId,
    phoneNumber: sessionData.phoneNumber,
    studentName: sessionData.studentName,
  });

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, currentResponse]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!inputValue.trim() || isStreaming) return;

    const prompt = inputValue.trim();
    setInputValue("");
    await sendMessage(prompt);
  };

  return (
    <div className="max-w-4xl mx-auto bg-white rounded-lg shadow-lg overflow-hidden flex flex-col" style={{ height: "calc(100vh - 200px)" }}>
      {/* Header */}
      <div className="bg-blue-600 text-white p-4 flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold">AI Admissions Advisor</h2>
          <p className="text-sm opacity-90">
            Chatting as {sessionData.studentName}
          </p>
        </div>
        <button
          onClick={onBack}
          className="px-4 py-2 bg-blue-700 hover:bg-blue-800 rounded-lg text-sm font-medium transition-colors"
        >
          Back to Form
        </button>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Welcome Message */}
        <div className="flex items-start space-x-2">
          <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold flex-shrink-0">
            AI
          </div>
          <div className="bg-gray-100 rounded-lg p-3 max-w-[80%]">
            <p className="text-gray-800">
              Hello {sessionData.studentName}! I'm your AI admissions advisor. I'm here to help you with:
            </p>
            <ul className="mt-2 space-y-1 text-sm text-gray-700">
              <li>• Admission requirements and deadlines</li>
              <li>• Program information</li>
              <li>• Application status</li>
              <li>• Financial aid and scholarships</li>
            </ul>
            <p className="mt-2 text-gray-800">
              How can I assist you today?
            </p>
          </div>
        </div>

        {/* Chat Messages */}
        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex items-start space-x-2 ${
              message.role === "user" ? "flex-row-reverse space-x-reverse" : ""
            }`}
          >
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-bold flex-shrink-0 ${
                message.role === "user" ? "bg-green-600" : "bg-blue-600"
              }`}
            >
              {message.role === "user" ? "U" : "AI"}
            </div>
            <div className="flex flex-col max-w-[80%]">
              <div
                className={`rounded-lg p-3 ${
                  message.role === "user"
                    ? "bg-green-100 text-gray-800"
                    : "bg-gray-100 text-gray-800"
                }`}
              >
                <p className="whitespace-pre-wrap">{message.content}</p>
                <p className="text-xs text-gray-500 mt-1">
                  {message.timestamp.toLocaleTimeString()}
                </p>
              </div>
              {/* Regenerate button for AI messages (Property 6-7) */}
              {message.role === "assistant" && index === messages.length - 1 && !isStreaming && (
                <button
                  onClick={() => {
                    // Find the last user message
                    const lastUserMessage = [...messages].reverse().find(m => m.role === "user");
                    if (lastUserMessage) {
                      sendMessage(lastUserMessage.content);
                    }
                  }}
                  className="mt-2 px-3 py-1 text-xs text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-md transition-colors self-start"
                >
                  🔄 Regenerate response
                </button>
              )}
            </div>
          </div>
        ))}

        {/* Tool Status Indicator (Property 11, 18, 40) */}
        {toolStatus && (
          <div className="flex items-start space-x-2">
            <div className="w-8 h-8 rounded-full bg-yellow-500 flex items-center justify-center text-white font-bold flex-shrink-0">
              🔧
            </div>
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 max-w-[80%]">
              <p className="text-yellow-800 text-sm">{toolStatus}</p>
            </div>
          </div>
        )}

        {/* Current Streaming Response */}
        {isStreaming && currentResponse && (
          <div className="flex items-start space-x-2">
            <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold flex-shrink-0">
              AI
            </div>
            <div className="bg-gray-100 rounded-lg p-3 max-w-[80%]">
              <p className="whitespace-pre-wrap">{currentResponse}</p>
              <span className="inline-block w-2 h-4 bg-blue-600 animate-pulse ml-1"></span>
            </div>
          </div>
        )}

        {/* Loading Indicator */}
        {isStreaming && !currentResponse && (
          <div className="flex items-start space-x-2">
            <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold flex-shrink-0">
              AI
            </div>
            <div className="bg-gray-100 rounded-lg p-3">
              <div className="flex space-x-2">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }}></div>
              </div>
            </div>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
            <p className="font-semibold">Error:</p>
            <p>{error}</p>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-200 p-4">
        <form onSubmit={handleSubmit} className="flex space-x-2">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            disabled={isStreaming}
            placeholder="Type your question here..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
          />
          <button
            type="submit"
            disabled={isStreaming || !inputValue.trim()}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {isStreaming ? "Sending..." : "Send"}
          </button>
        </form>
        <p className="text-xs text-gray-500 mt-2">
          Session ID: {sessionData.sessionId}
        </p>
      </div>
    </div>
  );
}
