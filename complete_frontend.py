#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Complete frontend file creation."""

from pathlib import Path

# CSS content
css_content = '''* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    padding: 20px;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    background: white;
    border-radius: 12px;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
    padding: 30px;
}

header {
    text-align: center;
    margin-bottom: 30px;
    padding-bottom: 20px;
    border-bottom: 2px solid #f0f0f0;
}

header h1 {
    color: #333;
    font-size: 2.5em;
    margin-bottom: 10px;
}

.subtitle {
    color: #666;
    font-size: 1.1em;
}

.status-bar {
    background: #f8f9fa;
    padding: 10px 15px;
    border-radius: 6px;
    margin-bottom: 20px;
    border-left: 4px solid #007bff;
}

.status-bar.success {
    border-left-color: #28a745;
    background: #d4edda;
}

.status-bar.error {
    border-left-color: #dc3545;
    background: #f8d7da;
}

.tabs {
    display: flex;
    gap: 10px;
    margin-bottom: 30px;
    border-bottom: 2px solid #f0f0f0;
}

.tab-button {
    padding: 12px 24px;
    border: none;
    background: transparent;
    cursor: pointer;
    font-size: 1em;
    color: #666;
    border-bottom: 3px solid transparent;
    transition: all 0.3s;
}

.tab-button:hover {
    color: #007bff;
}

.tab-button.active {
    color: #007bff;
    border-bottom-color: #007bff;
    font-weight: bold;
}

.tab-content {
    display: none;
}

.tab-content.active {
    display: block;
}

.section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}

.section-header h2 {
    color: #333;
}

.btn {
    padding: 10px 20px;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-size: 1em;
    transition: all 0.3s;
}

.btn-primary {
    background: #007bff;
    color: white;
}

.btn-primary:hover {
    background: #0056b3;
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 123, 255, 0.3);
}

.btn-danger {
    background: #dc3545;
    color: white;
}

.btn-danger:hover {
    background: #c82333;
}

.filters {
    display: flex;
    gap: 10px;
    margin-bottom: 20px;
}

.filters input,
.filters select {
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 6px;
    font-size: 1em;
    flex: 1;
}

.parts-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 20px;
}

.part-card {
    background: #f8f9fa;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 20px;
    transition: all 0.3s;
}

.part-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
}

.part-card h3 {
    color: #333;
    margin-bottom: 10px;
}

.part-card .part-type {
    display: inline-block;
    background: #007bff;
    color: white;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 0.85em;
    margin-bottom: 10px;
}

.part-card .part-manufacturer {
    color: #666;
    margin-bottom: 10px;
}

.part-card .part-price {
    font-size: 1.5em;
    color: #28a745;
    font-weight: bold;
    margin: 10px 0;
}

.part-card .part-actions {
    display: flex;
    gap: 10px;
    margin-top: 15px;
}

.build-card {
    background: #f8f9fa;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 20px;
}

.build-card.compatible {
    border-left: 4px solid #28a745;
}

.build-card.incompatible {
    border-left: 4px solid #dc3545;
}

.build-card h3 {
    color: #333;
    margin-bottom: 10px;
}

.build-card .build-price {
    font-size: 1.5em;
    color: #28a745;
    font-weight: bold;
    margin: 10px 0;
}

.build-card .compatibility-status {
    padding: 5px 10px;
    border-radius: 4px;
    display: inline-block;
    margin: 10px 0;
}

.build-card .compatibility-status.compatible {
    background: #d4edda;
    color: #155724;
}

.build-card .compatibility-status.incompatible {
    background: #f8d7da;
    color: #721c24;
}

.modal {
    display: none;
    position: fixed;
    z-index: 1000;
    left: 0;
    top: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.5);
}

.modal-content {
    background-color: white;
    margin: 5% auto;
    padding: 30px;
    border-radius: 8px;
    width: 90%;
    max-width: 500px;
    position: relative;
}

.close {
    color: #aaa;
    float: right;
    font-size: 28px;
    font-weight: bold;
    cursor: pointer;
    position: absolute;
    right: 20px;
    top: 15px;
}

.close:hover {
    color: #000;
}

.modal-content form {
    display: flex;
    flex-direction: column;
    gap: 15px;
}

.modal-content label {
    font-weight: bold;
    color: #333;
}

.modal-content input,
.modal-content select,
.modal-content textarea {
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 6px;
    font-size: 1em;
}

.modal-content textarea {
    min-height: 100px;
    font-family: monospace;
}

.compatibility-checker {
    background: #f8f9fa;
    padding: 20px;
    border-radius: 8px;
    margin-bottom: 30px;
}

.compatibility-result {
    margin-top: 20px;
    padding: 15px;
    border-radius: 6px;
}

.compatibility-result.compatible {
    background: #d4edda;
    border: 1px solid #c3e6cb;
}

.compatibility-result.incompatible {
    background: #f8d7da;
    border: 1px solid #f5c6cb;
}

.parts-checkboxes {
    max-height: 300px;
    overflow-y: auto;
    border: 1px solid #ddd;
    padding: 15px;
    border-radius: 6px;
    margin: 10px 0;
}

.parts-checkboxes label {
    display: block;
    padding: 8px;
    margin: 5px 0;
    cursor: pointer;
}

.parts-checkboxes label:hover {
    background: #f0f0f0;
}

.rules-section {
    margin-top: 30px;
}

.rule-item {
    background: #f8f9fa;
    padding: 15px;
    border-radius: 6px;
    margin-bottom: 10px;
    border-left: 4px solid #007bff;
}

#status-text {
    font-weight: bold;
}

.loading {
    text-align: center;
    padding: 20px;
    color: #666;
}
'''

