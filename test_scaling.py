
import numpy as np
from simulation import run_single_day
from users import generate_all_events

def test_scaling():
    print("--- WATER USAGE SCALING VERIFICATION ---")
    
    # Test 1 person (Garden disabled via logic override)
    s1 = run_single_day(seed=42, num_users=1, duration_minutes=1440, garden_time=-1000)
    print(f"1 Person Household (Indoor): {s1.cumulative_liters:.1f} L")
    
    # Test 4 persons
    s4 = run_single_day(seed=42, num_users=4, duration_minutes=1440, garden_time=-1000)
    print(f"4 Person Household (Indoor): {s4.cumulative_liters:.1f} L")
    
    # Test 10 persons
    s10 = run_single_day(seed=42, num_users=10, duration_minutes=1440, garden_time=-1000)
    print(f"10 Person Household (Indoor): {s10.cumulative_liters:.1f} L")
    
    # Check scaling ratios
    # Expected baseline: 179*n + 178.6
    # 1 person: ~357.6 L
    # 4 person: ~894.6 L
    # 10 person: ~1968.6 L
    
    print("\nScaling Verification:")
    print(f"1p vs 4p Ratio: {s4.cumulative_liters / s1.cumulative_liters:.2f} (Expected ~2.5)")
    print(f"1p vs 10p Ratio: {s10.cumulative_liters / s1.cumulative_liters:.2f} (Expected ~5.5)")
    
    # Event count check
    e1 = len(s1.events)
    e10 = len(s10.events)
    print(f"\nEvent Density:")
    print(f"1 Person events: {e1}")
    print(f"10 Person events: {e10}")
    print(f"Density increase: {e10/e1:.2f}x")

if __name__ == "__main__":
    test_scaling()
