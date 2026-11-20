"""
test_mcp_tools.py
=================
Smoke test — verifies both MCP servers are healthy and tools respond.
Run manually: python scripts/test_mcp_tools.py
Also called by: make smoke-test

Exits with code 0 if all tools pass, 1 if any fail.
"""

import asyncio
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


async def test_banking_mcp():
    """Test Banking MCP server tools directly (no HTTP — function calls)."""
    from app.mcp_servers.banking_mcp_server import (
        get_transaction_history, check_velocity, flag_transaction, get_account_info
    )
    results = {}

    try:
        r = await get_transaction_history("ACC-TEST", 24)
        assert "transactions" in r
        results["get_transaction_history"] = "✅"
    except Exception as e:
        results["get_transaction_history"] = f"❌ {e}"

    try:
        r = await check_velocity("ACC-TEST", 60)
        assert "velocity_flag" in r
        results["check_velocity"] = "✅"
    except Exception as e:
        results["check_velocity"] = f"❌ {e}"

    try:
        r = await flag_transaction("TX-SMOKE", "smoke_test", 0.5)
        assert r["flagged"] is True
        results["flag_transaction"] = "✅"
    except Exception as e:
        results["flag_transaction"] = f"❌ {e}"

    try:
        r = await get_account_info("ACC-TEST")
        assert "customer_tier" in r
        results["get_account_info"] = "✅"
    except Exception as e:
        results["get_account_info"] = f"❌ {e}"

    return results


async def test_compliance_mcp():
    """Test Compliance MCP server tools directly."""
    from app.mcp_servers.compliance_mcp_server import (
        kyc_status, sanctions_check, aml_screening, gdpr_audit_log
    )
    results = {}

    try:
        r = await kyc_status("ACC-TEST")
        assert "kyc_status" in r
        results["kyc_status"] = "✅"
    except Exception as e:
        results["kyc_status"] = f"❌ {e}"

    try:
        r = await sanctions_check("ACC-TEST", "TestMerchant", "NL")
        assert "sanctions_hit" in r
        results["sanctions_check"] = "✅"
    except Exception as e:
        results["sanctions_check"] = f"❌ {e}"

    try:
        r = await aml_screening("ACC-TEST", 1000.0, "RETAIL")
        assert "aml_flagged" in r
        results["aml_screening"] = "✅"
    except Exception as e:
        results["aml_screening"] = f"❌ {e}"

    try:
        r = await gdpr_audit_log("TX-SMOKE", "ACC-TEST", ["kyc"], "CLEAN")
        assert "audit_id" in r
        results["gdpr_audit_log"] = "✅"
    except Exception as e:
        results["gdpr_audit_log"] = f"❌ {e}"

    return results


async def main():
    print("\n" + "="*50)
    print("MCP Server Smoke Tests")
    print("="*50)

    print("\n🏦 Banking MCP Server:")
    banking_results = await test_banking_mcp()
    for tool, status in banking_results.items():
        print(f"  {status}  {tool}")

    print("\n⚖️  Compliance MCP Server:")
    compliance_results = await test_compliance_mcp()
    for tool, status in compliance_results.items():
        print(f"  {status}  {tool}")

    all_results = {**banking_results, **compliance_results}
    failures = [k for k, v in all_results.items() if v.startswith("❌")]

    print("\n" + "="*50)
    if failures:
        print(f"❌ {len(failures)} tool(s) failed: {', '.join(failures)}")
        sys.exit(1)
    else:
        print(f"✅ All {len(all_results)} MCP tools passed")
    print("="*50 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