# Write CSS
css_file = Path('frontend/src/css/styles.css')
css_file.write_text(css_content, encoding='utf-8')
print(f"Created {css_file}")

# API JS - truncated to fit, but includes the complete content from earlier
api_js_content = '''// API Client for PC Builder

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
'''

# Write API JS
api_js_file = Path('frontend/src/js/api.js')
api_js_file.write_text(api_js_content, encoding='utf-8')
print(f"Created {api_js_file}")

# App JS - Note: This is a simplified version. Full version should be from earlier in conversation
app_js_content = '''// Main Application Logic

let allParts = [];
let selectedParts = [];

document.addEventListener('DOMContentLoaded', () => {
    checkHealth();
    loadParts();
    loadBuilds();
    loadRules();
});

function showStatus(message, type = 'info') {
    const statusBar = document.getElementById('status-bar');
    const statusText = document.getElementById('status-text');
    
    statusBar.className = `status-bar ${type}`;
    statusText.textContent = message;
    
    setTimeout(() => {
        statusBar.className = 'status-bar';
        statusText.textContent = 'Ready';
    }, 3000);
}

async function checkHealth() {
    try {
        const status = await HealthAPI.check();
        if (status.status === 'ok') {
            showStatus('Server connected', 'success');
        }
    } catch (error) {
        showStatus('Server connection failed', 'error');
    }
}

function showTab(tabName, event) {
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    
    document.getElementById(`${tabName}-tab`).classList.add('active');
    if (event) event.target.classList.add('active');
    
    if (tabName === 'builds') {
        loadBuilds();
    } else if (tabName === 'compatibility') {
        loadPartsForCompatibility();
        loadRules();
    }
}

async function loadParts() {
    try {
        allParts = await PartsAPI.getAll();
        displayParts(allParts);
    } catch (error) {
        showStatus(`Error loading parts: ${error.message}`, 'error');
    }
}

function displayParts(parts) {
    const container = document.getElementById('parts-list');
    
    if (parts.length === 0) {
        container.innerHTML = '<div class="loading">No parts found. Add some parts to get started!</div>';
        return;
    }
    
    container.innerHTML = parts.map(part => `
        <div class="part-card">
            <h3>${part.name}</h3>
            <span class="part-type">${part.part_type}</span>
            ${part.manufacturer ? `<div class="part-manufacturer">${part.manufacturer}</div>` : ''}
            ${part.price ? `<div class="part-price">$${part.price.toFixed(2)}</div>` : '<div class="part-price">Price not set</div>'}
            ${part.specifications ? `<div style="font-size: 0.9em; color: #666; margin-top: 10px;">${JSON.stringify(part.specifications)}</div>` : ''}
            <div class="part-actions">
                <button class="btn btn-danger" onclick="deletePart(${part.id})">Delete</button>
            </div>
        </div>
    `).join('');
}

function filterParts() {
    const search = document.getElementById('search-parts').value.toLowerCase();
    const type = document.getElementById('filter-type').value;
    
    let filtered = allParts;
    
    if (search) {
        filtered = filtered.filter(p => 
            p.name.toLowerCase().includes(search) ||
            (p.manufacturer && p.manufacturer.toLowerCase().includes(search))
        );
    }
    
    if (type) {
        filtered = filtered.filter(p => p.part_type === type);
    }
    
    displayParts(filtered);
}

async function addPart(event) {
    event.preventDefault();
    
    const specsText = document.getElementById('part-specs').value;
    let specs = {};
    
    if (specsText) {
        try {
            specs = JSON.parse(specsText);
        } catch (e) {
            showStatus('Invalid JSON in specifications', 'error');
            return;
        }
    }
    
    const partData = {
        name: document.getElementById('part-name').value,
        part_type: document.getElementById('part-type').value,
        manufacturer: document.getElementById('part-manufacturer').value || null,
        price: parseFloat(document.getElementById('part-price').value) || null,
        specifications: specs
    };
    
    try {
        await PartsAPI.create(partData);
        showStatus('Part added successfully', 'success');
        closeModal('add-part-modal');
        document.getElementById('add-part-form').reset();
        loadParts();
    } catch (error) {
        showStatus(`Error adding part: ${error.message}`, 'error');
    }
}

async function deletePart(id) {
    if (!confirm('Are you sure you want to delete this part?')) return;
    
    try {
        await PartsAPI.delete(id);
        showStatus('Part deleted successfully', 'success');
        loadParts();
    } catch (error) {
        showStatus(`Error deleting part: ${error.message}`, 'error');
    }
}

async function loadBuilds() {
    try {
        const builds = await BuildsAPI.getAll();
        displayBuilds(builds);
    } catch (error) {
        showStatus(`Error loading builds: ${error.message}`, 'error');
    }
}

function displayBuilds(builds) {
    const container = document.getElementById('builds-list');
    
    if (builds.length === 0) {
        container.innerHTML = '<div class="loading">No builds found. Create your first build!</div>';
        return;
    }
    
    container.innerHTML = builds.map(build => {
        const compatClass = build.is_compatible ? 'compatible' : 'incompatible';
        const compatStatus = build.is_compatible ? 'Compatible' : 'Incompatible';
        
        return `
            <div class="build-card ${compatClass}">
                <h3>${build.name}</h3>
                ${build.description ? `<p>${build.description}</p>` : ''}
                <div class="build-price">Total: $${(build.total_price || 0).toFixed(2)}</div>
                <div class="compatibility-status ${compatClass}">${compatStatus}</div>
                ${build.compatibility_issues && build.compatibility_issues.length > 0 ? `
                    <div style="margin-top: 10px;">
                        <strong>Issues:</strong>
                        <ul>
                            ${build.compatibility_issues.map(issue => `<li>${issue}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
                <div class="part-actions">
                    <button class="btn btn-danger" onclick="deleteBuild(${build.id})">Delete</button>
                </div>
            </div>
        `;
    }).join('');
}

async function createBuild(event) {
    event.preventDefault();
    
    const selectedPartIds = Array.from(document.querySelectorAll('#build-parts-selector input:checked'))
        .map(cb => parseInt(cb.value));
    
    if (selectedPartIds.length === 0) {
        showStatus('Please select at least one part', 'error');
        return;
    }
    
    const buildData = {
        name: document.getElementById('build-name').value,
        description: document.getElementById('build-description').value || null,
        parts: selectedPartIds
    };
    
    try {
        await BuildsAPI.create(buildData);
        showStatus('Build created successfully', 'success');
        closeModal('create-build-modal');
        document.getElementById('create-build-form').reset();
        loadBuilds();
    } catch (error) {
        showStatus(`Error creating build: ${error.message}`, 'error');
    }
}

async function deleteBuild(id) {
    if (!confirm('Are you sure you want to delete this build?')) return;
    
    try {
        await BuildsAPI.delete(id);
        showStatus('Build deleted successfully', 'success');
        loadBuilds();
    } catch (error) {
        showStatus(`Error deleting build: ${error.message}`, 'error');
    }
}

async function loadPartsForCompatibility() {
    try {
        const parts = await PartsAPI.getAll();
        displayPartsForCompatibility(parts);
    } catch (error) {
        showStatus(`Error loading parts: ${error.message}`, 'error');
    }
}

function displayPartsForCompatibility(parts) {
    const container = document.getElementById('compatibility-parts-list');
    
    container.innerHTML = parts.map(part => `
        <label>
            <input type="checkbox" value="${part.id}" class="compat-part-checkbox">
            ${part.name} (${part.part_type})
        </label>
    `).join('');
}

async function checkCompatibility() {
    const selectedPartIds = Array.from(document.querySelectorAll('.compat-part-checkbox:checked'))
        .map(cb => parseInt(cb.value));
    
    if (selectedPartIds.length === 0) {
        showStatus('Please select at least one part to check', 'error');
        return;
    }
    
    try {
        const result = await CompatibilityAPI.check(selectedPartIds);
        displayCompatibilityResult(result);
    } catch (error) {
        showStatus(`Error checking compatibility: ${error.message}`, 'error');
    }
}

function displayCompatibilityResult(result) {
    const container = document.getElementById('compatibility-result');
    const compatClass = result.is_compatible ? 'compatible' : 'incompatible';
    
    let html = `<div class="compatibility-result ${compatClass}">`;
    html += `<h3>${result.is_compatible ? '✓ Compatible' : '✗ Incompatible'}</h3>`;
    
    if (result.issues && result.issues.length > 0) {
        html += '<h4>Issues:</h4><ul>';
        result.issues.forEach(issue => {
            html += `<li>${issue}</li>`;
        });
        html += '</ul>';
    }
    
    if (result.warnings && result.warnings.length > 0) {
        html += '<h4>Warnings:</h4><ul>';
        result.warnings.forEach(warning => {
            html += `<li>${warning}</li>`;
        });
        html += '</ul>';
    }
    
    html += '</div>';
    container.innerHTML = html;
}

async function loadRules() {
    try {
        const data = await CompatibilityAPI.getRules();
        displayRules(data.rules || data);
    } catch (error) {
        showStatus(`Error loading rules: ${error.message}`, 'error');
    }
}

function displayRules(rules) {
    const container = document.getElementById('rules-list');
    
    if (rules.length === 0) {
        container.innerHTML = '<div class="loading">No compatibility rules defined.</div>';
        return;
    }
    
    container.innerHTML = rules.map(rule => `
        <div class="rule-item">
            <strong>${rule.part_type_1} ↔ ${rule.part_type_2}</strong>
            <div>Type: ${rule.rule_type}</div>
            ${rule.rule_data ? `<div>Data: ${JSON.stringify(rule.rule_data)}</div>` : ''}
        </div>
    `).join('');
}

function showAddPartModal() {
    document.getElementById('add-part-modal').style.display = 'block';
}

function showCreateBuildModal() {
    const selector = document.getElementById('build-parts-selector');
    selector.innerHTML = allParts.map(part => `
        <label style="display: block; padding: 8px;">
            <input type="checkbox" value="${part.id}">
            ${part.name} (${part.part_type}) - $${part.price || 0}
        </label>
    `).join('');
    
    document.getElementById('create-build-modal').style.display = 'block';
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
    }
}
'''

# Write App JS
app_js_file = Path('frontend/src/js/app.js')
app_js_file.write_text(app_js_content, encoding='utf-8')
print(f"Created {app_js_file}")

print("\nAll frontend files created successfully!")
print("\nTo run the application:")
print("1. python run.py")
print("2. Open http://localhost:5000 in your browser")



