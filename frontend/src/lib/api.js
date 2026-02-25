/**
 * StrategyVault - API Client
 * Handles all communication with the FastAPI backend
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

class ApiClient {
  async get(endpoint) {
    const res = await fetch(`${API_BASE}${endpoint}`);
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(error.detail || 'API request failed');
    }
    return res.json();
  }

  async post(endpoint, body) {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(error.detail || 'API request failed');
    }
    return res.json();
  }

  // Strategy endpoints
  getStrategies(page = 1, perPage = 20, tier = null) {
    let url = `/strategies/?page=${page}&per_page=${perPage}`;
    if (tier) url += `&tier=${tier}`;
    return this.get(url);
  }

  getStrategy(id) {
    return this.get(`/strategies/${id}`);
  }

  generateStrategy(tradingIdea) {
    return this.post('/strategies/generate', { trading_idea: tradingIdea });
  }

  // Marketplace endpoints
  getMarketplace() {
    return this.get('/marketplace/');
  }

  searchStrategies(query, filters = {}) {
    const params = new URLSearchParams();
    if (query) params.set('query', query);
    if (filters.tier) params.set('tier', filters.tier);
    if (filters.minReturn) params.set('min_return', filters.minReturn);
    return this.get(`/marketplace/search?${params.toString()}`);
  }

  purchaseStrategy(id) {
    return this.post(`/marketplace/purchase/${id}`);
  }
}

export const api = new ApiClient();
export default api;
