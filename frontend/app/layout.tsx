import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Pic2Model",
  description: "Image -> part-segmented 3D assets for digital twins",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="flex min-h-screen flex-col">
          <header className="flex items-center gap-6 border-b border-zinc-800 px-6 py-3">
            <Link href="/" className="font-semibold tracking-tight text-zinc-100">
              Pic<span className="text-indigo-400">2</span>Model
            </Link>
            <nav className="flex gap-4 text-sm text-zinc-400">
              <Link href="/create" className="hover:text-zinc-100">Create</Link>
              <Link href="/library" className="hover:text-zinc-100">Library</Link>
            </nav>
            <span className="ml-auto text-xs text-zinc-600">digital-twin asset pipeline</span>
          </header>
          <main className="flex-1">{children}</main>
        </div>
      </body>
    </html>
  );
}
