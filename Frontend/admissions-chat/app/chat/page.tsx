"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import ChatInterface from "@/components/ChatInterface";

export default function ChatPage() {
  const router = useRouter();
  const [sessionData, setSessionData] = useState<{
    phoneNumber: string;
    studentName: string;
    sessionId: string;
  } | null>(null);

  useEffect(() => {
    // Retrieve session data from sessionStorage
    const storedSession = sessionStorage.getItem("chatSession");
    if (storedSession) {
      setSessionData(JSON.parse(storedSession));
    } else {
      // No session data, redirect to inquiry form
      router.push("/inquire");
    }
  }, [router]);

  const handleBackToForm = () => {
    sessionStorage.removeItem("chatSession");
    router.push("/");
  };

  if (!sessionData) {
    return (
      <main className="min-h-screen bg-gray-100 flex items-center justify-center">
        <p>Loading...</p>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <ChatInterface sessionData={sessionData} onBack={handleBackToForm} />
      </div>
    </main>
  );
}
