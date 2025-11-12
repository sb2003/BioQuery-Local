"""
Test script to verify all components are working.
Run with:  python test_bioquery.py
"""


def test_installation() -> None:
    print("Testing BioQuery Local Installation...\n")

    # Test EMBOSS
    print("1. Testing EMBOSS...")
    try:
        import subprocess

        result = subprocess.run(
            ["embossversion"],
            capture_output=True,
            text=True,
            check=True,
        )
        print(f"   ✅ EMBOSS: {result.stdout.strip()}")
    except Exception as e:
        print(f"   ❌ EMBOSS not found or failed: {e}")

    # Test BioPython
    print("2. Testing BioPython...")
    try:
        from Bio import SeqIO  # noqa: F401

        print("   ✅ BioPython installed")
    except Exception as e:
        print(f"   ❌ BioPython not found: {e}")

    # Test Ollama
    print("3. Testing Ollama...")
    try:
        import ollama

        client = ollama.Client()
        models = client.list()
        print(f"   ✅ Ollama running with {len(models.get('models', []))} model(s)")
    except Exception as e:
        print(f"   ❌ Ollama not running or not installed correctly: {e}")

    # Test main application
    print("4. Testing BioQuery Local...")
    try:
        from bioquery_local import BioQueryLocal

        bq = BioQueryLocal()
        result = bq.process_query("Translate ATGGCG")
        if result.get("success"):
            print("   ✅ BioQuery Local working!")
        else:
            print(f"   ⚠ BioQuery Local returned error: {result.get('error')}")
    except Exception as e:
        print(f"   ❌ BioQuery Local error: {e}")


if __name__ == "__main__":
    test_installation()

