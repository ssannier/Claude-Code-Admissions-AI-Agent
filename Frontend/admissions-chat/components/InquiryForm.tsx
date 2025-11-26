"use client";

import { useState, FormEvent } from "react";

interface InquiryFormProps {
  onSubmitSuccess: (data: {
    phoneNumber: string;
    studentName: string;
    sessionId: string;
  }) => void;
}

export default function InquiryForm({ onSubmitSuccess }: InquiryFormProps) {
  const [formData, setFormData] = useState({
    firstName: "",
    lastName: "",
    email: "",
    cellPhone: "",
    headquarters: "",
    programType: "",
    timingPreference: "2 hours",
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:3001";
      const response = await fetch(`${apiUrl}/submit`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || "Failed to submit form");
      }

      // Generate session ID (in production, this would come from the backend)
      const sessionId = `session-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;

      // Success - proceed to chat
      onSubmitSuccess({
        phoneNumber: formData.cellPhone,
        studentName: `${formData.firstName} ${formData.lastName}`,
        sessionId,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  return (
    <div className="max-w-2xl mx-auto bg-white rounded-lg shadow-lg p-8">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">
        Start Your Admissions Journey
      </h2>
      <p className="text-gray-600 mb-6">
        Fill out the form below to connect with our AI admissions advisor.
      </p>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="firstName" className="block text-sm font-medium text-gray-700 mb-1">
              First Name *
            </label>
            <input
              type="text"
              id="firstName"
              name="firstName"
              value={formData.firstName}
              onChange={handleChange}
              required
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div>
            <label htmlFor="lastName" className="block text-sm font-medium text-gray-700 mb-1">
              Last Name *
            </label>
            <input
              type="text"
              id="lastName"
              name="lastName"
              value={formData.lastName}
              onChange={handleChange}
              required
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>

        <div>
          <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
            Email Address *
          </label>
          <input
            type="email"
            id="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            required
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        <div>
          <label htmlFor="cellPhone" className="block text-sm font-medium text-gray-700 mb-1">
            Cell Phone *
          </label>
          <input
            type="tel"
            id="cellPhone"
            name="cellPhone"
            value={formData.cellPhone}
            onChange={handleChange}
            placeholder="+1234567890"
            required
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="headquarters" className="block text-sm font-medium text-gray-700 mb-1">
              Preferred Campus *
            </label>
            <select
              id="headquarters"
              name="headquarters"
              value={formData.headquarters}
              onChange={handleChange}
              required
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">Select Campus</option>
              <option value="Manila">Manila</option>
              <option value="Makati">Makati</option>
              <option value="Cebu">Cebu</option>
              <option value="Davao">Davao</option>
            </select>
          </div>

          <div>
            <label htmlFor="programType" className="block text-sm font-medium text-gray-700 mb-1">
              Program Type *
            </label>
            <select
              id="programType"
              name="programType"
              value={formData.programType}
              onChange={handleChange}
              required
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">Select Program</option>
              <option value="Undergraduate">Undergraduate</option>
              <option value="Graduate">Graduate</option>
              <option value="Doctorate">Doctorate</option>
            </select>
          </div>
        </div>

        <div>
          <label htmlFor="timingPreference" className="block text-sm font-medium text-gray-700 mb-1">
            When should we contact you?
          </label>
          <select
            id="timingPreference"
            name="timingPreference"
            value={formData.timingPreference}
            onChange={handleChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="as soon as possible">As soon as possible</option>
            <option value="2 hours">In 2 hours</option>
            <option value="4 hours">In 4 hours</option>
            <option value="tomorrow morning">Tomorrow morning</option>
          </select>
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          {isSubmitting ? "Submitting..." : "Start Chat with AI Advisor"}
        </button>
      </form>
    </div>
  );
}
