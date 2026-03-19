'use client';

import { useState, useEffect, use } from 'react';
import { ScoreRing, TierBadge, MetricPill } from '../../../components/StrategyCard';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// ── SVG Chart Components (zero dependencies) ────────────────────

function EquityCurveChart({ data, width = 700, height = 260 }) {
    if (!data || data.length < 2) return null;

    const pad = { top: 20, right: 20, bottom: 30, left: 60 };
    const w = width - pad.left - pad.right;
    const h = height - pad.top - pad.bottom;
    const minVal = Math.min(...data);
    const maxVal = Math.max(...data);
    const range = maxVal - minVal || 1;

    const points = data.map((v, i) => ({
        x: pad.left + (i / (data.length - 1)) * w,
        y: pad.top + (1 - (v - minVal) / range) * h,
    }));

    const pathD = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');
    const areaD = pathD + ` L ${points[points.length - 1].x} ${pad.top + h} L ${points[0].x} ${pad.top + h} Z`;

    // Y-axis labels
    const yTicks = 5;
    const yLabels = Array.from({ length: yTicks + 1 }, (_, i) => {
        const val = minVal + (range / yTicks) * i;
        return { y: pad.top + (1 - i / yTicks) * h, label: `$${(val / 1000).toFixed(1)}k` };
    });

    // X-axis labels
    const xTicks = 6;
    const xLabels = Array.from({ length: xTicks }, (_, i) => {
        const idx = Math.round((i / (xTicks - 1)) * (data.length - 1));
        const month = Math.floor(idx / (data.length / 24));
        return { x: pad.left + (idx / (data.length - 1)) * w, label: `M${month + 1}` };
    });

    const isPositive = data[data.length - 1] >= data[0];
    const lineColor = isPositive ? '#10b981' : '#ef4444';

    return (
        <svg width="100%" viewBox={`0 0 ${width} ${height}`} style={{ display: 'block' }}>
            {/* Grid lines */}
            {yLabels.map((t, i) => (
                <g key={i}>
                    <line x1={pad.left} y1={t.y} x2={pad.left + w} y2={t.y} stroke="rgba(255,255,255,0.06)" />
                    <text x={pad.left - 8} y={t.y + 4} textAnchor="end" fill="rgba(255,255,255,0.35)" fontSize="10">{t.label}</text>
                </g>
            ))}
            {xLabels.map((t, i) => (
                <text key={`x-${i}`} x={t.x} y={pad.top + h + 18} textAnchor="middle" fill="rgba(255,255,255,0.35)" fontSize="10">{t.label}</text>
            ))}
            {/* Area fill */}
            <defs>
                <linearGradient id="eq-grad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={lineColor} stopOpacity="0.25" />
                    <stop offset="100%" stopColor={lineColor} stopOpacity="0" />
                </linearGradient>
            </defs>
            <path d={areaD} fill="url(#eq-grad)" />
            {/* Line */}
            <path d={pathD} fill="none" stroke={lineColor} strokeWidth="2" strokeLinejoin="round" />
            {/* Start/End markers */}
            <circle cx={points[0].x} cy={points[0].y} r="3" fill={lineColor} />
            <circle cx={points[points.length - 1].x} cy={points[points.length - 1].y} r="4" fill={lineColor} stroke="rgba(255,255,255,0.3)" strokeWidth="1" />
        </svg>
    );
}

function DrawdownChart({ data, width = 700, height = 140 }) {
    if (!data || data.length < 2) return null;

    const pad = { top: 10, right: 20, bottom: 25, left: 60 };
    const w = width - pad.left - pad.right;
    const h = height - pad.top - pad.bottom;
    const minVal = Math.min(...data, -1);
    const range = Math.abs(minVal) || 1;

    const points = data.map((v, i) => ({
        x: pad.left + (i / (data.length - 1)) * w,
        y: pad.top + (Math.abs(v) / range) * h,
    }));

    const pathD = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');
    const areaD = `M ${points[0].x} ${pad.top} ` + points.map(p => `L ${p.x} ${p.y}`).join(' ') + ` L ${points[points.length - 1].x} ${pad.top} Z`;

    return (
        <svg width="100%" viewBox={`0 0 ${width} ${height}`} style={{ display: 'block' }}>
            <line x1={pad.left} y1={pad.top} x2={pad.left + w} y2={pad.top} stroke="rgba(255,255,255,0.1)" />
            <text x={pad.left - 8} y={pad.top + 4} textAnchor="end" fill="rgba(255,255,255,0.35)" fontSize="10">0%</text>
            <text x={pad.left - 8} y={pad.top + h + 4} textAnchor="end" fill="rgba(255,255,255,0.35)" fontSize="10">{minVal.toFixed(0)}%</text>
            <defs>
                <linearGradient id="dd-grad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#ef4444" stopOpacity="0" />
                    <stop offset="100%" stopColor="#ef4444" stopOpacity="0.3" />
                </linearGradient>
            </defs>
            <path d={areaD} fill="url(#dd-grad)" />
            <path d={pathD} fill="none" stroke="#ef4444" strokeWidth="1.5" strokeLinejoin="round" opacity="0.7" />
        </svg>
    );
}

