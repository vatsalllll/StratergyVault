'use client';

import { useState, useEffect } from 'react';
import StrategyCard from '../components/StrategyCard';

// Fallback demo strategies (used if API fails)
const DEMO_STRATEGIES = [
  {
    id: 1, name: 'MomentumAlpha', description: 'Trend-following strategy using RSI and dual SMA crossover with volatility-adaptive position sizing.',
    return_pct: 42.3, sharpe_ratio: 1.85, max_drawdown_pct: -12.4, consensus_vote: 'BUY', consensus_confidence: 0.92,
    strategy_score: 91, tier: 'gold', credit_cost: 1, is_featured: true,
  },
  {
    id: 2, name: 'VolBreakout', description: 'Bollinger Band breakout strategy with MACD confirmation and ATR-based stop losses.',
    return_pct: 35.7, sharpe_ratio: 1.62, max_drawdown_pct: -17.2, consensus_vote: 'BUY', consensus_confidence: 0.83,
    strategy_score: 87, tier: 'gold', credit_cost: 1, is_featured: true,
  },
  {
    id: 3, name: 'MeanRevertRSI', description: 'Mean reversion strategy buying oversold conditions with regime-aware market filtering.',
    return_pct: 28.1, sharpe_ratio: 1.45, max_drawdown_pct: -9.8, consensus_vote: 'BUY', consensus_confidence: 0.75,
    strategy_score: 82, tier: 'silver', credit_cost: 1, is_featured: false,
  },
  {
    id: 4, name: 'TrendRider', description: 'Multi-timeframe trend following with adaptive trailing stops and momentum confirmation.',
    return_pct: 31.5, sharpe_ratio: 1.38, max_drawdown_pct: -14.1, consensus_vote: 'BUY', consensus_confidence: 0.78,
    strategy_score: 78, tier: 'silver', credit_cost: 1, is_featured: false,
  },
  {
    id: 5, name: 'ScalpVWAP', description: 'Intraday VWAP-based scalping strategy with volume profile analysis and tight risk management.',
    return_pct: 18.9, sharpe_ratio: 1.12, max_drawdown_pct: -8.3, consensus_vote: 'HOLD', consensus_confidence: 0.58,
    strategy_score: 72, tier: 'silver', credit_cost: 1, is_featured: false,
  },
  {
    id: 6, name: 'SwingMACD', description: 'Swing trading using MACD divergences with Fibonacci retracement targets.',
    return_pct: 22.4, sharpe_ratio: 0.95, max_drawdown_pct: -19.6, consensus_vote: 'HOLD', consensus_confidence: 0.65,
    strategy_score: 65, tier: 'bronze', credit_cost: 1, is_featured: false,
  },
  {
    id: 7, name: 'GridTrader', description: 'Range-bound grid trading strategy optimized for sideways markets with dynamic grid spacing.',
    return_pct: 15.2, sharpe_ratio: 0.88, max_drawdown_pct: -11.5, consensus_vote: 'HOLD', consensus_confidence: 0.52,
    strategy_score: 58, tier: 'bronze', credit_cost: 1, is_featured: false,
  },
  {
    id: 8, name: 'ChannelBreak', description: 'Donchian Channel breakout with volume and volatility filters for trend entry confirmation.',
    return_pct: 19.8, sharpe_ratio: 1.05, max_drawdown_pct: -16.3, consensus_vote: 'BUY', consensus_confidence: 0.70,
    strategy_score: 73, tier: 'silver', credit_cost: 1, is_featured: false,
  },
];

const API_BASE = 'http://localhost:8000/api/v1';
const TIER_FILTERS = ['all', 'gold', 'silver', 'bronze'];

