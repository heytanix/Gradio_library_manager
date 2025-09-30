// PUIPM - Python User Interfaced Package Manager
// FINAL VERSION WITH AGGRESSIVE UI REFRESH TO SOLVE PERSISTENT DISPLAY ISSUES

class PUIPM {
    constructor() {
        this.socket = null;
        this.packages = [];
        this.filteredPackages = [];
        this.currentAction = null;
        this.selectedPackage = null;
        this.currentPathType = null;
        this.forceRefreshTimer = null;
        this.initializeApp();
    }

    initializeApp() {
        this.initializeSocket();
        this.bindEventListeners();
        this.loadInitialData();
        this.startAggressiveRefresh();
    }

    initializeSocket() {
        this.socket = io();

        // Console events
        this.socket.on('console_update', (data) => {
            this.appendToConsole(data.data);
        });

        this.socket.on('console_clear', (data) => {
            this.setConsoleContent(data.data);
        });

        // CRITICAL: Operation complete handler with AGGRESSIVE refresh
        this.socket.on('operation_complete', (data) => {
            console.log('🔄 Operation completed, FORCING UI refresh');
            this.hideLoading();

            // AGGRESSIVE: Multiple immediate refresh attempts
            this.forceRefreshPackageList();
            setTimeout(() => this.forceRefreshPackageList(), 500);
            setTimeout(() => this.forceRefreshPackageList(), 1500);
            setTimeout(() => this.forceRefreshPackageList(), 3000);
        });

        // Handle initial package load
        this.socket.on('initial_package_load', (data) => {
            console.log('📦 Initial package load:', data.count);
            this.forceUpdatePackageList(data.packages, 'initial');
        });

        // AGGRESSIVE: Multiple listeners for different refresh events
        this.socket.on('force_package_update', (data) => {
            console.log('📦 FORCE UPDATE received:', data.count, 'packages');
            this.forceUpdatePackageList(data.packages, 'force_update');
        });

        this.socket.on('package_list_changed', (data) => {
            console.log('📦 Package list changed:', data.count, 'packages');
            this.forceUpdatePackageList(data.packages, 'list_changed');
        });

        this.socket.on('refresh_package_display', (data) => {
            console.log('📦 Display refresh:', data.packages.length, 'packages');
            this.forceUpdatePackageList(data.packages, 'display_refresh');
        });

        this.socket.on('connect', () => {
            console.log('✅ Connected to server');
            this.forceRefreshPackageList();
        });

        this.socket.on('disconnect', () => {
            console.log('❌ Disconnected from server');
            this.showNotification('Connection lost. Refreshing...', 'warning');
        });

        this.socket.on('reconnect', () => {
            console.log('✅ Reconnected to server - FORCING REFRESH');
            this.forceRefreshPackageList();
        });
    }

    // AGGRESSIVE: Force update package list with complete UI rebuild
    forceUpdatePackageList(newPackages, source) {
        console.log(`🔄 FORCE UPDATING package list from ${source}: ${newPackages.length} packages`);

        // Clear everything first
        this.packages = [];
        this.filteredPackages = [];

        // Force clear the UI
        const container = document.getElementById('packages-container');
        if (container) {
            container.innerHTML = '<div style="text-align: center; padding: 2rem;"><i class="fas fa-spinner fa-spin"></i> Updating...</div>';
        }

        // Update with new data after a tiny delay to ensure DOM updates
        setTimeout(() => {
            this.packages = Array.isArray(newPackages) ? newPackages : [];
            this.filteredPackages = [...this.packages];

            // Force re-apply search filter if any
            const searchInput = document.getElementById('package-search');
            if (searchInput && searchInput.value.trim()) {
                this.filterPackages(searchInput.value.trim());
            } else {
                this.renderPackages();
            }

            this.updatePackageCount();

            console.log(`✅ UI FORCIBLY UPDATED: ${this.packages.length} packages displayed`);

            // Show success notification
            if (source !== 'initial') {
                this.showNotification(`Packages refreshed: ${this.packages.length} packages`, 'success');
            }
        }, 50);
    }

