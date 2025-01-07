import './globals.css'
import { Inter } from 'next/font/google'

const inter = Inter({ subsets: ['latin'] })

export const metadata = {
  title: 'Sales Copilot Agents',
  description: 'Synthesize customer feedback into actionable insights',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body className={`${inter.className} bg-[#111111] text-white`} suppressHydrationWarning>
        {children}
      </body>
    </html>
  )
}
