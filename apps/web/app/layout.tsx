import "./styles.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Dossier — DevSecOps Reporting Engine",
  description:
    "Turn raw findings from DevSecOps tools into executive, technical, remediation, compliance, and board-level reports."
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
