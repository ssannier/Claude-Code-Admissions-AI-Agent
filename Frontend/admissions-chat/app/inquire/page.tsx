"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import InquiryForm from "@/components/InquiryForm";

export default function InquirePage() {
  const router = useRouter();

  const handleFormSubmit = (data: {
    phoneNumber: string;
    studentName: string;
    sessionId: string;
  }) => {
    // Store session data in sessionStorage for the chat page
    sessionStorage.setItem("chatSession", JSON.stringify(data));
    // Navigate to chat page
    router.push("/chat");
  };

  return (
    <main className="min-h-screen bg-gray-100">
      <div className="container mx-auto px-4 py-8">
        <InquiryForm onSubmitSuccess={handleFormSubmit} />
      </div>
    </main>
  );
}
