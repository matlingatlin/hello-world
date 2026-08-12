import type { ReactNode } from "react";
import { SiteHeader } from "../components/site-header";
import "./globals.css";

export const metadata = { title: "Bistro Nord — spike" };

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <SiteHeader />
        <main data-scio-id="main" data-scio-package="pkg_foundation">
          {children}
        </main>
      </body>
    </html>
  );
}
