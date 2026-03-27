"""
StrategyVault - Multi-AI Consensus Engine (Swarm Agent)
Adapted from Moon Dev's Swarm Agent architecture

Provides:
- Parallel querying of multiple AI models
- Consensus scoring and voting
- AI-generated summary synthesis
"""

import os
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
from enum import Enum
import json
from datetime import datetime

from dotenv import load_dotenv

# Load environment variables (root .env first, then local fallback)
from pathlib import Path
_root_env = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(_root_env)
load_dotenv()


class AIProvider(Enum):
    """Supported AI providers for consensus."""
    GEMINI = "gemini"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    DEEPSEEK = "deepseek"


@dataclass
class ModelResponse:
    """Response from a single AI model."""
    provider: str
    model_name: str
    response: str
    vote: str  # "BUY", "SELL", "HOLD", "POSITIVE", "NEGATIVE", "NEUTRAL"
    confidence: float  # 0-1
    reasoning: str
    response_time: float
    success: bool
    error: Optional[str] = None


@dataclass 
class ConsensusResult:
    """Result from multi-model consensus."""
    responses: List[ModelResponse]
    consensus_vote: str
    consensus_confidence: float  # % of models agreeing
    consensus_summary: str
    total_models: int
    successful_models: int
    vote_breakdown: Dict[str, int]
    timestamp: datetime = field(default_factory=datetime.now)


