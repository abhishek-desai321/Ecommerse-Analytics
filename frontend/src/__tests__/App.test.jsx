import { render, screen, waitFor } from '@testing-library/react';
import { vi, describe, it, expect } from 'vitest';
import App from '../App';
import * as api from '../api';

// Mock the API module
vi.mock('../api');

// Mock Recharts to avoid rendering issues and verify data passing
vi.mock('recharts', () => {
    return {
        ResponsiveContainer: ({ children }) => <div>{children}</div>,
        BarChart: ({ data, children }) => (
            <div data-testid="bar-chart">
                <pre>{JSON.stringify(data)}</pre>
                {children}
            </div>
        ),
        Bar: () => <div>Bar</div>,
        XAxis: () => <div>XAxis</div>,
        YAxis: () => <div>YAxis</div>,
        CartesianGrid: () => <div>CartesianGrid</div>,
        Tooltip: () => <div>Tooltip</div>,
        Cell: () => <div>Cell</div>,
    };
});

describe('App Dashboard', () => {
    it('renders loading state initially', () => {
        api.fetchMetrics.mockResolvedValue(null);
        api.fetchActiveUsers.mockResolvedValue([]);
        render(<App />);
        // Initial state might show headers but data is loading. 
        expect(screen.getByText(/Real-Time Analytics/i)).toBeInTheDocument();
    });

    it('renders metrics after fetch', async () => {
        const mockMetrics = {
            active_users: 150,
            active_sessions: 300,
            avg_sessions_per_user: 2.0,
            top_pages: {
                "https://example.com/home": 100
            }
        };
        const mockUsers = ["user_1", "user_2"];

        api.fetchMetrics.mockResolvedValue(mockMetrics);
        api.fetchActiveUsers.mockResolvedValue(mockUsers);

        render(<App />);

        // Wait for metrics to appear
        await waitFor(() => {
            expect(screen.getByText('150')).toBeInTheDocument();
            expect(screen.getByText('300')).toBeInTheDocument();
            expect(screen.getByText('2')).toBeInTheDocument();
        });
    });

    it('renders top pages chart data', async () => {
        const mockMetrics = {
            active_users: 0,
            active_sessions: 0,
            avg_sessions_per_user: 0,
            top_pages: {
                "https://example.com/test-page": 50
            }
        };
        api.fetchMetrics.mockResolvedValue(mockMetrics);
        api.fetchActiveUsers.mockResolvedValue([]);
        render(<App />);

        await waitFor(() => {
            expect(screen.getByText(/Top 5 Pages/i)).toBeInTheDocument();
            // Check if the URL is present in the mocked chart data (JSON)
            expect(screen.getByText(/https:\/\/example\.com\/test-page/)).toBeInTheDocument();
        });
    });
});
