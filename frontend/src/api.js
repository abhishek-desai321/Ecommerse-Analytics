const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function fetchMetrics() {
    try {
        const response = await fetch(`${API_URL}/metrics`);
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return await response.json();
    } catch (error) {
        console.error("Failed to fetch metrics:", error);
        return null;
    }
}

export async function fetchUserSessions(userId) {
    try {
        const response = await fetch(`${API_URL}/users/${userId}/sessions`);
        if (!response.ok) return null;
        const data = await response.json();
        return data;
    } catch (error) {
        console.error("Failed to fetch user sessions:", error);
        return null;
    }
}

export async function fetchActiveUsers() {
    try {
        const response = await fetch(`${API_URL}/users/active`);
        if (!response.ok) return [];
        const data = await response.json();
        return data.users || [];
    } catch (error) {
        console.error("Failed to fetch active users:", error);
        return [];
    }
}
