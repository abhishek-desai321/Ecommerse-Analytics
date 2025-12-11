import React, { useState, useEffect } from 'react';
import { fetchMetrics, fetchUserSessions, fetchActiveUsers } from './api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { Activity, Users, Globe, Search, BarChart2 } from 'lucide-react';

function App() {
    const [metrics, setMetrics] = useState({
        active_users: 0,
        active_sessions: 0,
        avg_sessions_per_user: 0,
        top_pages: {}
    });
    const [loading, setLoading] = useState(true);
    const [isConnected, setIsConnected] = useState(true);

    // Search State
    const [searchUser, setSearchUser] = useState("");
    const [userSessionCount, setUserSessionCount] = useState(null);
    const [activeUsersList, setActiveUsersList] = useState([]);

    const updateMetrics = async () => {
        const data = await fetchMetrics();
        const users = await fetchActiveUsers();
        if (data) {
            setMetrics(data);
            setActiveUsersList(users);
            setLoading(false);
            setIsConnected(true);
        } else {
            setIsConnected(false);
        }
    };

    const handleSearch = async (e) => {
        e.preventDefault();
        if (!searchUser) return;
        const data = await fetchUserSessions(searchUser);
        if (data) {
            setUserSessionCount(data.active_sessions);
        } else {
            setUserSessionCount("Not Found");
        }
    };

    useEffect(() => {
        updateMetrics(); // Initial fetch
        const interval = setInterval(updateMetrics, 30000); // 30s Poll
        return () => clearInterval(interval);
    }, []);

    const chartData = Object.entries(metrics.top_pages).map(([url, count]) => ({
        name: url,
        views: count
    })).sort((a, b) => b.views - a.views);

    return (
        <div className="dashboard-container">
            {/* Header */}
            <header className="dashboard-header">
                <div className="logo-badge">
                    <BarChart2 size={24} color="white" />
                    <h1>Realtime Analytics Dashboard</h1>
                </div>
                <div className={`status-pill ${isConnected ? 'live' : 'offline'}`}>
                    <span className="status-dot"></span>
                    {isConnected ? 'System Live' : 'Disconnected'}
                </div>
            </header>

            {/* Main Content Grid */}
            <main className="dashboard-grid">

                {/* Top Row: Metrics & Search */}
                <div className="metrics-row">
                    <MetricCard
                        title="Active Users"
                        value={metrics.active_users}
                        icon={<Users size={20} color="#60a5fa" />}
                        subtitle="Last 5 minutes"
                    />
                    <MetricCard
                        title="Active Sessions"
                        value={metrics.active_sessions}
                        icon={<Globe size={20} color="#34d399" />}
                        subtitle="Global connectivity"
                    />
                    <MetricCard
                        title="Avg Sessions/User"
                        value={metrics.avg_sessions_per_user}
                        icon={<Activity size={20} color="#f472b6" />}
                        subtitle="Engagement Score"
                    />

                    {/* Search Component */}
                    <div className="card search-card">
                        <div className="card-header">
                            <h3>User Lookup</h3>
                        </div>
                        <div className="search-body">
                            <form onSubmit={handleSearch} className="search-form">
                                <div className="input-group">
                                    <Search size={16} className="search-icon" />
                                    <input
                                        type="text"
                                        placeholder="User ID..."
                                        value={searchUser}
                                        onChange={(e) => setSearchUser(e.target.value)}
                                        list="user-suggestions"
                                    />
                                    <datalist id="user-suggestions">
                                        {activeUsersList.slice(0, 50).map(user => (
                                            <option key={user} value={user} />
                                        ))}
                                    </datalist>
                                </div>
                                <button type="submit">Check</button>
                            </form>
                            {userSessionCount !== null && (
                                <div className="search-result">
                                    {userSessionCount === "Not Found" ? (
                                        <span className="error">Not Found</span>
                                    ) : (
                                        <span className="success">{userSessionCount} Sessions</span>
                                    )}
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Bottom Row: Chart (Flexible Height) */}
                <div className="card chart-card">
                    <div className="card-header">
                        <h3>Top Pages (Real-time)</h3>
                        <span className="badge">Last 15m</span>
                    </div>
                    <div className="chart-wrapper">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={chartData} layout="vertical" margin={{ top: 5, right: 30, left: 40, bottom: 5 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" horizontal={true} vertical={false} />
                                <XAxis type="number" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                                <YAxis type="category" dataKey="name" stroke="#e2e8f0" width={250} fontSize={18} tickLine={false} axisLine={false} />
                                <Tooltip
                                    cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                                    contentStyle={{
                                        backgroundColor: 'rgba(15, 23, 42, 0.9)',
                                        backdropFilter: 'blur(8px)',
                                        border: '1px solid rgba(255,255,255,0.1)',
                                        borderRadius: '8px',
                                        color: '#fff'
                                    }}
                                />
                                <Bar dataKey="views" radius={[0, 4, 4, 0]} barSize={32}>
                                    {chartData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={index === 0 ? '#818cf8' : 'rgba(99, 102, 241, 0.6)'} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

            </main>

            <style>{`
                :root {
                    --bg-dark: #0f172a;
                    --text-main: #f8fafc;
                    --text-sub: #94a3b8;
                    --accent: #6366f1;
                    --card-bg: rgba(30, 41, 59, 0.7);
                    --border: rgba(255, 255, 255, 0.08);
                }
                
                * { box-sizing: border-box; }
                
                body {
                    background-color: var(--bg-dark);
                    background-image: 
                        radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.15) 0px, transparent 50%),
                        radial-gradient(at 100% 100%, rgba(168, 85, 247, 0.15) 0px, transparent 50%);
                    color: var(--text-main);
                    margin: 0;
                    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                    height: 100vh;
                    overflow: hidden; /* Prevent body scroll */
                }

                .dashboard-container {
                    height: 100vh;
                    display: flex;
                    flex-direction: column;
                    padding: 1.5rem;
                    max-width: 1600px;
                    margin: 0 auto;
                }

                /* Header */
                .dashboard-header {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    margin-bottom: 1.5rem;
                    flex-shrink: 0;
                }

                .logo-badge {
                    background: linear-gradient(135deg, #6366f1, #a855f7);
                    padding: 0.5rem 1rem;
                    border-radius: 12px;
                    display: flex;
                    align-items: center;
                    gap: 0.75rem;
                    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
                }

                h1 {
                    font-size: 1.25rem;
                    font-weight: 700;
                    margin: 0;
                    letter-spacing: -0.025em;
                }

                .status-pill {
                    background: rgba(16, 185, 129, 0.1);
                    color: #34d399;
                    padding: 0.375rem 0.75rem;
                    border-radius: 999px;
                    font-size: 0.875rem;
                    font-weight: 600;
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                    border: 1px solid rgba(16, 185, 129, 0.2);
                }
                .status-pill.offline {
                    background: rgba(239, 68, 68, 0.1);
                    color: #ef4444;
                    border-color: rgba(239, 68, 68, 0.2);
                }
                .status-dot {
                    width: 6px;
                    height: 6px;
                    border-radius: 50%;
                    background: currentColor;
                    box-shadow: 0 0 8px currentColor;
                }

                /* Layout */
                .dashboard-grid {
                    flex: 1;
                    display: flex;
                    flex-direction: column;
                    gap: 1.5rem;
                    min-height: 0; /* Important for flex scrolling */
                }

                .metrics-row {
                    display: grid;
                    grid-template-columns: repeat(4, 1fr);
                    gap: 1.5rem;
                    flex-shrink: 0;
                }

                /* Cards */
                .card {
                    background: var(--card-bg);
                    backdrop-filter: blur(12px);
                    border: 1px solid var(--border);
                    border-radius: 1rem;
                    padding: 1.25rem;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                }

                .card-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 0.5rem;
                }

                .card-header h3 {
                    margin: 0;
                    font-size: 0.875rem;
                    color: var(--text-sub);
                    font-weight: 500;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                }

                .metric-value {
                    font-size: 2.5rem;
                    font-weight: 700;
                    margin: 0.5rem 0 0 0;
                    line-height: 1;
                    letter-spacing: -0.02em;
                    background: linear-gradient(to right, #fff, #cbd5e1);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                }

                .metric-footer {
                    margin-top: 0.75rem;
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                    font-size: 0.875rem;
                    color: var(--text-sub);
                }

                /* Search Card Specifics */
                .search-card {
                    display: flex;
                    flex-direction: column;
                }
                .search-body {
                    flex: 1;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                }
                .search-form {
                    display: flex;
                    gap: 0.5rem;
                    margin-top: 0.25rem;
                }
                .input-group {
                    position: relative;
                    flex: 1;
                }
                .search-icon {
                    position: absolute;
                    left: 0.75rem;
                    top: 50%;
                    transform: translateY(-50%);
                    color: var(--text-sub);
                }
                input {
                    width: 100%;
                    background: rgba(15, 23, 42, 0.5);
                    border: 1px solid var(--border);
                    padding: 0.5rem 0.75rem 0.5rem 2.25rem;
                    border-radius: 0.5rem;
                    color: white;
                    font-family: inherit;
                    font-size: 0.9em;
                    outline: none;
                    transition: all 0.2s;
                }
                input:focus {
                    border-color: var(--accent);
                    box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
                }
                button {
                    background: var(--accent);
                    border: none;
                    padding: 0 1rem;
                    border-radius: 0.5rem;
                    color: white;
                    font-weight: 600;
                    font-size: 0.875rem;
                    cursor: pointer;
                    transition: opacity 0.2s;
                }
                button:hover { opacity: 0.9; }
                
                .search-result {
                    margin-top: 0.5rem;
                    font-size: 0.875rem;
                    font-weight: 500;
                }
                .success { color: #34d399; }
                .error { color: #f87171; }

                /* Chart Card - Flexible Fill */
                .chart-card {
                    flex: 1; /* Fills remaining space */
                    min-height: 250px;
                    display: flex;
                    flex-direction: column;
                    overflow: hidden;
                }
                .chart-wrapper {
                    flex: 1;
                    width: 100%;
                    min-height: 0; /* Allows strict flex sizing */
                    margin-top: 1rem;
                }
                .badge {
                    background: rgba(255,255,255,0.05);
                    padding: 2px 8px;
                    border-radius: 4px;
                    font-size: 0.75rem;
                    color: var(--text-sub);
                }
            `}</style>
        </div>
    );
}

function MetricCard({ title, value, icon, subtitle }) {
    return (
        <div className="card metric-card">
            <div className="card-header">
                <h3>{title}</h3>
                {icon}
            </div>
            <div className="metric-content">
                <p className="metric-value">{value}</p>
                <div className="metric-footer">
                    {subtitle}
                </div>
            </div>
        </div>
    );
}

export default App;
