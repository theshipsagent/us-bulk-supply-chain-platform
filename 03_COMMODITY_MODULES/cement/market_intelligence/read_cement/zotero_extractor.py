import sqlite3
import os
import shutil
from pathlib import Path

# Paths
ZOTERO_DB = r"C:\Users\wsd3\Zotero\zotero.sqlite"
ZOTERO_STORAGE = r"C:\Users\wsd3\Zotero\storage"
ZOTERO_STORAGE_GDRIVE = r"G:\My Drive\LLM\Zotero\storage"
OUTPUT_DIR = r"G:\My Drive\LLM\project_cement_markets\read_cement\cement_docs"

def find_cement_collection_items():
    """Query Zotero database to find items in the Cement collection"""
    conn = sqlite3.connect(ZOTERO_DB)
    cursor = conn.cursor()

    # First, find the collection ID for "Cement" under "Cargo"
    # Zotero collections are hierarchical
    cursor.execute("""
        SELECT collectionID, collectionName, parentCollectionID
        FROM collections
    """)

    collections = cursor.fetchall()
    print(f"Found {len(collections)} collections")

    # Find Cargo and Cement
    cargo_id = None
    cement_id = None

    for coll_id, name, parent_id in collections:
        if name == "Cargo":
            cargo_id = coll_id
            print(f"Found Cargo collection: ID={coll_id}")
        elif name == "Cement":
            cement_id = coll_id
            print(f"Found Cement collection: ID={coll_id}, Parent={parent_id}")

    if cement_id is None:
        print("Cement collection not found!")
        # List all collections to help debug
        print("\nAll collections:")
        for coll_id, name, parent_id in collections:
            print(f"  {name} (ID: {coll_id}, Parent: {parent_id})")
        return []

    # Get items in the Cement collection
    cursor.execute("""
        SELECT items.itemID, items.key, itemDataValues.value as title
        FROM collectionItems
        JOIN items ON collectionItems.itemID = items.itemID
        LEFT JOIN itemData ON items.itemID = itemData.itemID AND itemData.fieldID = 1
        LEFT JOIN itemDataValues ON itemData.valueID = itemDataValues.valueID
        WHERE collectionItems.collectionID = ?
    """, (cement_id,))

    items = cursor.fetchall()
    print(f"\nFound {len(items)} items in Cement collection")

    # Get attachments for these items
    results = []
    for item_id, item_key, title in items:
        cursor.execute("""
            SELECT items.key, itemAttachments.path, itemAttachments.contentType
            FROM itemAttachments
            JOIN items ON itemAttachments.itemID = items.itemID
            WHERE itemAttachments.parentItemID = ?
        """, (item_id,))

        attachments = cursor.fetchall()
        for att_key, att_path, content_type in attachments:
            results.append({
                'item_id': item_id,
                'item_key': item_key,
                'title': title,
                'attachment_key': att_key,
                'path': att_path,
                'content_type': content_type
            })

    conn.close()
    return results

def copy_files(items):
    """Copy files from Zotero storage to output directory"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    copied_files = []

    for item in items:
        att_key = item['attachment_key']
        storage_dir = os.path.join(ZOTERO_STORAGE, att_key)

        # Try local storage first, then Google Drive storage
        if not os.path.exists(storage_dir):
            storage_dir = os.path.join(ZOTERO_STORAGE_GDRIVE, att_key)
            if not os.path.exists(storage_dir):
                print(f"Storage directory not found in either location: {att_key}")
                continue

        # Find PDF or other files in the storage directory
        for filename in os.listdir(storage_dir):
            src_path = os.path.join(storage_dir, filename)

            # Create a meaningful filename
            title = item['title'] or 'untitled'
            # Clean title for filename
            clean_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            clean_title = clean_title[:100]  # Limit length

            ext = os.path.splitext(filename)[1]
            dest_filename = f"{clean_title}_{att_key}{ext}"
            dest_path = os.path.join(OUTPUT_DIR, dest_filename)

            try:
                shutil.copy2(src_path, dest_path)
                copied_files.append({
                    'source': src_path,
                    'destination': dest_path,
                    'title': item['title'],
                    'content_type': item['content_type']
                })
                print(f"Copied: {dest_filename}")
            except Exception as e:
                print(f"Error copying {src_path}: {e}")

    return copied_files

if __name__ == "__main__":
    print("Searching Zotero library for Cement collection items...")
    items = find_cement_collection_items()

    print(f"\nFound {len(items)} attachments to copy")

    if items:
        print("\nCopying files...")
        copied = copy_files(items)
        print(f"\nSuccessfully copied {len(copied)} files to {OUTPUT_DIR}")

        # Save manifest
        manifest_path = os.path.join(OUTPUT_DIR, "manifest.txt")
        with open(manifest_path, 'w', encoding='utf-8') as f:
            for item in copied:
                f.write(f"Title: {item['title']}\n")
                f.write(f"File: {os.path.basename(item['destination'])}\n")
                f.write(f"Type: {item['content_type']}\n")
                f.write("-" * 80 + "\n")
        print(f"Manifest saved to {manifest_path}")
    else:
        print("No items found to copy")
