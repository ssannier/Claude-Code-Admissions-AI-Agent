"use client";

import { useState, useRef, useEffect } from "react";
import Image from "next/image";
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
    <div className="max-w-4xl mx-auto bg-white rounded-lg shadow-xl overflow-hidden flex flex-col" style={{ height: "calc(100vh - 200px)" }}>
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Image
            src="/logo-mapua-nemo-rot-1.png"
            alt="Nemo"
            width={40}
            height={40}
            className="rounded-full"
          />
          <div>
            <h2 className="text-lg font-bold text-gray-900">Nemo</h2>
            <p className="text-sm text-gray-500">
              AI Virtual Admissions Advisor
            </p>
          </div>
        </div>
        <button
          onClick={onBack}
          className="text-gray-400 hover:text-gray-600 transition-colors"
          aria-label="Close chat"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Welcome Message */}
        <div className="flex items-start space-x-3">
          <Image
            src="/logo-mapua-nemo-rot-1.png"
            alt="Nemo"
            width={32}
            height={32}
            className="rounded-full flex-shrink-0"
          />
          <div className="bg-gray-100 rounded-lg p-4 max-w-[80%]">
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
            className={`flex items-start space-x-3 ${
              message.role === "user" ? "flex-row-reverse space-x-reverse" : ""
            }`}
          >
            {message.role === "user" ? (
              <div className="w-8 h-8 rounded-full bg-[#9B4444] flex items-center justify-center text-white font-bold flex-shrink-0">
                U
              </div>
            ) : (
              <Image
                src="/logo-mapua-nemo-rot-1.png"
                alt="Nemo"
                width={32}
                height={32}
                className="rounded-full flex-shrink-0"
              />
            )}
            <div className="flex flex-col max-w-[80%]">
              <div
                className={`rounded-lg p-4 ${
                  message.role === "user"
                    ? "bg-[#F5D5D5] text-gray-800"
                    : "bg-gray-100 text-gray-800"
                }`}
              >
                <p className="whitespace-pre-wrap">{message.content}</p>
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
          <div className="flex items-start space-x-3">
            <Image
              src="/logo-mapua-nemo-rot-1.png"
              alt="Nemo"
              width={32}
              height={32}
              className="rounded-full flex-shrink-0"
            />
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 max-w-[80%]">
              <div className="flex items-center gap-2 text-blue-800 text-sm">
                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>{toolStatus}</span>
              </div>
            </div>
          </div>
        )}

        {/* Current Streaming Response */}
        {isStreaming && currentResponse && (
          <div className="flex items-start space-x-3">
            <Image
              src="/logo-mapua-nemo-rot-1.png"
              alt="Nemo"
              width={32}
              height={32}
              className="rounded-full flex-shrink-0"
            />
            <div className="bg-gray-100 rounded-lg p-4 max-w-[80%]">
              <p className="whitespace-pre-wrap">{currentResponse}</p>
              <span className="inline-block w-2 h-4 bg-gray-600 animate-pulse ml-1"></span>
            </div>
          </div>
        )}

        {/* Loading Indicator */}
        {isStreaming && !currentResponse && (
          <div className="flex items-start space-x-3">
            <Image
              src="/logo-mapua-nemo-rot-1.png"
              alt="Nemo"
              width={32}
              height={32}
              className="rounded-full flex-shrink-0"
            />
            <div className="bg-gray-100 rounded-lg p-4 inline-flex items-center gap-2">
              <svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <span className="text-gray-600 text-sm">Searching...</span>
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
      <div className="border-t border-gray-200 p-4 bg-white">
        <form onSubmit={handleSubmit} className="flex items-center gap-3">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            disabled={isStreaming}
            placeholder="Ask me about programs, scholarships, or admissions..."
            className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#9B4444] focus:border-transparent disabled:bg-gray-100 text-gray-900 placeholder:text-gray-400"
          />
          <button
            type="submit"
            disabled={isStreaming || !inputValue.trim()}
            className="w-12 h-12 bg-[#9B4444] text-white rounded-full font-semibold hover:bg-[#7d3636] disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center justify-center flex-shrink-0"
            aria-label="Send message"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </form>
      </div>
    </div>
  );
}
