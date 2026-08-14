import "./globals.css";

export const metadata = { title: "Local-data spike" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body data-scio-id="app-shell" data-scio-package="pkg_foundation">{children}</body>
    </html>
  );
}
