"""
Generate separate research and proposal outputs for Kalamandir.
Saves to test_kalamandir_research.txt and test_kalamandir_proposal.txt
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from sdr import research_business, generate_proposal


def main():
    """Generate research and proposal for Kalamandir."""

    # Business data - Kalamandir jewelry brand
    business_data = {
        "name": "Kalamandir",
        "industry": "Jewelry - Retail",
        "business_type": "Traditional jewelry store",
        "location": "India",
        "target_solution": "Modern POS System - Interactive customer experience platform"
    }

    print("=" * 80)
    print("GENERATING KALAMANDIR RESEARCH & PROPOSAL")
    print("=" * 80)
    print()

    # ========================================================================
    # STEP 1: RESEARCH
    # ========================================================================
    print("📊 Step 1: Researching Kalamandir...")
    print()

    try:
        research_results = research_business(business_data)

        # Save research to file
        research_file = Path(__file__).parent / "test_kalamandir_research.txt"
        with open(research_file, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("KALAMANDIR - BUSINESS RESEARCH FINDINGS\n")
            f.write("=" * 80 + "\n\n")

            f.write("BUSINESS INFORMATION:\n")
            f.write("-" * 80 + "\n")
            for key, value in business_data.items():
                f.write(f"{key}: {value}\n")
            f.write("\n" + "=" * 80 + "\n\n")

            f.write("RESEARCH FINDINGS:\n")
            f.write("-" * 80 + "\n")
            f.write(research_results)
            f.write("\n")

        print(f"✅ Research saved to: {research_file}\n")

    except Exception as e:
        print(f"❌ Research failed: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False

    # ========================================================================
    # STEP 2: PROPOSAL
    # ========================================================================
    print("✍️  Step 2: Generating Proposal...")
    print()

    try:
        proposal = generate_proposal(business_data, research_results)

        # Save proposal to file
        proposal_file = Path(__file__).parent / "test_kalamandir_proposal.txt"
        with open(proposal_file, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("KALAMANDIR - MODERN POS SYSTEM PROPOSAL\n")
            f.write("=" * 80 + "\n\n")

            f.write("BUSINESS INFORMATION:\n")
            f.write("-" * 80 + "\n")
            for key, value in business_data.items():
                f.write(f"{key}: {value}\n")
            f.write("\n" + "=" * 80 + "\n\n")

            f.write("PROPOSAL:\n")
            f.write("-" * 80 + "\n")
            f.write(proposal)
            f.write("\n")

        print(f"✅ Proposal saved to: {proposal_file}\n")

        print("=" * 80)
        print("✅ SUCCESS! Both files generated:")
        print(f"   📄 {research_file}")
        print(f"   📄 {proposal_file}")
        print("=" * 80)
        print()

        return True

    except Exception as e:
        print(f"❌ Proposal generation failed: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
