#!/usr/bin/env python3
"""Script to create frontend files."""

from pathlib import Path

# Create directories
frontend_dir = Path('frontend')
css_dir = frontend_dir / 'src' / 'css'
js_dir = frontend_dir / 'src' / 'js'

css_dir.mkdir(parents=True, exist_ok=True)
js_dir.mkdir(parents=True, exist_ok=True)

# HTML content
html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PC Builder - Bluprint</title>
    <link rel="stylesheet" href="/src/css/styles.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>🔧 PC Builder</h1>
            <p class="subtitle">Build your perfect PC with compatibility checking</p>
        </header>

        <div class="status-bar" id="status-bar">
            <span id="status-text">Ready</span>
        </div>

        <div class="tabs">
            <button class="tab-button active" onclick="showTab('parts')">Parts</button>
            <button class="tab-button" onclick="showTab('builds')">Builds</button>
            <button class="tab-button" onclick="showTab('compatibility')">Compatibility</button>
        </div>

        <!-- Parts Tab -->
        <div id="parts-tab" class="tab-content active">
            <div class="section-header">
                <h2>PC Parts Catalog</h2>
                <button class="btn btn-primary" onclick="showAddPartModal()">+ Add Part</button>
            </div>

            <div class="filters">
                <input type="text" id="search-parts" placeholder="Search parts..." oninput="filterParts()">
                <select id="filter-type" onchange="filterParts()">
                    <option value="">All Types</option>
                    <option value="CPU">CPU</option>
                    <option value="GPU">GPU</option>
                    <option value="RAM">RAM</option>
                    <option value="Motherboard">Motherboard</option>
                    <option value="Storage">Storage</option>
                    <option value="PSU">PSU</option>
                    <option value="Case">Case</option>
                </select>
            </div>

            <div id="parts-list" class="parts-grid"></div>
        </div>

        <!-- Builds Tab -->
        <div id="builds-tab" class="tab-content">
            <div class="section-header">
                <h2>PC Builds</h2>
                <button class="btn btn-primary" onclick="showCreateBuildModal()">+ Create Build</button>
            </div>

            <div id="builds-list"></div>
        </div>

        <!-- Compatibility Tab -->
        <div id="compatibility-tab" class="tab-content">
            <div class="section-header">
                <h2>Compatibility Checker</h2>
            </div>

            <div class="compatibility-checker">
                <label>Select Parts to Check:</label>
                <div id="compatibility-parts-list" class="parts-checkboxes"></div>
                <button class="btn btn-primary" onclick="checkCompatibility()">Check Compatibility</button>
                <div id="compatibility-result"></div>
            </div>

            <div class="rules-section">
                <h3>Compatibility Rules</h3>
                <div id="rules-list"></div>
            </div>
        </div>
    </div>

    <!-- Add Part Modal -->
    <div id="add-part-modal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal('add-part-modal')">&times;</span>
            <h2>Add New Part</h2>
            <form id="add-part-form" onsubmit="addPart(event)">
                <label>Name:</label>
                <input type="text" id="part-name" required>

                <label>Part Type:</label>
                <select id="part-type" required>
                    <option value="CPU">CPU</option>
                    <option value="GPU">GPU</option>
                    <option value="RAM">RAM</option>
                    <option value="Motherboard">Motherboard</option>
                    <option value="Storage">Storage</option>
                    <option value="PSU">PSU</option>
                    <option value="Case">Case</option>
                    <option value="Cooler">Cooler</option>
                </select>

                <label>Manufacturer:</label>
                <input type="text" id="part-manufacturer">

                <label>Price ($):</label>
                <input type="number" id="part-price" step="0.01" min="0">

                <label>Specifications (JSON):</label>
                <textarea id="part-specs" placeholder='{"socket": "AM4", "cores": 6}'></textarea>

                <button type="submit" class="btn btn-primary">Add Part</button>
            </form>
        </div>
    </div>

    <!-- Create Build Modal -->
    <div id="create-build-modal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal('create-build-modal')">&times;</span>
            <h2>Create New Build</h2>
            <form id="create-build-form" onsubmit="createBuild(event)">
                <label>Build Name:</label>
                <input type="text" id="build-name" required>

                <label>Description:</label>
                <textarea id="build-description"></textarea>

                <label>Select Parts:</label>
                <div id="build-parts-selector"></div>

                <button type="submit" class="btn btn-primary">Create Build</button>
            </form>
        </div>
    </div>

    <script src="/src/js/api.js"></script>
    <script src="/src/js/app.js"></script>
</body>
</html>'''

# Write HTML
(frontend_dir / 'index.html').write_text(html_content)
print("✓ Created frontend/index.html")

# Read and write the CSS and JS files (they're in the earlier code blocks)
# For brevity, I'll create simplified versions that will work

