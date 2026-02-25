import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata = {
  title: "StrategyVault — AI-Powered Trading Strategy Marketplace",
  description:
    "Discover, validate, and purchase AI-generated trading strategies with multi-model consensus ratings and walk-forward validation.",
  keywords: "trading strategies, AI, backtesting, algorithmic trading, marketplace",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className={inter.variable}>
      <body>
        {/* Navigation */}
        <nav className="nav-bar">
          <div className="nav-inner">
            <a href="/" className="nav-logo">
              <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
                <rect width="28" height="28" rx="8" fill="url(#logo-grad)" />
                <path d="M8 14L12 10L16 14L20 8" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                <path d="M8 20L12 16L16 20L20 14" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" opacity="0.5" />
                <defs>
                  <linearGradient id="logo-grad" x1="0" y1="0" x2="28" y2="28">
                    <stop stopColor="#6366f1" />
                    <stop offset="1" stopColor="#7c3aed" />
                  </linearGradient>
                </defs>
              </svg>
              <span>StrategyVault</span>
            </a>

            <div className="nav-links">
              <a href="/" className="nav-link active">Marketplace</a>
              <a href="/generate" className="nav-link">Generate</a>
              <a href="/dashboard" className="nav-link">Dashboard</a>
            </div>

            <div className="nav-actions">
              <button className="btn-secondary" style={{ padding: '8px 16px', fontSize: '0.8rem' }}>Sign In</button>
              <button className="btn-primary" style={{ padding: '8px 16px', fontSize: '0.8rem' }}>Get Started</button>
            </div>
          </div>
        </nav>

        <main>{children}</main>

        {/* Footer */}
        <footer className="site-footer">
          <div className="footer-inner">
            <div className="footer-brand">
              <span className="footer-logo">StrategyVault</span>
              <p className="footer-desc">AI-Powered Trading Strategy Marketplace</p>
            </div>
            <div className="footer-links">
              <div>
                <h4>Platform</h4>
                <a href="/">Marketplace</a>
                <a href="/generate">Generate</a>
                <a href="/pricing">Pricing</a>
              </div>
              <div>
                <h4>Resources</h4>
                <a href="/docs">Documentation</a>
                <a href="/blog">Blog</a>
                <a href="/support">Support</a>
              </div>
              <div>
                <h4>Legal</h4>
                <a href="/terms">Terms</a>
                <a href="/privacy">Privacy</a>
                <a href="/disclaimer">Disclaimer</a>
              </div>
            </div>
          </div>
          <div className="footer-bottom">
            <p>© 2026 StrategyVault. For educational purposes only. Not financial advice.</p>
          </div>
        </footer>
      </body>
    </html>
  );
}
