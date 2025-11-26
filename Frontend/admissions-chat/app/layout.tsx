import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "University Admissions Chat",
  description: "AI-powered admissions assistance for prospective students",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
