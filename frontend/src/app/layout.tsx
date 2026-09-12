import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Jerry - AI Executive Agent",
  description: "Executive AI Chief of Staff & Operations Agent",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased min-h-screen bg-slate-950 text-slate-50">
        {children}
      </body>
    </html>
  );
}
