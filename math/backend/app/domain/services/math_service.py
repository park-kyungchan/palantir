from typing import List

class MathService:
    @staticmethod
    def get_prime_factors(n: int) -> List[int]:
        """
        Returns a list of prime factors for a given integer n.
        Uses trial division optimized for n <= 1,000,000.
        """
        factors = []
        if n == 1:
            return [1]
        d = 2
        temp = n
        while d * d <= temp:
            while temp % d == 0:
                factors.append(d)
                temp //= d
            d += 1
        if temp > 1:
            factors.append(temp)
        return factors

    @staticmethod
    def is_prime_number(n: int) -> bool:
        """
        Checks if a number is prime.
        """
        if n < 2:
            return False
        for i in range(2, int(n**0.5) + 1):
            if n % i == 0:
                return False
        return True
