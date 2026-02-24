# read_cement Folder Status

## Reorganization Date: 2026-02-09

This folder has been reorganized. Most data files have been moved to the ATLAS pipeline.

## Files Moved To:

### atlas/data/source/usgs/
- USGS Monthly Industry Surveys (MIS)
- USGS Minerals Yearbook (MYB)
- Historical archives

### atlas/data/source/trade/panjiva/
- Panjiva US imports data (copies made)

### atlas/data/source/reports/
- Cement Weekly newsletters
- US Gulf Cement reports

### atlas/data/reference/rag_documents/
- Processed PDFs for RAG system
- Zotero extracted documents

### atlas/data/archive/
- Duplicate files
- Older versions of GEM/Ownership trackers
- Global Cement Directory PDFs

## Files Remaining Here:

### Still Here (Originals - Safe to Keep)
- `Panjiva-*.csv/xlsx` - Originals (copies in atlas/data/source/trade)
- `US_Import_Cement.xlsx` - Originals (copy in atlas/data/source/trade)
- `usgs_minerals/` - Original USGS folder (copies in atlas/data/source/usgs)

### Python Scripts (Keep for Reference)
- `process_documents.py` - Document processing script
- `rag_system.py` - RAG system implementation
- `zotero_extractor.py` - Zotero integration script

### Python Projects (Can Be Deleted If Unused)
- `Cement/` - Python project with .venv
- `PythonProject/` - Python project with .venv

## Recommended Action

The original files here are now redundant with copies in atlas/data/source/.
They can remain here as backup or be deleted if space is needed.
