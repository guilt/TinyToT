"""
tinytot.tests.test_codegen_exec -- Execute generated code and verify output.

Generates code for each supported language, runs it in a subprocess,
and asserts the output matches the expected value.
"""

import os
import shutil
import subprocess
import tempfile

import pytest

from tinytot.codegen import _loadPatterns, generateCode

_loadPatterns.cache_clear()

TMPDIR = os.environ.get("TMPDIR", tempfile.gettempdir())


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _strip_fences(code: str) -> str:
    lines = code.strip().splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines)


def _run(cmd, src="", timeout=20):
    try:
        r = subprocess.run(
            cmd,
            input=src,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return (r.stdout + r.stderr).strip(), r.returncode
    except subprocess.TimeoutExpired:
        return "TIMEOUT", 1
    except FileNotFoundError:
        return "RUNTIME_NOT_FOUND", 127


def _runtime_available(name: str) -> bool:
    return shutil.which(name) is not None


def _gen(prompt: str) -> str:
    raw = generateCode(prompt)
    assert raw and raw.startswith("```"), f"No code generated for: {prompt!r}"
    return _strip_fences(raw)


# ---------------------------------------------------------------------------
# Python tests (always available)
# ---------------------------------------------------------------------------


class TestPython:
    LANG = "python3"

    def _run_py(self, code: str) -> str:
        out, rc = _run(["python3", "-"], code)
        return out

    def test_fibonacci(self):
        code = _gen("Write a Python function to compute Fibonacci numbers")
        out = self._run_py(code + "\nprint(fibonacci(10))")
        assert "55" in out

    def test_binary_search(self):
        code = _gen("Implement binary search in Python")
        out = self._run_py(code + "\nprint(binary_search([1,3,5,7,9], 7))")
        assert "3" in out

    def test_reverse_string(self):
        code = _gen("Write a Python function to reverse a string")
        out = self._run_py(code + '\nprint(reverse_string("hello"))')
        assert "olleh" in out

    def test_two_sum(self):
        code = _gen("Write a Python function for the two sum problem")
        out = self._run_py(code + "\nprint(two_sum([2,7,11,15], 9))")
        assert "0" in out and "1" in out

    def test_gcd(self):
        code = _gen("Compute the GCD of two numbers in Python")
        out = self._run_py(code + "\nprint(gcd(48, 18))")
        assert "6" in out

    def test_is_prime(self):
        code = _gen("Check if a number is prime in Python")
        out = self._run_py(code + "\nprint(is_prime(17), is_prime(18))")
        assert "True" in out and "False" in out

    def test_fizzbuzz(self):
        code = _gen("FizzBuzz from 1 to 100")
        out = self._run_py(code + "\nresult = fizzbuzz(15)\nprint(result[-1])")
        assert "fizzbuzz" in out.lower()

    def test_kadane(self):
        code = _gen("Maximum subarray sum Kadane algorithm")
        out = self._run_py(code + "\nprint(max_subarray([-2,1,-3,4,-1,2,1,-5,4]))")
        assert "6" in out

    def test_coin_change(self):
        code = _gen("Coin change minimum coins DP")
        out = self._run_py(code + "\nprint(coin_change([1,5,10,25], 41))")
        assert "4" in out

    def test_climb_stairs(self):
        code = _gen("Number of ways to climb stairs")
        out = self._run_py(code + "\nprint(climb_stairs(5))")
        assert "8" in out

    def test_lcs(self):
        code = _gen("Longest common subsequence Python")
        out = self._run_py(code + '\nprint(lcs_length("ABCBDAB", "BDCAB"))')
        assert "4" in out

    def test_knapsack(self):
        code = _gen("Knapsack 0/1 dynamic programming")
        out = self._run_py(code + "\nprint(knapsack([2,3,4,5],[3,4,5,6],8))")
        assert "10" in out

    def test_sort_and_median(self):
        code = _gen("Find the median of a list Python")
        out = self._run_py(code + "\nprint(median([3,1,4,1,5,9,2,6]))")
        assert "3.5" in out

    def test_anagram(self):
        code = _gen("Check if two strings are anagrams Python")
        out = self._run_py(code + '\nprint(are_anagrams("listen", "silent"), are_anagrams("hello", "world"))')
        assert "True" in out and "False" in out

    def test_palindrome(self):
        code = _gen("Palindrome check Python")
        out = self._run_py(code + '\nprint(is_palindrome("racecar"), is_palindrome("hello"))')
        assert "True" in out and "False" in out


# ---------------------------------------------------------------------------
# JavaScript tests
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _runtime_available("node"), reason="node not installed")
class TestJavaScript:
    def _run_js(self, code: str) -> str:
        out, _ = _run(["node", "-e", code])
        return out

    def test_fibonacci(self):
        code = _gen("Write a JavaScript function to compute Fibonacci numbers")
        out = self._run_js(code + "\nconsole.log(fibonacci(10));")
        assert "55" in out

    def test_binary_search(self):
        code = _gen("Implement binary search in JavaScript")
        out = self._run_js(code + "\nconsole.log(binarySearch([1,3,5,7,9], 7));")
        assert "3" in out

    def test_reverse_string(self):
        code = _gen("Write a JavaScript function to reverse a string")
        out = self._run_js(code + '\nconsole.log(reverse("hello"));')
        assert "olleh" in out

    def test_two_sum(self):
        code = _gen("Two sum problem in JavaScript")
        out = self._run_js(code + "\nconsole.log(JSON.stringify(twoSum([2,7,11,15], 9)));")
        assert "0" in out and "1" in out

    def test_fizzbuzz(self):
        code = _gen("FizzBuzz in JavaScript")
        out = self._run_js(code + "\nconst r = fizzbuzz(15); console.log(r[r.length-1]);")
        assert "fizzbuzz" in out.lower()


