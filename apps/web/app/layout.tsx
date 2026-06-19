import "./styles.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Dossier",
  description: "DevSecOps report generator for findings, remediation plans, and stakeholder summaries"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
