import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Mia OB-GYN | Women's Health OS",
  description: "Synthetic-data women’s health workflow prototype with source-first OB-GYN references.",
  robots: { index: false, follow: false },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en" suppressHydrationWarning><body>{children}</body></html>;
}
