# StrategyVault 🚀

> AI-Powered Trading Strategy Marketplace

A subscription-based platform where AI generates, validates, and sells institutional-grade trading strategies.

## Architecture

This platform combines the best features from three projects:

| Component | Source | Purpose |
|-----------|--------|---------|
| Strategy Generation | Moon Dev RBI Agent | AI creates strategies from natural language |
| Validation | AgentQuant | Walk-forward analysis, ablation studies |
| Rating | Moon Dev Swarm | 6-model AI consensus scoring |

## Quick Start

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Project Structure

```
strategy-vault/
├── backend/
│   ├── src/
│   │   ├── api/          # FastAPI routes
│   │   ├── core/         # Configuration
│   │   ├── data/         # Market data fetching
│   │   ├── features/     # Technical indicators
│   │   ├── generation/   # AI strategy generation
│   │   ├── validation/   # Walk-forward, ablation
│   │   ├── rating/       # Multi-AI consensus
│   │   ├── models/       # Database models
│   │   └── services/     # Business logic
│   ├── tests/
│   ├── main.py
│   └── requirements.txt
└── frontend/             # Next.js app
```

## Subscription Tiers

| Tier | Price | Strategies/Month |
|------|-------|------------------|
| Explorer | $29/mo | 3 |
| Investor | $79/mo | 10 |
| Pro | $199/mo | Unlimited |

## License

MIT License - Educational purposes only. Not financial advice.
