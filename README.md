# StrategyVault 🚀

> AI-Powered Trading Strategy Marketplace — Generate · Validate · Trade

A subscription-based platform where AI generates, validates, and ranks institutional-grade trading strategies. Built by combining the best of three open-source quant projects into a single production-ready system.

---

## How It Works

```
User describes strategy idea (e.g. "momentum breakout on BTC")
                    │
                    ▼
   ┌────────────────────────────────┐
   │   AI Strategy Generator        │  ← Gemini generates backtesting.py code
   │   (Moon Dev RBI Pattern)       │     using curated Harvard templates
   └───────────────┬────────────────┘
                   ▼
   ┌────────────────────────────────┐
   │   Feature Engine               │  ← AgentQuant feature computation
   │   (Volatility, RSI, Momentum)  │     feeds market context to the AI
   └───────────────┬────────────────┘
                   ▼
   ┌────────────────────────────────┐
   │   RBI Debug Loop               │  ← Moon Dev pattern: generate → test
   │   (Auto-fix failing code)      │     → AI fix → retest (up to 3x)
   └───────────────┬────────────────┘
                   ▼
   ┌────────────────────────────────┐
   │   Backtester                   │  ← backtesting.py engine with
   │   (Multi-asset, tx costs)      │     commission + slippage modeling
   └───────────────┬────────────────┘
                   ▼
   ┌────────────────────────────────┐
   │   Walk-Forward Validation      │  ← AgentQuant: rolling windows,
   │   + Monte Carlo Simulation     │     ablation studies, p-value test
   └───────────────┬────────────────┘
                   ▼
   ┌────────────────────────────────┐
   │   Swarm AI Consensus           │  ← Moon Dev pattern: multiple AI
   │   (Gemini + OpenAI + Claude)   │     models vote BUY/HOLD/REJECT
   └───────────────┬────────────────┘
                   ▼
           Strategy Score (0-100)
           Published to Marketplace
```

---

## Three Source Projects — How They Integrate

### 1. Moon Dev AI Agents (`source_repos/moon-dev-ai-agents/`)

**What it provides**: The RBI (Research → Backtest → Implement) agent loop and the multi-model Swarm consensus pattern.

| Moon Dev Component | StrategyVault Integration | File |
|---|---|---|
| RBI Agent pattern | Debug loop: AI generates strategy → backtest → if fail → AI fix → retry | `backend/src/services/pipeline.py` |
| SwarmAgent (multi-model parallel query) | Swarm consensus: query Gemini/OpenAI/Claude in parallel, aggregate BUY/HOLD/REJECT verdicts | `backend/src/features/swarm_consensus.py` |
| `backtesting.lib` fix pattern | `package_check()` auto-removes broken imports before execution | `backend/src/generation/generator.py` |

**How it works**: When a user submits a strategy idea, the pipeline follows Moon Dev's RBI loop — the AI generates code, runs it, and if the backtest crashes, the AI reads the error and fixes the code (up to 3 retries). After a successful backtest, the Swarm consensus module queries multiple AI models in parallel (like Moon Dev's `SwarmAgent`) to evaluate strategy quality.

---

### 2. Harvard Algorithmic Trading with AI (`source_repos/Harvard-Algorithmic-Trading-with-AI/`)

**What it provides**: Battle-tested strategy templates and backtest patterns using `backtesting.py` + TA-Lib.

| Harvard Component | StrategyVault Integration | File |
|---|---|---|
| BB Squeeze + ADX strategy | Curated template: Bollinger Band squeeze with Keltner Channels + ADX trend filter | `backend/src/features/strategy_templates.py` |
| SMA Crossover pattern | Template: classic 21/63 dual-SMA crossover with proper position sizing | `backend/src/features/strategy_templates.py` |
| Backtest structure (optimization, SL/TP) | Reference architecture for how AI-generated strategies should be structured | `backend/src/generation/executor.py` |

**How it works**: The strategy templates serve as reference implementations that the AI generator can learn from. When generating a new strategy, the AI has access to these proven patterns (BB squeeze, SMA crossover, RSI mean reversion) as examples of correct `backtesting.py` structure, proper indicator calculation, and risk management (stop-loss/take-profit).

---

### 3. AgentQuant (`source_repos/AgentQuant/`)

**What it provides**: Robust feature engineering, market regime detection, and walk-forward validation framework.

| AgentQuant Component | StrategyVault Integration | File |
|---|---|---|
| Feature Engine (`_find_field_series`, `compute_features`) | MultiIndex-safe feature computation: volatility (21d/63d), momentum, SMA, RSI, BB-width, ATR | `backend/src/features/feature_engine.py` |
| Regime Detection | Market regime classification (crisis, trending, mean-reverting) to contextualize strategies | `backend/src/analysis/regime.py` |
| Walk-Forward Validation | Rolling out-of-sample validation with train/test windows, overfitting detection | `backend/src/validation/walk_forward.py` |

