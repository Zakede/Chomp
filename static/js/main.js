let completenessChart = null;
let cuisineChart = null;

document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
});

function initializeEventListeners() {
    const searchBtn = document.getElementById('searchBtn');
    const locationInput = document.getElementById('locationInput');

    searchBtn.addEventListener('click', handleSearch);

    locationInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            handleSearch();
        }
    });
}

async function handleSearch() {
    const location = document.getElementById('locationInput').value.trim();
    const radius = document.getElementById('radiusInput').value;

    if (!location) {
        alert('Please enter a location');
        return;
    }

    if (radius < 100 || radius > 50000) {
        alert('Radius must be between 100 and 50000 meters');
        return;
    }

    showLoading();

    try {
        const response = await fetch('/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                location: location,
                radius: parseInt(radius)
            })
        });

        const data = await response.json();

        if (response.ok) {
            displayResults(data);
        } else {
            alert('Error: ' + (data.error || 'An unknown error occurred'));
        }
    } catch (error) {
        console.error('Fetch error:', error);
        alert('Error fetching data: ' + error.message);
    } finally {
        hideLoading();
    }
}

function showLoading() {
    document.getElementById('loading').classList.remove('hidden');
    document.getElementById('results').classList.add('hidden');
}

function hideLoading() {
    document.getElementById('loading').classList.add('hidden');
}

function displayResults(data) {
    updateStatistics(data.stats);

    document.getElementById('results').classList.remove('hidden');

    createCompletenessChart(data.stats);
    createCuisineChart(data.restaurants);
    populateRestaurantTable(data.restaurants);

    document.getElementById('results').scrollIntoView({
        behavior: 'smooth',
        block: 'start'
    });
}

function updateStatistics(stats) {
    document.getElementById('stat-total').textContent = stats.total || 0;
    document.getElementById('stat-phone').textContent = stats.with_phone || 0;
    document.getElementById('stat-email').textContent = stats.with_email || 0;
    document.getElementById('stat-website').textContent = stats.with_website || 0;
    document.getElementById('stat-cuisine').textContent = stats.with_cuisine || 0;
    document.getElementById('stat-address').textContent = stats.with_address || 0;
}

function createCompletenessChart(stats) {
    const ctx = document.getElementById('completenessChart');

    if (completenessChart) {
        completenessChart.destroy();
    }

    completenessChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Phone', 'Email', 'Website', 'Cuisine', 'Address'],
            datasets: [{
                label: 'Count',
                data: [
                    stats.with_phone || 0,
                    stats.with_email || 0,
                    stats.with_website || 0,
                    stats.with_cuisine || 0,
                    stats.with_address || 0
                ],
                backgroundColor: [
                    '#00674f',
                    '#5B8FA3',
                    '#D4A5A5',
                    '#9FA8DA',
                    '#FFB74D'
                ],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1,
                        precision: 0,
                        color: '#8D99AE'
                    },
                    grid: {
                        color: '#EDF2F4'
                    }
                },
                x: {
                    ticks: {
                        color: '#8D99AE'
                    },
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

function createCuisineChart(restaurants) {
    const cuisineCounts = {};

    restaurants.forEach(restaurant => {
        if (restaurant.cuisine) {
            const cuisine = restaurant.cuisine;
            cuisineCounts[cuisine] = (cuisineCounts[cuisine] || 0) + 1;
        }
    });

    const sortedCuisines = Object.entries(cuisineCounts)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10);

    const ctx = document.getElementById('cuisineChart');

    if (cuisineChart) {
        cuisineChart.destroy();
    }

    if (sortedCuisines.length === 0) {
        cuisineChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['No Cuisine Data'],
                datasets: [{
                    data: [1],
                    backgroundColor: ['#e0e0e0'],
                    borderWidth: 2,
                    borderColor: '#fffcf2'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'right'
                    }
                }
            }
        });
        return;
    }

    cuisineChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: sortedCuisines.map(c => c[0]),
            datasets: [{
                data: sortedCuisines.map(c => c[1]),
                backgroundColor: [
                    '#00674f',
                    '#5B8FA3',
                    '#D4A5A5',
                    '#9FA8DA',
                    '#FFB74D',
                    '#81C784',
                    '#A1887F',
                    '#90CAF9',
                    '#FFCC80',
                    '#B39DDB'
                ],
                borderWidth: 2,
                borderColor: '#FFFFFF'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        padding: 12,
                        font: {
                            size: 12
                        },
                        color: '#2B2D42',
                        usePointStyle: true,
                        pointStyle: 'circle'
                    }
                }
            }
        }
    });
}

function populateRestaurantTable(restaurants) {
    const tbody = document.getElementById('restaurantTableBody');
    tbody.innerHTML = '';

    if (restaurants.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td colspan="4" style="text-align: center; padding: 2rem; color: #666;">
                No restaurants found in this area
            </td>
        `;
        tbody.appendChild(row);
        return;
    }

    restaurants.forEach(restaurant => {
        const row = document.createElement('tr');

        const name = restaurant.name || 'Unnamed Restaurant';
        const cuisine = restaurant.cuisine || '-';
        const phone = restaurant.phone || '-';
        const website = restaurant.website
            ? `<a href="${escapeHtml(restaurant.website)}" target="_blank" rel="noopener noreferrer">Link</a>`
            : '-';

        row.innerHTML = `
            <td>${escapeHtml(name)}</td>
            <td>${escapeHtml(cuisine)}</td>
            <td>${escapeHtml(phone)}</td>
            <td>${website}</td>
        `;

        tbody.appendChild(row);
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
