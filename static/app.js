let temperatureChart;
let comfortChart;

async function loadCurrentData() {
    try {
        const response = await fetch("/api/current");
        const data = await response.json();

        document.getElementById("temperature").innerText = Number(data.temperature).toFixed(1);
        document.getElementById("humidity").innerText = Number(data.humidity).toFixed(1);
        document.getElementById("motion").innerText = data.motion ? "Motion Detected" : "No Motion";
        document.getElementById("sound").innerText = data.sound ? "Noise Detected" : "Quiet";
        document.getElementById("light").innerText = data.light ? "Bright" : "Dark";

        const comfortScore = Number(data.comfort_score || 0);
        document.getElementById("comfort-score").innerText = comfortScore;
        updateComfortChart(comfortScore);

        const warningCard = document.querySelector(".warning-card");
        const warningList = document.getElementById("warning-list");

        warningList.innerHTML = "";

        let warnings = data.recommendations || [];

        if (warnings.length > 0) {
            warningCard.style.display = "block";

            warnings.forEach(warning => {
                const li = document.createElement("li");
                li.textContent = warning;
                warningList.appendChild(li);
            });
        } else {
            warningCard.style.display = "none";
        }

    } catch (error) {
        console.error("Current data error:", error);
    }
}

async function loadHistoryData() {
    try {
        const response = await fetch("/api/history");
        const data = await response.json();

const labels = data.map(item => {

    const nzDate = new Date(item.timestamp);

    const year = nzDate.getFullYear();

    const month = String(
        nzDate.getMonth() + 1
    ).padStart(2, "0");

    const day = String(
        nzDate.getDate()
    ).padStart(2, "0");

    const hours = String(
        nzDate.getHours()
    ).padStart(2, "0");

    const minutes = String(
        nzDate.getMinutes()
    ).padStart(2, "0");

    const seconds = String(
        nzDate.getSeconds()
    ).padStart(2, "0");

    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
});


        const temperatures = data.map(item => item.temperature);

        if (!labels.length || !temperatures.length) return;

        if (temperatureChart) {
            temperatureChart.destroy();
        }

        const ctx = document.getElementById("temperatureChart").getContext("2d");

        temperatureChart = new Chart(ctx, {
            type: "line",
            data: {
                labels: labels,
                datasets: [{
                    label: "Temperature (°C)",
                    data: temperatures,
                    borderColor: "#7ea6ff",
                    backgroundColor: "rgba(126,166,255,0.20)",
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointBackgroundColor: "#dbe7ff"
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: { color: "white" }
                    }
                },
                scales: {
                   x: {
    ticks: {
        color: "#b9c2e3",
        maxRotation: 0,
        minRotation: 0,
        autoSkip: true,
        maxTicksLimit: 6
    },

    grid: {
        color: "rgba(255,255,255,0.08)"
    }
},
                    y: {
                        ticks: { color: "#b9c2e3" },
                        grid: { color: "rgba(255,255,255,0.08)" }
                    }
                }
            }
        });

    } catch (error) {
        console.error("History data error:", error);
    }
}

function createComfortChart() {
    const ctx = document.getElementById("comfortChart").getContext("2d");

    comfortChart = new Chart(ctx, {
        type: "doughnut",
        data: {
            labels: ["Comfort", "Remaining"],
            datasets: [{
                data: [0, 100],
                backgroundColor: ["#557dff", "#1d2b52"],
                borderWidth: 0
            }]
        },
        options: {
            cutout: "72%",
            plugins: {
                legend: { display: false }
            }
        }
    });
}

function updateComfortChart(score) {
    score = Math.max(0, Math.min(100, Number(score)));

    if (!comfortChart) {
        createComfortChart();
    }

    comfortChart.data.datasets[0].data = [score, 100 - score];
    comfortChart.update();
}

async function loadLambdaAnalysis() {
    try {
        const response = await fetch("/api/lambda-analysis");
        const data = await response.json();

        document.getElementById("lambda-status").innerText =
            data.status || "No analysis available.";

        document.getElementById("lambda-recommendation").innerText =
            data.recommendation || "No recommendation available.";

    } catch (error) {
        console.error("Lambda analysis error:", error);

        document.getElementById("lambda-status").innerText = "Error loading analysis.";
        document.getElementById("lambda-recommendation").innerText =
            "Could not connect to AWS Lambda.";
    }
}

async function saveThresholds() {
    const thresholds = {
        light_enabled: document.getElementById("light-enabled").checked,
        sound_enabled: document.getElementById("sound-enabled").checked,
        motion_enabled: document.getElementById("motion-enabled").checked
    };

    const tempMin = document.getElementById("temp-min").value;
    const tempMax = document.getElementById("temp-max").value;
    const humMin = document.getElementById("hum-min").value;
    const humMax = document.getElementById("hum-max").value;

    if (tempMin !== "") {
        thresholds.temp_min = parseFloat(tempMin);
    }

    if (tempMax !== "") {
        thresholds.temp_max = parseFloat(tempMax);
    }

    if (humMin !== "") {
        thresholds.humidity_min = parseFloat(humMin);
    }

    if (humMax !== "") {
        thresholds.humidity_max = parseFloat(humMax);
    }

    try {
        const response = await fetch("/api/thresholds", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(thresholds)
        });

        const result = await response.json();
        const messageBox = document.getElementById("threshold-message");

         if (response.ok) {
             messageBox.innerText = result.message || "Threshold settings saved!";
             messageBox.className = "threshold-message success";
        } else {
              messageBox.innerText = result.error || "Could not save thresholds.";
              messageBox.className = "threshold-message error";
}

    } catch (error) {
        console.error("Threshold save error:", error);
        const messageBox = document.getElementById("threshold-message");
        messageBox.innerText = "Error saving threshold settings.";
        messageBox.className = "threshold-message error";
    }
}

loadCurrentData();
loadHistoryData();
loadLambdaAnalysis();

setInterval(() => {
    loadCurrentData();
    loadHistoryData();
    loadLambdaAnalysis();
}, 5000);