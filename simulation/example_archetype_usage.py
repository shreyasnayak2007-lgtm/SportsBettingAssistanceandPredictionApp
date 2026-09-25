# simulation/example_archetype_usage.py

from data_loader import StatcastDataLoader
from pitcher_archetype import PitcherArchetype, ArchetypePool, ArchetypeComparison

# Load data
loader = StatcastDataLoader()
df = loader.load_season(2023)

# Example 1: Classify a single pitcher
pitcher_stats = {
    'pitcher_name': 'Clayton Kershaw',
    'fastball_avg_velo': 97,
    'fastball_pct': 0.65,
    'breaking_avg_velo': 81,
    'whiff_rate': 0.28,
    'pitcher_hand': 'R'
}

classifier = PitcherArchetype()
archetype = classifier.classify(pitcher_stats)
print(f"Kershaw classified as: {archetype}")
# Output: Kershaw classified as: elite_heat

# Example 2: Get explanation for classification
explanation = classifier.explain_classification(pitcher_stats)
print(f"\nExplanation:")
for key, value in explanation['thresholds_checked'].items():
    print(f"  {key}: {value}")

# Example 3: Manage archetype pools
archetype_pool = ArchetypePool(df)

# Get all pitchers of a specific archetype
elite_heat_pitchers = archetype_pool.get_pitchers_by_archetype(
    'elite_heat',
    {pid: loader.get_pitcher_stats(pid) for pid in df['pitcher'].unique()}
)
print(f"\nFound {len(elite_heat_pitchers)} elite heat pitchers")

# Get aggregate stats for an archetype
elite_heat_stats = archetype_pool.get_archetype_stats('elite_heat', elite_heat_pitchers)
print(f"Elite heat archetype stats:")
print(f"  Avg fastball velo: {elite_heat_stats['avg_fastball_velo']:.1f} mph")
print(f"  Whiff rate: {elite_heat_stats['avg_whiff_rate']:.1%}")
print(f"  K rate: {elite_heat_stats['k_rate']:.1%}")

# Example 4: Analyze batter vs archetypes
comparison = ArchetypeComparison(archetype_pool)
batter_performance = comparison.explain_batter_vs_archetypes(batter_id=430945)  # Mike Trout

print(f"\nMike Trout vs archetypes:")
for archetype, stats in batter_performance.items():
    if stats['pa_count'] > 0:
        print(f"  vs {archetype}: {stats['pa_count']} PA, BA: {stats['ba']:.3f}, K%: {stats['k_rate']:.1%}")

# Example 5: Compare all archetypes
comparison_all = comparison.compare_all_archetypes()
print(f"\nAll archetype comparisons:")
for archetype, stats in comparison_all.items():
    print(f"  {archetype}: {stats['pitcher_count']} pitchers, K%: {stats['k_rate']:.1%}")