// State
let players = [];
let selectedPlayerId = null;
let currentSort = { field: null, asc: true };
let confirmCallback = null;
let statsChart = null;
let currentProfileId = null;

// Auth Logic
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
});

function initApp() {
    refreshData();
}

function checkAuth() {
    const isAuthenticated = sessionStorage.getItem('arena_auth');
    const overlay = document.getElementById('loginOverlay');

    if (isAuthenticated === 'true') {
        overlay.style.display = 'none';
        initApp(); // Initialize app data only after login
        addLogoutButton();
    } else {
        overlay.style.display = 'flex';
    }
}

function addLogoutButton() {
    if (!document.getElementById('btnLogout')) {
        const actionBar = document.querySelector('.action-buttons');
        if (actionBar) {
            const logoutBtn = document.createElement('button');
            logoutBtn.id = 'btnLogout';
            logoutBtn.className = 'btn btn-text';
            logoutBtn.innerHTML = '<i class="fas fa-sign-out-alt"></i> Logout';
            logoutBtn.onclick = logout;
            actionBar.appendChild(logoutBtn);
        }
    }
}

function attemptLogin() {
    const user = document.getElementById('loginUser').value;
    const pass = document.getElementById('loginPass').value;

    if (user === 'user' && pass === 'password') {
        sessionStorage.setItem('arena_auth', 'true');
        checkAuth();
    } else {
        showError('Access Denied: Invalid Credentials');
        document.getElementById('loginPass').value = '';
    }
}

function logout() {
    sessionStorage.removeItem('arena_auth');
    location.reload();
}

// Ensure enter key works for login
document.getElementById('loginPass').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') attemptLogin();
});

async function refreshData() {
    setStatus('Loading players...');
    try {
        const response = await fetch('/api/players?t=' + new Date().getTime());
        const result = await response.json();
        players = result.data || [];
        renderTable();
        loadStats();
        setStatus(`⚔ ARENA READY - ${players.length} players in arena`);
    } catch (error) {
        showError('Failed to load data: ' + error.message);
    }
}

async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const result = await response.json();
        const stats = result.data || {};

        const totalPlayersEl = document.getElementById('statTotalPlayers');
        if (totalPlayersEl) totalPlayersEl.textContent = stats.total_players || 0;

        const avgWinRateEl = document.getElementById('statAvgWinRate');
        if (avgWinRateEl) avgWinRateEl.textContent = (stats.avg_win_rate || 0).toFixed(1) + '%';

        const avgKDAEl = document.getElementById('statAvgKDA');
        if (avgKDAEl) avgKDAEl.textContent = (stats.avg_kda || 0).toFixed(2);

        const totalGamesEl = document.getElementById('statTotalGames');
        if (totalGamesEl) totalGamesEl.textContent = stats.total_games || 0;
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}

