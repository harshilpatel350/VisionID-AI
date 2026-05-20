import "./globals.css";
import Providers from "@/components/providers";

export const metadata = {
  title: "VisionID AI",
  description: "Face Registry & Recognition Platform",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body suppressHydrationWarning>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
