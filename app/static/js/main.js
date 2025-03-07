// Initialize Socket.IO connection with explicit configuration
const socket = io({
    transports: ['websocket'],
    upgrade: false,
    reconnection: true,
    reconnectionAttempts: 5,
    reconnectionDelay: 1000
});

// Traffic light timing configurations
const timings = {
    low: {
        green: 40,
        yellow: 3,
        red: 20
    },
    moderate: {
        green: 20,
        yellow: 3,
        red: 40
    },
    high: {
        green: 15,
        yellow: 3,
        red: 45
    },
    severe: {
        green: 10,
        yellow: 3,
        red: 50
    }
};

// Class name mapping for YOLOv5 classes
const classNames = {
    0: 'person',
    1: 'bicycle',
    2: 'car',
    3: 'motorcycle',
    4: 'airplane',
    5: 'bus',
    6: 'train',
    7: 'truck',
    8: 'boat',
    9: 'traffic light',
    10: 'fire hydrant',
    11: 'stop sign',
    12: 'parking meter',
    13: 'bench'
};

// Traffic congestion thresholds
const congestionLevels = {
    low: { max: 5, color: '#2ecc71' },
    moderate: { max: 10, color: '#f1c40f' },
    high: { max: 15, color: '#e74c3c' },
    severe: { max: Infinity, color: '#9b59b6' }
};

// Initialize Chart.js with gradient backgrounds
const ctx = document.getElementById('trafficChart').getContext('2d');

// Create gradients
const totalObjectsGradient = ctx.createLinearGradient(0, 0, 0, 400);
totalObjectsGradient.addColorStop(0, 'rgba(52, 152, 219, 0.25)');
totalObjectsGradient.addColorStop(1, 'rgba(52, 152, 219, 0.02)');

const vehiclesGradient = ctx.createLinearGradient(0, 0, 0, 400);
vehiclesGradient.addColorStop(0, 'rgba(46, 204, 113, 0.25)');
vehiclesGradient.addColorStop(1, 'rgba(46, 204, 113, 0.02)');

const trafficChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: [],
        datasets: [{
            label: 'Total Objects',
            data: [],
            borderColor: '#3498db',
            backgroundColor: totalObjectsGradient,
            tension: 0.4,
            fill: true,
            pointRadius: 0,
            borderWidth: 2,
            cubicInterpolationMode: 'monotone'
        }, {
            label: 'Vehicles',
            data: [],
            borderColor: '#2ecc71',
            backgroundColor: vehiclesGradient,
            tension: 0.4,
            fill: true,
            pointRadius: 0,
            borderWidth: 2,
            cubicInterpolationMode: 'monotone'
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
            intersect: false,
            mode: 'index'
        },
        scales: {
            y: {
                beginAtZero: true,
                grid: {
                    color: 'rgba(255, 255, 255, 0.05)',
                    drawBorder: false,
                    lineWidth: 1
                },
                border: {
                    display: false
                },
                ticks: {
                    color: 'rgba(255, 255, 255, 0.7)',
                    font: {
                        size: 11,
                        family: "'Helvetica Neue', 'Helvetica', 'Arial', sans-serif"
                    },
                    padding: 10,
                    maxTicksLimit: 5
                }
            },
            x: {
                grid: {
                    display: false
                },
                border: {
                    display: false
                },
                ticks: {
                    color: 'rgba(255, 255, 255, 0.7)',
                    font: {
                        size: 11,
                        family: "'Helvetica Neue', 'Helvetica', 'Arial', sans-serif"
                    },
                    maxRotation: 45,
                    minRotation: 45,
                    padding: 10,
                    maxTicksLimit: 8,
                    autoSkip: true
                }
            }
        },
        plugins: {
            legend: {
                labels: {
                    color: 'rgba(255, 255, 255, 0.9)',
                    font: {
                        size: 12,
                        family: "'Helvetica Neue', 'Helvetica', 'Arial', sans-serif",
                        weight: '500'
                    },
                    usePointStyle: true,
                    padding: 20,
                    boxWidth: 8
                }
            },
            tooltip: {
                mode: 'index',
                intersect: false,
                backgroundColor: 'rgba(0, 0, 0, 0.85)',
                titleColor: 'rgba(255, 255, 255, 0.9)',
                bodyColor: 'rgba(255, 255, 255, 0.9)',
                borderColor: 'rgba(255, 255, 255, 0.1)',
                borderWidth: 1,
                padding: 12,
                displayColors: true,
                titleFont: {
                    size: 13,
                    family: "'Helvetica Neue', 'Helvetica', 'Arial', sans-serif",
                    weight: '600'
                },
                bodyFont: {
                    size: 12,
                    family: "'Helvetica Neue', 'Helvetica', 'Arial', sans-serif"
                },
                callbacks: {
                    label: function(context) {
                        let label = context.dataset.label || '';
                        if (label) {
                            label += ': ';
                        }
                        label += context.parsed.y;
                        return label;
                    }
                }
            }
        },
        animations: {
            tension: {
                duration: 750,
                easing: 'easeOutQuart'
            },
            y: {
                duration: 750,
                easing: 'easeOutQuart'
            },
            x: {
                duration: 750,
                easing: 'easeOutQuart'
            }
        },
        transitions: {
            active: {
                animation: {
                    duration: 750
                }
            }
        },
        elements: {
            line: {
                borderCapStyle: 'round',
                borderJoinStyle: 'round'
            }
        }
    }
});

