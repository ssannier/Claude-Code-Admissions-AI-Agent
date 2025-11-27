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
    homePhone: "",
    headquarters: "",
    programType: "",
    privacyConsent: false,
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
    const { name, value, type } = e.target;
    const checked = (e.target as HTMLInputElement).checked;

    setFormData({
      ...formData,
      [name]: type === "checkbox" ? checked : value,
    });
  };

  return (
    <div className="max-w-2xl mx-auto bg-white rounded-lg shadow-lg p-8">
      <h2 className="text-3xl font-bold text-center mb-2">
        <span className="text-gray-900">REQUEST</span> <span className="text-[#9B4444]">INFORMATION</span>
      </h2>
      <p className="text-gray-600 text-center mb-8">
        Fill out the form below and we'll get back to you soon
      </p>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Line 1: Campus / Location */}
        <div>
          <label htmlFor="headquarters" className="block text-sm font-medium text-gray-700 mb-1">
            Campus / Location *
          </label>
          <select
            id="headquarters"
            name="headquarters"
            value={formData.headquarters}
            onChange={handleChange}
            required
            className={`w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#9B4444] focus:border-transparent ${formData.headquarters ? 'text-gray-900' : 'text-gray-400'}`}
          >
            <option value="" disabled hidden>Select a campus...</option>
            <option value="Manila" className="text-gray-900">Manila</option>
            <option value="Makati" className="text-gray-900">Makati</option>
            <option value="Cebu" className="text-gray-900">Cebu</option>
            <option value="Davao" className="text-gray-900">Davao</option>
          </select>
        </div>

        {/* Line 2: Program Type */}
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
            className={`w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#9B4444] focus:border-transparent ${formData.programType ? 'text-gray-900' : 'text-gray-400'}`}
          >
            <option value="" disabled hidden>Select a program type...</option>
            <option value="Undergraduate" className="text-gray-900">Undergraduate</option>
            <option value="Graduate" className="text-gray-900">Graduate</option>
            <option value="Senior High School" className="text-gray-900">Senior High School</option>
            <option value="Fully Online" className="text-gray-900">Fully Online</option>
          </select>
        </div>

        {/* Line 3: First Name and Last Name */}
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
              placeholder="Juan"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#9B4444] focus:border-transparent text-gray-900 placeholder:text-gray-400"
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
              placeholder="Dela Cruz"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#9B4444] focus:border-transparent text-gray-900 placeholder:text-gray-400"
            />
          </div>
        </div>

        {/* Line 4: Email Address */}
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
            placeholder="juan.delacruz@example.com"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#9B4444] focus:border-transparent text-gray-900 placeholder:text-gray-400"
          />
        </div>

        {/* Line 5: Cell Phone and Home Phone */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
              required
              placeholder="+63 912 345 6789"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#9B4444] focus:border-transparent text-gray-900 placeholder:text-gray-400"
            />
          </div>

          <div>
            <label htmlFor="homePhone" className="block text-sm font-medium text-gray-700 mb-1">
              Home Phone <span className="text-gray-500">(Optional)</span>
            </label>
            <input
              type="tel"
              id="homePhone"
              name="homePhone"
              value={formData.homePhone}
              onChange={handleChange}
              placeholder="(02) 1234 5678"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#9B4444] focus:border-transparent text-gray-900 placeholder:text-gray-400"
            />
          </div>
        </div>

        {/* Privacy Policy Checkbox */}
        <div className="flex items-start gap-3 p-4 bg-gray-50 rounded-lg">
          <input
            type="checkbox"
            id="privacyConsent"
            name="privacyConsent"
            checked={formData.privacyConsent}
            onChange={handleChange}
            required
            className="mt-1 h-4 w-4 text-[#9B4444] focus:ring-[#9B4444] border-gray-300 rounded"
          />
          <label htmlFor="privacyConsent" className="text-sm text-gray-700">
            I authorize Mapuia University to verify the authenticity of the information provided and
            use it for academic, administrative, and marketing purposes. I understand that my data
            will be processed in accordance with the{" "}
            <a
              href="#"
              className="text-[#9B4444] hover:underline font-medium"
              onClick={(e) => {
                e.preventDefault();
                // Placeholder for privacy policy link
                alert("Privacy Policy link - to be implemented");
              }}
            >
              Mapuia Privacy Policy
            </a>
            . I have the right to request access, rectification, or deletion of my data at any time. *
          </label>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full bg-[#9B4444] text-white py-3 px-6 rounded-lg font-semibold hover:bg-[#7d3636] disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          {isSubmitting ? "Submitting..." : "Submit Request"}
        </button>
      </form>
    </div>
  );
}
