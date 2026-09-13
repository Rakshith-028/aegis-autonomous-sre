import type { Metadata } from "next";
import "./globals.css";


export const metadata: Metadata = {
  title: "AEGIS | Autonomous SRE Command Center",
  description:
    "Autonomous observability, root-cause analysis and self-healing control plane.",
};


export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