// Traffic Light Control
let currentLight = 'red';
let currentCongestion = 'moderate';
let timeLeft = timings[currentCongestion][currentLight];
let lightInterval;

function updateTrafficLight() {
    // Clear previous active states
    document.querySelectorAll('.light').forEach(light => light.classList.remove('active'));
    document.getElementById(`${currentLight}-light`).classList.add('active');
    
    // Update current light badge
    document.getElementById('current-light').textContent = `${currentLight.charAt(0).toUpperCase() + currentLight.slice(1)} (${timeLeft}s)`;
    
    // Update timers
    document.getElementById(`${currentLight}-timer`).textContent = `${timeLeft}s`;
}

function cycleTrafficLight() {
    timeLeft--;
    
    if (timeLeft <= 0) {
        switch (currentLight) {
            case 'green':
                currentLight = 'yellow';
                timeLeft = timings[currentCongestion].yellow;
                break;
            case 'yellow':
                currentLight = 'red';
                timeLeft = timings[currentCongestion].red;
                break;
            case 'red':
                currentLight = 'green';
                timeLeft = timings[currentCongestion].green;
                break;
        }
    }
    
    updateTrafficLight();
}

function updateTimings(congestion) {
    // Update congestion level
    currentCongestion = congestion;
    
    // Update displayed timings
    ['green', 'yellow', 'red'].forEach(light => {
        const timer = document.getElementById(`${light}-timer`);
        const timerAdjusted = document.getElementById(`${light}-timer-adjusted`);
        
        // Current timing (moderate)
        timer.textContent = `${timings.moderate[light]}s`;
        timer.classList.toggle('active', congestion === 'moderate');
        
        // Adjusted timing (low)
        timerAdjusted.textContent = `${timings.low[light]}s`;
        timerAdjusted.classList.toggle('active', congestion === 'low');
    });
}

// Start traffic light cycle
lightInterval = setInterval(cycleTrafficLight, 1000);
updateTrafficLight();

// Keep track of data
const maxDataPoints = 30;
let vehicleData = [];
let peakTraffic = 0;

// Calculate congestion level
function getCongestionLevel(vehicleCount) {
    if (vehicleCount <= congestionLevels.low.max) return { level: 'low', color: congestionLevels.low.color };
    if (vehicleCount <= congestionLevels.moderate.max) return { level: 'moderate', color: congestionLevels.moderate.color };
    if (vehicleCount <= congestionLevels.high.max) return { level: 'high', color: congestionLevels.high.color };
    return { level: 'severe', color: congestionLevels.severe.color };
}

// Update congestion display
function updateCongestionDisplay(vehicleCount, totalObjects) {
    const congestion = getCongestionLevel(vehicleCount);
    const congestionCard = document.getElementById('congestion-card');
    const congestionLevel = document.getElementById('congestion-level');
    const vehicleCountElement = document.getElementById('vehicle-count');

    // Remove all previous classes
    congestionCard.classList.remove('low', 'moderate', 'high', 'severe');
    // Add current class
    congestionCard.classList.add(congestion.level);

    congestionLevel.textContent = congestion.level.charAt(0).toUpperCase() + congestion.level.slice(1);
    vehicleCountElement.textContent = `${vehicleCount} vehicles (${totalObjects} total objects)`;

    // Update timings based on congestion
    updateTimings(congestion.level);
}

