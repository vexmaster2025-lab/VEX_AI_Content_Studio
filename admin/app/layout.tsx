import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'VEX Admin Dashboard',
  description: 'Admin console for VEX AI Content Studio',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
