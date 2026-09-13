import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "AEGIS | Autonomous SRE",
    template: "%s | AEGIS",
  },
  description:
    "Autonomous SRE control plane for observability, root-cause analysis, safe remediation, and verified recovery.",
  applicationName: "AEGIS",
  keywords: [
    "SRE",
    "Site Reliability Engineering",
    "Self-Healing",
    "Observability",
    "Root Cause Analysis",
    "Prometheus",
    "Docker",
    "FastAPI",
    "Next.js",
    "Chaos Engineering",
  ],
  authors: [
    {
      name: "Rakshith",
    },
  ],
  creator: "Rakshith",
  icons: {
    icon: "/icon.png",
    apple: "/apple-icon.png",
  },
  openGraph: {
    title: "AEGIS | Autonomous SRE",
    description:
      "Autonomous observability, evidence-driven RCA, safe remediation, and verified recovery.",
    type: "website",
    siteName: "AEGIS",
  },
  twitter: {
    card: "summary",
    title: "AEGIS | Autonomous SRE",
    description:
      "Autonomous SRE control plane for detection, diagnosis, remediation, and recovery.",
  },
};

export const viewport: Viewport = {
  themeColor: "#020617",
  colorScheme: "dark",
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