    // AGGRESSIVE: Force refresh via both WebSocket and HTTP
    forceRefreshPackageList() {
        console.log('🔄 FORCE REFRESHING package list (dual method)');

        // Method 1: WebSocket request
        if (this.socket && this.socket.connected) {
            this.socket.emit('force_refresh_request');
        }

        // Method 2: Direct HTTP request as backup
        setTimeout(() => {
            this.httpRefreshPackageList();
        }, 100);
    }

    // HTTP method to get fresh package list
    async httpRefreshPackageList() {
        try {
            console.log('🌐 HTTP refresh request');
            const response = await fetch('/api/packages?t=' + Date.now()); // Cache buster
            if (!response.ok) throw new Error('HTTP refresh failed');

            const packages = await response.json();
            console.log('📦 HTTP refresh got:', packages.length, 'packages');
            this.forceUpdatePackageList(packages, 'http_refresh');
        } catch (error) {
            console.error('HTTP refresh failed:', error);
        }
    }

    // Start aggressive refresh timer
    startAggressiveRefresh() {
        // Refresh every 10 seconds (more frequent)
        this.forceRefreshTimer = setInterval(() => {
            console.log('⏰ Periodic aggressive refresh');
            this.forceRefreshPackageList();
        }, 10000);

        console.log('⏰ Aggressive refresh timer started (10 second intervals)');
    }

    bindEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                this.switchSection(item.dataset.section);
            });
        });

        // Package management - ENHANCED with aggressive refresh
        document.getElementById('refresh-packages')?.addEventListener('click', () => {
            console.log('🔄 Manual refresh button clicked');
            this.showLoading();
            this.forceRefreshPackageList();
            setTimeout(() => this.hideLoading(), 1000);
        });

        document.getElementById('install-package')?.addEventListener('click', () => {
            this.installPackage();
        });

        document.getElementById('package-search')?.addEventListener('input', (e) => {
            this.filterPackages(e.target.value);
        });

        document.getElementById('sort-packages')?.addEventListener('change', (e) => {
            this.sortPackages(e.target.value);
        });

        // Paths management
        document.getElementById('refresh-storage')?.addEventListener('click', () => {
            this.loadStorageInfo();
        });

        // Console management
        document.getElementById('clear-console')?.addEventListener('click', () => {
            this.clearConsole();
        });

        document.getElementById('copy-console')?.addEventListener('click', () => {
            this.copyConsole();
        });

        // Modal events
        document.querySelector('.close')?.addEventListener('click', () => {
            this.closeModal();
        });

        document.getElementById('modal-cancel')?.addEventListener('click', () => {
            this.closeModal();
        });

        document.getElementById('modal-confirm')?.addEventListener('click', () => {
            this.confirmAction();
        });

        // Click outside modal to close
        document.getElementById('action-modal')?.addEventListener('click', (e) => {
            if (e.target.id === 'action-modal') {
                this.closeModal();
            }
        });

        document.getElementById('path-modal')?.addEventListener('click', (e) => {
            if (e.target.id === 'path-modal') {
                this.closePathModal();
            }
        });

        // Enter key handlers
        document.getElementById('package-name')?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.installPackage();
            }
        });

        document.getElementById('package-version')?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.installPackage();
            }
        });

        document.getElementById('new-path')?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.savePath();
            }
        });
    }

    loadInitialData() {
        this.forceRefreshPackageList(); // Use aggressive refresh for initial load
        this.loadCacheLocations();
        this.loadStorageInfo();
        this.loadOtherLibraries();
    }

    switchSection(section) {
        // Update navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-section="${section}"]`)?.classList.add('active');

        // Update content sections
        document.querySelectorAll('.content-section').forEach(contentSection => {
            contentSection.classList.remove('active');
        });
        document.getElementById(`${section}-section`)?.classList.add('active');

        // Load section-specific data if needed
        if (section === 'paths') {
            this.loadCacheLocations();
            this.loadStorageInfo();
            this.loadOtherLibraries();
        } else if (section === 'packages') {
            // AGGRESSIVE refresh when switching to packages
            console.log('📦 Switched to packages section - forcing refresh');
            this.forceRefreshPackageList();
        }
    }

    // LEGACY: Keep for compatibility
    async loadPackages() {
        this.forceRefreshPackageList();
    }

    renderPackages() {
        const container = document.getElementById('packages-container');
        if (!container) return;

        // FORCE clear container first
        container.innerHTML = '';

        if (this.filteredPackages.length === 0) {
            container.innerHTML = `
            <div class="no-packages" style="text-align: center; padding: 3rem; color: #6b7280;">
            <i class="fas fa-box-open" style="font-size: 2rem; margin-bottom: 1rem;"></i>
            <p style="font-size: 1.1rem; margin-bottom: 0.5rem;">No packages found</p>
            ${this.packages.length === 0 ? '<p style="font-size: 0.9rem; opacity: 0.7;">Click refresh or check your connection</p>' : ''}
            </div>
            `;
            return;
        }

        console.log(`🎨 Rendering ${this.filteredPackages.length} packages in UI`);

        // Create document fragment for better performance
        const fragment = document.createDocumentFragment();

        this.filteredPackages.forEach(pkg => {
            const packageCard = document.createElement('div');
            packageCard.className = 'package-card';

            // ENHANCED: More distinctive package cards with better data attributes
            packageCard.innerHTML = `
            <div class="package-info">
            <div class="package-name" title="${this.escapeHtml(pkg.name)}">${this.escapeHtml(pkg.name)}</div>
            <div class="package-version" title="Version ${this.escapeHtml(pkg.version)}">v${this.escapeHtml(pkg.version)}</div>
            </div>
            <div class="package-actions">
            <button class="action-btn action-btn-delete"
            data-action="uninstall"
            data-package-name="${this.escapeHtml(pkg.name)}"
            title="Uninstall ${this.escapeHtml(pkg.name)}">
            <i class="fas fa-trash"></i>
            </button>
            <button class="action-btn action-btn-reinstall"
            data-action="reinstall"
            data-package-name="${this.escapeHtml(pkg.name)}"
            title="Reinstall ${this.escapeHtml(pkg.name)}">
            <i class="fas fa-sync-alt"></i>
            </button>
            <button class="action-btn action-btn-update"
            data-action="update"
            data-package-name="${this.escapeHtml(pkg.name)}"
            title="Update ${this.escapeHtml(pkg.name)}">
            <i class="fas fa-arrow-up"></i>
            </button>
            </div>
            `;

            fragment.appendChild(packageCard);
        });

        // Add all cards at once for better performance
        container.appendChild(fragment);

        // Add event delegation for action buttons
        container.removeEventListener('click', this.handleActionClick);
        this.handleActionClick = this.handleActionClick.bind(this);
        container.addEventListener('click', this.handleActionClick);

        console.log(`✅ Successfully rendered ${this.filteredPackages.length} package cards`);
    }

    handleActionClick(e) {
        const actionBtn = e.target.closest('.action-btn');
        if (!actionBtn) return;

        e.preventDefault();
        e.stopPropagation();

        const action = actionBtn.dataset.action;
        const packageName = actionBtn.dataset.packageName;

        console.log('🎯 Action clicked:', action, packageName);

        if (action && packageName) {
            this.showActionModal(action, packageName);
        } else {
            console.error('❌ Missing action or package name:', { action, packageName });
            this.showNotification('Error: Invalid action or package', 'error');
        }
    }

    filterPackages(searchTerm) {
        const term = searchTerm.toLowerCase().trim();
        console.log('🔍 Filtering packages:', term);

        if (!term) {
            this.filteredPackages = [...this.packages];
        } else {
            this.filteredPackages = this.packages.filter(pkg =>
            pkg.name.toLowerCase().includes(term) ||
            pkg.version.toLowerCase().includes(term)
            );
        }

        this.renderPackages();
        this.updatePackageCount();
    }

    sortPackages(sortBy) {
        console.log('📊 Sorting packages by:', sortBy);

        this.filteredPackages.sort((a, b) => {
            if (sortBy === 'name') {
                return a.name.localeCompare(b.name);
            } else if (sortBy === 'version') {
                return a.version.localeCompare(b.version);
            }
            return 0;
        });

        this.renderPackages();
    }

    updatePackageCount() {
        const total = this.packages.length;
        const filtered = this.filteredPackages.length;
        const countText = filtered === total
        ? `Total packages: ${total}`
        : `Showing ${filtered} of ${total} packages`;

        const countElement = document.getElementById('total-packages');
        if (countElement) {
            countElement.textContent = countText;
        }

        console.log(`📊 Package count updated: ${countText}`);
    }

    async installPackage() {
        const packageNameEl = document.getElementById('package-name');
        const packageVersionEl = document.getElementById('package-version');

        if (!packageNameEl || !packageVersionEl) return;

        const packageName = packageNameEl.value.trim();
        const packageVersion = packageVersionEl.value.trim();

        if (!packageName) {
            this.showNotification('Please enter a package name', 'warning');
            return;
        }

        console.log('📦 Installing package:', packageName, packageVersion);
        this.showLoading();

        try {
            const response = await fetch('/api/install', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    package_name: packageName,
                    version: packageVersion
                })
            });

            if (!response.ok) throw new Error('Installation request failed');

            const result = await response.json();
            if (result.success) {
                this.showNotification(result.message, 'success');
                packageNameEl.value = '';
                packageVersionEl.value = '';
                // Switch to console to show progress
                this.switchSection('console');
            } else {
                this.showNotification(result.message, 'error');
                this.hideLoading();
            }
        } catch (error) {
            console.error('Error installing package:', error);
            this.showNotification('Error installing package: ' + error.message, 'error');
            this.hideLoading();
        }
    }

    showActionModal(action, packageName) {
        console.log('🎯 Showing action modal:', { action, packageName });

        if (!action || !packageName) {
            console.error('❌ Invalid modal parameters');
            this.showNotification('Error: Invalid action or package name', 'error');
            return;
        }

        this.currentAction = action;
        this.selectedPackage = packageName;

        const modal = document.getElementById('action-modal');
        const title = document.getElementById('modal-title');
        const message = document.getElementById('modal-message');
        const packageInfo = document.getElementById('modal-package-name');
        const confirmBtn = document.getElementById('modal-confirm');

        if (!modal || !title || !message || !packageInfo || !confirmBtn) {
            console.error('❌ Modal elements not found');
            this.showNotification('Error: Modal not available', 'error');
            return;
        }

        packageInfo.textContent = packageName;

        switch (action) {
            case 'uninstall':
                title.textContent = 'Uninstall Package';
                message.textContent = 'Are you sure you want to uninstall this package?';
                confirmBtn.className = 'btn btn-danger';
                confirmBtn.innerHTML = '<i class="fas fa-trash"></i> Uninstall';
                break;
            case 'reinstall':
                title.textContent = 'Reinstall Package';
                message.textContent = 'This will force reinstall the package. Continue?';
                confirmBtn.className = 'btn btn-success';
                confirmBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Reinstall';
                break;
            case 'update':
                title.textContent = 'Update Package';
                message.textContent = 'This will update the package to the latest version. Continue?';
                confirmBtn.className = 'btn btn-primary';
                confirmBtn.innerHTML = '<i class="fas fa-arrow-up"></i> Update';
                break;
            default:
                console.error('❌ Unknown action:', action);
                this.showNotification('Error: Unknown action type', 'error');
                return;
        }

        modal.style.display = 'block';
    }

    closeModal() {
        const modal = document.getElementById('action-modal');
        if (modal) {
            modal.style.display = 'none';
        }
        this.currentAction = null;
        this.selectedPackage = null;
    }

    async confirmAction() {
        if (!this.currentAction || !this.selectedPackage) {
            console.error('❌ Missing action or package for confirmation');
            this.showNotification('Error: Missing action or package information', 'error');
            return;
        }

        const action = this.currentAction;
        const packageName = this.selectedPackage;

        console.log(`🚀 Confirming action: ${action} on ${packageName}`);

        this.closeModal();
        this.showLoading();

        try {
            const response = await fetch(`/api/${action}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    package_name: packageName
                })
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`${action} request failed: ${errorText}`);
            }

            const result = await response.json();

            if (result.success) {
                this.showNotification(result.message, 'success');
                this.switchSection('console');

                // AGGRESSIVE: Force refresh after action starts
                setTimeout(() => this.forceRefreshPackageList(), 1000);
            } else {
                this.showNotification(result.message || 'Operation failed', 'error');
                this.hideLoading();
            }
        } catch (error) {
            console.error(`❌ Error performing ${action}:`, error);
            this.showNotification(`Error performing ${action}: ${error.message}`, 'error');
            this.hideLoading();
        }
    }

    async loadCacheLocations() {
        try {
            const response = await fetch('/api/cache-locations');
            if (!response.ok) throw new Error('Failed to fetch cache locations');

            const cacheInfo = await response.json();

            const pycacheEl = document.getElementById('pycache-path');
            const pipCacheEl = document.getElementById('pip-cache-path');
            const torchCacheEl = document.getElementById('torch-cache-path');

            if (pycacheEl) pycacheEl.textContent = cacheInfo.pycache || 'Not set';
            if (pipCacheEl) pipCacheEl.textContent = cacheInfo.pip_cache || 'Not set';
            if (torchCacheEl) torchCacheEl.textContent = cacheInfo.torch_cache || 'Not set';
        } catch (error) {
            console.error('Error loading cache locations:', error);
        }
    }

    async loadStorageInfo() {
        try {
            const response = await fetch('/api/storage');
            if (!response.ok) throw new Error('Failed to fetch storage info');

            const storageInfo = await response.json();
            this.renderStorageInfo(Array.isArray(storageInfo) ? storageInfo : []);
        } catch (error) {
            console.error('Error loading storage info:', error);
            this.renderStorageInfo([]);
        }
    }

    renderStorageInfo(storageInfo) {
        const container = document.getElementById('storage-container');
        if (!container) return;

        container.innerHTML = '';

        if (storageInfo.length === 0) {
            container.innerHTML = '<div class="no-storage"><p>No storage information available.</p></div>';
            return;
        }

        storageInfo.forEach(storage => {
            const storageCard = document.createElement('div');
            storageCard.className = 'storage-card';
            storageCard.innerHTML = `
            <div class="storage-header">
            <div class="storage-device">${this.escapeHtml(storage.device)}</div>
            <div class="storage-type ${storage.type.toLowerCase()}">${this.escapeHtml(storage.type)}</div>
            </div>
            <div class="storage-details">
            <div><strong>Mount Point:</strong> ${this.escapeHtml(storage.mountpoint)}</div>
            <div><strong>File System:</strong> ${this.escapeHtml(storage.filesystem)}</div>
            <div><strong>Total:</strong> ${storage.total_gb} GB</div>
            <div><strong>Used:</strong> ${storage.used_gb} GB (${storage.used_percent}%)</div>
            <div><strong>Free:</strong> ${storage.free_gb} GB</div>
            </div>
            `;
            container.appendChild(storageCard);
        });
    }

    async loadOtherLibraries() {
        try {
            const otherLibraries = await this.detectOtherLibraries();
            if (otherLibraries.length > 0) {
                this.renderOtherLibraries(otherLibraries);
            } else {
                const container = document.getElementById('other-libraries-container');
                if (container) {
                    container.style.display = 'none';
                }
            }
        } catch (error) {
            console.error('Error loading other libraries:', error);
        }
    }

    async detectOtherLibraries() {
        return [];
    }

    renderOtherLibraries(libraries) {
        const container = document.getElementById('other-libraries-container');
        if (!container) return;

        container.innerHTML = '';
        container.style.display = 'block';

        const title = document.createElement('h3');
        title.textContent = 'Other Libraries Found:';
        container.appendChild(title);

        libraries.forEach(lib => {
            const libraryItem = document.createElement('div');
            libraryItem.className = 'library-item';
            libraryItem.innerHTML = `
            <h4>${this.escapeHtml(lib.name)}</h4>
            <p><strong>Type:</strong> ${this.escapeHtml(lib.type)}</p>
            <p><strong>Location:</strong> ${this.escapeHtml(lib.location)}</p>
            `;
            container.appendChild(libraryItem);
        });
    }

    appendToConsole(text) {
        const consoleOutput = document.getElementById('console-output');
        if (consoleOutput) {
            consoleOutput.textContent += text;
            consoleOutput.scrollTop = consoleOutput.scrollHeight;
        }
    }

    setConsoleContent(text) {
        const consoleOutput = document.getElementById('console-output');
        if (consoleOutput) {
            consoleOutput.textContent = text;
            consoleOutput.scrollTop = consoleOutput.scrollHeight;
        }
    }

    clearConsole() {
        this.socket.emit('clear_console');
    }

    copyConsole() {
        const consoleOutput = document.getElementById('console-output');
        if (!consoleOutput) return;

        const consoleText = consoleOutput.textContent;
        navigator.clipboard.writeText(consoleText).then(() => {
            this.showNotification('Console output copied to clipboard', 'success');
        }).catch(() => {
            this.showNotification('Failed to copy console output', 'error');
        });
    }

    showLoading() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.style.display = 'flex';
        }
    }

    hideLoading() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.style.display = 'none';
        }
    }

    showNotification(message, type = 'info') {
        console.log(`📢 Notification (${type}): ${message}`);

        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
        <i class="fas fa-${this.getNotificationIcon(type)}"></i>
        <span>${this.escapeHtml(message)}</span>
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            if (notification.parentNode) {
                notification.classList.add('fade-out');
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.remove();
                    }
                }, 300);
            }
        }, 5000);

        notification.addEventListener('click', () => {
            if (notification.parentNode) {
                notification.remove();
            }
        });
    }

    getNotificationIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        return icons[type] || icons.info;
    }

    escapeHtml(text) {
        if (!text) return '';
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return String(text).replace(/[&<>"']/g, m => map[m]);
    }

    // Cleanup method
    destroy() {
        if (this.forceRefreshTimer) {
            clearInterval(this.forceRefreshTimer);
            this.forceRefreshTimer = null;
        }
        if (this.socket) {
            this.socket.disconnect();
        }
        console.log('🧹 PUIPM cleanup completed');
    }
}

// Path editing functions (global scope for onclick handlers)
function editPath(pathType) {
    app.currentPathType = pathType;
    const modal = document.getElementById('path-modal');
    const title = document.getElementById('path-modal-title');
    const input = document.getElementById('new-path');

    if (!modal || !title || !input) return;

    const pathNames = {
        'pycache': 'PyCache',
        'pip_cache': 'PIP Cache',
        'torch_cache': 'Torch Cache'
    };

    title.textContent = `Edit ${pathNames[pathType]} Path`;
    input.value = '';
    input.placeholder = `Enter new ${pathNames[pathType].toLowerCase()} path...`;
    modal.style.display = 'block';
    input.focus();
}

function closePathModal() {
    const modal = document.getElementById('path-modal');
    if (modal) {
        modal.style.display = 'none';
    }
    app.currentPathType = null;
}

async function savePath() {
    const input = document.getElementById('new-path');
    if (!input || !app.currentPathType) return;

    const newPath = input.value.trim();
    if (!newPath) {
        app.showNotification('Please enter a valid path', 'warning');
        return;
    }

    try {
        app.showLoading();

        const response = await fetch('/api/set-cache', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                cache_type: app.currentPathType,
                location: newPath
            })
        });

        if (!response.ok) throw new Error('Failed to set cache path');

        const result = await response.json();
        app.showNotification(result.message, 'success');
        closePathModal();
        app.loadCacheLocations();
    } catch (error) {
        console.error('Error setting cache path:', error);
        app.showNotification('Error setting cache path', 'error');
    } finally {
        app.hideLoading();
    }
}

// Initialize the application
console.log('🚀 Initializing PUIPM with AGGRESSIVE REFRESH');
const app = new PUIPM();

// Make app globally available
window.app = app;

// Enhanced cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (app) {
        console.log('🧹 Cleaning up PUIPM before unload');
        app.destroy();
    }
});

// Additional debug info
console.log('✅ PUIPM AGGRESSIVE REFRESH VERSION LOADED');
