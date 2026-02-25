"""
StrategyVault - Ablation Study Module
Adapted from AgentQuant's ablation methodology

Provides:
- Component importance analysis
- Feature contribution scoring
- Parameter sensitivity testing
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class AblationComponent:
    """A component being tested in ablation study."""
    name: str
    description: str
    enabled: bool
    contribution_pct: Optional[float] = None


@dataclass
class AblationResult:
    """Results from ablation study."""
    baseline_return: float
    components: List[AblationComponent]
    total_contribution: float
    most_important: str
    least_important: str


def calculate_component_contribution(
    baseline_return: float,
    ablated_return: float
) -> float:
    """
    Calculate the contribution of a component.
    
    Args:
        baseline_return: Return with all components enabled
        ablated_return: Return with this component disabled
        
    Returns:
        Contribution percentage (positive = component helps)
    """
    if baseline_return == 0:
        return 0.0
    
    # Contribution = how much return drops when component is removed
    return ((baseline_return - ablated_return) / abs(baseline_return)) * 100


def run_ablation_study(
    baseline_return: float,
    component_results: Dict[str, float]
) -> AblationResult:
    """
    Run ablation study to determine component importance.
    
    Args:
        baseline_return: Return with all components enabled
        component_results: Dictionary mapping component name to return without that component
        
    Returns:
        AblationResult with component contributions
    """
    components = []
    
    for name, ablated_return in component_results.items():
        contribution = calculate_component_contribution(baseline_return, ablated_return)
        components.append(AblationComponent(
            name=name,
            description=f"Return without {name}: {ablated_return:.2f}%",
            enabled=True,
            contribution_pct=contribution
        ))
    
    # Sort by contribution
    components.sort(key=lambda x: x.contribution_pct or 0, reverse=True)
    
    total_contribution = sum(c.contribution_pct for c in components if c.contribution_pct)
    
    return AblationResult(
        baseline_return=baseline_return,
        components=components,
        total_contribution=total_contribution,
        most_important=components[0].name if components else "N/A",
        least_important=components[-1].name if components else "N/A"
    )


def generate_ablation_report(result: AblationResult) -> str:
    """Generate human-readable ablation report."""
    report = []
    report.append("=" * 60)
    report.append("ABLATION STUDY REPORT")
    report.append("=" * 60)
    
    report.append(f"\nBaseline Return: {result.baseline_return:.2f}%")
    
    report.append(f"\nComponent Contributions:")
    for comp in result.components:
        if comp.contribution_pct is not None:
            bar = "█" * int(min(20, max(0, comp.contribution_pct / 5)))
            report.append(f"  {comp.name}: {comp.contribution_pct:+.1f}% {bar}")
    
    report.append(f"\nMost Important: {result.most_important}")
    report.append(f"Least Important: {result.least_important}")
    
    report.append("\n" + "=" * 60)
    
    return "\n".join(report)


if __name__ == "__main__":
    # Test ablation study
    print("Testing ablation study...")
    
    baseline = 25.0  # 25% return with all components
    
    # Results when each component is disabled
    ablated_results = {
        "RSI Filter": 18.0,      # Return drops to 18% without RSI
        "Momentum": 12.0,        # Return drops to 12% without momentum
        "Volume Filter": 22.0,   # Return drops to 22% without volume
        "Stop Loss": 15.0,       # Return drops to 15% without stop loss
    }
    
    result = run_ablation_study(baseline, ablated_results)
    print(generate_ablation_report(result))
