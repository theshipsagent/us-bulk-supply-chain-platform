import json
import re
from collections import defaultdict
from urllib.parse import urlparse

def extract_all_bookmarks(node, folder_path="", bookmarks_list=None):
    """Recursively extract all bookmarks from the Chrome bookmarks structure."""
    if bookmarks_list is None:
        bookmarks_list = []

    if isinstance(node, dict):
        node_type = node.get('type', '')
        name = node.get('name', '')

        # Update folder path
        current_path = f"{folder_path}/{name}" if folder_path and name else name

        if node_type == 'url':
            # This is a bookmark
            bookmarks_list.append({
                'title': node.get('name', ''),
                'url': node.get('url', ''),
                'folder_path': folder_path,
                'date_added': node.get('date_added', ''),
                'date_last_used': node.get('date_last_used', '')
            })
        elif node_type == 'folder' or 'children' in node:
            # This is a folder, process children
            children = node.get('children', [])
            for child in children:
                extract_all_bookmarks(child, current_path, bookmarks_list)

        # Check if there are roots
        if 'roots' in node:
            roots = node['roots']
            for root_key in roots:
                extract_all_bookmarks(roots[root_key], "", bookmarks_list)

    return bookmarks_list

def categorize_url(url, title=""):
    """Categorize URLs based on domain and content patterns."""
    url_lower = url.lower()
    title_lower = title.lower()
    domain = urlparse(url).netloc.lower()

    # Data source patterns
    patterns = {
        'Government - Federal Data': [
            'data.gov', 'census.gov', 'usgs.gov', 'noaa.gov', 'nasa.gov',
            'fgdc.gov', 'geoplatform.gov', 'niem.gov', 'data.cdc.gov'
        ],
        'Government - Transportation': [
            'bts.gov', 'dot.gov', 'fhwa.dot.gov', 'faa.gov', 'fmcsa.dot.gov',
            'nhtsa.gov', 'fra.dot.gov', 'marad.dot.gov', 'phmsa.dot.gov'
        ],
        'Government - Maritime/Waterways': [
            'usace.army.mil', 'navigationdatacenter.us', 'marinetraffic.com',
            'uscg.mil', 'st.nmfs.noaa.gov', 'ports.com'
        ],
        'Government - Energy': [
            'eia.gov', 'energy.gov', 'netl.doe.gov', 'ferc.gov', 'nrc.gov'
        ],
        'Government - Environmental': [
            'epa.gov', 'fws.gov', 'blm.gov', 'fs.usda.gov', 'nps.gov',
            'usbr.gov', 'nrcs.usda.gov'
        ],
        'Government - State/Local': [
            '.state.', '.gov', 'county', 'city', 'municipality'
        ],
        'International Data': [
            'data.gov.uk', 'eurostat.', 'data.gov.au', 'data.gov.ca',
            'unstats.un.org', 'worldbank.org', 'oecd.org', 'who.int'
        ],
        'GIS/Mapping': [
            'arcgis.com', 'esri.com', 'openstreetmap.org', 'mapbox.com',
            'qgis.org', 'gis', 'geospatial', 'maps.google.com'
        ],
        'Academic/Research': [
            '.edu', 'scholar.google', 'researchgate.net', 'academia.edu',
            'arxiv.org', 'sciencedirect.com', 'ieee.org'
        ],
        'Open Data Portals': [
            'opendata', 'data.world', 'kaggle.com', 'dataverse',
            'figshare.com', 'zenodo.org', 'dryad.org'
        ],
        'APIs/Developer Resources': [
            'api.', 'developers.', 'github.com', 'gitlab.com',
            'stackoverflow.com', 'developer.'
        ],
        'Commercial Data Providers': [
            'bloomberg.com', 'refinitiv.com', 'factset.com', 'spglobal.com',
            'ihs.com', 'platts.com', 'argus.com'
        ],
        'Statistics': [
            'statistics', 'stats', 'statistical', 'fred.stlouisfed.org',
            'bls.gov', 'bea.gov'
        ],
        'Transportation Industry': [
            'aar.org', 'railinc.com', 'bnsf.com', 'up.com', 'csx.com',
            'nscorp.com', 'trains.com', 'railway-technology.com'
        ],
        'Energy Industry': [
            'oilprice.com', 'rigzone.com', 'enverus.com', 'ihs.com',
            'wood-mackenzie.com', 'baker-hughes.com'
        ]
    }

    # Check patterns
    for category, keywords in patterns.items():
        for keyword in keywords:
            if keyword in url_lower or keyword in domain or keyword in title_lower:
                return category

    # Default categories based on URL structure
    if '/data/' in url_lower or '/dataset' in url_lower or '/datasets' in url_lower:
        return 'Data Portal/Repository'
    elif 'download' in url_lower or 'export' in url_lower:
        return 'Data Download/Export'
    elif '.pdf' in url_lower or '.xlsx' in url_lower or '.csv' in url_lower:
        return 'Direct Data File'

    return 'Other/Uncategorized'

