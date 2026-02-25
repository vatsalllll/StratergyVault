"""
StrategyVault - AI Strategy Generator
Adapted from Moon Dev's RBI Agent for automated strategy creation

Provides:
- Natural language to strategy code conversion
- AI-powered backtest code generation
- Multi-model support (Gemini, DeepSeek, OpenAI)
"""

import os
import re
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

from dotenv import load_dotenv

from src.core.config import settings


class AIModel(Enum):
    """Supported AI models for strategy generation."""
    GEMINI_FLASH = "gemini-2.5-flash"
    GEMINI_PRO = "gemini-2.0-pro"
    DEEPSEEK = "deepseek-chat"
    GPT4 = "gpt-4o"


@dataclass
class GeneratedStrategy:
    """Container for AI-generated strategy."""
    name: str
    description: str
    code: str
    model_used: str
    generation_prompt: str
    raw_response: str


# Strategy Generation Prompt
STRATEGY_GENERATION_PROMPT = """
You are an expert quantitative trading strategy developer.
Create a complete backtesting.py strategy based on the following idea:

TRADING IDEA:
{trading_idea}

REQUIREMENTS:
1. Use the backtesting.py library
2. Include all necessary imports (backtesting, talib, pandas, numpy)
3. Create a Strategy class with proper indicators wrapped in self.I()
4. Implement clear entry/exit logic
5. Use proper risk management (position sizing, stop losses)
6. The initial cash should be 100,000

CRITICAL RULES:
1. ALWAYS use self.I() wrapper for indicator calculations
2. Use talib for indicators: self.I(talib.SMA, self.data.Close, timeperiod=20)
3. Position sizes must be integers or fractions (0-1)
4. No plotting - only print stats
5. Include data loading that works with this CSV format:
   datetime, open, high, low, close, volume

INDICATOR EXAMPLES:
- SMA: self.sma = self.I(talib.SMA, self.data.Close, timeperiod=20)
- RSI: self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
- MACD: self.macd, self.macd_signal, _ = self.I(talib.MACD, self.data.Close)
- BB: self.bb_upper, self.bb_mid, self.bb_lower = self.I(talib.BBANDS, self.data.Close)

DATA LOADING TEMPLATE:
```python
import pandas as pd
data = pd.read_csv(DATA_PATH)
data.columns = data.columns.str.strip().str.lower()
data = data.rename(columns={{'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}})
data['datetime'] = pd.to_datetime(data['datetime'])
data = data.set_index('datetime')
```

OUTPUT FORMAT:
First, provide a STRATEGY_NAME (two words, unique):
STRATEGY_NAME: [YourStrategyName]

Then provide the complete Python code:
```python
# Your complete strategy code here
```

ONLY OUTPUT THE STRATEGY NAME AND CODE. NO OTHER TEXT.
"""


STRATEGY_DEBUG_PROMPT = """
You are a Python debugging expert specializing in backtesting.py strategies.

Fix the following error in this backtest code WITHOUT changing the strategy logic:

ERROR:
{error_message}

ORIGINAL CODE:
```python
{code}
```

COMMON FIXES:
1. KeyError with columns: Use proper column renaming after .str.lower()
2. Position sizing: Must be int(round(size)) or fraction 0-1
3. Indicator issues: All indicators must use self.I() wrapper
4. .shift() on indicators: Use array indexing [-2] instead
5. Position.entry_price: Use self.trades[-1].entry_price instead

Return the COMPLETE fixed code. ONLY CODE, NO OTHER TEXT.
"""


STRATEGY_OPTIMIZE_PROMPT = """
You are an expert strategy optimizer. Improve this strategy to achieve better returns.

CURRENT PERFORMANCE:
- Return: {current_return}%
- Target: {target_return}%

CURRENT CODE:
```python
{code}
```

OPTIMIZATION TECHNIQUES:
1. Tighten entry conditions with additional filters
2. Improve exit logic (trailing stops, take profits)
3. Add volatility-based position sizing
4. Fine-tune indicator parameters
5. Add trend/regime filters

RULES:
- Keep the same general strategy approach
- Position sizes must be int or fraction (0-1)
- Use self.I() for all indicators
- No plotting

Return the COMPLETE optimized code. ONLY CODE, NO OTHER TEXT.
"""