function MonthlyReturnsChart({ returns, labels, width = 700, height = 180 }) {
    if (!returns || returns.length === 0) return null;

    const pad = { top: 10, right: 20, bottom: 30, left: 60 };
    const w = width - pad.left - pad.right;
    const h = height - pad.top - pad.bottom;
    const maxAbs = Math.max(...returns.map(Math.abs), 1);
    const midY = pad.top + h / 2;
    const barW = Math.max(4, Math.min(18, (w / returns.length) * 0.7));
    const gap = w / returns.length;

    return (
        <svg width="100%" viewBox={`0 0 ${width} ${height}`} style={{ display: 'block' }}>
            <line x1={pad.left} y1={midY} x2={pad.left + w} y2={midY} stroke="rgba(255,255,255,0.15)" />
            <text x={pad.left - 8} y={midY + 4} textAnchor="end" fill="rgba(255,255,255,0.35)" fontSize="10">0%</text>
            {returns.map((val, i) => {
                const barH = (Math.abs(val) / maxAbs) * (h / 2 - 4);
                const x = pad.left + i * gap + (gap - barW) / 2;
                const y = val >= 0 ? midY - barH : midY;
                const color = val >= 0 ? '#10b981' : '#ef4444';
                return (
                    <g key={i}>
                        <rect x={x} y={y} width={barW} height={barH} rx={2} fill={color} opacity="0.75" />
                        {i % Math.max(1, Math.floor(returns.length / 8)) === 0 && labels[i] && (
                            <text x={x + barW / 2} y={pad.top + h + 14} textAnchor="middle" fill="rgba(255,255,255,0.3)" fontSize="9">
                                {labels[i]}
                            </text>
                        )}
                    </g>
                );
            })}
        </svg>
    );
}

// ── Validation Gauge ────────────────────────────────────────────

function ValidationGauge({ label, value, max = 100, suffix = '', color }) {
    const pct = Math.min(100, (value / max) * 100);
    return (
        <div style={{ flex: 1 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: 6 }}>
                <span style={{ color: 'var(--sv-text-secondary)' }}>{label}</span>
                <span style={{ fontWeight: 700, color }}>{value}{suffix}</span>
            </div>
            <div style={{ height: 6, borderRadius: 3, background: 'rgba(255,255,255,0.06)', overflow: 'hidden' }}>
                <div style={{ height: '100%', borderRadius: 3, width: `${pct}%`, background: color, transition: 'width 0.8s ease' }} />
            </div>
        </div>
    );
}

// ── Main Page ───────────────────────────────────────────────────