def is_likely_data_source(url, title=""):
    """Determine if a URL is likely a data source."""
    url_lower = url.lower()
    title_lower = title.lower()
    domain = urlparse(url).netloc.lower()

    # Data source indicators
    data_indicators = [
        'data.', 'dataset', 'statistics', 'stats', 'census', 'api.',
        'download', 'export', 'geospatial', 'gis', 'map', 'portal',
        '.gov', '.mil', 'opendata', 'research', 'analytics',
        '.csv', '.json', '.xml', '.xlsx', '.xls', '.pdf',
        'database', 'repository', 'archive', 'library',
        'eia.gov', 'usgs.gov', 'noaa.gov', 'census.gov', 'bts.gov',
        'usace.', 'energy.', 'epa.gov', 'fgdc.gov'
    ]

    # Check if URL or title contains data indicators
    for indicator in data_indicators:
        if indicator in url_lower or indicator in title_lower or indicator in domain:
            return True

    return False

def main():
    # Read Chrome bookmarks
    bookmarks_file = r'C:\Users\wsd3\AppData\Local\Google\Chrome\User Data\Default\Bookmarks'

    print("Loading Chrome bookmarks file...")
    with open(bookmarks_file, 'r', encoding='utf-8') as f:
        bookmarks_data = json.load(f)

    print("Extracting all bookmarks...")
    all_bookmarks = extract_all_bookmarks(bookmarks_data)

    print(f"\nTotal bookmarks found: {len(all_bookmarks)}")

    # Filter for potential data sources
    print("\nCategorizing bookmarks...")
    data_sources = []
    url_set = set()

    for bookmark in all_bookmarks:
        url = bookmark['url']
        title = bookmark['title']

        # Skip empty URLs or duplicates
        if not url or url in url_set:
            continue

        url_set.add(url)

        # Check if it's a likely data source
        if is_likely_data_source(url, title):
            category = categorize_url(url, title)

            data_sources.append({
                'title': title,
                'url': url,
                'source': urlparse(url).netloc,
                'category': category,
                'bookmark_folder_path': bookmark['folder_path'],
                'date_added': bookmark.get('date_added', ''),
                'description': ''  # To be filled in later if needed
            })

    print(f"Potential data sources identified: {len(data_sources)}")

    # Save to JSON
    output_file = r'G:\My Drive\LLM\sources_data_maps\chrome_bookmarks_datasets.json'
    print(f"\nSaving to {output_file}...")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data_sources, f, indent=2, ensure_ascii=False)

    # Create summary by category
    category_counts = defaultdict(int)
    category_sources = defaultdict(list)

    for ds in data_sources:
        category = ds['category']
        category_counts[category] += 1
        category_sources[category].append({
            'title': ds['title'],
            'url': ds['url'],
            'source': ds['source']
        })

    # Save summary report
    summary_file = r'G:\My Drive\LLM\sources_data_maps\chrome_bookmarks_summary.json'
    summary = {
        'total_bookmarks': len(all_bookmarks),
        'unique_urls': len(url_set),
        'data_sources_identified': len(data_sources),
        'categories': dict(category_counts),
        'sources_by_category': dict(category_sources)
    }

    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print("\nSummary by Category:")
    print("-" * 60)
    for category in sorted(category_counts.keys(), key=lambda x: category_counts[x], reverse=True):
        print(f"{category}: {category_counts[category]}")

    print(f"\nFiles saved:")
    print(f"  - {output_file}")
    print(f"  - {summary_file}")

    return data_sources, summary

if __name__ == '__main__':
    data_sources, summary = main()