class StrategyGenerator:
    """AI-powered strategy generator using multiple models."""
    
    def __init__(self, model: AIModel = AIModel.GEMINI_FLASH):
        """
        Initialize the strategy generator.
        
        Args:
            model: AI model to use for generation
        """
        load_dotenv()
        self.model = model
        self._setup_model()
    
    def _setup_model(self):
        """Configure the AI model."""
        if self.model in [AIModel.GEMINI_FLASH, AIModel.GEMINI_PRO]:
            api_key = os.getenv("GOOGLE_API_KEY") or settings.GOOGLE_API_KEY
            if not api_key:
                raise ValueError("GOOGLE_API_KEY not found in environment")
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self.client = genai.GenerativeModel(self.model.value)
        # Add support for other models as needed
    
    def generate_strategy(self, trading_idea: str) -> GeneratedStrategy:
        """
        Generate a trading strategy from a natural language idea.
        
        Args:
            trading_idea: Natural language description of the trading strategy
            
        Returns:
            GeneratedStrategy with name, code, and metadata
        """
        prompt = STRATEGY_GENERATION_PROMPT.format(trading_idea=trading_idea)
        
        response = self.client.generate_content(prompt)
        raw_text = response.text
        
        # Parse strategy name
        name_match = re.search(r'STRATEGY_NAME:\s*(\w+)', raw_text)
        strategy_name = name_match.group(1) if name_match else "GeneratedStrategy"
        
        # Extract code
        code = self._extract_code(raw_text)
        
        return GeneratedStrategy(
            name=strategy_name,
            description=trading_idea,
            code=code,
            model_used=self.model.value,
            generation_prompt=prompt,
            raw_response=raw_text
        )
    
    def debug_strategy(self, code: str, error_message: str) -> str:
        """
        Fix errors in strategy code using AI.
        
        Args:
            code: The broken strategy code
            error_message: Error message from execution
            
        Returns:
            Fixed strategy code
        """
        prompt = STRATEGY_DEBUG_PROMPT.format(
            error_message=error_message,
            code=code
        )
        
        response = self.client.generate_content(prompt)
        return self._extract_code(response.text)
    
    def optimize_strategy(
        self, 
        code: str, 
        current_return: float,
        target_return: float = 50.0
    ) -> str:
        """
        Optimize a strategy to improve returns.
        
        Args:
            code: Current strategy code
            current_return: Current return percentage
            target_return: Target return percentage
            
        Returns:
            Optimized strategy code
        """
        prompt = STRATEGY_OPTIMIZE_PROMPT.format(
            current_return=current_return,
            target_return=target_return,
            code=code
        )
        
        response = self.client.generate_content(prompt)
        return self._extract_code(response.text)
    
    def _extract_code(self, text: str) -> str:
        """Extract Python code from AI response."""
        # Try to find code blocks
        code_match = re.search(r'```python\n(.*?)```', text, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
        
        # Try without language specifier
        code_match = re.search(r'```\n(.*?)```', text, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
        
        # If no code blocks, return cleaned text
        # Remove common non-code prefixes
        lines = text.split('\n')
        code_lines = []
        in_code = False
        
        for line in lines:
            # Skip strategy name lines
            if line.strip().startswith('STRATEGY_NAME:'):
                continue
            # Start collecting after import statements
            if line.strip().startswith('import') or line.strip().startswith('from'):
                in_code = True
            if in_code:
                code_lines.append(line)
        
        return '\n'.join(code_lines) if code_lines else text


def generate_backtest_template(strategy_name: str) -> str:
    """
    Generate a basic backtest template that can be customized.
    
    Args:
        strategy_name: Name for the strategy class
        
    Returns:
        Python code template for backtesting
    """
    return f'''"""
{strategy_name} - Generated by StrategyVault
"""

import pandas as pd
import numpy as np
import talib
from backtesting import Backtest, Strategy


class {strategy_name}(Strategy):
    """Trading strategy generated by StrategyVault AI."""
    
    # Parameters (can be optimized)
    fast_period = 10
    slow_period = 30
    rsi_period = 14
    rsi_oversold = 30
    rsi_overbought = 70
    
    def init(self):
        """Initialize indicators."""
        # Moving averages
        self.fast_ma = self.I(talib.SMA, self.data.Close, timeperiod=self.fast_period)
        self.slow_ma = self.I(talib.SMA, self.data.Close, timeperiod=self.slow_period)
        
        # RSI
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=self.rsi_period)
        
        print(f"🚀 {strategy_name} initialized!")
    
    def next(self):
        """Execute trading logic on each bar."""
        # Skip if not enough data
        if len(self.data) < self.slow_period:
            return
        
        # Entry logic: Fast MA crosses above Slow MA and RSI not overbought
        if not self.position:
            if (self.fast_ma[-2] < self.slow_ma[-2] and 
                self.fast_ma[-1] > self.slow_ma[-1] and
                self.rsi[-1] < self.rsi_overbought):
                
                # Calculate position size (use fraction of equity)
                self.buy(size=0.95)
                print(f"📈 BUY at {{self.data.Close[-1]:.2f}}")
        
        # Exit logic: Fast MA crosses below Slow MA or RSI overbought
        elif self.position.is_long:
            if (self.fast_ma[-2] > self.slow_ma[-2] and 
                self.fast_ma[-1] < self.slow_ma[-1]):
                
                self.position.close()
                print(f"📉 SELL at {{self.data.Close[-1]:.2f}}")
            
            elif self.rsi[-1] > self.rsi_overbought:
                self.position.close()
                print(f"📉 SELL (RSI overbought) at {{self.data.Close[-1]:.2f}}")


def load_data(file_path: str) -> pd.DataFrame:
    """Load and prepare data for backtesting."""
    data = pd.read_csv(file_path)
    data.columns = data.columns.str.strip().str.lower()
    data = data.rename(columns={{
        'open': 'Open',
        'high': 'High', 
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume'
    }})
    data['datetime'] = pd.to_datetime(data['datetime'])
    data = data.set_index('datetime')
    return data


if __name__ == "__main__":
    # Example usage with sample data
    DATA_PATH = "path/to/your/data.csv"
    
    # Load data
    data = load_data(DATA_PATH)
    
    # Run backtest
    bt = Backtest(
        data,
        {strategy_name},
        cash=100000,
        commission=0.001,
        exclusive_orders=True
    )
    
    # Execute
    stats = bt.run()
    print(stats)
    print(f"\\n✅ Backtest complete!")
'''


if __name__ == "__main__":
    # Test strategy generation
    print("Testing strategy generator...")
    
    generator = StrategyGenerator(AIModel.GEMINI_FLASH)
    
    idea = "Buy when RSI is below 30 and price crosses above the 20-day SMA. Sell when RSI is above 70 or price crosses below the 20-day SMA."
    
    try:
        strategy = generator.generate_strategy(idea)
        print(f"\nGenerated strategy: {strategy.name}")
        print(f"Model used: {strategy.model_used}")
        print(f"\nCode preview (first 500 chars):")
        print(strategy.code[:500])
    except Exception as e:
        print(f"Error: {e}")
        print("\nGenerating template instead...")
        template = generate_backtest_template("RSIMomentum")
        print(template[:500])
