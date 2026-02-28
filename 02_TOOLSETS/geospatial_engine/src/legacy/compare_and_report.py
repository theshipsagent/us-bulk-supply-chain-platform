import json
from urllib.parse import urlparse
from collections import defaultdict

def load_json(filepath):
    """Load JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return []

def normalize_url(url):
    """Normalize URL for comparison."""
    parsed = urlparse(url.lower())
    # Remove www. and trailing slashes
    domain = parsed.netloc.replace('www.', '')
    path = parsed.path.rstrip('/')
    return f"{domain}{path}"

def main():
    # Load bookmarks
    bookmarks_file = r'G:\My Drive\LLM\sources_data_maps\chrome_bookmarks_datasets.json'
    bookmarks = load_json(bookmarks_file)

    # Load existing inventory files
    eia_file = r'G:\My Drive\LLM\sources_data_maps\eia_datasets_complete.json'
    fgdc_file = r'G:\My Drive\LLM\sources_data_maps\fgdc_datasets_complete.json'
    maritime_file = r'G:\My Drive\LLM\sources_data_maps\maritime_usace_noaa_datasets.json'

    eia_datasets = load_json(eia_file)
    fgdc_datasets = load_json(fgdc_file)
    maritime_datasets = load_json(maritime_file)

    # Create a set of normalized URLs from existing inventories
    existing_urls = set()
    existing_url_map = {}  # Map normalized URL to original entry

    for dataset in eia_datasets:
        if 'url' in dataset:
            norm_url = normalize_url(dataset['url'])
            existing_urls.add(norm_url)
            existing_url_map[norm_url] = {
                'source': 'EIA Inventory',
                'title': dataset.get('title', '')
            }

    for dataset in fgdc_datasets:
        if 'url' in dataset:
            norm_url = normalize_url(dataset['url'])
            existing_urls.add(norm_url)
            existing_url_map[norm_url] = {
                'source': 'FGDC Inventory',
                'title': dataset.get('title', dataset.get('name', ''))
            }

    for dataset in maritime_datasets:
        if 'url' in dataset:
            norm_url = normalize_url(dataset['url'])
            existing_urls.add(norm_url)
            existing_url_map[norm_url] = {
                'source': 'Maritime Inventory',
                'title': dataset.get('title', '')
            }

    # Check bookmarks against existing inventories
    duplicates = []
    new_sources = []

    for bookmark in bookmarks:
        norm_url = normalize_url(bookmark['url'])

        if norm_url in existing_urls:
            duplicates.append({
                'bookmark_title': bookmark['title'],
                'bookmark_url': bookmark['url'],
                'bookmark_category': bookmark['category'],
                'existing_in': existing_url_map[norm_url]['source'],
                'existing_title': existing_url_map[norm_url]['title']
            })
        else:
            new_sources.append(bookmark)

    # Generate comprehensive report
    report = {
        'summary': {
            'total_bookmarks_found': len(bookmarks),
            'data_sources_identified': len(bookmarks),
            'duplicates_found': len(duplicates),
            'new_sources': len(new_sources),
            'existing_inventory_sizes': {
                'EIA Datasets': len(eia_datasets),
                'FGDC Datasets': len(fgdc_datasets),
                'Maritime/USACE/NOAA Datasets': len(maritime_datasets),
                'Total Existing': len(eia_datasets) + len(fgdc_datasets) + len(maritime_datasets)
            }
        },
        'duplicates': duplicates,
        'new_sources_by_category': {},
        'all_new_sources': new_sources
    }

    # Organize new sources by category
    category_counts = defaultdict(int)
    category_sources = defaultdict(list)

    for source in new_sources:
        category = source['category']
        category_counts[category] += 1
        category_sources[category].append({
            'title': source['title'],
            'url': source['url'],
            'source': source['source'],
            'bookmark_folder': source['bookmark_folder_path']
        })

    report['new_sources_by_category'] = {
        'counts': dict(category_counts),
        'sources': dict(category_sources)
    }

    # Save report
    report_file = r'G:\My Drive\LLM\sources_data_maps\chrome_bookmarks_analysis_report.json'
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Create a text summary report
    text_report_file = r'G:\My Drive\LLM\sources_data_maps\chrome_bookmarks_analysis_report.txt'
    with open(text_report_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("CHROME BOOKMARKS DATA SOURCES ANALYSIS REPORT\n")
        f.write("=" * 80 + "\n\n")

        f.write("SUMMARY\n")
        f.write("-" * 80 + "\n")
        f.write(f"Total bookmarks found: {len(bookmarks)}\n")
        f.write(f"Data sources identified: {len(bookmarks)}\n")
        f.write(f"New sources (not in existing inventory): {len(new_sources)}\n")
        f.write(f"Duplicates (already in inventory): {len(duplicates)}\n\n")

        f.write("EXISTING INVENTORY STATUS\n")
        f.write("-" * 80 + "\n")
        f.write(f"EIA Datasets: {len(eia_datasets)}\n")
        f.write(f"FGDC Datasets: {len(fgdc_datasets)}\n")
        f.write(f"Maritime/USACE/NOAA Datasets: {len(maritime_datasets)}\n")
        f.write(f"Total Existing: {len(eia_datasets) + len(fgdc_datasets) + len(maritime_datasets)}\n\n")

        f.write("NEW SOURCES BY CATEGORY\n")
        f.write("-" * 80 + "\n")
        for category in sorted(category_counts.keys(), key=lambda x: category_counts[x], reverse=True):
            f.write(f"\n{category}: {category_counts[category]} sources\n")
            f.write("-" * 40 + "\n")
            for source in category_sources[category][:10]:  # First 10 per category
                f.write(f"  - {source['title']}\n")
                f.write(f"    URL: {source['url']}\n")
                f.write(f"    Folder: {source['bookmark_folder']}\n\n")
            if len(category_sources[category]) > 10:
                f.write(f"  ... and {len(category_sources[category]) - 10} more\n\n")

        f.write("\n" + "=" * 80 + "\n")
        f.write("DUPLICATES FOUND IN EXISTING INVENTORY\n")
        f.write("=" * 80 + "\n\n")

        if duplicates:
            for i, dup in enumerate(duplicates, 1):
                f.write(f"{i}. {dup['bookmark_title']}\n")
                f.write(f"   URL: {dup['bookmark_url']}\n")
                f.write(f"   Category: {dup['bookmark_category']}\n")
                f.write(f"   Already in: {dup['existing_in']}\n")
                f.write(f"   As: {dup['existing_title']}\n\n")
        else:
            f.write("No duplicates found - all bookmarks are new sources!\n\n")

        f.write("=" * 80 + "\n")
        f.write("RECOMMENDATIONS\n")
        f.write("=" * 80 + "\n")
        f.write(f"1. Review {len(new_sources)} new data sources identified\n")
        f.write(f"2. Add relevant sources to appropriate inventory files\n")
        f.write(f"3. Assign DS-XXX identifiers starting from DS-178 onwards\n")
        f.write(f"4. Verify and enhance metadata for each source\n")
        f.write(f"5. Cross-reference with existing datasets to avoid duplication\n")

    print(f"\nAnalysis complete!")
    print(f"Files generated:")
    print(f"  - {report_file}")
    print(f"  - {text_report_file}")
    print(f"\nSummary:")
    print(f"  Total bookmarks: {len(bookmarks)}")
    print(f"  New sources: {len(new_sources)}")
    print(f"  Duplicates: {len(duplicates)}")

    return report

if __name__ == '__main__':
    report = main()
