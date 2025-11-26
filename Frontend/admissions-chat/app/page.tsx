"use client";

import { useState } from "react";
import InquiryForm from "@/components/InquiryForm";
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
    <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        <header className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            University Admissions
          </h1>
          <p className="text-gray-600">
            AI-powered assistance for prospective students
          </p>
        </header>

        {!showChat ? (
          <InquiryForm onSubmitSuccess={handleFormSubmit} />
        ) : (
          <ChatInterface
            sessionData={sessionData!}
            onBack={handleBackToForm}
          />
        )}
      </div>
    </main>
  );
}
