// API Client for PC Builder

const API_BASE = 'http://localhost:5000/api/v1';

async function apiCall(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });

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

const HealthAPI = {
    check: () => fetch('http://localhost:5000/health').then(r => r.json())
};