# ---------------------------------------------------------------------------
# Go tests
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _runtime_available("go"), reason="go not installed")
class TestGo:
    def _run_go(self, src: str) -> str:
        full = "package main\n" + src
        with tempfile.NamedTemporaryFile(suffix=".go", delete=False, dir=TMPDIR, mode="w") as f:
            f.write(full)
            fname = f.name
        out, _ = _run(["go", "run", fname])
        os.unlink(fname)
        return out

    def test_fibonacci(self):
        code = _gen("Write a Go function to compute Fibonacci numbers")
        out = self._run_go('import "fmt"\n' + code + "\nfunc main() { fmt.Println(fibonacci(10)) }")
        assert "55" in out

    def test_binary_search(self):
        code = _gen("Write a Go function for binary search")
        out = self._run_go('import "fmt"\n' + code + "\nfunc main() { fmt.Println(binarySearch([]int{1,3,5,7,9}, 7)) }")
        assert "3" in out

    def test_reverse_string(self):
        code = _gen("Write a Go function to reverse a string")
        out = self._run_go('import "fmt"\n' + code + '\nfunc main() { fmt.Println(reverseString("hello")) }')
        assert "olleh" in out

    def test_two_sum(self):
        code = _gen("Two sum in Go")
        out = self._run_go('import "fmt"\n' + code + "\nfunc main() { fmt.Println(twoSum([]int{2,7,11,15}, 9)) }")
        assert "0" in out and "1" in out


# ---------------------------------------------------------------------------
# Rust tests
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _runtime_available("rustc"), reason="rustc not installed")
class TestRust:
    def _run_rust(self, src: str) -> str:
        d = tempfile.mkdtemp(dir=TMPDIR)
        srcFile = os.path.join(d, "main.rs")
        binFile = os.path.join(d, "main")
        with open(srcFile, "w") as f:
            f.write(src)
        out1, rc = _run(["rustc", srcFile, "-o", binFile])
        if rc != 0:
            shutil.rmtree(d)
            return f"COMPILE_ERROR: {out1[:200]}"
        out2, _ = _run([binFile])
        shutil.rmtree(d)
        return out2

    def test_fibonacci(self):
        code = _gen("Write a Rust function to compute Fibonacci numbers")
        out = self._run_rust(code + '\nfn main() { println!("{}", fibonacci(10)); }')
        assert "55" in out, out

    def test_binary_search(self):
        code = _gen("Write a Rust function for binary search")
        out = self._run_rust(code + '\nfn main() { println!("{:?}", binary_search(&[1,3,5,7,9], 7)); }')
        assert "Some(3)" in out or "3" in out, out

    def test_reverse_string(self):
        code = _gen("Write a Rust function to reverse a string")
        out = self._run_rust(code + '\nfn main() { println!("{}", reverse_string("hello")); }')
        assert "olleh" in out, out

    def test_two_sum(self):
        code = _gen("Two sum in Rust")
        out = self._run_rust(code + '\nfn main() { let v = vec![2,7,11,15]; println!("{:?}", two_sum(v, 9)); }')
        assert "0" in out and "1" in out, out


# ---------------------------------------------------------------------------
# Ruby tests
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _runtime_available("ruby"), reason="ruby not installed")
class TestRuby:
    def _run_rb(self, code: str) -> str:
        out, _ = _run(["ruby", "-e", code])
        return out

    def test_fibonacci(self):
        code = _gen("Write a Ruby function to compute Fibonacci numbers")
        out = self._run_rb(code + "\nputs fibonacci(10)")
        assert "55" in out

    def test_reverse_string(self):
        code = _gen("Write a Ruby function to reverse a string")
        out = self._run_rb(code + '\nputs reverse_string("hello")')
        assert "olleh" in out


# ---------------------------------------------------------------------------
# Swift tests
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _runtime_available("swift"), reason="swift not installed")
class TestSwift:
    def _run_swift(self, src: str) -> str:
        with tempfile.NamedTemporaryFile(suffix=".swift", delete=False, dir=TMPDIR, mode="w") as f:
            f.write(src)
            fname = f.name
        out, _ = _run(["swift", fname], timeout=30)
        os.unlink(fname)
        return out

    def test_fibonacci(self):
        code = _gen("Write a Swift function to compute Fibonacci numbers")
        out = self._run_swift(code + "\nprint(fibonacci(10))")
        assert "55" in out

    def test_reverse_string(self):
        code = _gen("Write a Swift function to reverse a string")
        out = self._run_swift(code + '\nprint(reverseString("hello"))')
        assert "olleh" in out
