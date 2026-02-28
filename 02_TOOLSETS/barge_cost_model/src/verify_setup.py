"""Verify system setup before running data loaders."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import subprocess

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def check_postgresql():
    """Check if PostgreSQL is installed and running."""
    print("Checking PostgreSQL...")
    try:
        result = subprocess.run(
            ['psql', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"  [OK] PostgreSQL installed: {result.stdout.strip()}")
            return True
        else:
            print("  [FAIL] PostgreSQL not found")
            return False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("  [FAIL] PostgreSQL not found or not in PATH")
        return False


def check_database_exists():
    """Check if barge_db database exists."""
    print("\nChecking database...")
    try:
        result = subprocess.run(
            ['psql', '-lqt'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if 'barge_db' in result.stdout:
            print("  [OK] Database 'barge_db' exists")
            return True
        else:
            print("  [FAIL] Database 'barge_db' not found")
            print("\n  To create:")
            print("    createdb barge_db")
            print("    psql -d barge_db -c \"CREATE EXTENSION postgis;\"")
            print("    psql -d barge_db -f src/db/schema.sql")
            return False
    except Exception as e:
        print(f"  [FAIL] Could not check database: {e}")
        return False


def check_python_packages():
    """Check if required Python packages are installed."""
    print("\nChecking Python packages...")
    required = ['pandas', 'networkx', 'sqlalchemy', 'psycopg2', 'tqdm', 'python-dotenv', 'pydantic']

    all_installed = True
    for package in required:
        try:
            __import__(package.replace('-', '_'))
            print(f"  [OK] {package}")
        except ImportError:
            print(f"  [FAIL] {package} - not installed")
            all_installed = False

    if not all_installed:
        print("\n  To install missing packages:")
        print("    pip install -r requirements.txt")

    return all_installed


def check_data_files():
    """Check if data files exist."""
    print("\nChecking data files...")
    data_files = {
        "Waterway Networks": "data/09_bts_waterway_networks/Waterway_Networks_7107995240912772581.csv",
        "Locks": "data/04_bts_locks/Locks_-3795028687405442582.csv",
        "Docks": "data/05_bts_navigation_fac/Docks_8605051818000540974.csv",
        "Link Tonnages": "data/03_bts_link_tons/Link_Tonnages_1612260770216529761.csv",
        "Vessels": "data/01.03_vessels/01_ships_register.csv",
    }

    all_exist = True
    for name, path in data_files.items():
        file_path = project_root / path
        if file_path.exists():
            size_mb = file_path.stat().st_size / (1024 * 1024)
            print(f"  [OK] {name}: {size_mb:.1f} MB")
        else:
            print(f"  [FAIL] {name}: not found at {path}")
            all_exist = False

    return all_exist


def check_env_file():
    """Check if .env file exists."""
    print("\nChecking environment configuration...")
    env_file = project_root / '.env'

    if env_file.exists():
        print(f"  [OK] .env file exists")
        return True
    else:
        print(f"  [FAIL] .env file not found")
        print("\n  To create:")
        print("    cp .env.example .env")
        print("    # Then edit .env with your database credentials")
        return False


def main():
    """Run all verification checks."""
    print("=" * 80)
    print("BARGE DASHBOARD - SYSTEM VERIFICATION")
    print("=" * 80)

    checks = {
        "PostgreSQL": check_postgresql(),
        "Database": check_database_exists(),
        "Python Packages": check_python_packages(),
        "Data Files": check_data_files(),
        "Environment File": check_env_file(),
    }

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    all_passed = all(checks.values())

    for check_name, passed in checks.items():
        status = "[OK] PASS" if passed else "[FAIL] FAIL"
        print(f"{check_name:20s} {status}")

    print("=" * 80)

    if all_passed:
        print("[OK] All checks passed! Ready to load data.")
        print("\nNext steps:")
        print("  python src/data_loaders/load_waterways.py")
        return 0
    else:
        print("[FAIL] Some checks failed. Please fix the issues above before proceeding.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