class SwarmAgent:
    """
    Multi-model AI Swarm Agent for strategy rating.
    
    Queries multiple AI models in parallel and generates consensus.
    """
    
    # Default models configuration
    DEFAULT_MODELS = {
        "gemini": {
            "enabled": True,
            "model_name": "gemini-2.5-flash",
        },
        "openai": {
            "enabled": True,
            "model_name": "gpt-4o",
        },
        "anthropic": {
            "enabled": True,
            "model_name": "claude-sonnet-4-5",
        },
        "deepseek": {
            "enabled": True,
            "model_name": "deepseek-chat",
        },
    }
    
    RATING_PROMPT = """
You are an expert trading strategy analyst. Evaluate the following trading strategy and provide your assessment.

STRATEGY DETAILS:
{strategy_details}

BACKTEST RESULTS:
- Return: {return_pct}%
- Sharpe Ratio: {sharpe_ratio}
- Max Drawdown: {max_drawdown}%
- Win Rate: {win_rate}%
- Number of Trades: {num_trades}

VALIDATION RESULTS:
- Walk-Forward Score: {walk_forward_score}/100
- Robustness: {is_robust}

YOUR TASK:
1. Analyze the strategy logic and backtest results
2. Assess if this strategy is worth purchasing for real trading

OUTPUT FORMAT (JSON):
{{
    "vote": "BUY" | "HOLD" | "SELL",
    "confidence": 0.0-1.0,
    "reasoning": "Your detailed analysis (2-3 sentences)",
    "strengths": ["strength1", "strength2"],
    "weaknesses": ["weakness1", "weakness2"],
    "recommendation": "One sentence summary"
}}

Respond ONLY with the JSON object.
"""
    
    CONSENSUS_PROMPT = """
You are synthesizing multiple AI analyst opinions into a single consensus summary.

INDIVIDUAL AI RESPONSES:
{responses}

VOTING BREAKDOWN:
{vote_breakdown}

Create a concise 3-sentence consensus summary that:
1. States the majority opinion and confidence level
2. Highlights the key agreement points
3. Notes any significant disagreements

Be objective and factual. Output only the summary text.
"""
    
    def __init__(self, custom_models: Optional[Dict] = None):
        """
        Initialize the Swarm Agent.
        
        Args:
            custom_models: Optional dict to override default model configuration
        """
        self.models = custom_models or self.DEFAULT_MODELS
        self._setup_clients()
    
    def _setup_clients(self):
        """Set up API clients for each provider."""
        self.clients = {}
        
        # Gemini
        if self.models.get("gemini", {}).get("enabled"):
            api_key = os.getenv("GOOGLE_API_KEY")
            if api_key:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                self.clients["gemini"] = genai.GenerativeModel(
                    self.models["gemini"]["model_name"]
                )
        
        # OpenAI
        if self.models.get("openai", {}).get("enabled"):
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                from openai import OpenAI
                self.clients["openai"] = OpenAI(api_key=api_key)
        
        # Anthropic
        if self.models.get("anthropic", {}).get("enabled"):
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if api_key:
                from anthropic import Anthropic
                self.clients["anthropic"] = Anthropic(api_key=api_key)
        
        # DeepSeek (OpenAI-compatible)
        if self.models.get("deepseek", {}).get("enabled"):
            api_key = os.getenv("DEEPSEEK_API_KEY")
            if api_key:
                from openai import OpenAI
                self.clients["deepseek"] = OpenAI(
                    api_key=api_key,
                    base_url="https://api.deepseek.com"
                )
    
    def _query_gemini(self, prompt: str) -> ModelResponse:
        """Query Gemini model."""
        start_time = datetime.now()
        try:
            response = self.clients["gemini"].generate_content(prompt)
            response_time = (datetime.now() - start_time).total_seconds()
            
            # Parse JSON response
            result = self._parse_json_response(response.text)
            
            return ModelResponse(
                provider="gemini",
                model_name=self.models["gemini"]["model_name"],
                response=response.text,
                vote=result.get("vote", "HOLD"),
                confidence=result.get("confidence", 0.5),
                reasoning=result.get("reasoning", ""),
                response_time=response_time,
                success=True
            )
        except Exception as e:
            return ModelResponse(
                provider="gemini",
                model_name=self.models["gemini"]["model_name"],
                response="",
                vote="HOLD",
                confidence=0.0,
                reasoning="",
                response_time=(datetime.now() - start_time).total_seconds(),
                success=False,
                error=str(e)
            )
    
    def _query_openai(self, prompt: str) -> ModelResponse:
        """Query OpenAI model."""
        start_time = datetime.now()
        try:
            response = self.clients["openai"].chat.completions.create(
                model=self.models["openai"]["model_name"],
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            response_time = (datetime.now() - start_time).total_seconds()
            
            text = response.choices[0].message.content
            result = self._parse_json_response(text)
            
            return ModelResponse(
                provider="openai",
                model_name=self.models["openai"]["model_name"],
                response=text,
                vote=result.get("vote", "HOLD"),
                confidence=result.get("confidence", 0.5),
                reasoning=result.get("reasoning", ""),
                response_time=response_time,
                success=True
            )
        except Exception as e:
            return ModelResponse(
                provider="openai",
                model_name=self.models["openai"]["model_name"],
                response="",
                vote="HOLD",
                confidence=0.0,
                reasoning="",
                response_time=(datetime.now() - start_time).total_seconds(),
                success=False,
                error=str(e)
            )
    
    def _query_anthropic(self, prompt: str) -> ModelResponse:
        """Query Anthropic model."""
        start_time = datetime.now()
        try:
            response = self.clients["anthropic"].messages.create(
                model=self.models["anthropic"]["model_name"],
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            response_time = (datetime.now() - start_time).total_seconds()
            
            text = response.content[0].text
            result = self._parse_json_response(text)
            
            return ModelResponse(
                provider="anthropic",
                model_name=self.models["anthropic"]["model_name"],
                response=text,
                vote=result.get("vote", "HOLD"),
                confidence=result.get("confidence", 0.5),
                reasoning=result.get("reasoning", ""),
                response_time=response_time,
                success=True
            )
        except Exception as e:
            return ModelResponse(
                provider="anthropic",
                model_name=self.models["anthropic"]["model_name"],
                response="",
                vote="HOLD",
                confidence=0.0,
                reasoning="",
                response_time=(datetime.now() - start_time).total_seconds(),
                success=False,
                error=str(e)
            )
    
    def _query_deepseek(self, prompt: str) -> ModelResponse:
        """Query DeepSeek model."""
        start_time = datetime.now()
        try:
            response = self.clients["deepseek"].chat.completions.create(
                model=self.models["deepseek"]["model_name"],
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            response_time = (datetime.now() - start_time).total_seconds()
            
            text = response.choices[0].message.content
            result = self._parse_json_response(text)
            
            return ModelResponse(
                provider="deepseek",
                model_name=self.models["deepseek"]["model_name"],
                response=text,
                vote=result.get("vote", "HOLD"),
                confidence=result.get("confidence", 0.5),
                reasoning=result.get("reasoning", ""),
                response_time=response_time,
                success=True
            )
        except Exception as e:
            return ModelResponse(
                provider="deepseek",
                model_name=self.models["deepseek"]["model_name"],
                response="",
                vote="HOLD",
                confidence=0.0,
                reasoning="",
                response_time=(datetime.now() - start_time).total_seconds(),
                success=False,
                error=str(e)
            )
    
    def _parse_json_response(self, text: str) -> Dict:
        """Parse JSON from AI response."""
        try:
            # Try direct JSON parse
            return json.loads(text)
        except json.JSONDecodeError:
            # Try extracting JSON from text
            import re
            json_match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass
        return {}
    
    def rate_strategy(
        self,
        strategy_details: str,
        return_pct: float,
        sharpe_ratio: float,
        max_drawdown: float,
        win_rate: float,
        num_trades: int,
        walk_forward_score: float,
        is_robust: bool
    ) -> ConsensusResult:
        """
        Rate a strategy using multi-model consensus.
        
        Args:
            strategy_details: Description of the strategy
            return_pct: Backtest return percentage
            sharpe_ratio: Sharpe ratio
            max_drawdown: Maximum drawdown percentage
            win_rate: Win rate percentage
            num_trades: Number of trades
            walk_forward_score: Walk-forward validation score (0-100)
            is_robust: Whether strategy passed robustness tests
            
        Returns:
            ConsensusResult with voting and summary
        """
        # Build the prompt
        prompt = self.RATING_PROMPT.format(
            strategy_details=strategy_details,
            return_pct=return_pct,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            num_trades=num_trades,
            walk_forward_score=walk_forward_score,
            is_robust="Yes" if is_robust else "No"
        )
        
        # Query all models in parallel
        responses = []
        query_functions = {
            "gemini": self._query_gemini,
            "openai": self._query_openai,
            "anthropic": self._query_anthropic,
            "deepseek": self._query_deepseek,
        }
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {}
            for provider, func in query_functions.items():
                if provider in self.clients:
                    futures[executor.submit(func, prompt)] = provider
            
            for future in as_completed(futures):
                try:
                    response = future.result(timeout=60)
                    responses.append(response)
                except Exception as e:
                    provider = futures[future]
                    responses.append(ModelResponse(
                        provider=provider,
                        model_name=self.models.get(provider, {}).get("model_name", "unknown"),
                        response="",
                        vote="HOLD",
                        confidence=0.0,
                        reasoning="",
                        response_time=0,
                        success=False,
                        error=str(e)
                    ))
        
        # Calculate consensus
        return self._calculate_consensus(responses)
    
    def _calculate_consensus(self, responses: List[ModelResponse]) -> ConsensusResult:
        """Calculate consensus from all model responses."""
        successful = [r for r in responses if r.success]
        
        # Vote breakdown
        votes = {}
        for r in successful:
            vote = r.vote.upper()
            votes[vote] = votes.get(vote, 0) + 1
        
        # Determine consensus vote
        if votes:
            consensus_vote = max(votes, key=votes.get)
            consensus_confidence = votes[consensus_vote] / len(successful) if successful else 0
        else:
            consensus_vote = "HOLD"
            consensus_confidence = 0
        
        # Generate consensus summary
        summary = self._generate_consensus_summary(responses, votes)
        
        return ConsensusResult(
            responses=responses,
            consensus_vote=consensus_vote,
            consensus_confidence=consensus_confidence,
            consensus_summary=summary,
            total_models=len(responses),
            successful_models=len(successful),
            vote_breakdown=votes
        )
    
    def _generate_consensus_summary(
        self,
        responses: List[ModelResponse],
        vote_breakdown: Dict[str, int]
    ) -> str:
        """Generate a consensus summary from all responses."""
        successful = [r for r in responses if r.success]
        
        if not successful:
            return "No successful model responses to generate consensus."
        
        # Build summary from reasoning
        reasonings = [r.reasoning for r in successful if r.reasoning]
        
        if not reasonings:
            return f"Consensus vote: {max(vote_breakdown, key=vote_breakdown.get) if vote_breakdown else 'HOLD'} based on {len(successful)} models."
        
        # Simple summary (could use AI for more sophisticated synthesis)
        total = sum(vote_breakdown.values())
        breakdown_str = ", ".join([f"{v}: {c}/{total}" for v, c in vote_breakdown.items()])
        
        return f"Multi-AI Consensus ({breakdown_str}). " + " | ".join(reasonings[:3])


def calculate_strategy_score(
    return_pct: float,
    sharpe_ratio: float,
    max_drawdown: float,
    consensus_confidence: float,
    walk_forward_score: float,
    is_robust: bool
) -> int:
    """
    Calculate overall strategy score (0-100).
    
    Weights:
    - AI Consensus: 25%
    - Walk-Forward Score: 25%
    - Return Performance: 20%
    - Risk-Adjusted (Sharpe): 20%
    - Robustness: 10%
    """
    score = 0
    
    # AI Consensus (25 points max)
    score += consensus_confidence * 25
    
    # Walk-Forward Score (25 points max)
    score += (walk_forward_score / 100) * 25
    
    # Return Performance (20 points max)
    # Scale: 0-10% = 0-10 points, 10-50% = 10-20 points
    if return_pct > 0:
        return_score = min(20, return_pct / 2.5)
        score += return_score
    
    # Sharpe Ratio (20 points max)
    # Scale: 0-1 = 0-10 points, 1-2 = 10-20 points
    if sharpe_ratio > 0:
        sharpe_score = min(20, sharpe_ratio * 10)
        score += sharpe_score
    
    # Robustness (10 points)
    if is_robust:
        score += 10
    
    # Penalty for high drawdown
    if max_drawdown < -30:
        score -= 10
    elif max_drawdown < -20:
        score -= 5
    
    return max(0, min(100, int(score)))


if __name__ == "__main__":
    # Test the swarm agent
    print("Testing Swarm Agent...")
    print("Note: Requires API keys to be set in environment")
    
    # Test score calculation
    score = calculate_strategy_score(
        return_pct=35.0,
        sharpe_ratio=1.5,
        max_drawdown=-15.0,
        consensus_confidence=0.75,
        walk_forward_score=80,
        is_robust=True
    )
    print(f"\nTest Strategy Score: {score}/100")
