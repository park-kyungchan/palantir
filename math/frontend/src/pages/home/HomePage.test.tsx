import { render, screen } from '@testing-library/react';
import { HomePage } from './HomePage';
import { describe, it, expect, vi } from 'vitest';

// Mock the API client
vi.mock('../../shared/api/health', () => ({
    checkHealth: vi.fn().mockResolvedValue({ status: 'ok', version: '0.1.0' }),
}));

describe('HomePage', () => {
    it('renders system status title', () => {
        render(<HomePage />);
        expect(screen.getByText('System Status')).toBeInTheDocument();
    });

    it('renders backend status label', () => {
        render(<HomePage />);
        expect(screen.getByText('Backend API')).toBeInTheDocument();
    });
});