function renderTable() {
    const tbody = document.getElementById('playerTableBody');
    if (!tbody) return;

    if (players.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="9" class="empty-state">
                    <h3>No players in the arena</h3>
                    <p>Import from Leaguepedia or recruit a new player</p>
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = players.map(player => {
        const isSelected = player.id === selectedPlayerId;
        const roleClass = getRoleClass(player.role);
        const initials = getInitials(player.ign);

        return `
            <tr class="${isSelected ? 'selected' : ''}" 
                onclick="selectPlayer(${player.id})"
                ondblclick="showProfile(${player.id})">
                <td>
                    <div class="player-cell">
                        <span class="player-avatar">${initials}</span>
                        <span class="player-name">${player.ign || 'Unknown'}</span>
                    </div>
                </td>
                <td><span class="role-badge ${roleClass}">${player.role || '-'}</span></td>
                <td>${player.team || '-'}</td>
                <td>${player.games_played || 0}</td>
                <td class="win-rate">${(player.win_rate || 0).toFixed(1)}%</td>
                <td class="kda">${(player.kda || 0).toFixed(2)}</td>
                <td>${player.gold_per_min || 0}</td>
                <td>${(player.cs_per_min || 0).toFixed(1)}</td>
                <td>${player.dmg_per_min || 0}</td>
            </tr>
        `;
    }).join('');
}

function getRoleClass(role) {
    if (!role) return '';
    const r = role.toLowerCase();
    if (r === 'top') return 'role-top';
    if (r === 'jungle' || r === 'jng') return 'role-jungle';
    if (r === 'mid' || r === 'middle') return 'role-mid';
    if (r === 'adc' || r === 'bot' || r === 'bottom') return 'role-adc';
    if (r === 'support' || r === 'sup') return 'role-support';
    return '';
}

function getInitials(name) {
    if (!name) return '?';
    const words = name.trim().split(/\s+/);
    if (words.length === 1) {
        return name.substring(0, 2).toUpperCase();
    }
    return (words[0][0] + words[1][0]).toUpperCase();
}

function sortBy(field) {
    if (currentSort.field === field) {
        currentSort.asc = !currentSort.asc;
    } else {
        currentSort.field = field;
        currentSort.asc = true;
    }

    players.sort((a, b) => {
        let valA = a[field];
        let valB = b[field];

        if (typeof valA === 'string') {
            valA = valA.toLowerCase();
            valB = (valB || '').toLowerCase();
        }

        if (valA < valB) return currentSort.asc ? -1 : 1;
        if (valA > valB) return currentSort.asc ? 1 : -1;
        return 0;
    });

    renderTable();
    updateSortIndicators();
}

function updateSortIndicators() {
    document.querySelectorAll('.sort-icon').forEach(el => {
        el.textContent = '';
    });

    if (currentSort.field) {
        const indicator = document.getElementById(`sort-${currentSort.field}`);
        if (indicator) {
            indicator.textContent = currentSort.asc ? '▲' : '▼';
        }
    }
}

function handleSearch() {
    const query = document.getElementById('searchInput').value.toLowerCase();

    if (!query) {
        refreshData();
        return;
    }

    fetch('/api/players')
        .then(res => res.json())
        .then(result => {
            const allPlayers = result.data || [];
            players = allPlayers.filter(p =>
                (p.ign && p.ign.toLowerCase().includes(query)) ||
                (p.team && p.team.toLowerCase().includes(query)) ||
                (p.role && p.role.toLowerCase().includes(query))
            );
            renderTable();
            setStatus(`Found ${players.length} players matching "${query}"`);
        });
}

function selectPlayer(id) {
    selectedPlayerId = (selectedPlayerId === id) ? null : id;
    renderTable();
}

function showAddModal() {
    document.getElementById('modalTitle').textContent = 'Recruit Player';
    document.getElementById('playerId').value = '';
    document.getElementById('playerForm').reset();
    document.getElementById('playerModal').classList.add('active');
}

function showEditModal(player) {
    document.getElementById('modalTitle').textContent = 'Edit Player';
    document.getElementById('playerId').value = player.id;
    document.getElementById('playerIGN').value = player.ign || '';
    document.getElementById('playerRole').value = player.role || '';
    document.getElementById('playerTeam').value = player.team || '';
    document.getElementById('playerGames').value = player.games_played || 0;
    document.getElementById('playerWinRate').value = player.win_rate || 0;
    document.getElementById('playerKDA').value = player.kda || 0;
    document.getElementById('playerGPM').value = player.gold_per_min || 0;
    document.getElementById('playerCSPM').value = player.cs_per_min || 0;
    document.getElementById('playerDPM').value = player.dmg_per_min || 0;
    document.getElementById('playerModal').classList.add('active');
}

function closePlayerModal() {
    document.getElementById('playerModal').classList.remove('active');
}

async function savePlayer() {
    const id = document.getElementById('playerId').value;
    const data = {
        ign: document.getElementById('playerIGN').value,
        role: document.getElementById('playerRole').value,
        team: document.getElementById('playerTeam').value,
        games_played: parseInt(document.getElementById('playerGames').value) || 0,
        win_rate: parseFloat(document.getElementById('playerWinRate').value) || 0,
        kda: parseFloat(document.getElementById('playerKDA').value) || 0,
        gold_per_min: parseInt(document.getElementById('playerGPM').value) || 0,
        cs_per_min: parseFloat(document.getElementById('playerCSPM').value) || 0,
        dmg_per_min: parseInt(document.getElementById('playerDPM').value) || 0
    };

    try {
        const url = id ? `/api/players/${id}` : '/api/players';
        const method = id ? 'PUT' : 'POST';

        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (!response.ok) throw new Error('Failed to save');

        closePlayerModal();
        await refreshData();
        setStatus(id ? 'Player updated!' : 'New player recruited!');
    } catch (error) {
        showError('Failed to save: ' + error.message);
    }
}

function editSelectedPlayer() {
    if (!selectedPlayerId) {
        showAlert('Select a player first');
        return;
    }
    const player = players.find(p => p.id === selectedPlayerId);
    if (player) showEditModal(player);
}

function deleteSelectedPlayer() {
    if (!selectedPlayerId) {
        showAlert('Select a player first');
        return;
    }

    const player = players.find(p => p.id === selectedPlayerId);
    showConfirm(
        'Eliminate Player',
        `Are you sure you want to eliminate ${player?.ign || 'this player'}?`,
        async () => {
            console.log('Executing delete callback for ID:', selectedPlayerId);
            try {
                const response = await fetch(`/api/players/${selectedPlayerId}`, { method: 'DELETE' });
                console.log('Delete response status:', response.status);

                if (!response.ok) {
                    const errText = await response.text();
                    console.error('Delete failed response:', errText);
                    throw new Error('Delete failed: ' + response.status);
                }

                selectedPlayerId = null;
                await refreshData();
                setStatus('Player eliminated from arena');
            } catch (error) {
                console.error('Delete error:', error);
                showError('Failed to eliminate: ' + error.message);
            }
        }
    );
}

function clearAllPlayers() {
    if (players.length === 0) {
        showAlert('Arena is already empty');
        return;
    }

    showConfirm(
        'Clear Arena',
        `This will eliminate ALL ${players.length} players. Are you sure?`,
        async () => {
            console.log('Executing Clear Arena callback');
            try {
                // Using new POST endpoint to bypass DELETE issues
                const response = await fetch('/api/clear-all', { method: 'POST' });
                console.log('Clear response status:', response.status);

                if (!response.ok) {
                    const errText = await response.text();
                    console.error('Clear failed response:', errText);
                    throw new Error('Clear failed: ' + response.status);
                }

                selectedPlayerId = null;
                await refreshData();
                setStatus('Arena cleared - All players eliminated');
            } catch (error) {
                console.error('Clear error:', error);
                showError('Failed to clear: ' + error.message);
            }
        }
    );
}

function showConfirm(title, message, callback) {
    document.getElementById('confirmTitle').textContent = title;
    document.getElementById('confirmMessage').textContent = message;
    confirmCallback = callback;

    const yesBtn = document.getElementById('confirmYes');
    yesBtn.onclick = () => {
        console.log('Confirm YES clicked. Callback present:', !!confirmCallback);
        if (confirmCallback) confirmCallback();
        closeConfirmModal();
    };

    document.getElementById('confirmModal').classList.add('active');
}

function closeConfirmModal() {
    document.getElementById('confirmModal').classList.remove('active');
    confirmCallback = null;
}

function showImportModal() {
    document.getElementById('importProgress').style.display = 'none';
    document.getElementById('importBtn').disabled = false;
    document.getElementById('importModal').classList.add('active');
}

function closeImportModal() {
    document.getElementById('importModal').classList.remove('active');
}

async function doImport() {
    const tournament = document.getElementById('importTournament').value;
    const year = document.getElementById('importYear').value;

    document.getElementById('importProgress').style.display = 'flex';
    document.getElementById('importStatus').textContent = 'Connecting to Leaguepedia...';
    document.getElementById('importBtn').disabled = true;

    try {
        const response = await fetch('/api/import', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tournament, year })
        });

        const result = await response.json();

        if (result.success) {
            const msg = result.message || `Imported ${result.data?.players_imported || 0} players!`;
            document.getElementById('importStatus').textContent = msg;
            setTimeout(() => {
                closeImportModal();
                refreshData();
            }, 1500);
        } else {
            document.getElementById('importStatus').textContent = 'Import failed: ' + result.error;
            document.getElementById('importBtn').disabled = false;
        }
    } catch (error) {
        document.getElementById('importStatus').textContent = 'Error: ' + error.message;
        document.getElementById('importBtn').disabled = false;
    }
}

