import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import '../styles/globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Viral Video SaaS - Create TikTok Videos with AI',
  description: 'Generate professional viral TikTok videos in seconds using AI. Create, customize, and share.',
  keywords: 'TikTok, video generation, AI, viral, creator tools',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </head>
      <body className={inter.className}>
        <div className="min-h-screen bg-dark-bg text-white">
          {children}
        </div>
      </body>
    </html>
  )
}
