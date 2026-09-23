import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "NFL Intelligence Platform",
  description:
    "A leak-free, walk-forward-validated NFL win probability model with a live prediction platform.",
};

const NAV_LINKS = [
  {
    href: "/",
    label: "Home",
    enabled: true,
  },
  {
    href: "/model-performance",
    label: "Model Performance",
    enabled: true,
  },
  {
    href: "/predictions",
    label: "Predictions",
    enabled: true,
  },
];

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${jetbrainsMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <header className="border-b border-border">
          <div className="mx-auto max-w-6xl px-6 py-5 flex items-center justify-between gap-6">
            <Link href="/" className="flex items-center gap-3 shrink-0">
              <span className="h-2 w-2 rounded-full bg-foreground" />
              <span className="text-sm font-semibold tracking-tight">
                NFL Intelligence Platform
              </span>
            </Link>
            <nav className="flex items-center gap-6 overflow-x-auto">
              {NAV_LINKS.map((link) =>
                link.enabled ? (
                  <Link
                    key={link.href}
                    href={link.href}
                    className="text-sm text-muted hover:text-foreground transition-colors whitespace-nowrap"
                  >
                    {link.label}
                  </Link>
                ) : (
                  <span
                    key={link.href}
                    className="text-sm text-gray-400 whitespace-nowrap cursor-default"
                    title="Coming soon"
                  >
                    {link.label}
                  </span>
                ),
              )}
            </nav>
          </div>
        </header>
        <main className="flex-1">{children}</main>
        <footer className="border-t border-border">
          <div className="mx-auto max-w-6xl px-6 py-6 text-xs text-muted">
            Leak-free EPA features &middot; walk-forward validation &middot;
            logistic regression
          </div>
        </footer>
      </body>
    </html>
  );
}
