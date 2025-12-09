// API Client for PC Builder

// Use relative URL for production compatibility, fallback to localhost for dev
const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
    ? 'http://localhost:5000/api/v1' 
    : '/api/v1';

// Token management
const TOKEN_KEY = 'bluprint_auth_token';

function getToken() {
    return localStorage.getItem(TOKEN_KEY);
}

function setToken(token) {
    if (token) {
        localStorage.setItem(TOKEN_KEY, token);
    } else {
        localStorage.removeItem(TOKEN_KEY);
    }
}

function clearToken() {
    localStorage.removeItem(TOKEN_KEY);
}

async function apiCall(endpoint, options = {}) {
    try {
        const token = getToken();
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const response = await fetch(`${API_BASE}${endpoint}`, {
            ...options,
            headers
        });

        // Handle 401 Unauthorized - token expired or invalid
        if (response.status === 401) {
            clearToken();
            if (window.handleAuthError) {
                window.handleAuthError();
            }
            throw new Error('Authentication required. Please login again.');
        }

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || `HTTP error! status: ${response.status}`);
        }

        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

const PartsAPI = {
    getAll: (filters = {}) => {
        const params = new URLSearchParams();
        if (filters.search) params.append('search', filters.search);
        if (filters.part_type) params.append('part_type', filters.part_type);
        if (filters.min_price) params.append('min_price', filters.min_price);
        if (filters.max_price) params.append('max_price', filters.max_price);
        
        const query = params.toString();
        return apiCall(`/parts${query ? '?' + query : ''}`);
    },

    getById: (id) => apiCall(`/parts/${id}`),

    create: (partData) => apiCall('/parts', {
        method: 'POST',
        body: JSON.stringify(partData)
    }),

    update: (id, partData) => apiCall(`/parts/${id}`, {
        method: 'PUT',
        body: JSON.stringify(partData)
    }),

    delete: (id) => apiCall(`/parts/${id}`, {
        method: 'DELETE'
    })
};

const BuildsAPI = {
    getAll: () => apiCall('/builds'),

    getById: (id) => apiCall(`/builds/${id}`),

    create: (buildData) => apiCall('/builds', {
        method: 'POST',
        body: JSON.stringify(buildData)
    }),

    update: (id, buildData) => apiCall(`/builds/${id}`, {
        method: 'PUT',
        body: JSON.stringify(buildData)
    }),

    delete: (id) => apiCall(`/builds/${id}`, {
        method: 'DELETE'
    })
};

const CompatibilityAPI = {
    check: (partIds) => apiCall('/compatibility/check', {
        method: 'POST',
        body: JSON.stringify({ part_ids: partIds })
    }),

    getRules: () => apiCall('/compatibility/rules'),

    createRule: (ruleData) => apiCall('/compatibility/rules', {
        method: 'POST',
        body: JSON.stringify(ruleData)
    })
};

const AuthAPI = {
    register: async (username, email, password) => {
        const response = await fetch(`${API_BASE}/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, email, password })
        });

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || 'Registration failed');
        }

        if (data.access_token) {
            setToken(data.access_token);
        }
        return data;
    },

    login: async (username, password) => {
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || 'Login failed');
        }

        if (data.access_token) {
            setToken(data.access_token);
        }
        return data;
    },

    logout: () => {
        clearToken();
    },

    getCurrentUser: async () => {
        return apiCall('/auth/me');
    }
};

const RecommendationsAPI = {
    recommendParts: (preferences) => apiCall('/recommendations/parts', {
        method: 'POST',
        body: JSON.stringify(preferences)
    }),

    getModelStatus: () => apiCall('/recommendations/model/status')
};

const AgentAPI = {
    chat: (message) => apiCall('/agent/chat', {
        method: 'POST',
        body: JSON.stringify({ message })
    }),

    getContext: () => apiCall('/agent/context'),

    reset: () => apiCall('/agent/reset', {
        method: 'POST'
    }),

    saveBuild: (buildData) => apiCall('/agent/save-build', {
        method: 'POST',
        body: JSON.stringify(buildData)
    })
};

const HealthAPI = {
    check: () => {
        const healthUrl = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
            ? 'http://localhost:5000/health'
            : '/health';
        return fetch(healthUrl).then(r => r.json());
    }
};
