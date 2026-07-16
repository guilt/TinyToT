# HumanEval Code Knowledge

## Python Functions

Function HumanEval/5: Insert a number 'delimeter' between every two consecutive elements of input list `numbers'
    >>> intersperse([], 4)
    []
    >>> intersperse([1, 2 Solution: if not numbers:
        return []

    result = []

    for n in numbers[:-1]:
        result.append

Function HumanEval/9: From a given list of integers, generate a list of rolling maximum element found until given moment
    in the sequence.
    >>> rolling_max([1, 2, 3,  Solution: running_max = None
    result = []

    for n in numbers:
        if running_max is None:


Function HumanEval/10: Test if given string is a palindrome Solution: if not string:
        return ''

    beginning_of_suffix = 0

    while not is_palindrome(string[be

Function HumanEval/11: Input are two strings a and b consisting only of 1s and 0s.
    Perform binary XOR on these inputs and return result also as a string.
    >>> string_ Solution: def xor(i, j):
        if i == j:
            return '0'
        else:
            return '1'

    r

Function HumanEval/13: Return a greatest common divisor of two integers a and b
    >>> greatest_common_divisor(3, 5)
    1
    >>> greatest_common_divisor(25, 15)
    5 Solution: while b:
        a, b = b, a % b
    return a

Function HumanEval/14: Return list of all prefixes from shortest to longest of the input string
    >>> all_prefixes('abc')
    ['a', 'ab', 'abc'] Solution: result = []

    for i in range(len(string)):
        result.append(string[:i+1])
    return result

Function HumanEval/15: Return a string containing space-delimited numbers starting from 0 upto n inclusive.
    >>> string_sequence(0)
    '0'
    >>> string_sequence(5)
    Solution: return ' '.join([str(x) for x in range(n + 1)])

Function HumanEval/16: Given a string, find out how many distinct characters (regardless of case) does it consist of
    >>> count_distinct_characters('xyzXYZ')
    3
    >> Solution: return len(set(string.lower()))

Function HumanEval/18: Find how many times a given substring can be found in the original string. Count overlaping cases.
    >>> how_many_times('', 'a')
    0
    >>> how_m Solution: times = 0

    for i in range(len(string) - len(substring) + 1):
        if string[i:i+len(substring

Function HumanEval/22: Filter given list of any python values only for integers
    >>> filter_integers(['a', 3.14, 5])
    [5]
    >>> filter_integers([1, 2, 3, 'abc', {},  Solution: return [x for x in values if isinstance(x, int)]

Function HumanEval/23: Return length of given string
    >>> strlen('')
    0
    >>> strlen('abc')
    3 Solution: return len(string)

Function HumanEval/24: For a given number n, find the largest number that divides n evenly, smaller than n
    >>> largest_divisor(15)
    5 Solution: for i in reversed(range(n)):
        if n % i == 0:
            return i

Function HumanEval/26: From a list of integers, remove all elements that occur more than once.
    Keep order of elements left the same as in the input.
    >>> remove_dupli Solution: import collections
    c = collections.Counter(numbers)
    return [n for n in numbers if c[n] <= 1]

Function HumanEval/27: For a given string, flip lowercase characters to uppercase and uppercase to lowercase.
    >>> flip_case('Hello')
    'hELLO' Solution: return string.swapcase()

Function HumanEval/28: Concatenate list of strings into a single string
    >>> concatenate([])
    ''
    >>> concatenate(['a', 'b', 'c'])
    'abc' Solution: return ''.join(strings)

Function HumanEval/30: Return only positive numbers in the list.
    >>> get_positive([-1, 2, -4, 5, 6])
    [2, 5, 6]
    >>> get_positive([5, 3, -5, 2, -3, 3, 9, 0, 123, 1 Solution: return [e for e in l if e > 0]

Function HumanEval/32: Evaluates polynomial with coefficients xs at point x.
    return xs[0] + xs[1] * x + xs[1] * x^2 + .... xs[n] * x^n Solution: begin, end = -1., 1.
    while poly(xs, begin) * poly(xs, end) > 0:
        begin *= 2.0
        end

Function HumanEval/34: Return sorted unique elements in a list
    >>> unique([5, 3, 5, 2, 3, 3, 9, 0, 123])
    [0, 2, 3, 5, 9, 123] Solution: return sorted(list(set(l)))

Function HumanEval/35: Return maximum element in the list.
    >>> max_element([1, 2, 3])
    3
    >>> max_element([5, 3, -5, 2, -3, 3, 9, 0, 123, 1, -10])
    123 Solution: m = l[0]
    for e in l:
        if e > m:
            m = e
    return m

Function HumanEval/36: Return the number of times the digit 7 appears in integers less than n which are divisible by 11 or 13.
    >>> fizz_buzz(50)
    0
    >>> fizz_buzz( Solution: ns = []
    for i in range(n):
        if i % 11 == 0 or i % 13 == 0:
            ns.append(i)
    s

Function HumanEval/38: returns encoded string by cycling groups of three characters. Solution: return encode_cyclic(encode_cyclic(s))

Function HumanEval/39: prime_fib returns n-th number that is a Fibonacci number and it's also prime.
    >>> prime_fib(1)
    2
    >>> prime_fib(2)
    3
    >>> prime_fib( Solution: import math

    def is_prime(p):
        if p < 2:
            return False
        for k in range(

Function HumanEval/42: Return list with elements incremented by 1.
    >>> incr_list([1, 2, 3])
    [2, 3, 4]
    >>> incr_list([5, 3, 5, 2, 3, 3, 9, 0, 123])
    [6, 4, 6,  Solution: return [(e + 1) for e in l]

Function HumanEval/44: Change numerical base of input number x to base.
    return string representation after the conversion.
    base numbers are less than 10.
    >>> cha Solution: ret = ""
    while x > 0:
        ret = str(x % base) + ret
        x //= base
    return ret

Function HumanEval/45: Given length of a side and high return area for a triangle.
    >>> triangle_area(5, 3)
    7.5 Solution: return a * h / 2.0

Function HumanEval/47: Return median of elements in the list l.
    >>> median([3, 1, 2, 4, 5])
    3
    >>> median([-10, 4, 6, 1000, 10, 20])
    15.0 Solution: l = sorted(l)
    if len(l) % 2 == 1:
        return l[len(l) // 2]
    else:
        return (l[len(

Function HumanEval/48: Checks if given string is a palindrome
    >>> is_palindrome('')
    True
    >>> is_palindrome('aba')
    True
    >>> is_palindrome('aaaaa')
    Tru Solution: for i in range(len(text)):
        if text[i] != text[len(text) - 1 - i]:
            return False


Function HumanEval/49: Return 2^n modulo p (be aware of numerics).
    >>> modp(3, 5)
    3
    >>> modp(1101, 101)
    2
    >>> modp(0, 101)
    1
    >>> modp(3, 11)
     Solution: ret = 1
    for i in range(n):
        ret = (2 * ret) % p
    return ret

Function HumanEval/50: returns encoded string by shifting every character by 5 in the alphabet. Solution: return "".join([chr(((ord(ch) - 5 - ord("a")) % 26) + ord("a")) for ch in s])

Function HumanEval/52: Return True if all numbers in the list l are below threshold t.
    >>> below_threshold([1, 2, 4, 10], 100)
    True
    >>> below_threshold([1, 20, 4 Solution: for e in l:
        if e >= t:
            return False
    return True

Function HumanEval/53: Add two numbers x and y
    >>> add(2, 3)
    5
    >>> add(5, 7)
    12 Solution: return x + y

Function HumanEval/55: Return n-th Fibonacci number.
    >>> fib(10)
    55
    >>> fib(1)
    1
    >>> fib(8)
    21 Solution: if n == 0:
        return 0
    if n == 1:
        return 1
    return fib(n - 1) + fib(n - 2)

Function HumanEval/57: Return True is list elements are monotonically increasing or decreasing.
    >>> monotonic([1, 2, 4, 20])
    True
    >>> monotonic([1, 20, 4, 10])
  Solution: if l == sorted(l) or l == sorted(l, reverse=True):
        return True
    return False

Function HumanEval/58: Return sorted unique common elements for two lists.
    >>> common([1, 4, 3, 34, 653, 2, 5], [5, 7, 1, 5, 9, 653, 121])
    [1, 5, 653]
    >>> common Solution: ret = set()
    for e1 in l1:
        for e2 in l2:
            if e1 == e2:
                ret.add

Function HumanEval/59: Return the largest prime factor of n. Assume n > 1 and is not a prime.
    >>> largest_prime_factor(13195)
    29
    >>> largest_prime_factor(2048)
  Solution: def is_prime(k):
        if k < 2:
            return False
        for i in range(2, k - 1):


Function HumanEval/60: sum_to_n is a function that sums numbers from 1 to n.
    >>> sum_to_n(30)
    465
    >>> sum_to_n(100)
    5050
    >>> sum_to_n(5)
    15
    >>> s Solution: return sum(range(n + 1))

Function HumanEval/62: xs represent coefficients of a polynomial.
    xs[0] + xs[1] * x + xs[2] * x^2 + ....
     Return derivative of this polynomial in the same form.
     Solution: return [(i * x) for i, x in enumerate(xs)][1:]

Function HumanEval/64: Add more test cases. Solution: vowels = "aeiouAEIOU"
    n_vowels = sum(c in vowels for c in s)
    if s[-1] == 'y' or s[-1] == 'Y'

Function HumanEval/65: Circular shift the digits of the integer x, shift the digits right by shift
    and return the result as a string.
    If shift > number of digits, re Solution: s = str(x)
    if shift > len(s):
        return s[::-1]
    else:
        return s[len(s) - shift:]

Function HumanEval/75: Write a function that returns true if the given number is the multiplication of 3 prime numbers
    and false otherwise.
    Knowing that (a) is less  Solution: def is_prime(n):
        for j in range(2,n):
            if n%j == 0:
                return False


Function HumanEval/83: Given a positive integer n, return the count of the numbers of n-digit
    positive integers that start or end with 1. Solution: if n == 1: return 1
    return 18 * (10 ** (n - 2))

Function HumanEval/85: Given a non-empty list of integers lst. add the even elements that are at odd indices..


    Examples:
        add([4, 2, 6, 7]) ==> 2 Solution: return sum([lst[i] for i in range(1, len(lst), 2) if lst[i]%2 == 0])

Function HumanEval/98: Given a string s, count the number of uppercase vowels in even indices.

    For example:
    count_upper('aBCdEf') returns 1
    count_upper('abc Solution: count = 0
    for i in range(0,len(s),2):
        if s[i] in "AEIOU":
            count += 1
    ret

Function HumanEval/114: Given an array of integers nums, find the minimum sum of any non-empty sub-array
    of nums.
    Example
    minSubArraySum([2, 3, 4, 1, 2, 4]) == 1
 Solution: max_sum = 0
    s = 0
    for num in nums:
        s += -num
        if (s < 0):
            s = 0


Function HumanEval/121: Given a non-empty list of integers, return the sum of all of the odd elements that are in even positions.


    Examples
    solution([5, 8, 7, 1] Solution: return sum([x for idx, x in enumerate(lst) if idx%2==0 and x%2==1])

Function HumanEval/131: Given a positive integer n, return the product of the odd digits.
    Return 0 if all digits are even.
    For example:
    digits(1)  == 1
    digits Solution: product = 1
    odd_count = 0
    for digit in str(n):
        int_digit = int(digit)
        if int

Function HumanEval/138: Evaluate whether the given number n can be written as the sum of exactly 4 positive even numbers
    Example
    is_equal_to_sum_even(4) == False
     Solution: return n%2 == 0 and n >= 8

Function HumanEval/150: A simple program which should return the value of x if n is
    a prime number and should return the value of y otherwise.

    Examples:
    for x_o Solution: if n == 1:
        return y
    for i in range(2, n):
        if n % i == 0:
            return y


Function HumanEval/155: Given an integer. return a tuple that has the number of even and odd digits respectively.

     Example:
        even_odd_count(-12) ==> (1, 1)
       Solution: even_count = 0
    odd_count = 0
    for i in str(abs(num)):
        if int(i)%2==0:
            eve

Function HumanEval/162: Given a string 'text', return its md5 hash equivalent string.
    If 'text' is an empty string, return None.

    >>> string_to_md5('Hello world') ==  Solution: import hashlib
    return hashlib.md5(text.encode('ascii')).hexdigest() if text else None

Function HumanEval/163: Given two positive integers a and b, return the even digits between a
    and b, in ascending order.

    For example:
    generate_integers(2, 8) =>  Solution: lower = max(2, min(a, b))
    upper = min(8, max(a, b))

    return [i for i in range(lower, upper+1
