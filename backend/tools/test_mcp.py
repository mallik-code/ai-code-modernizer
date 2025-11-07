"""Test MCP Tool Manager connectivity and functionality."""
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.mcp_tools import MCPToolManager
from utils.logger import setup_logger

logger = setup_logger("mcp_test")


def test_mcp_configuration():
    """Test 1: MCP configuration loading."""
    logger.info("=" * 60)
    logger.info("TEST 1: MCP Configuration Loading")
    logger.info("=" * 60)

    try:
        manager = MCPToolManager(auto_connect=False)
        logger.info("MCP configuration loaded",
                   servers=list(manager.config.keys()))

        if not manager.config:
            logger.warning("No MCP servers configured in mcp_config.json")
            return False

        for server_name, config in manager.config.items():
            logger.info("server_config",
                       server=server_name,
                       command=config.get("command"),
                       args=config.get("args", []))

        return True
    except Exception as e:
        logger.error("Configuration loading failed", error=str(e))
        return False


def test_mcp_server_connection():
    """Test 2: MCP server subprocess creation."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 2: MCP Server Connection")
    logger.info("=" * 60)

    try:
        manager = MCPToolManager(auto_connect=True)

        if manager.servers:
            logger.info("MCP servers connected", count=len(manager.servers))
            for server_name, server_data in manager.servers.items():
                process = server_data["process"]
                logger.info("server_status",
                           server=server_name,
                           pid=process.pid,
                           running=process.poll() is None)
        else:
            logger.warning("No MCP servers connected")
            logger.info("This is expected if MCP servers are not installed")
            logger.info("Install with: npm install -g @modelcontextprotocol/server-filesystem @modelcontextprotocol/server-github")

        manager.cleanup()
        return True
    except Exception as e:
        logger.error("[FAIL] Server connection failed", error=str(e))
        return False


def test_list_tools():
    """Test 3: List available tools."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 3: List Available Tools")
    logger.info("=" * 60)

    try:
        manager = MCPToolManager(auto_connect=False)
        tools = manager.list_tools()

        logger.info("[OK] Tools listed", count=len(tools))
        for tool in tools:
            logger.info("tool_available",
                       name=tool["name"],
                       description=tool.get("description", ""),
                       server=tool.get("server", "unknown"))

        manager.cleanup()
        return True
    except Exception as e:
        logger.error("[FAIL] List tools failed", error=str(e))
        return False


def test_filesystem_operations():
    """Test 4: Filesystem tool operations."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 4: Filesystem Operations")
    logger.info("=" * 60)

    try:
        manager = MCPToolManager(auto_connect=False)

        # Test file write
        test_file = "test_mcp_temp.txt"
        test_content = "Hello from MCP Tool Manager test!"

        logger.info("writing_test_file", path=test_file)
        result = manager.write_file(test_file, test_content)
        logger.info("[OK] File written", result=result)

        # Test file read
        logger.info("reading_test_file", path=test_file)
        read_content = manager.read_file(test_file)

        if read_content == test_content:
            logger.info("[OK] File read successfully", length=len(read_content))
        else:
            logger.error("[FAIL] File content mismatch")
            manager.cleanup()
            return False

        # Cleanup test file
        os.remove(test_file)
        logger.info("test_file_cleaned_up", path=test_file)

        manager.cleanup()
        return True
    except Exception as e:
        logger.error("[FAIL] Filesystem operations failed", error=str(e))
        # Try to cleanup test file
        try:
            if os.path.exists("test_mcp_temp.txt"):
                os.remove("test_mcp_temp.txt")
        except:
            pass
        return False


def test_tool_call():
    """Test 5: Generic tool call interface."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 5: Generic Tool Call Interface")
    logger.info("=" * 60)

    try:
        manager = MCPToolManager(auto_connect=False)

        # Test read_file via call_tool
        test_file = "README.md"
        if os.path.exists(test_file):
            logger.info("calling_tool", tool="read_file", args={"path": test_file})
            result = manager.call_tool("read_file", {"path": test_file})

            if result:
                logger.info("[OK] Tool call successful",
                           tool="read_file",
                           result_length=len(result))
            else:
                logger.warning("Tool call returned empty result")
        else:
            logger.info("README.md not found, skipping tool call test")

        manager.cleanup()
        return True
    except Exception as e:
        logger.error("[FAIL] Tool call failed", error=str(e))
        return False


def test_github_tools_mock():
    """Test 6: GitHub tools (mock mode)."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 6: GitHub Tools (Mock Mode)")
    logger.info("=" * 60)

    try:
        manager = MCPToolManager(auto_connect=False)

        # Test GitHub file get (mock)
        result = manager.github_get_file("owner", "repo", "package.json")
        logger.info("[OK] github_get_file (mock)", result=result[:50] if len(result) > 50 else result)

        # Test GitHub PR creation (mock)
        result = manager.github_create_pr(
            owner="owner",
            repo="repo",
            title="Test PR",
            body="Test body",
            head="feature-branch",
            base="main"
        )
        logger.info("[OK] github_create_pr (mock)", result=result)

        manager.cleanup()
        return True
    except Exception as e:
        logger.error("[FAIL] GitHub tools failed", error=str(e))
        return False


def main():
    """Run all MCP tests."""
    logger.info("=" * 60)
    logger.info("MCP TOOL MANAGER TEST SUITE")
    logger.info("=" * 60)

    tests = [
        ("Configuration Loading", test_mcp_configuration),
        ("Server Connection", test_mcp_server_connection),
        ("List Tools", test_list_tools),
        ("Filesystem Operations", test_filesystem_operations),
        ("Generic Tool Call", test_tool_call),
        ("GitHub Tools (Mock)", test_github_tools_mock),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error("test_exception", test=test_name, error=str(e))
            results.append((test_name, False))

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        logger.info("test_result", status=status, test=test_name, passed=result)

    logger.info("test_summary", passed=passed, total=total)

    if passed == total:
        logger.info("ALL TESTS PASSED")
        return 0
    else:
        logger.warning("some_tests_failed", failed_count=total - passed)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