export default function StrategyDetailPage({ params }) {
    const resolvedParams = use(params);
    const strategyId = resolvedParams.id;
    const [detail, setDetail] = useState(null);
    const [perf, setPerf] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [activeChart, setActiveChart] = useState('equity');

    useEffect(() => {
        if (!strategyId) return;
        setLoading(true);
        Promise.all([
            fetch(`${API_BASE}/strategies/${strategyId}/detail`).then(r => r.ok ? r.json() : Promise.reject('Not found')),
            fetch(`${API_BASE}/strategies/${strategyId}/performance`).then(r => r.ok ? r.json() : Promise.reject('No data')),
        ])
            .then(([d, p]) => { setDetail(d); setPerf(p); setLoading(false); })
            .catch(err => { setError(String(err)); setLoading(false); });
    }, [strategyId]);

    if (loading) return (
        <div className="gradient-mesh" style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '2rem', marginBottom: 12, animation: 'pulse-glow 1.5s infinite' }}>📊</div>
                <p style={{ color: 'var(--sv-text-secondary)' }}>Loading strategy data...</p>
            </div>
        </div>
    );

    if (error || !detail) return (
        <div className="gradient-mesh" style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <div className="glass-card" style={{ padding: 40, textAlign: 'center', maxWidth: 400 }}>
                <div style={{ fontSize: '2rem', marginBottom: 12 }}>😔</div>
                <h2 style={{ margin: '0 0 8px', fontSize: '1.2rem' }}>Strategy Not Found</h2>
                <p style={{ color: 'var(--sv-text-secondary)', fontSize: '0.85rem', marginBottom: 20 }}>{error || 'This strategy may have been removed.'}</p>
                <a href="/" className="btn-primary" style={{ textDecoration: 'none', padding: '10px 24px' }}>← Back to Marketplace</a>
            </div>
        </div>
    );

    const tierColors = {
        gold: '#ffc107', silver: '#c0c0d3', bronze: '#cd7f32', rejected: '#ef4444',
    };
    const summary = perf?.summary || {};

    return (
        <div className="gradient-mesh" style={{ minHeight: '100vh', padding: '40px 24px 80px' }}>
            <div style={{ maxWidth: 900, margin: '0 auto' }}>
                {/* Back link */}
                <a href="/" className="animate-in" style={{
                    display: 'inline-block', marginBottom: 24, fontSize: '0.8rem',
                    color: 'var(--sv-text-secondary)', textDecoration: 'none', opacity: 0,
                }}>
                    ← Back to Marketplace
                </a>

                {/* Header Card */}
                <div className="glass-card animate-in" style={{ padding: '28px 32px', marginBottom: 24, opacity: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: 20, flexWrap: 'wrap' }}>
                        <ScoreRing score={detail.strategy_score || 0} size={72} />
                        <div style={{ flex: 1, minWidth: 200 }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap', marginBottom: 6 }}>
                                <h1 style={{ margin: 0, fontSize: 'clamp(1.3rem, 3vw, 1.8rem)', fontWeight: 800, letterSpacing: '-0.02em' }}>
                                    {detail.name}
                                </h1>
                                <TierBadge tier={detail.tier || 'bronze'} />
                            </div>
                            <p style={{ margin: 0, color: 'var(--sv-text-secondary)', fontSize: '0.9rem', lineHeight: 1.5, maxWidth: 600 }}>
                                {detail.description || 'AI-generated trading strategy'}
                            </p>
                            <div style={{ display: 'flex', gap: 16, marginTop: 12, flexWrap: 'wrap', fontSize: '0.75rem', color: 'var(--sv-text-muted)' }}>
                                {detail.model_used && <span>🤖 {detail.model_used}</span>}
                                {detail.best_asset && <span>📈 Best on {detail.best_asset}</span>}
                                {detail.created_at && <span>📅 {new Date(detail.created_at).toLocaleDateString()}</span>}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Metrics Bar */}
                <div className="glass-card animate-in" style={{ padding: 20, marginBottom: 24, opacity: 0, animationDelay: '0.1s' }}>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(110px, 1fr))', gap: 12 }}>
                        <MetricPill label="Total Return" value={`${(detail.return_pct || 0) > 0 ? '+' : ''}${(detail.return_pct || 0).toFixed(1)}%`} positive={(detail.return_pct || 0) > 0} />
                        <MetricPill label="Sharpe Ratio" value={(detail.sharpe_ratio || 0).toFixed(2)} positive={(detail.sharpe_ratio || 0) > 1} />
                        <MetricPill label="Max Drawdown" value={`${(detail.max_drawdown_pct || 0).toFixed(1)}%`} positive={(detail.max_drawdown_pct || 0) > -15} />
                        <MetricPill label="Win Rate" value={`${(detail.win_rate || 0).toFixed(0)}%`} positive={(detail.win_rate || 0) > 50} />
                        <MetricPill label="Trades" value={detail.num_trades || 0} />
                        <MetricPill label="AI Vote" value={detail.consensus_vote || 'N/A'} positive={detail.consensus_vote === 'BUY' ? true : detail.consensus_vote === 'SELL' ? false : undefined} />
                    </div>
                </div>

                {/* Chart Section */}
                <div className="glass-card animate-in" style={{ padding: '24px 24px 16px', marginBottom: 24, opacity: 0, animationDelay: '0.2s' }}>
                    {/* Chart Tabs */}
                    <div style={{ display: 'flex', gap: 4, marginBottom: 20 }}>
                        {[
                            { key: 'equity', label: '📈 Equity Curve' },
                            { key: 'drawdown', label: '📉 Drawdown' },
                            { key: 'monthly', label: '📊 Monthly Returns' },
                        ].map(tab => (
                            <button
                                key={tab.key}
                                onClick={() => setActiveChart(tab.key)}
                                style={{
                                    padding: '8px 16px', borderRadius: 8, fontSize: '0.78rem', fontWeight: 600,
                                    background: activeChart === tab.key ? 'rgba(99, 102, 241, 0.15)' : 'transparent',
                                    color: activeChart === tab.key ? 'var(--sv-accent-light)' : 'var(--sv-text-muted)',
                                    border: `1px solid ${activeChart === tab.key ? 'rgba(99, 102, 241, 0.3)' : 'transparent'}`,
                                    cursor: 'pointer', transition: 'all 0.2s',
                                }}
                            >
                                {tab.label}
                            </button>
                        ))}
                    </div>

                    {/* Charts */}
                    {perf ? (
                        <div>
                            {activeChart === 'equity' && (
                                <div>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8, fontSize: '0.75rem', color: 'var(--sv-text-muted)' }}>
                                        <span>Portfolio value starting at $10,000</span>
                                        <span style={{
                                            fontWeight: 700,
                                            color: (perf.equity_curve[perf.equity_curve.length - 1] || 10000) >= 10000 ? 'var(--sv-green)' : '#ef4444',
                                        }}>
                                            Final: ${((perf.equity_curve[perf.equity_curve.length - 1] || 10000) / 1000).toFixed(1)}k
                                        </span>
                                    </div>
                                    <EquityCurveChart data={perf.equity_curve} />
                                </div>
                            )}
                            {activeChart === 'drawdown' && (
                                <div>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8, fontSize: '0.75rem', color: 'var(--sv-text-muted)' }}>
                                        <span>Drawdown from peak equity</span>
                                        <span style={{ fontWeight: 700, color: '#ef4444' }}>
                                            Max: {Math.min(...perf.drawdown_series).toFixed(1)}%
                                        </span>
                                    </div>
                                    <DrawdownChart data={perf.drawdown_series} />
                                </div>
                            )}
                            {activeChart === 'monthly' && (
                                <div>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8, fontSize: '0.75rem', color: 'var(--sv-text-muted)' }}>
                                        <span>Monthly return distribution</span>
                                        <span>
                                            <span style={{ color: 'var(--sv-green)', fontWeight: 600 }}>{perf.monthly_returns.filter(r => r >= 0).length} winning</span>
                                            {' / '}
                                            <span style={{ color: '#ef4444', fontWeight: 600 }}>{perf.monthly_returns.filter(r => r < 0).length} losing</span>
                                        </span>
                                    </div>
                                    <MonthlyReturnsChart returns={perf.monthly_returns} labels={perf.month_labels} />
                                </div>
                            )}
                        </div>
                    ) : (
                        <div style={{ textAlign: 'center', padding: 40, color: 'var(--sv-text-muted)' }}>
                            No performance data available
                        </div>
                    )}
                </div>

                {/* Validation & Robustness */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 24, marginBottom: 24 }}>
                    {/* Validation Card */}
                    <div className="glass-card animate-in" style={{ padding: 24, opacity: 0, animationDelay: '0.3s' }}>
                        <h3 style={{ margin: '0 0 16px', fontSize: '0.95rem', fontWeight: 700 }}>
                            🔬 Validation & Robustness
                        </h3>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                            <ValidationGauge
                                label="Walk-Forward Score"
                                value={detail.walk_forward_score || 0}
                                max={100}
                                color={detail.walk_forward_score >= 60 ? '#10b981' : '#eab308'}
                            />
                            <ValidationGauge
                                label="Strategy Score"
                                value={detail.strategy_score || 0}
                                max={100}
                                suffix=""
                                color={tierColors[detail.tier] || '#818cf8'}
                            />
                            <ValidationGauge
                                label="Win Rate"
                                value={detail.win_rate || 0}
                                max={100}
                                suffix="%"
                                color={(detail.win_rate || 0) >= 50 ? '#10b981' : '#ef4444'}
                            />
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 12px', borderRadius: 8, background: detail.is_robust ? 'rgba(16, 185, 129, 0.08)' : 'rgba(239, 68, 68, 0.08)', border: `1px solid ${detail.is_robust ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)'}` }}>
                                <span style={{ fontSize: '1.1rem' }}>{detail.is_robust ? '✅' : '⚠️'}</span>
                                <div>
                                    <div style={{ fontSize: '0.8rem', fontWeight: 600, color: detail.is_robust ? 'var(--sv-green)' : '#eab308' }}>
                                        {detail.is_robust ? 'Robust Strategy' : 'Needs Review'}
                                    </div>
                                    <div style={{ fontSize: '0.7rem', color: 'var(--sv-text-muted)' }}>
                                        {detail.is_robust ? 'Passed walk-forward validation' : 'Below robustness threshold'}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* AI Consensus Card */}
                    <div className="glass-card animate-in" style={{ padding: 24, opacity: 0, animationDelay: '0.35s' }}>
                        <h3 style={{ margin: '0 0 16px', fontSize: '0.95rem', fontWeight: 700 }}>
                            🤖 AI Consensus Rating
                        </h3>
                        <div style={{ textAlign: 'center', marginBottom: 16 }}>
                            <div style={{
                                display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                                width: 80, height: 80, borderRadius: '50%',
                                background: detail.consensus_vote === 'BUY' ? 'rgba(16, 185, 129, 0.1)' : detail.consensus_vote === 'SELL' ? 'rgba(239, 68, 68, 0.1)' : 'rgba(99, 102, 241, 0.1)',
                                border: `2px solid ${detail.consensus_vote === 'BUY' ? 'rgba(16, 185, 129, 0.3)' : detail.consensus_vote === 'SELL' ? 'rgba(239, 68, 68, 0.3)' : 'rgba(99, 102, 241, 0.3)'}`,
                            }}>
                                <span style={{
                                    fontSize: '1.3rem', fontWeight: 800,
                                    color: detail.consensus_vote === 'BUY' ? 'var(--sv-green)' : detail.consensus_vote === 'SELL' ? '#ef4444' : 'var(--sv-accent-light)',
                                }}>
                                    {detail.consensus_vote || 'N/A'}
                                </span>
                            </div>
                            <div style={{ fontSize: '0.75rem', color: 'var(--sv-text-muted)', marginTop: 8 }}>
                                Multi-model consensus
                            </div>
                        </div>
                        <ValidationGauge
                            label="Confidence"
                            value={Math.round((detail.consensus_confidence || 0) * 100)}
                            max={100}
                            suffix="%"
                            color={detail.consensus_vote === 'BUY' ? '#10b981' : detail.consensus_vote === 'SELL' ? '#ef4444' : '#818cf8'}
                        />
                        {detail.ai_summary && (
                            <p style={{ fontSize: '0.78rem', color: 'var(--sv-text-secondary)', lineHeight: 1.6, marginTop: 16, padding: '10px 12px', borderRadius: 8, background: 'rgba(255,255,255,0.03)' }}>
                                {detail.ai_summary}
                            </p>
                        )}
                        {!detail.ai_summary && (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 16 }}>
                                {['Gemini Flash', 'Gemini Pro', 'Gemini Ultra'].map((model, i) => (
                                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.75rem', padding: '6px 10px', borderRadius: 6, background: 'rgba(255,255,255,0.03)' }}>
                                        <span style={{ color: 'var(--sv-text-muted)' }}>🤖</span>
                                        <span style={{ flex: 1, color: 'var(--sv-text-secondary)' }}>{model}</span>
                                        <span style={{
                                            fontWeight: 600,
                                            color: detail.consensus_vote === 'BUY' ? 'var(--sv-green)' : detail.consensus_vote === 'SELL' ? '#ef4444' : 'var(--sv-text-secondary)',
                                        }}>
                                            {detail.consensus_vote || 'HOLD'}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                {/* Bottom CTA */}
                <div className="glass-card animate-in" style={{ padding: 24, textAlign: 'center', opacity: 0, animationDelay: '0.4s' }}>
                    <p style={{ color: 'var(--sv-text-secondary)', fontSize: '0.85rem', marginBottom: 16 }}>
                        Interested in this strategy? Purchase to unlock the full backtest report.
                    </p>
                    <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
                        <a href="/" className="btn-secondary" style={{ padding: '10px 24px', fontSize: '0.85rem', textDecoration: 'none' }}>
                            ← Back
                        </a>
                        <a href="/generate" className="btn-primary" style={{ padding: '10px 24px', fontSize: '0.85rem', textDecoration: 'none' }}>
                            🚀 Generate Your Own
                        </a>
                    </div>
                </div>
            </div>
        </div>
    );
}