async function showProfile(id) {
    currentProfileId = id;
    const player = players.find(p => p.id === id);
    if (!player) return;

    document.getElementById('profileModal').classList.add('active');
    document.getElementById('profileLoading').style.display = 'flex';
    document.getElementById('profileContent').style.display = 'none';

    try {
        const response = await fetch(`/api/players/${id}/profile`);
        const data = await response.json();

        populateProfile(data.data || data); // Handle both wrapped and unwrapped data

        document.getElementById('profileLoading').style.display = 'none';
        document.getElementById('profileContent').style.display = 'block';
    } catch (error) {
        console.error('Failed to load profile:', error);
        document.getElementById('profileLoading').innerHTML = '<span>Failed to load profile</span>';
    }
}

function populateProfile(data) {
    // Basic info
    document.getElementById('profileName').textContent = data.ign || 'Unknown';
    document.getElementById('profileTeam').textContent = data.team || 'No Team';
    document.getElementById('profileRole').textContent = data.role || 'Unknown';

    // Real name and country
    const realNameEl = document.getElementById('profileRealName');
    if (data.real_name) {
        realNameEl.textContent = data.real_name;
        realNameEl.style.display = 'block';
    } else {
        realNameEl.style.display = 'none';
    }

    const countryEl = document.getElementById('profileCountry');
    const countrySep = document.getElementById('profileCountrySep');
    if (data.country) {
        countryEl.textContent = data.country;
        countryEl.style.display = 'inline';
        if (countrySep) countrySep.style.display = 'inline';
    } else {
        countryEl.style.display = 'none';
        if (countrySep) countrySep.style.display = 'none';
    }

    // Profile image
    const imageEl = document.getElementById('profileImage');
    const placeholderEl = document.getElementById('profilePlaceholder');
    const initialsEl = document.getElementById('profileInitials');

    initialsEl.textContent = getInitials(data.ign);

    if (data.image_url) {
        imageEl.src = data.image_url;
        imageEl.style.display = 'block';
        imageEl.onload = () => { placeholderEl.style.display = 'none'; };
        imageEl.onerror = () => {
            imageEl.style.display = 'none';
            placeholderEl.style.display = 'flex';
        };
    } else {
        imageEl.style.display = 'none';
        placeholderEl.style.display = 'flex';
    }

    // Quick stats
    document.getElementById('profileGames').textContent = data.games_played || 0;
    document.getElementById('profileWinRate').textContent = (data.win_rate || 0).toFixed(1) + '%';
    document.getElementById('profileKDA').textContent = (data.kda || 0).toFixed(2);

    // Detailed stats
    document.getElementById('profileAvgKills').textContent = (data.avg_kills || 0).toFixed(1);
    document.getElementById('profileAvgDeaths').textContent = (data.avg_deaths || 0).toFixed(1);
    document.getElementById('profileAvgAssists').textContent = (data.avg_assists || 0).toFixed(1);
    document.getElementById('profileGPM').textContent = data.gold_per_min || 0;
    document.getElementById('profileCSPM').textContent = (data.cs_per_min || 0).toFixed(1);
    document.getElementById('profileDPM').textContent = data.dmg_per_min || 0;

    // Totals
    document.getElementById('profileTotalKills').textContent = formatNumber(data.kills || 0);
    document.getElementById('profileTotalDeaths').textContent = formatNumber(data.deaths || 0);
    document.getElementById('profileTotalAssists').textContent = formatNumber(data.assists || 0);
    document.getElementById('profileTotalGold').textContent = formatNumber(data.total_gold || 0);
    document.getElementById('profileTotalCS').textContent = formatNumber(data.total_cs || 0);

    // Chart
    if (data.chart_data) {
        createStatsChart(data.chart_data);
    }
}

