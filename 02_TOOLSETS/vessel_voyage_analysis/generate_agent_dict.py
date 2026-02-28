import os
import csv
from collections import Counter
from pathlib import Path

# Path to source files
source_dir = r'G:\My Drive\LLM\project_mrtis\00_source_files'

# Dictionary to store agent counts
agent_counts = Counter()

# Process all CSV files
csv_files = list(Path(source_dir).glob('*.csv'))
print(f"Found {len(csv_files)} CSV files to process")

for csv_file in csv_files:
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                agent = row.get('Agent', '').strip()
                # Only count if Agent is not empty
                if agent:
                    agent_counts[agent] += 1
    except Exception as e:
        print(f"Error reading {csv_file}: {e}")

# Sort by count descending
sorted_agents = sorted(agent_counts.items(), key=lambda x: x[1], reverse=True)

print(f"\nFound {len(sorted_agents)} unique agents")
print("\nTop 20 agents by event count:")
for agent, count in sorted_agents[:20]:
    print(f"  {agent}: {count} events")

# Create output CSV
output_file = r'G:\My Drive\LLM\project_mrtis\agent_dictionary.csv'
with open(output_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Agent', 'EventCount', 'Note'])
    for agent, count in sorted_agents:
        writer.writerow([agent, count, ''])

print(f"\nCreated {output_file}")
print(f"Total unique agents: {len(sorted_agents)}")
print(f"Total events processed: {sum(agent_counts.values())}")
