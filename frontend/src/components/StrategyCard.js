'use client';

/**
 * StrategyCard - Displays a trading strategy in the marketplace
 * Shows score ring, tier badge, key metrics, and purchase CTA
 */

export function ScoreRing({ score, size = 56 }) {
    const radius = (size - 8) / 2;
    const circumference = 2 * Math.PI * radius;
    const progress = (score / 100) * circumference;
    const color = score >= 85 ? '#f59e0b' : score >= 70 ? '#94a3b8' : score >= 50 ? '#d97706' : '#ef4444';

    return (
        <div className="score-ring" style={{ width: size, height: size }}>
            <svg width={size} height={size}>
                <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="4" />
                <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke={color} strokeWidth="4"
                    strokeDasharray={circumference} strokeDashoffset={circumference - progress}
                    strokeLinecap="round" />
            </svg>
            <span className="score-value" style={{ color }}>{score}</span>
        </div>
    );
}

export function TierBadge({ tier }) {
    const icon = tier === 'gold' ? '⭐' : tier === 'silver' ? '◆' : '●';
    return (
        <span className={`tier-badge tier-${tier}`}>
            {icon} {tier}
        </span>
    );
}

export function MetricPill({ label, value, positive }) {
    return (
        <div style={{
            display: 'flex', flexDirection: 'column', alignItems: 'center',
            padding: '8px 12px', borderRadius: '10px',
            background: 'rgba(255,255,255,0.03)',
        }}>
            <span style={{
                fontSize: '0.95rem', fontWeight: 700,
                color: positive === true ? 'var(--sv-green)' : positive === false ? 'var(--sv-red)' : 'var(--sv-text-primary)'
            }}>
                {value}
            </span>
            <span style={{ fontSize: '0.65rem', color: 'var(--sv-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginTop: 2 }}>
                {label}
            </span>
        </div>
    );
}

export default function StrategyCard({ strategy, index = 0 }) {
    const {
        id = 0,
        name = 'Unnamed Strategy',
        description = '',
        return_pct = 0,
        sharpe_ratio = 0,
        max_drawdown_pct = 0,
        consensus_vote = 'HOLD',
        consensus_confidence = 0,
        strategy_score = 0,
        tier = 'bronze',
        credit_cost = 1,
        is_featured = false,
    } = strategy;

    const voteColor = consensus_vote === 'BUY' ? 'var(--sv-green)' : consensus_vote === 'SELL' ? 'var(--sv-red)' : 'var(--sv-text-secondary)';

    return (
        <div
            className="glass-card animate-in"
            onClick={() => { if (id) window.location.href = `/strategy/${id}`; }}
            style={{
                padding: '24px',
                display: 'flex',
                flexDirection: 'column',
                gap: '16px',
                animationDelay: `${index * 0.08}s`,
                opacity: 0,
                position: 'relative',
                overflow: 'hidden',
                cursor: id ? 'pointer' : 'default',
                transition: 'transform 0.2s, box-shadow 0.2s',
            }}
            onMouseEnter={(e) => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = '0 8px 30px rgba(99, 102, 241, 0.15)'; }}
            onMouseLeave={(e) => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.boxShadow = 'none'; }}
        >
            {/* Featured shimmer */}
            {is_featured && (
                <div style={{
                    position: 'absolute', top: 0, right: 0,
                    background: 'linear-gradient(135deg, transparent 50%, rgba(245, 158, 11, 0.15) 50%)',
                    width: 60, height: 60,
                }} />
            )}

            {/* Header: Score + Name + Tier */}
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '14px' }}>
                <ScoreRing score={strategy_score} />
                <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                        <h3 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 700, letterSpacing: '-0.01em' }}>{name}</h3>
                        <TierBadge tier={tier} />
                    </div>
                    <p style={{ margin: '4px 0 0', fontSize: '0.8rem', color: 'var(--sv-text-muted)', lineHeight: 1.4, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                        {description || 'AI-generated trading strategy'}
                    </p>
                </div>
            </div>

            {/* Metrics */}
            <div style={{ display: 'flex', gap: '8px', justifyContent: 'space-between' }}>
                <MetricPill label="Return" value={`${return_pct > 0 ? '+' : ''}${return_pct?.toFixed(1)}%`} positive={return_pct > 0} />
                <MetricPill label="Sharpe" value={sharpe_ratio?.toFixed(2)} positive={sharpe_ratio > 1} />
                <MetricPill label="Drawdown" value={`${max_drawdown_pct?.toFixed(1)}%`} positive={max_drawdown_pct > -15} />
                <MetricPill label="AI Vote" value={consensus_vote} positive={consensus_vote === 'BUY' ? true : consensus_vote === 'SELL' ? false : undefined} />
            </div>

            {/* AI Confidence Bar */}
            <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: 'var(--sv-text-muted)', marginBottom: 4 }}>
                    <span>AI Consensus</span>
                    <span style={{ color: voteColor, fontWeight: 600 }}>{(consensus_confidence * 100).toFixed(0)}%</span>
                </div>
                <div style={{ height: 4, borderRadius: 2, background: 'rgba(255,255,255,0.06)', overflow: 'hidden' }}>
                    <div style={{
                        height: '100%', borderRadius: 2,
                        width: `${consensus_confidence * 100}%`,
                        background: `linear-gradient(90deg, var(--sv-accent), ${voteColor})`,
                        transition: 'width 0.6s ease',
                    }} />
                </div>
            </div>

            {/* CTA */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 'auto' }}>
                <span style={{ fontSize: '0.8rem', color: 'var(--sv-text-muted)' }}>
                    {credit_cost === 1 ? '1 credit' : `${credit_cost} credits`}
                </span>
                <a href={id ? `/strategy/${id}` : '#'} className="btn-primary" style={{ padding: '8px 18px', fontSize: '0.8rem', textDecoration: 'none' }}>
                    View Strategy →
                </a>
            </div>
        </div>
    );
}
