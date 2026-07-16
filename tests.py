#!/usr/bin/env python3
"""
TinyToT Test Runner
Runs comprehensive tests against the TinyToT server using mcphost
Tests are schema-driven and should pass without code changes
"""

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

model = os.getenv("MODEL", "tinytot")
providerName = os.getenv("PROVIDER_NAME", "ollama")
providerUrl = os.getenv("PROVIDER_URL")
mcpConfig = os.getenv("MCP_CONFIG", os.path.expanduser("~/.mcphost.json"))
testTimeout = int(os.getenv("TEST_TIMEOUT", "15"))


class TestRunner:
    def __init__(self):
        self.testDir = Path(__file__).parent / "tests"
        self.passed = 0
        self.failed = 0
        self.results = []

    def runSingleTest(
        self,
        prompt: str,
        expectedCategory: str,
        expectedTool: str,
        expectedPatterns: List[str],
    ) -> Tuple[bool, str]:
        """Run a single test case using mcphost"""
        try:
            # Run mcphost with our TinyToT model
            env = os.environ.copy()

            # Build command with optional provider URL for custom ports
            cmd = ["mcphost"]
            cmd.extend(["--quiet"])
            if providerUrl:
                cmd.extend(["--provider-url", providerUrl])
            if mcpConfig and os.path.exists(mcpConfig):
                cmd.extend(["--config", mcpConfig])
            if model and providerName:
                cmd.extend(["-m", f"{providerName}:{model}"])
            cmd.extend(["-p", prompt])

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=testTimeout, env=env)

            if result.returncode != 0:
                return False, f"Command failed: {result.stderr}"

            output = result.stdout

            # Check expected patterns
            for pattern in expectedPatterns:
                if not re.search(pattern, output, re.IGNORECASE | re.DOTALL):
                    return False, f"Pattern not found: {pattern}"

            return True, "PASSED"

        except subprocess.TimeoutExpired:
            return False, "Test timed out"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def parseTestFile(self, filepath: Path) -> List[Tuple[str, str, str, List[str]]]:
        """Parse a .tst file and return test cases"""
        testCases = []

        with open(filepath, "r") as f:
            for lineNum, line in enumerate(f, 1):
                line = line.strip()
                if line.startswith("#") or not line:
                    continue

                # Parse: PROMPT | EXPECTED_CATEGORY | EXPECTED_TOOL | EXPECTED_PATTERNS
                if "|" in line:
                    parts = [part.strip() for part in line.split("|")]
                    if len(parts) >= 4:
                        prompt = parts[0]
                        expectedCategory = parts[1]
                        expectedTool = parts[2]
                        # Split patterns by .* for multiple patterns
                        expectedPatterns = [p.strip() for p in parts[3].split(".*") if p.strip()]

                        testCases.append((prompt, expectedCategory, expectedTool, expectedPatterns))

        return testCases

    def runAllTests(self):
        """Run all test files"""
        print(f"{model} Model Test Suite")
        print("=" * 50)
        print(f"Timeout: {testTimeout}", flush=True)

        # Find all .tst files
        testFiles = list(self.testDir.glob("*.tst"))
        print(f"Found {len(testFiles)} test files\n")

        for testFile in testFiles:
            print(f"\nRunning tests from: {testFile.name}")
            print("-" * 40)

            testCases = self.parseTestFile(testFile)

            for i, (
                prompt,
                expectedCategory,
                expectedTool,
                expectedPatterns,
            ) in enumerate(testCases, 1):
                print(f"Test {i}: {prompt[:50]}{'...' if len(prompt) > 50 else ''}")

                success, message = self.runSingleTest(prompt, expectedCategory, expectedTool, expectedPatterns)

                if success:
                    print("  ✓ PASSED")
                    self.passed += 1
                else:
                    print(f"  ✗ FAILED: {message}")
                    self.failed += 1

                self.results.append(
                    {
                        "file": testFile.name,
                        "test_num": i,
                        "prompt": prompt,
                        "expected_category": expectedCategory,
                        "expected_tool": expectedTool,
                        "success": success,
                        "message": message,
                    }
                )

    def printSummary(self):
        """Print test results summary"""
        print("\n" + "=" * 50)
        print("TEST RESULTS SUMMARY")
        print("=" * 50)
        print(f"Total Tests: {self.passed + self.failed}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")

        if self.failed > 0:
            print("\nFAILED TESTS:")
            for result in self.results:
                if not result["success"]:
                    print(f"  {result['file']} Test {result['test_num']}: {result['prompt'][:40]}...")
                    print(f"    Reason: {result['message']}")

        if self.passed == self.passed + self.failed:
            print("\nALL TESTS PASSED! Schema-driven system working perfectly!")
        else:
            print(f"\n{self.failed} tests failed. Run the server, install mcphost, and update data files to fix.")


if __name__ == "__main__":
    runner = TestRunner()
    runner.runAllTests()
    runner.printSummary()

    # Exit with appropriate code
    sys.exit(0 if runner.failed == 0 else 1)
