// Main Application Logic

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
