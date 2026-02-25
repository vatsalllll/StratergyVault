'use client';

import { ScoreRing, TierBadge } from '../../components/StrategyCard';

const USER_STATS = {
    name: 'Vatsal',
    tier: 'Explorer',
    credits: 47,
    strategies_generated: 12,
    strategies_purchased: 5,
};

const MY_STRATEGIES = [
    { id: 1, name: 'MomentumAlpha', tier: 'gold', score: 91, return_pct: 42.3, date: '2026-02-08', status: 'active' },
    { id: 2, name: 'MeanRevertRSI', tier: 'silver', score: 82, return_pct: 28.1, date: '2026-02-06', status: 'active' },
    { id: 3, name: 'VolBreakout', tier: 'gold', score: 87, return_pct: 35.7, date: '2026-02-03', status: 'active' },
    { id: 4, name: 'SwingMACD', tier: 'bronze', score: 65, return_pct: 22.4, date: '2026-01-28', status: 'expired' },
    { id: 5, name: 'GridTrader', tier: 'bronze', score: 58, return_pct: 15.2, date: '2026-01-20', status: 'active' },
];

const RECENT_ACTIVITY = [
    { action: 'Generated', strategy: 'MomentumAlpha', time: '2 days ago', icon: '🧠' },
    { action: 'Purchased', strategy: 'VolBreakout', time: '5 days ago', icon: '💳' },
    { action: 'Downloaded', strategy: 'MeanRevertRSI', time: '6 days ago', icon: '📥' },
    { action: 'Generated', strategy: 'SwingMACD', time: '2 weeks ago', icon: '🧠' },
];

export default function DashboardPage() {
    return (
        <div className="gradient-mesh" style={{ minHeight: '100vh', padding: '40px 24px 80px' }}>
            <div style={{ maxWidth: 1100, margin: '0 auto' }}>
                {/* Header */}
                <div className="animate-in" style={{ marginBottom: 32, opacity: 0 }}>
                    <h1 style={{ fontSize: '1.8rem', fontWeight: 800, letterSpacing: '-0.02em', marginBottom: 4 }}>
                        Welcome back, {USER_STATS.name} 👋
                    </h1>
                    <p style={{ color: 'var(--sv-text-secondary)', fontSize: '0.95rem' }}>
                        Manage your strategies and track performance.
                    </p>
                </div>

                {/* Stats Grid */}
                <div className="animate-in" style={{
                    display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                    gap: 16, marginBottom: 32, opacity: 0, animationDelay: '0.1s'
                }}>
                    {[
                        { label: 'Subscription', value: USER_STATS.tier, color: 'var(--sv-accent-light)', icon: '👤' },
                        { label: 'Credits', value: USER_STATS.credits, color: 'var(--sv-gold)', icon: '🪙' },
                        { label: 'Generated', value: USER_STATS.strategies_generated, color: 'var(--sv-green)', icon: '🧠' },
                        { label: 'Purchased', value: USER_STATS.strategies_purchased, color: 'var(--sv-accent-light)', icon: '🛒' },
                    ].map((stat, i) => (
                        <div key={i} className="glass-card" style={{ padding: 20, display: 'flex', alignItems: 'center', gap: 14 }}>
                            <span style={{ fontSize: '1.5rem' }}>{stat.icon}</span>
                            <div>
                                <div style={{ fontSize: '1.3rem', fontWeight: 800, color: stat.color }}>{stat.value}</div>
                                <div style={{ fontSize: '0.7rem', color: 'var(--sv-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{stat.label}</div>
                            </div>
                        </div>
                    ))}
                </div>

                {/* Two Column Layout */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: 24, alignItems: 'start' }}>
                    {/* My Strategies */}
                    <div className="glass-card animate-in" style={{ padding: 24, opacity: 0, animationDelay: '0.2s' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
                            <h2 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 700 }}>My Strategies</h2>
                            <a href="/generate" className="btn-primary" style={{ padding: '6px 14px', fontSize: '0.75rem' }}>
                                + Generate New
                            </a>
                        </div>

                        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                            {MY_STRATEGIES.map((s) => (
                                <div key={s.id} style={{
                                    display: 'flex', alignItems: 'center', gap: 14, padding: '14px 16px',
                                    borderRadius: 12, background: 'rgba(255,255,255,0.02)',
                                    border: '1px solid var(--sv-border)', transition: 'all 0.2s',
                                    cursor: 'pointer',
                                }}
                                    onMouseEnter={(e) => { e.currentTarget.style.borderColor = 'var(--sv-accent)'; e.currentTarget.style.background = 'rgba(99, 102, 241, 0.05)'; }}
                                    onMouseLeave={(e) => { e.currentTarget.style.borderColor = 'var(--sv-border)'; e.currentTarget.style.background = 'rgba(255,255,255,0.02)'; }}
                                >
                                    <ScoreRing score={s.score} size={44} />
                                    <div style={{ flex: 1 }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                            <span style={{ fontWeight: 700, fontSize: '0.9rem' }}>{s.name}</span>
                                            <TierBadge tier={s.tier} />
                                        </div>
                                        <span style={{ fontSize: '0.72rem', color: 'var(--sv-text-muted)' }}>{s.date}</span>
                                    </div>
                                    <div style={{ textAlign: 'right' }}>
                                        <div style={{
                                            fontSize: '0.95rem', fontWeight: 700,
                                            color: s.return_pct > 0 ? 'var(--sv-green)' : 'var(--sv-red)',
                                        }}>
                                            {s.return_pct > 0 ? '+' : ''}{s.return_pct}%
                                        </div>
                                        <div style={{
                                            fontSize: '0.65rem', fontWeight: 600,
                                            color: s.status === 'active' ? 'var(--sv-green)' : 'var(--sv-text-muted)',
                                            textTransform: 'uppercase',
                                        }}>
                                            {s.status}
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Sidebar */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                        {/* Activity */}
                        <div className="glass-card animate-in" style={{ padding: 24, opacity: 0, animationDelay: '0.3s' }}>
                            <h3 style={{ margin: '0 0 16px', fontSize: '0.95rem', fontWeight: 700 }}>Recent Activity</h3>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                                {RECENT_ACTIVITY.map((a, i) => (
                                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                                        <span style={{ fontSize: '1.1rem' }}>{a.icon}</span>
                                        <div style={{ flex: 1 }}>
                                            <div style={{ fontSize: '0.82rem', fontWeight: 500 }}>
                                                {a.action} <span style={{ color: 'var(--sv-accent-light)' }}>{a.strategy}</span>
                                            </div>
                                            <div style={{ fontSize: '0.68rem', color: 'var(--sv-text-muted)' }}>{a.time}</div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Upgrade CTA */}
                        <div className="glass-card animate-in" style={{
                            padding: 24, opacity: 0, animationDelay: '0.4s', textAlign: 'center',
                            background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.08), rgba(124, 58, 237, 0.06))',
                            border: '1px solid rgba(99, 102, 241, 0.25)',
                        }}>
                            <div style={{ fontSize: '1.4rem', marginBottom: 8 }}>🚀</div>
                            <h3 style={{ margin: '0 0 8px', fontSize: '0.95rem', fontWeight: 700 }}>Upgrade to Pro</h3>
                            <p style={{ fontSize: '0.8rem', color: 'var(--sv-text-muted)', marginBottom: 16, lineHeight: 1.4 }}>
                                Unlimited strategy generation, priority AI models, and advanced analytics.
                            </p>
                            <button className="btn-primary" style={{ width: '100%', justifyContent: 'center', fontSize: '0.85rem' }}>
                                View Plans →
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
