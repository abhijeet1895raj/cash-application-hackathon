import "./globals.css";

export const metadata = {
  title: "Cash Application Foundry - Azure AI Agent Service",
  description: "Intelligent cash application powered by Azure AI Foundry Agent Service",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
