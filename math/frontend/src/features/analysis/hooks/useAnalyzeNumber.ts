import { useState } from 'react';

export function useAnalyzeNumber() {
    const [result, setResult] = useState<any>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const analyze = async (number: number) => {
        setLoading(true);
        setError(null);
        try {
            // Mock API call for now
            await new Promise(resolve => setTimeout(resolve, 1000));
            if (isNaN(number)) throw new Error("Invalid number");

            setResult({
                number,
                isPrime: checkPrime(number),
                factors: getFactors(number),
                square: number * number,
                cube: number * number * number,
            });
        } catch (err) {
            setError(err instanceof Error ? err.message : "An error occurred");
        } finally {
            setLoading(false);
        }
    };

    return { result, loading, error, analyze };
}

function checkPrime(num: number) {
    if (num <= 1) return false;
    for (let i = 2; i <= Math.sqrt(num); i++) {
        if (num % i === 0) return false;
    }
    return true;
}

function getFactors(num: number) {
    const factors = [];
    for (let i = 1; i <= num; i++) {
        if (num % i === 0) factors.push(i);
    }
    return factors;
}