function formatNumber(num) {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
}

function createStatsChart(chartData) {
    const canvas = document.getElementById('statsChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');

    if (statsChart) statsChart.destroy();

    statsChart = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: chartData.labels,
            datasets: [{
                label: 'Performance',
                data: chartData.values,
                backgroundColor: 'rgba(139, 44, 255, 0.1)',
                borderColor: '#8b2cff',
                borderWidth: 2,
                pointBackgroundColor: '#8b2cff',
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: '#8b2cff'
            }, {
                label: 'Arena Avg',
                data: [50, 50, 50, 50, 50, 50],
                backgroundColor: 'rgba(255, 183, 77, 0.15)',
                borderColor: '#ffb74d',
                borderWidth: 2,
                borderDash: [5, 5],
                pointBackgroundColor: '#ffb74d',
                pointBorderColor: '#fff',
                pointRadius: 3,
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: '#ffb74d'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                r: {
                    beginAtZero: true,
                    max: 100,
                    ticks: { display: false, stepSize: 20 },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' },
                    angleLines: { color: 'rgba(255, 255, 255, 0.1)' },
                    pointLabels: {
                        color: '#8892a0',
                        font: { size: 11, family: 'Segoe UI' }
                    }
                }
            },
            plugins: {
                legend: {
                    display: true,
                    labels: { color: '#8892a0', boxWidth: 10 }
                }
            }
        }
    });
}

function closeProfileModal() {
    document.getElementById('profileModal').classList.remove('active');
    currentProfileId = null;
}

function editFromProfile() {
    const player = players.find(p => p.id === currentProfileId);
    if (player) {
        closeProfileModal();
        showEditModal(player);
    }
}

function setStatus(message) {
    const el = document.getElementById('statusText');
    if (el) el.textContent = message;
}

function showAlert(message) {
    alert(message);
}

function showError(message) {
    console.error(message);
    setStatus('Error: ' + message);
}
