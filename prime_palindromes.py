def is_prime(n):
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True

def is_palindrome(n):
    s = str(n)
    return s == s[::-1]

prime_palindromes = []
for n in range(2, 10_000_000):
    if is_palindrome(n) and is_prime(n):
        prime_palindromes.append(n)

count = len(prime_palindromes)
largest = max(prime_palindromes) if prime_palindromes else 0
total_sum = sum(prime_palindromes)

print(f"Count of prime palindromes: {count}")
print(f"Largest prime palindrome below 10,000,000: {largest}")
print(f"Sum of all prime palindromes: {total_sum}")

if count <= 100:
    print(f"\nAll prime palindromes ({count}):")
    for p in prime_palindromes:
        print(p)
else:
    print(f"\nFirst 100 prime palindromes (of {count} total):")
    for p in prime_palindromes[:100]:
        print(p)
