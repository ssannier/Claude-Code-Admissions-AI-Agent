"use client";

import { useState } from "react";
import MapuaLandingPage from "@/components/MapuaLandingPage";
import ChatInterface from "@/components/ChatInterface";

export default function Home() {
  const [showChat, setShowChat] = useState(false);
  const [sessionData, setSessionData] = useState<{
    phoneNumber: string;
    studentName: string;
    sessionId: string;
  } | null>(null);

  const handleFormSubmit = (data: {
    phoneNumber: string;
    studentName: string;
    sessionId: string;
  }) => {
    setSessionData(data);
    setShowChat(true);
  };

  const handleBackToForm = () => {
    setShowChat(false);
    setSessionData(null);
  };

  return (
    <>
      {!showChat ? (
        <MapuaLandingPage onFormSubmit={handleFormSubmit} />
      ) : (
        <main className="min-h-screen bg-gray-100">
          <div className="container mx-auto px-4 py-8">
            <ChatInterface
              sessionData={sessionData!}
              onBack={handleBackToForm}
            />
          </div>
        </main>
      )}
    </>
  );
}
