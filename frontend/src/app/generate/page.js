'use client';

import { useState } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export default function GeneratePage() {
    const [idea, setIdea] = useState('');
    const [asset, setAsset] = useState('BTC-USD');
    const [status, setStatus] = useState(null); // null | 'generating' | 'complete' | 'error'
    const [progress, setProgress] = useState(0);
    const [currentStep, setCurrentStep] = useState('');
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);

    const EXAMPLE_IDEAS = [
        'Buy Bitcoin when RSI drops below 30 and sell when RSI goes above 70',
        'Follow the 21/63 SMA crossover trend on ETH with trailing stops',
        'Mean reversion strategy using Bollinger Bands on SPY in low-vol regimes',
        'Momentum breakout on top 5 crypto assets with volume confirmation',
        'Pairs trading between gold and silver using z-score divergence',
    ];

    const ASSETS = [
        { value: 'BTC-USD', label: '₿ Bitcoin' },
        { value: 'ETH-USD', label: 'Ξ Ethereum' },
        { value: 'SOL-USD', label: '◎ Solana' },
        { value: 'SPY', label: '📈 S&P 500' },
        { value: 'QQQ', label: '💻 Nasdaq 100' },
        { value: 'AAPL', label: '🍎 Apple' },
        { value: 'NVDA', label: '🟢 NVIDIA' },
        { value: 'TSLA', label: '⚡ Tesla' },
    ];

    const steps = [
        { label: 'AI Generation', desc: 'Converting idea to strategy code', icon: '🧠', key: 'generation' },
        { label: 'Market Data', desc: 'Fetching real market data via yfinance', icon: '📊', key: 'data_fetch' },
        { label: 'Backtesting', desc: 'Running backtest against historical data', icon: '🔬', key: 'backtest' },
        { label: 'Scoring', desc: 'Computing StrategyScore™ and tier', icon: '⭐', key: 'scoring' },
        { label: 'Saving', desc: 'Persisting to database', icon: '💾', key: 'save' },
    ];

    const handleGenerate = async () => {
        if (!idea.trim()) return;
        setStatus('generating');
        setProgress(0);
        setCurrentStep('Starting pipeline...');
        setResult(null);
        setError(null);

        // Animate progress while waiting for API
        let progressVal = 0;
        const progressInterval = setInterval(() => {
            progressVal += 1;
            if (progressVal >= 90) {
                clearInterval(progressInterval);
            }
            setProgress(prev => Math.min(prev + 1, 90));
        }, 300);

        // Simulate step transitions based on time
        const stepTimers = [
            setTimeout(() => { setCurrentStep('generation'); setProgress(15); }, 500),
            setTimeout(() => { setCurrentStep('data_fetch'); setProgress(35); }, 3000),
            setTimeout(() => { setCurrentStep('backtest'); setProgress(55); }, 6000),
            setTimeout(() => { setCurrentStep('scoring'); setProgress(75); }, 9000),
        ];

        try {
            const res = await fetch(`${API_BASE}/strategies/generate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ trading_idea: idea, asset }),
            });

            clearInterval(progressInterval);
            stepTimers.forEach(clearTimeout);

            if (!res.ok) throw new Error(`API error: ${res.status}`);

            const data = await res.json();

            if (data.status === 'complete') {
                setCurrentStep('save');
                setProgress(100);
                setResult(data);
                setStatus('complete');
            } else {
                setError(data.message || 'Generation failed');
                setStatus('error');
                // Even on error, show what steps ran
                if (data.steps) setResult(data);
                setProgress(100);
            }
        } catch (err) {
            clearInterval(progressInterval);
            stepTimers.forEach(clearTimeout);
            setError(err.message);
            setStatus('error');
            setProgress(0);
        }
    };

    // Determine step status based on API response
    const getStepStatus = (stepKey) => {
        if (!result?.steps) {
            // Fallback to time-based animation
            const stepIndex = steps.findIndex(s => s.key === stepKey);
            const currentIndex = steps.findIndex(s => s.key === currentStep);
            if (currentIndex < 0) return 'pending';
            if (stepIndex < currentIndex) return 'done';
            if (stepIndex === currentIndex) return 'active';
            return 'pending';
        }
        const step = result.steps.find(s => s.step === stepKey);
        if (!step) {
            // Use progress-based fallback
            const stepObj = steps.find(s => s.key === stepKey);
            if (!stepObj) return 'pending';
            return status === 'complete' ? 'done' : 'pending';
        }
        if (step.status === 'success') return 'done';
        if (step.status === 'fallback' || step.status === 'applied') return 'fallback';
        if (step.status === 'failed' || step.status === 'error') return 'failed';
        return 'active';
    };

    const tierColors = {
        gold: { bg: 'rgba(255, 193, 7, 0.15)', border: 'rgba(255, 193, 7, 0.4)', color: '#ffc107', label: '⭐ GOLD' },
        silver: { bg: 'rgba(192, 192, 211, 0.15)', border: 'rgba(192, 192, 211, 0.4)', color: '#c0c0d3', label: '◆ SILVER' },
        bronze: { bg: 'rgba(205, 127, 50, 0.15)', border: 'rgba(205, 127, 50, 0.4)', color: '#cd7f32', label: '● BRONZE' },
        rejected: { bg: 'rgba(239, 68, 68, 0.15)', border: 'rgba(239, 68, 68, 0.4)', color: '#ef4444', label: '✕ REJECTED' },
    };

    return (
        <div className="gradient-mesh" style={{ minHeight: '100vh', padding: '40px 24px 80px' }}>
            <div style={{ maxWidth: 720, margin: '0 auto' }}>
                {/* Header */}
                <div className="animate-in" style={{ textAlign: 'center', marginBottom: 40, opacity: 0 }}>
                    <a href="/" style={{
                        display: 'inline-block', marginBottom: 16, fontSize: '0.78rem',
                        color: 'var(--sv-text-secondary)', textDecoration: 'none',
                    }}>
                        ← Back to Marketplace
                    </a>
                    <h1 style={{
                        fontSize: 'clamp(1.8rem, 4vw, 2.5rem)', fontWeight: 900, letterSpacing: '-0.03em',
                        background: 'linear-gradient(135deg, #f1f5f9, #818cf8)',
                        WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', marginBottom: 12,
                    }}>
                        Generate a Strategy
                    </h1>
                    <p style={{ color: 'var(--sv-text-secondary)', fontSize: '1rem', lineHeight: 1.6 }}>
                        Describe any trading idea in plain English. Our AI pipeline will generate,
                        backtest, validate, and rate it — <strong>for real</strong>.
                    </p>
                </div>

                {/* Input Area */}
                <div className="glass-card animate-in" style={{ padding: 32, marginBottom: 24, opacity: 0, animationDelay: '0.15s' }}>
                    <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--sv-text-secondary)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                        Your Trading Idea
                    </label>
                    <textarea
                        value={idea}
                        onChange={(e) => setIdea(e.target.value)}
                        placeholder="e.g., Buy when RSI drops below 30 and MACD crosses above signal line, sell when RSI exceeds 70..."
                        disabled={status === 'generating'}
                        style={{
                            width: '100%', minHeight: 120, padding: 16, borderRadius: 12,
                            background: 'var(--sv-bg-primary)', border: '1px solid var(--sv-border)',
                            color: 'var(--sv-text-primary)', fontSize: '0.95rem', lineHeight: 1.6,
                            resize: 'vertical', outline: 'none', fontFamily: 'inherit',
                            transition: 'border-color 0.2s',
                        }}
                        onFocus={(e) => e.target.style.borderColor = 'var(--sv-accent)'}
                        onBlur={(e) => e.target.style.borderColor = 'var(--sv-border)'}
                    />

                    {/* Asset Selector + Submit */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 16, flexWrap: 'wrap', gap: 12 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--sv-text-muted)' }}>
                                Asset:
                            </label>
                            <select
                                value={asset}
                                onChange={(e) => setAsset(e.target.value)}
                                disabled={status === 'generating'}
                                style={{
                                    padding: '6px 12px', borderRadius: '8px', border: '1px solid var(--sv-border)',
                                    background: 'var(--sv-bg-card)', color: 'var(--sv-text-secondary)',
                                    fontSize: '0.8rem', cursor: 'pointer', outline: 'none',
                                }}
                            >
                                {ASSETS.map(a => (
                                    <option key={a.value} value={a.value}>{a.label}</option>
                                ))}
                            </select>
                        </div>
                        <button
                            className="btn-primary"
                            onClick={handleGenerate}
                            disabled={!idea.trim() || status === 'generating'}
                            style={{
                                opacity: !idea.trim() || status === 'generating' ? 0.5 : 1,
                                cursor: !idea.trim() || status === 'generating' ? 'not-allowed' : 'pointer',
                            }}
                        >
                            {status === 'generating' ? '⏳ Generating...' : '🚀 Generate Strategy'}
                        </button>
                    </div>
                </div>

                {/* Example Ideas */}
                {!status && (
                    <div className="animate-in" style={{ marginBottom: 32, opacity: 0, animationDelay: '0.3s' }}>
                        <p style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--sv-text-muted)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                            💡 Try an example
                        </p>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                            {EXAMPLE_IDEAS.map((ex, i) => (
                                <button
                                    key={i}
                                    onClick={() => setIdea(ex)}
                                    style={{
                                        padding: '6px 14px', borderRadius: '8px', fontSize: '0.78rem',
                                        background: 'rgba(99, 102, 241, 0.08)', color: 'var(--sv-text-secondary)',
                                        border: '1px solid var(--sv-border)', cursor: 'pointer',
                                        transition: 'all 0.2s', lineHeight: 1.4,
                                    }}
                                    onMouseEnter={(e) => { e.target.style.borderColor = 'var(--sv-accent)'; e.target.style.color = 'var(--sv-text-primary)'; }}
                                    onMouseLeave={(e) => { e.target.style.borderColor = 'var(--sv-border)'; e.target.style.color = 'var(--sv-text-secondary)'; }}
                                >
                                    {ex.length > 60 ? ex.slice(0, 60) + '…' : ex}
                                </button>
                            ))}
                        </div>
                    </div>
                )}

                {/* Pipeline Progress */}
                {status && (
                    <div className="glass-card animate-in" style={{ padding: 32, opacity: 0, marginBottom: 24 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
                            <h3 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 700 }}>
                                {status === 'complete' ? '✅ Strategy Ready!' : status === 'error' ? '⚠️ Pipeline Completed with Issues' : '⚡ Pipeline Running'}
                            </h3>
                            <span style={{ fontSize: '0.85rem', fontWeight: 700, color: status === 'complete' ? 'var(--sv-green)' : status === 'error' ? '#eab308' : 'var(--sv-accent-light)' }}>
                                {progress}%
                            </span>
                        </div>

                        {/* Progress Bar */}
                        <div style={{ height: 6, borderRadius: 3, background: 'rgba(255,255,255,0.06)', marginBottom: 24, overflow: 'hidden' }}>
                            <div style={{
                                height: '100%', borderRadius: 3,
                                width: `${progress}%`,
                                background: status === 'complete'
                                    ? 'linear-gradient(90deg, #10b981, #34d399)'
                                    : status === 'error'
                                        ? 'linear-gradient(90deg, #eab308, #f59e0b)'
                                        : 'linear-gradient(90deg, var(--sv-accent), #7c3aed)',
                                transition: 'width 0.3s ease',
                            }} />
                        </div>

                        {/* Pipeline Steps */}
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                            {steps.map((step, i) => {
                                const stepStatus = getStepStatus(step.key);
                                const isDone = stepStatus === 'done';
                                const isFallback = stepStatus === 'fallback';
                                const isFailed = stepStatus === 'failed';
                                const isActive = stepStatus === 'active' || (status === 'generating' && step.key === currentStep);

                                // Get step detail from API response
                                const stepData = result?.steps?.find(s => s.step === step.key);
                                let detail = step.desc;
                                if (stepData) {
                                    if (stepData.status === 'fallback') detail = `Fallback used — ${stepData.error?.slice(0, 60) || 'API key issue'}`;
                                    else if (stepData.status === 'failed') detail = stepData.error?.slice(0, 80) || 'Failed';
                                    else if (stepData.status === 'applied') detail = 'Synthetic metrics generated';
                                    else if (stepData.return_pct) detail = `Return: ${stepData.return_pct}% | Sharpe: ${stepData.sharpe_ratio}`;
                                    else if (stepData.rows) detail = `${stepData.rows} data points for ${stepData.asset}`;
                                    else if (stepData.score) detail = `Score: ${stepData.score} → ${stepData.tier?.toUpperCase()}`;
                                    else if (stepData.id) detail = `Saved with ID #${stepData.id}`;
                                    else if (stepData.name) detail = `Generated: "${stepData.name}"`;
                                }

                                return (
                                    <div key={i} style={{
                                        display: 'flex', alignItems: 'center', gap: 12, padding: '10px 14px',
                                        borderRadius: 10,
                                        background: isActive ? 'rgba(99, 102, 241, 0.1)'
                                            : isDone ? 'rgba(16, 185, 129, 0.06)'
                                                : isFallback ? 'rgba(234, 179, 8, 0.06)'
                                                    : isFailed ? 'rgba(239, 68, 68, 0.06)'
                                                        : 'transparent',
                                        border: `1px solid ${isActive ? 'var(--sv-accent)'
                                            : isDone ? 'rgba(16, 185, 129, 0.2)'
                                                : isFallback ? 'rgba(234, 179, 8, 0.2)'
                                                    : isFailed ? 'rgba(239, 68, 68, 0.2)'
                                                        : 'transparent'}`,
                                        transition: 'all 0.3s',
                                    }}>
                                        <span style={{ fontSize: '1.2rem', width: 28, textAlign: 'center' }}>
                                            {isDone ? '✅' : isFallback ? '⚡' : isFailed ? '❌' : isActive ? '🔄' : step.icon}
                                        </span>
                                        <div style={{ flex: 1 }}>
                                            <div style={{
                                                fontSize: '0.85rem', fontWeight: 600,
                                                color: isDone ? 'var(--sv-green)'
                                                    : isFallback ? '#eab308'
                                                        : isFailed ? '#ef4444'
                                                            : isActive ? 'var(--sv-text-primary)'
                                                                : 'var(--sv-text-muted)',
                                            }}>
                                                {step.label}
                                                {isFallback && ' (fallback)'}
                                                {isFailed && ' (failed)'}
                                            </div>
                                            <div style={{ fontSize: '0.72rem', color: 'var(--sv-text-muted)' }}>
                                                {detail}
                                            </div>
                                        </div>
                                        {isActive && (
                                            <div style={{
                                                width: 8, height: 8, borderRadius: '50%',
                                                background: 'var(--sv-accent)', animation: 'pulse-glow 1s infinite',
                                            }} />
                                        )}
                                    </div>
                                );
                            })}
                        </div>

                        {/* Error message */}
                        {error && status === 'error' && !result && (
                            <div style={{ marginTop: 20, padding: '12px 16px', borderRadius: 10, background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)' }}>
                                <p style={{ color: '#ef4444', fontSize: '0.85rem', margin: 0 }}>
                                    ❌ {error}
                                </p>
                            </div>
                        )}
                    </div>
                )}

                {/* Strategy Result Card */}
                {result?.strategy && status === 'complete' && (
                    <div className="glass-card animate-in" style={{ padding: 32, opacity: 0 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24 }}>
                            <div>
                                <h2 style={{ margin: '0 0 4px', fontSize: '1.4rem', fontWeight: 800 }}>
                                    {result.strategy.name}
                                </h2>
                                <p style={{ color: 'var(--sv-text-secondary)', fontSize: '0.85rem', margin: 0 }}>
                                    {result.strategy.description}
                                </p>
                            </div>
                            {result.strategy.tier && (
                                <span style={{
                                    padding: '4px 12px', borderRadius: '6px', fontSize: '0.7rem', fontWeight: 700,
                                    letterSpacing: '0.04em',
                                    background: tierColors[result.strategy.tier]?.bg || tierColors.bronze.bg,
                                    border: `1px solid ${tierColors[result.strategy.tier]?.border || tierColors.bronze.border}`,
                                    color: tierColors[result.strategy.tier]?.color || tierColors.bronze.color,
                                    whiteSpace: 'nowrap',
                                }}>
                                    {tierColors[result.strategy.tier]?.label || result.strategy.tier.toUpperCase()}
                                </span>
                            )}
                        </div>

                        {/* Metrics Grid */}
                        <div style={{
                            display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16,
                            marginBottom: 24,
                        }}>
                            <div style={{ textAlign: 'center' }}>
                                <div style={{
                                    fontSize: '1.4rem', fontWeight: 800,
                                    color: (result.strategy.return_pct || 0) >= 0 ? 'var(--sv-green)' : '#ef4444',
                                }}>
                                    {result.strategy.return_pct >= 0 ? '+' : ''}{result.strategy.return_pct?.toFixed(1)}%
                                </div>
                                <div style={{ fontSize: '0.7rem', color: 'var(--sv-text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Return</div>
                            </div>
                            <div style={{ textAlign: 'center' }}>
                                <div style={{
                                    fontSize: '1.4rem', fontWeight: 800,
                                    color: (result.strategy.sharpe_ratio || 0) >= 1 ? 'var(--sv-green)' : 'var(--sv-text-primary)',
                                }}>
                                    {result.strategy.sharpe_ratio?.toFixed(2)}
                                </div>
                                <div style={{ fontSize: '0.7rem', color: 'var(--sv-text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Sharpe</div>
                            </div>
                            <div style={{ textAlign: 'center' }}>
                                <div style={{
                                    fontSize: '1.4rem', fontWeight: 800, color: '#ef4444',
                                }}>
                                    {result.strategy.max_drawdown_pct?.toFixed(1)}%
                                </div>
                                <div style={{ fontSize: '0.7rem', color: 'var(--sv-text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Max DD</div>
                            </div>
                            <div style={{ textAlign: 'center' }}>
                                <div style={{
                                    fontSize: '1.4rem', fontWeight: 800,
                                    background: 'linear-gradient(135deg, #818cf8, #a78bfa)',
                                    WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
                                }}>
                                    {result.strategy.strategy_score}
                                </div>
                                <div style={{ fontSize: '0.7rem', color: 'var(--sv-text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Score</div>
                            </div>
                        </div>

                        {/* Action Buttons */}
                        <div style={{ display: 'flex', gap: 12, justifyContent: 'center', paddingTop: 16, borderTop: '1px solid var(--sv-border)' }}>
                            <a href="/" className="btn-secondary" style={{ padding: '10px 24px', fontSize: '0.85rem', textDecoration: 'none' }}>
                                ← Back to Marketplace
                            </a>
                            <button
                                className="btn-primary"
                                style={{ padding: '10px 24px', fontSize: '0.85rem' }}
                                onClick={() => {
                                    setStatus(null);
                                    setResult(null);
                                    setIdea('');
                                    setProgress(0);
                                }}
                            >
                                🚀 Generate Another
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
