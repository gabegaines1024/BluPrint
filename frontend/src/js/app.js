// Main Application Logic

let allParts = [];
let selectedParts = [];
let currentUser = null;

// Authentication state management
window.handleAuthError = function() {
    showStatus('Session expired. Please login again.', 'error');
    showLoginModal();
    updateAuthUI();
};

document.addEventListener('DOMContentLoaded', async () => {
    checkHealth();
    await checkAuthentication();
    if (currentUser) {
        loadParts();
        loadBuilds();
        loadRules();
    }
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

async function checkAuthentication() {
    const token = localStorage.getItem('bluprint_auth_token');
    if (!token) {
        updateAuthUI();
        showLoginModal();
        return;
    }

    try {
        const response = await AuthAPI.getCurrentUser();
        currentUser = response.user;
        updateAuthUI();
    } catch (error) {
        console.error('Auth check failed:', error);
        localStorage.removeItem('bluprint_auth_token');
        updateAuthUI();
        showLoginModal();
    }
}

function updateAuthUI() {
    const authButtons = document.getElementById('auth-buttons');
    const userInfo = document.getElementById('user-info');
    const usernameDisplay = document.getElementById('username-display');

    if (currentUser) {
        authButtons.style.display = 'none';
        userInfo.style.display = 'block';
        usernameDisplay.textContent = currentUser.username;
    } else {
        authButtons.style.display = 'block';
        userInfo.style.display = 'none';
    }
}

async function handleLogin(event) {
    event.preventDefault();
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;

    try {
        const response = await AuthAPI.login(username, password);
        currentUser = response.user;
        updateAuthUI();
        closeModal('login-modal');
        document.getElementById('login-form').reset();
        showStatus('Login successful!', 'success');
        loadParts();
        loadBuilds();
        loadRules();
    } catch (error) {
        showStatus(`Login failed: ${error.message}`, 'error');
    }
}

async function handleRegister(event) {
    event.preventDefault();
    const username = document.getElementById('register-username').value;
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;

    try {
        const response = await AuthAPI.register(username, email, password);
        currentUser = response.user;
        updateAuthUI();
        closeModal('register-modal');
        document.getElementById('register-form').reset();
        showStatus('Registration successful!', 'success');
        loadParts();
        loadBuilds();
        loadRules();
    } catch (error) {
        showStatus(`Registration failed: ${error.message}`, 'error');
    }
}

function logout() {
    AuthAPI.logout();
    currentUser = null;
    updateAuthUI();
    showStatus('Logged out successfully', 'success');
    showLoginModal();
    // Clear all data
    allParts = [];
    document.getElementById('parts-list').innerHTML = '';
    document.getElementById('builds-list').innerHTML = '';
}

function showLoginModal() {
    document.getElementById('login-modal').style.display = 'block';
}

function showRegisterModal() {
    document.getElementById('register-modal').style.display = 'block';
}

function showTab(tabName, event) {
    if (!currentUser && tabName !== 'agent') {
        showStatus('Please login to access this feature', 'error');
        showLoginModal();
        return;
    }

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
    } else if (tabName === 'agent') {
        initializeAgent();
    }
}

async function loadParts() {
    if (!currentUser) return;
    try {
        allParts = await PartsAPI.getAll();
        displayParts(allParts);
    } catch (error) {
        if (error.message.includes('Authentication')) {
            handleAuthError();
        } else {
            showStatus(`Error loading parts: ${error.message}`, 'error');
        }
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
    if (!currentUser) return;
    try {
        const builds = await BuildsAPI.getAll();
        displayBuilds(builds);
    } catch (error) {
        if (error.message.includes('Authentication')) {
            handleAuthError();
        } else {
            showStatus(`Error loading builds: ${error.message}`, 'error');
        }
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

// Agent functionality
let agentMessages = [];

async function initializeAgent() {
    const chatMessages = document.getElementById('chat-messages');
    if (chatMessages.children.length === 0) {
        addAgentMessage('Hello! I\'m your PC building assistant. I can help you:\n- Find parts within your budget\n- Check compatibility\n- Build a complete PC step by step\n\nWhat would you like to build today?', 'agent');
    }
}

async function sendAgentMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    if (!currentUser) {
        showStatus('Please login to use the agent', 'error');
        showLoginModal();
        return;
    }

    // Add user message
    addAgentMessage(message, 'user');
    input.value = '';

    // Show loading
    const loadingId = addAgentMessage('Thinking...', 'agent', true);

    try {
        const response = await AgentAPI.chat(message);
        
        // Remove loading message
        const loadingEl = document.getElementById(loadingId);
        if (loadingEl) loadingEl.remove();

        // Add agent response
        addAgentMessage(response.message, 'agent');

        // If there are recommended parts, display them
        if (response.recommended_parts && response.recommended_parts.length > 0) {
            displayRecommendedParts(response.recommended_parts);
        }

        // If there's a build suggestion, show it
        if (response.build_suggestion) {
            displayBuildSuggestion(response.build_suggestion);
        }
    } catch (error) {
        const loadingEl = document.getElementById(loadingId);
        if (loadingEl) loadingEl.remove();
        addAgentMessage(`Sorry, I encountered an error: ${error.message}`, 'agent');
        if (error.message.includes('Authentication')) {
            handleAuthError();
        }
    }
}

function handleChatKeyPress(event) {
    if (event.key === 'Enter') {
        sendAgentMessage();
    }
}

function addAgentMessage(text, type, isLoading = false) {
    const chatMessages = document.getElementById('chat-messages');
    const messageId = 'msg-' + Date.now();
    const messageDiv = document.createElement('div');
    messageDiv.id = messageId;
    messageDiv.className = `chat-message ${type}`;
    
    if (isLoading) {
        messageDiv.innerHTML = `<div class="chat-text">${text}</div>`;
    } else {
        messageDiv.innerHTML = `<div class="chat-text">${text.replace(/\n/g, '<br>')}</div>`;
    }
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return messageId;
}

function displayRecommendedParts(parts) {
    const chatMessages = document.getElementById('chat-messages');
    const partsDiv = document.createElement('div');
    partsDiv.className = 'recommended-parts';
    partsDiv.innerHTML = '<strong>Recommended Parts:</strong>';
    
    parts.forEach(part => {
        const partCard = document.createElement('div');
        partCard.className = 'recommended-part-card';
        partCard.innerHTML = `
            <strong>${part.name}</strong>
            <div>Type: ${part.part_type}</div>
            ${part.price ? `<div>Price: $${part.price.toFixed(2)}</div>` : ''}
            ${part.reason ? `<div style="font-size: 0.9em; color: #666;">${part.reason}</div>` : ''}
            <button class="btn btn-primary" style="margin-top: 5px;" onclick="addPartFromAgent(${part.id})">Add to Build</button>
        `;
        partsDiv.appendChild(partCard);
    });
    
    chatMessages.appendChild(partsDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function displayBuildSuggestion(build) {
    const chatMessages = document.getElementById('chat-messages');
    const buildDiv = document.createElement('div');
    buildDiv.className = 'build-suggestion';
    buildDiv.innerHTML = `
        <strong>Build Suggestion:</strong>
        <div>Name: ${build.name || 'Untitled Build'}</div>
        ${build.total_price ? `<div>Total Price: $${build.total_price.toFixed(2)}</div>` : ''}
        ${build.is_compatible !== undefined ? `<div>Compatibility: ${build.is_compatible ? '✓ Compatible' : '✗ Issues Found'}</div>` : ''}
        <button class="btn btn-primary" style="margin-top: 5px;" onclick="saveBuildFromAgent(${JSON.stringify(build).replace(/"/g, '&quot;')})">Save Build</button>
    `;
    chatMessages.appendChild(buildDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

async function addPartFromAgent(partId) {
    try {
        const part = await PartsAPI.getById(partId);
        showStatus(`Part "${part.name}" is already in your catalog`, 'info');
        loadParts();
    } catch (error) {
        showStatus(`Error: ${error.message}`, 'error');
    }
}

async function saveBuildFromAgent(buildData) {
    try {
        await AgentAPI.saveBuild(buildData);
        showStatus('Build saved successfully!', 'success');
        loadBuilds();
        showTab('builds', null);
    } catch (error) {
        showStatus(`Error saving build: ${error.message}`, 'error');
    }
}

async function resetAgentConversation() {
    if (!currentUser) {
        showStatus('Please login to use the agent', 'error');
        return;
    }

    try {
        await AgentAPI.reset();
        const chatMessages = document.getElementById('chat-messages');
        chatMessages.innerHTML = '';
        initializeAgent();
        showStatus('Conversation reset', 'success');
    } catch (error) {
        showStatus(`Error resetting conversation: ${error.message}`, 'error');
    }
}