export default function Home() {
  const [strategies, setStrategies] = useState(DEMO_STRATEGIES);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTier, setActiveTier] = useState('all');
  const [sortBy, setSortBy] = useState('score');
  const [loading, setLoading] = useState(true);
  const [dataSource, setDataSource] = useState('demo'); // 'api' or 'demo'

  // Fetch strategies from API on mount
  useEffect(() => {
    async function fetchStrategies() {
      try {
        const res = await fetch(`${API_BASE}/strategies/?per_page=50`);
        if (!res.ok) throw new Error('API error');
        const data = await res.json();
        if (data.strategies && data.strategies.length > 0) {
          setStrategies(data.strategies);
          setDataSource('api');
        } else {
          // API returned empty — use demo data
          setDataSource('demo');
        }
      } catch (err) {
        console.warn('Backend API not available, using demo data', err);
        setDataSource('demo');
      } finally {
        setLoading(false);
      }
    }
    fetchStrategies();
  }, []);

  // Filter and sort strategies
  let filtered = strategies.filter(s => {
    if (activeTier !== 'all' && s.tier !== activeTier) return false;
    if (searchQuery && !s.name.toLowerCase().includes(searchQuery.toLowerCase()) &&
      !s.description.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  filtered.sort((a, b) => {
    if (sortBy === 'score') return (b.strategy_score || 0) - (a.strategy_score || 0);
    if (sortBy === 'return') return (b.return_pct || 0) - (a.return_pct || 0);
    if (sortBy === 'sharpe') return (b.sharpe_ratio || 0) - (a.sharpe_ratio || 0);
    return 0;
  });

  const goldCount = strategies.filter(s => s.tier === 'gold').length;
  const silverCount = strategies.filter(s => s.tier === 'silver').length;
  const bronzeCount = strategies.filter(s => s.tier === 'bronze').length;

  return (
    <div className="gradient-mesh" style={{ minHeight: '100vh' }}>
      {/* Hero Section */}
      <section style={{ padding: '60px 24px 40px', textAlign: 'center', maxWidth: 800, margin: '0 auto' }}>
        <div className="animate-in" style={{ animationDelay: '0.1s', opacity: 0 }}>
          <span style={{
            display: 'inline-block', padding: '6px 16px', borderRadius: '9999px', fontSize: '0.75rem',
            fontWeight: 600, color: 'var(--sv-accent-light)', letterSpacing: '0.05em',
            background: 'rgba(99, 102, 241, 0.12)', border: '1px solid rgba(99, 102, 241, 0.25)', marginBottom: 20,
          }}>
            🤖 AI-POWERED • VALIDATED • MULTI-MODEL CONSENSUS
          </span>
        </div>

        <h1 className="animate-in" style={{
          animationDelay: '0.2s', opacity: 0,
          fontSize: 'clamp(2rem, 5vw, 3.2rem)', fontWeight: 900, lineHeight: 1.1,
          letterSpacing: '-0.03em', margin: '0 0 16px',
          background: 'linear-gradient(135deg, #f1f5f9, #818cf8)',
          WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
        }}>
          Discover Battle-Tested
          <br />Trading Strategies
        </h1>

        <p className="animate-in" style={{
          animationDelay: '0.3s', opacity: 0,
          fontSize: '1.05rem', color: 'var(--sv-text-secondary)', lineHeight: 1.6,
          maxWidth: 560, margin: '0 auto 32px',
        }}>
          AI-generated strategies validated with walk-forward analysis and rated by multi-model consensus.
          No guesswork — just data-driven edge.
        </p>

        {/* Search */}
        <div className="animate-in" style={{ animationDelay: '0.4s', opacity: 0, position: 'relative', maxWidth: 500, margin: '0 auto' }}>
          <svg style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', opacity: 0.4 }}
            width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8" /><path d="M21 21l-4.3-4.3" />
          </svg>
          <input
            className="input-search"
            placeholder="Search strategies... (e.g., momentum, RSI, breakout)"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </section>

      {/* Data Source Indicator */}
      <div style={{ textAlign: 'center', marginBottom: 8 }}>
        <span style={{
          fontSize: '0.7rem', padding: '3px 10px', borderRadius: '6px',
          background: dataSource === 'api' ? 'rgba(34, 197, 94, 0.15)' : 'rgba(234, 179, 8, 0.15)',
          color: dataSource === 'api' ? '#22c55e' : '#eab308',
          fontWeight: 600, letterSpacing: '0.04em',
        }}>
          {dataSource === 'api' ? '🟢 LIVE DATA' : '🟡 DEMO DATA'}
        </span>
      </div>

      {/* Stats Bar */}
      <section style={{ maxWidth: 1280, margin: '0 auto 40px', padding: '0 24px' }}>
        <div className="glass-card animate-in" style={{ animationDelay: '0.5s', opacity: 0, display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)' }}>
          <div className="stat-card">
            <div className="stat-value" style={{ color: 'var(--sv-accent-light)' }}>{strategies.length}</div>
            <div className="stat-label">Total Strategies</div>
          </div>
          <div className="stat-card" style={{ borderLeft: '1px solid var(--sv-border)' }}>
            <div className="stat-value" style={{ color: 'var(--sv-gold)' }}>{goldCount}</div>
            <div className="stat-label">Gold Tier</div>
          </div>
          <div className="stat-card" style={{ borderLeft: '1px solid var(--sv-border)' }}>
            <div className="stat-value" style={{ color: 'var(--sv-green)' }}>
              {(strategies.reduce((a, s) => a + (s.return_pct || 0), 0) / strategies.length).toFixed(1)}%
            </div>
            <div className="stat-label">Avg. Return</div>
          </div>
          <div className="stat-card" style={{ borderLeft: '1px solid var(--sv-border)' }}>
            <div className="stat-value">
              {(strategies.reduce((a, s) => a + (s.sharpe_ratio || 0), 0) / strategies.length).toFixed(2)}
            </div>
            <div className="stat-label">Avg. Sharpe</div>
          </div>
        </div>
      </section>

      {/* Filter Bar */}
      <section style={{ maxWidth: 1280, margin: '0 auto 24px', padding: '0 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
        <div style={{ display: 'flex', gap: 6 }}>
          {TIER_FILTERS.map(tier => (
            <button
              key={tier}
              onClick={() => setActiveTier(tier)}
              style={{
                padding: '6px 16px', borderRadius: '8px', border: '1px solid',
                borderColor: activeTier === tier ? 'var(--sv-accent)' : 'var(--sv-border)',
                background: activeTier === tier ? 'rgba(99, 102, 241, 0.15)' : 'transparent',
                color: activeTier === tier ? 'var(--sv-accent-light)' : 'var(--sv-text-secondary)',
                fontSize: '0.8rem', fontWeight: 600, cursor: 'pointer',
                textTransform: 'capitalize', transition: 'all 0.2s',
              }}
            >
              {tier === 'all' ? 'All' : `${tier === 'gold' ? '⭐' : tier === 'silver' ? '◆' : '●'} ${tier}`}
            </button>
          ))}
        </div>
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          style={{
            padding: '6px 12px', borderRadius: '8px', border: '1px solid var(--sv-border)',
            background: 'var(--sv-bg-card)', color: 'var(--sv-text-secondary)',
            fontSize: '0.8rem', cursor: 'pointer', outline: 'none',
          }}
        >
          <option value="score">Sort: Score</option>
          <option value="return">Sort: Return</option>
          <option value="sharpe">Sort: Sharpe</option>
        </select>
      </section>

      {/* Strategy Grid */}
      <section style={{ maxWidth: 1280, margin: '0 auto', padding: '0 24px 60px' }}>
        {loading ? (
          <div className="glass-card" style={{ padding: 48, textAlign: 'center' }}>
            <div style={{ fontSize: '2rem', marginBottom: 16 }}>⏳</div>
            <p style={{ fontSize: '1.1rem', color: 'var(--sv-text-secondary)' }}>Loading strategies...</p>
          </div>
        ) : filtered.length === 0 ? (
          <div className="glass-card" style={{ padding: 48, textAlign: 'center' }}>
            <p style={{ fontSize: '1.1rem', color: 'var(--sv-text-secondary)' }}>No strategies match your filters</p>
            <button className="btn-secondary" style={{ marginTop: 16 }} onClick={() => { setSearchQuery(''); setActiveTier('all'); }}>
              Clear Filters
            </button>
          </div>
        ) : (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))',
            gap: '20px',
          }}>
            {filtered.map((strategy, i) => (
              <StrategyCard key={strategy.id} strategy={strategy} index={i} />
            ))}
          </div>
        )}
      </section>

      {/* CTA Section */}
      <section style={{ maxWidth: 800, margin: '0 auto 60px', padding: '0 24px', textAlign: 'center' }}>
        <div className="glass-card animate-glow" style={{ padding: '48px 32px' }}>
          <h2 style={{ fontSize: '1.6rem', fontWeight: 800, marginBottom: 12, letterSpacing: '-0.02em' }}>
            Generate Your Own Strategy
          </h2>
          <p style={{ color: 'var(--sv-text-secondary)', marginBottom: 24, fontSize: '0.95rem' }}>
            Describe any trading idea in plain English. Our AI will generate, backtest, validate, and
            rate it using multiple AI models — in minutes.
          </p>
          <a href="/generate" className="btn-primary" style={{ padding: '12px 32px', fontSize: '1rem' }}>
            🚀 Start Generating
          </a>
        </div>
      </section>
    </div>
  );
}
