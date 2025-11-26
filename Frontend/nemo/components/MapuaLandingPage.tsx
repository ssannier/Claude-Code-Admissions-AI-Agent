"use client";

import { useState } from "react";
import Image from "next/image";
import InquiryForm from "./InquiryForm";

interface MapuaLandingPageProps {
  onFormSubmit: (data: {
    phoneNumber: string;
    studentName: string;
    sessionId: string;
  }) => void;
}

export default function MapuaLandingPage({ onFormSubmit }: MapuaLandingPageProps) {
  const scrollToForm = () => {
    const formSection = document.getElementById("inquiry-form-section");
    if (formSection) {
      formSection.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <div className="min-h-screen">
      {/* Navigation Bar */}
      <nav className="sticky top-0 z-50 bg-white shadow-md">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          {/* Logo */}
          <div className="flex items-center">
            <Image
              src="/components/branding/mapua-univ-logo.png"
              alt="Mapua University"
              width={200}
              height={60}
              className="h-12 w-auto"
              priority
            />
          </div>

          {/* Navigation Buttons */}
          <div className="flex items-center gap-4">
            <button
              onClick={scrollToForm}
              className="px-6 py-2 border-2 border-[#9B4444] text-[#9B4444] rounded-lg font-semibold hover:bg-[#9B4444] hover:text-white transition-colors"
            >
              GET HELP
            </button>
            <button
              onClick={scrollToForm}
              className="px-6 py-2 bg-[#9B4444] text-white rounded-lg font-semibold hover:bg-[#7d3636] transition-colors"
            >
              APPLY NOW
            </button>
          </div>
        </div>
      </nav>

      {/* Hero Banner */}
      <section className="bg-gradient-to-r from-[#C47B7B] to-[#B86B6B] py-12 text-center">
        <div className="container mx-auto px-4">
          <button
            onClick={scrollToForm}
            className="px-8 py-3 bg-[#F4B942] text-gray-900 rounded-lg font-bold text-lg hover:bg-[#e5a832] transition-colors shadow-lg"
          >
            FIND YOUR PROGRAM
          </button>
        </div>
      </section>

      {/* About Section */}
      <section className="bg-white py-16">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            {/* Text Column */}
            <div>
              <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6 leading-tight">
                IGNITING EXCELLENCE AS A PREMIER ENGINEERING SCHOOL IN THE PHILIPPINES
              </h1>

              <p className="text-gray-600 mb-4 text-lg leading-relaxed">
                Mapúa University, founded in 1925 by Don Tomas Mapúa, is a world-class
                higher education institution in the Philippines dedicated to providing a
                learning environment rooted in discipline, excellence, commitment,
                integrity, and relevance. Recognized by the 2025 Times Higher Education
                (THE) World University Rankings (WUR) as one of the best schools in the
                world, our academic stronghold provides a diverse array of programs
                grounded in engineering and science, architecture and design, information
                technology, business and health sciences, and media studies.
              </p>

              <p className="text-gray-600 mb-8 text-lg leading-relaxed">
                Our goal is to foster an atmosphere that promotes academic rigor and
                practical expertise, enabling students to compete on a global scale. And
                with strong moral fibers and first-rate student support, graduates are
                empowered to make a lasting and meaningful impact.
              </p>

              <div className="flex gap-4">
                <button
                  onClick={scrollToForm}
                  className="px-6 py-3 bg-[#9B4444] text-white rounded-lg font-semibold hover:bg-[#7d3636] transition-colors"
                >
                  INQUIRE NOW
                </button>
                <button
                  onClick={() => alert('About Us page - to be implemented')}
                  className="px-6 py-3 border-2 border-[#9B4444] text-[#9B4444] rounded-lg font-semibold hover:bg-[#9B4444] hover:text-white transition-colors"
                >
                  ABOUT US →
                </button>
              </div>
            </div>

            {/* Image Column */}
            <div className="relative h-[500px] rounded-lg overflow-hidden shadow-xl">
              <Image
                src="/components/branding/img-mapua-sec-1.webp"
                alt="Mapua University Students"
                fill
                className="object-cover"
                sizes="(max-width: 1024px) 100vw, 50vw"
                priority
              />
            </div>
          </div>
        </div>
      </section>

      {/* Inquiry Form Section */}
      <section id="inquiry-form-section" className="bg-gray-100 py-16">
        <div className="container mx-auto px-4">
          <InquiryForm onSubmitSuccess={onFormSubmit} />
        </div>
      </section>
    </div>
  );
}