// Socket.IO event handlers
socket.on('connect', () => {
    console.log('Connected to server');
    document.getElementById('status-badge').textContent = 'Connected';
    document.getElementById('status-badge').classList.add('connected');
});

socket.on('disconnect', () => {
    console.log('Disconnected from server');
    document.getElementById('status-badge').textContent = 'Disconnected';
    document.getElementById('status-badge').classList.remove('connected');
});

// Update detection information
socket.on('detection_update', (data) => {
    // Update congestion level and vehicle count
    const congestionElement = document.getElementById('congestion-level');
    const vehicleCountElement = document.getElementById('vehicle-count');
    const congestionCard = document.getElementById('congestion-card');
    
    congestionElement.textContent = data.congestion_level.charAt(0).toUpperCase() + data.congestion_level.slice(1);
    vehicleCountElement.textContent = `${data.vehicle_count} vehicles`;
    
    // Update traffic light timings based on congestion
    updateTimings(data.congestion_level);
    
    // Update congestion card color
    congestionCard.className = 'card stat-card';
    switch (data.congestion_level) {
        case 'low':
            congestionCard.classList.add('bg-success');
            break;
        case 'moderate':
            congestionCard.classList.add('bg-warning');
            break;
        case 'high':
        case 'severe':
            congestionCard.classList.add('bg-danger');
            break;
    }
    
    // Update traffic chart
    const timestamp = new Date(data.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    // Keep last 30 data points for a smoother chart
    if (trafficChart.data.labels.length > 30) {
        trafficChart.data.labels.shift();
        trafficChart.data.datasets[0].data.shift();
        trafficChart.data.datasets[1].data.shift();
    }
    
    trafficChart.data.labels.push(timestamp);
    trafficChart.data.datasets[0].data.push(data.total_objects);
    trafficChart.data.datasets[1].data.push(data.vehicle_count);
    
    // Update chart with animation
    trafficChart.update('active');
});

// Handle incoming detection updates
socket.on('detection_update', function(data) {
    console.log('Received detection update:', data);
    
    // Update detection list
    const detectionList = document.getElementById('detection-list');
    detectionList.innerHTML = ''; // Clear current list

    // Count objects by class
    const counts = {};
    data.detections.forEach(detection => {
        const classId = detection.class;
        counts[classId] = (counts[classId] || 0) + 1;
    });

    // Update detection list with class names and sort by count
    const sortedDetections = Object.entries(counts)
        .sort(([, a], [, b]) => b - a)
        .map(([classId, count]) => {
            const className = classNames[classId] || `class_${classId}`;
            return { className, classId, count };
        });

    sortedDetections.forEach(({ className, classId, count }) => {
        const item = document.createElement('li');
        item.className = 'list-group-item d-flex justify-content-between align-items-center';
        item.innerHTML = `
            <div class="detection-info">
                <span class="detection-name">${className}</span>
                <span class="text-muted">(ID: ${classId})</span>
            </div>
            <span class="badge bg-primary rounded-pill">${count}</span>
        `;
        detectionList.appendChild(item);
    });

    // Calculate total objects and vehicle count
    const totalObjects = data.total_objects;
    const vehicleCount = data.vehicle_count;

    // Update congestion display with both counts
    updateCongestionDisplay(vehicleCount, totalObjects);

    // Update peak traffic if necessary
    if (vehicleCount > peakTraffic) {
        peakTraffic = vehicleCount;
        document.getElementById('peak-traffic').textContent = peakTraffic;
    }

    // Update traffic chart
    const now = new Date();
    const timeLabel = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    trafficChart.data.labels.push(timeLabel);
    trafficChart.data.datasets[0].data.push(totalObjects);
    trafficChart.data.datasets[1].data.push(vehicleCount);
    
    // Keep only last maxDataPoints
    if (trafficChart.data.labels.length > maxDataPoints) {
        trafficChart.data.labels.shift();
        trafficChart.data.datasets[0].data.shift();
        trafficChart.data.datasets[1].data.shift();
    }
    
    trafficChart.update('active');
});

// Clear detection list
document.getElementById('clear-detections').addEventListener('click', () => {
    document.getElementById('detection-list').innerHTML = '';
});

// Update current time
function updateTime() {
    const now = new Date();
    document.getElementById('current-time').textContent = now.toLocaleString();
}

setInterval(updateTime, 1000);
updateTime();