**How it works**: Before generating a strategy, the feature engine (ported from AgentQuant) computes current market conditions — volatility, momentum, RSI — and feeds them to the AI as context. After backtesting, AgentQuant's walk-forward validation tests the strategy on unseen data to detect overfitting. The regime detector classifies the current market state so strategies are evaluated in the right context.

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI (Python 3.12) |
| Frontend | Next.js 14 (React) |
| AI Model | Google Gemini 2.0 Flash |
| Backtesting | backtesting.py + TA-Lib |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Cache | Redis (with graceful NoOp fallback) |
| Deployment | Docker Compose / Render / Railway |

---

## Quick Start

### Docker (Recommended)

```bash
cp backend/.env.example backend/.env
# Edit backend/.env with your GOOGLE_API_KEY

docker compose up --build -d
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/docs

### Manual Setup

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # add your GOOGLE_API_KEY
uvicorn main:app --reload

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

---

## Project Structure

```
strategy-vault/
├── backend/
│   ├── src/
│   │   ├── api/              # FastAPI routes (strategies, users, generate)
│   │   ├── core/             # Config, cache manager, security
│   │   ├── data/             # Market data (yfinance OHLCV fetcher)
│   │   ├── features/         # Feature engine, strategy templates, swarm consensus
│   │   ├── generation/       # AI code generation + sandboxed executor
│   │   ├── validation/       # Walk-forward, Monte Carlo, ablation
│   │   ├── analysis/         # Market regime detection
│   │   ├── models/           # SQLAlchemy models (Strategy, User, Purchase)
│   │   └── services/         # Pipeline orchestrator
│   ├── tests/                # 249 tests (unit + integration)
│   │   └── enhancements/     # Tests for new features
│   ├── main.py
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                 # Next.js marketplace UI
│   ├── src/app/              # Pages (home, generate, strategy detail)
│   ├── src/components/       # StrategyCard, ScoreRing, TierBadge
│   └── Dockerfile
├── source_repos/             # Full source code of the 3 integrated projects
│   ├── moon-dev-ai-agents/
│   ├── Harvard-Algorithmic-Trading-with-AI/
│   └── AgentQuant/
├── docker-compose.yml
└── render.yaml               # One-click Render deployment
```

---

## Key Features

| Feature | Description |
|---------|-------------|
| 🤖 AI Strategy Generation | Natural language → backtesting.py code via Gemini |
| 🔄 RBI Debug Loop | Auto-fix failing strategies (up to 3 retries) |
| 📊 Walk-Forward Validation | Rolling out-of-sample testing to detect overfitting |
| 🎲 Monte Carlo Simulation | Statistical significance testing (p < 0.05) |
| 🧠 Swarm AI Consensus | Multi-model voting (Gemini + OpenAI + Claude) |
| 📈 Risk Metrics | Sharpe, Calmar, VaR, CVaR, Omega, Ulcer Index |
| 💰 Transaction Cost Modeling | Commission + slippage injection |
| 🌍 Multi-Asset Backtesting | Test across BTC, ETH, SOL, SPY |
| ⚡ Redis Caching | With graceful fallback when Redis is unavailable |
| 🔒 Security | Code sanitization, rate limiting, JWT auth |

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | ✅ | Gemini API key ([aistudio.google.com](https://aistudio.google.com)) |
| `JWT_SECRET_KEY` | ✅ | Random 32+ char string |
| `DATABASE_URL` | ✅ | `sqlite:///./strategyvault.db` or PostgreSQL URL |
| `REDIS_URL` | Optional | `redis://localhost:6379` (falls back to NoOp) |
| `CORS_ORIGINS` | ✅ | Frontend URL (e.g., `http://localhost:3000`) |
| `OPENAI_API_KEY` | Optional | For swarm consensus multi-model |
| `ANTHROPIC_API_KEY` | Optional | For swarm consensus multi-model |

---

## Deployment

See [render.yaml](render.yaml) for one-click Render deployment or use Docker Compose for self-hosting.

```bash
# Deploy to Render (free tier)
# 1. Push to GitHub
# 2. render.com → New → Blueprint → select this repo
# 3. Set GOOGLE_API_KEY → Deploy
```

---

## Running Tests

```bash
cd backend
source venv/bin/activate
pytest tests/ -v  # 249 tests
```

---

## Subscription Tiers

| Tier | Price | Strategies/Month |
|------|-------|------------------|
| Explorer | $29/mo | 3 |
| Investor | $79/mo | 10 |
| Pro | $199/mo | Unlimited |

---

## License

MIT License — Educational purposes only. Not financial advice.
