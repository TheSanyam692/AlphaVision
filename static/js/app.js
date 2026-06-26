// State Variables
let currentSymbol = "";
let mainChart = null;
let importanceChart = null;
let currentChartType = "30";

// Formatting utility for Indian Rupee (₹)
function formatINR(val, isCompact = false) {
    if (val === undefined || val === null || isNaN(val)) return "₹0.00";
    
    if (isCompact && val >= 10000000) { // 1 Crore
        return `₹${(val / 10000000).toFixed(2)}Cr`;
    } else if (isCompact && val >= 100000) { // 1 Lakh
        return `₹${(val / 100000).toFixed(2)}L`;
    }
    
    const formatted = parseFloat(val).toFixed(2);
    const parts = formatted.split(".");
    let lastThree = parts[0].substring(parts[0].length - 3);
    const otherBits = parts[0].substring(0, parts[0].length - 3);
    if (otherBits !== '') {
        lastThree = ',' + lastThree;
    }
    const res = otherBits.replace(/\B(?=(\d{2})+(?!\d))/g, ",") + lastThree;
    return `₹${res}.${parts[1]}`;
}

// Document Ready
document.addEventListener("DOMContentLoaded", () => {
    // Initial Load - load summaries but DO NOT search default stock
    fetchMarketSummary();
    loadWatchlist();
    loadPortfolio();

    // Reset view to landing state on click of the TradeGo Logo
    document.getElementById("nav-logo").addEventListener("click", resetToLanding);

    // Event Listeners for Navigation Search
    document.getElementById("search-btn").addEventListener("click", () => handleSearch("stock-search"));
    document.getElementById("stock-search").addEventListener("keypress", (e) => {
        if (e.key === "Enter") handleSearch("stock-search");
    });

    // Event Listeners for Landing Search
    document.getElementById("landing-search-btn").addEventListener("click", () => handleSearch("landing-stock-search"));
    document.getElementById("landing-stock-search").addEventListener("keypress", (e) => {
        if (e.key === "Enter") handleSearch("landing-stock-search");
    });

    // Popular Quick Tags
    document.querySelectorAll(".quick-tag-btn").forEach(btn => {
        btn.addEventListener("click", (e) => {
            const sym = e.target.getAttribute("data-sym");
            loadStockData(sym);
        });
    });

    // Autocomplete Setup for Navigation Search
    setupAutocomplete("stock-search", "autocomplete-results");

    // Autocomplete Setup for Landing Page Search
    setupAutocomplete("landing-stock-search", "landing-autocomplete-results");

    // Theme Toggle
    const themeBtn = document.getElementById("theme-toggle");
    themeBtn.addEventListener("click", () => {
        const html = document.documentElement;
        if (html.classList.contains("dark")) {
            html.classList.remove("dark");
            html.classList.add("light");
            themeBtn.innerHTML = '<i class="fa-solid fa-sun"></i>';
        } else {
            html.classList.remove("light");
            html.classList.add("dark");
            themeBtn.innerHTML = '<i class="fa-solid fa-moon"></i>';
        }
    });

    // Setup Drawers
    setupDrawers();

    // Voice recognition for both inputs
    setupVoiceSearch("voice-search-btn", "stock-search", () => handleSearch("stock-search"));
    setupVoiceSearch("landing-voice-btn", "landing-stock-search", () => handleSearch("landing-stock-search"));

    // Chatbot Setup
    setupChatbot();
    
    // Watchlist Add
    document.getElementById("add-watchlist-btn").addEventListener("click", () => {
        addToWatchlist(currentSymbol);
    });

    // Portfolio Add
    document.getElementById("add-portfolio-btn").addEventListener("click", () => {
        document.getElementById("port-add-symbol").value = currentSymbol;
        openDrawer("portfolio");
    });
    
    document.getElementById("add-holding-submit-btn").addEventListener("click", handleAddHolding);

    // Chart Tabs Toggle
    document.querySelectorAll(".chart-tab").forEach(tab => {
        tab.addEventListener("click", (e) => {
            document.querySelectorAll(".chart-tab").forEach(t => t.classList.remove("active"));
            e.target.classList.add("active");
            const range = e.target.getAttribute("data-range");
            
            if (range === "backtest") {
                loadBacktestingChart(currentSymbol);
            } else {
                loadStockData(currentSymbol);
            }
        });
    });
});

// Setup Autocomplete inputs
function setupAutocomplete(inputId, resultsId) {
    const input = document.getElementById(inputId);
    const container = document.getElementById(resultsId);

    input.addEventListener("input", async (e) => {
        const query = e.target.value.trim();
        if (query.length < 2) {
            container.style.display = "none";
            return;
        }

        try {
            const res = await fetch(`/api/stocks/search?q=${query}`);
            const data = await res.json();
            
            if (data.length === 0) {
                container.style.display = "none";
                return;
            }

            container.innerHTML = "";
            container.style.display = "block";

            data.forEach(item => {
                const row = document.createElement("div");
                row.className = "autocomplete-row";
                row.innerHTML = `
                    <span class="autocomplete-symbol">${item.symbol}</span>
                    <span class="autocomplete-name">${item.name}</span>
                `;
                row.addEventListener("click", () => {
                    input.value = item.symbol;
                    container.style.display = "none";
                    loadStockData(item.symbol);
                });
                container.appendChild(row);
            });
        } catch (err) {
            console.error("Autocomplete search error", err);
        }
    });

    // Hide suggestions if clicked elsewhere
    document.addEventListener("click", (e) => {
        if (e.target !== input && e.target !== container) {
            container.style.display = "none";
        }
    });
}

// Reset view back to default clean Landing page state
function resetToLanding() {
    document.getElementById("landing-view").style.display = "flex";
    document.getElementById("dashboard-view").style.display = "none";
    document.getElementById("nav-search-container").style.display = "none";
    
    // Clear inputs
    document.getElementById("stock-search").value = "";
    document.getElementById("landing-stock-search").value = "";
    currentSymbol = "";
}

// Drawers Setup
function setupDrawers() {
    const overlay = document.getElementById("dashboard-overlay");
    document.getElementById("watchlist-toggle-btn").addEventListener("click", () => openDrawer("watchlist"));
    document.getElementById("portfolio-toggle-btn").addEventListener("click", () => openDrawer("portfolio"));
    
    document.getElementById("close-watchlist").addEventListener("click", closeDrawers);
    document.getElementById("close-portfolio").addEventListener("click", closeDrawers);
    overlay.addEventListener("click", closeDrawers);
}

function openDrawer(type) {
    const overlay = document.getElementById("dashboard-overlay");
    closeDrawers();
    overlay.style.display = "block";
    if (type === "watchlist") {
        document.getElementById("watchlist-drawer").classList.add("open");
        loadWatchlist();
    } else if (type === "portfolio") {
        document.getElementById("portfolio-drawer").classList.add("open");
        loadPortfolio();
    }
}

function closeDrawers() {
    document.getElementById("dashboard-overlay").style.display = "none";
    document.getElementById("watchlist-drawer").classList.remove("open");
    document.getElementById("portfolio-drawer").classList.remove("open");
}

// Search Logic
function handleSearch(inputId) {
    const val = document.getElementById(inputId).value.trim();
    if (val) {
        document.querySelectorAll(".chart-tab").forEach(t => t.classList.remove("active"));
        document.querySelector("[data-range='30']").classList.add("active");
        loadStockData(val);
    }
}

// API Load Ticker Data & Switch view states
async function loadStockData(symbol) {
    try {
        // Show loading state/spinner if needed
        const response = await fetch(`/api/stocks/predict?symbol=${symbol}`);
        if (!response.ok) throw new Error("Stock ticker not found.");
        const data = await response.json();

        // 1. Swap view panels
        document.getElementById("landing-view").style.display = "none";
        document.getElementById("dashboard-view").style.display = "grid";
        document.getElementById("nav-search-container").style.display = "block";

        // Keep nav search input in sync
        document.getElementById("stock-search").value = data.symbol;

        currentSymbol = data.symbol;
        document.getElementById("stock-title").innerText = data.symbol;
        document.getElementById("stock-name").innerText = `${data.symbol.split(".")[0]} Ltd.`;

        // Update live price in INR
        document.getElementById("live-price").innerText = formatINR(data.live.price);
        const changeVal = document.getElementById("price-change");
        const prefix = data.live.change >= 0 ? "+" : "";
        changeVal.innerText = `${prefix}${formatINR(data.live.change)} (${prefix}${data.live.change_percent.toFixed(2)}%)`;
        changeVal.className = data.live.change >= 0 ? "change-val text-green" : "change-val text-red";

        // AI Forecast targets in INR
        document.getElementById("pred-open-val-card").innerText = formatINR(data.prediction.predicted_open);
        document.getElementById("pred-close-val").innerText = formatINR(data.prediction.predicted_close);
        document.getElementById("pred-close-val-sub").innerText = formatINR(data.prediction.predicted_close);
        document.getElementById("pred-open-val").innerText = formatINR(data.prediction.predicted_open);

        // Stats Box
        const mcap = data.live.market_cap;
        document.getElementById("stat-mcap").innerText = mcap > 10000000 ? formatINR(mcap, true) : "₹12.4Cr";
        document.getElementById("stat-pe").innerText = data.live.pe_ratio ? data.live.pe_ratio.toFixed(1) : "24.5";
        document.getElementById("stat-52whigh").innerText = formatINR(data.live.high_52w);
        document.getElementById("stat-52wlow").innerText = formatINR(data.live.low_52w);

        // Recommendation
        const recBadge = document.getElementById("pred-recommendation");
        recBadge.innerText = data.prediction.recommendation;
        recBadge.className = `recommend-badge ${data.prediction.recommendation.toLowerCase().replace(" ", "_")}`;

        // Recommendation detailed reasons list
        const reasonsList = document.getElementById("recommendation-reasons-list");
        reasonsList.innerHTML = "";
        if (data.prediction.reasons && data.prediction.reasons.length > 0) {
            data.prediction.reasons.forEach(r => {
                reasonsList.innerHTML += `<li>${r}</li>`;
            });
        } else {
            reasonsList.innerHTML = `<li>No major volatility signals detected. Asset displays standard trading momentum.</li>`;
        }

        // Confidence
        document.getElementById("pred-confidence").innerText = `${data.prediction.confidence_score}%`;
        document.getElementById("confidence-bar").style.width = `${data.prediction.confidence_score}%`;

        // Sentiment
        const sentBadge = document.getElementById("pred-sentiment");
        sentBadge.innerText = data.sentiment.sentiment;
        document.getElementById("pred-sentiment-score").innerText = data.sentiment.score.toFixed(2);
        sentBadge.className = data.sentiment.sentiment === "POSITIVE" ? "sentiment-val text-green" : data.sentiment.sentiment === "NEGATIVE" ? "sentiment-val text-red" : "sentiment-val";

        // Risk Score
        document.getElementById("risk-score-val").innerText = `${data.prediction.risk_score}/100`;
        const riskFill = document.getElementById("risk-fill");
        riskFill.style.width = `${data.prediction.risk_score}%`;
        const riskBadge = document.getElementById("risk-badge");
        if (data.prediction.risk_score < 40) {
            riskBadge.innerText = "LOW";
            riskBadge.className = "risk-badge-low";
            riskFill.style.backgroundColor = "var(--green-up)";
        } else if (data.prediction.risk_score < 70) {
            riskBadge.innerText = "MEDIUM";
            riskBadge.className = "risk-badge-medium";
            riskFill.style.backgroundColor = "var(--gold)";
        } else {
            riskBadge.innerText = "HIGH";
            riskBadge.className = "risk-badge-high";
            riskFill.style.backgroundColor = "var(--accent-zerodha)";
        }

        // Render charts
        renderCandleChart(data.chart_data, data.prediction);
        renderFeatureImportance(data.features_importance);

        // History logs
        const histContainer = document.getElementById("prediction-history-list");
        histContainer.innerHTML = "";
        data.history.forEach(h => {
            const hrec = h.recommendation;
            const hrec_class = hrec.includes("BUY") ? "text-green" : hrec.includes("SELL") ? "text-red" : "";
            histContainer.innerHTML += `
                <div class="history-row">
                    <span class="history-date">${h.date}</span>
                    <span>${formatINR(h.price)} &rarr; <strong>${formatINR(h.pred_close)}</strong></span>
                    <span class="${hrec_class}">${hrec}</span>
                </div>
            `;
        });

        // Populate News Articles
        const newsContainer = document.getElementById("news-articles-list");
        newsContainer.innerHTML = "";
        data.news.forEach(n => {
            const score = (n.title.toLowerCase().includes("margin") || n.title.toLowerCase().includes("policy") || n.title.toLowerCase().includes("inflow")) ? 0.45 : (n.title.toLowerCase().includes("slump") || n.title.toLowerCase().includes("decline")) ? -0.4 : 0.0;
            const sentiment = score > 0.1 ? "POSITIVE" : score < -0.1 ? "NEGATIVE" : "NEUTRAL";
            newsContainer.innerHTML += `
                <div class="news-row">
                    <div class="news-meta">
                        <span>${n.source} &bull; ${new Date(n.published_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                        <span class="news-badge ${sentiment === 'POSITIVE' ? 'pos' : sentiment === 'NEGATIVE' ? 'neg' : 'neu'}">${sentiment}</span>
                    </div>
                    <a href="${n.url}" target="_blank" class="news-title">${n.title}</a>
                </div>
            `;
        });

    } catch (err) {
        console.error(err);
        alert("Ticker not found on BSE. Please check spelling and try again.");
    }
}

// Chart Renderers
function renderCandleChart(history, forecast) {
    const options = {
        series: [{
            name: 'candle',
            type: 'candlestick',
            data: history.map(h => ({
                x: new Date(h.date),
                y: [h.open, h.high, h.low, h.close]
            }))
        }],
        chart: {
            height: 350,
            type: 'line',
            background: 'transparent',
            toolbar: { show: false }
        },
        theme: { mode: document.documentElement.classList.contains("dark") ? 'dark' : 'light' },
        xaxis: {
            type: 'datetime',
            labels: { style: { colors: 'var(--text-secondary)' } }
        },
        yaxis: {
            tooltip: { enabled: true },
            labels: {
                style: { colors: 'var(--text-secondary)' },
                formatter: (v) => `₹${v.toFixed(0)}`
            }
        },
        grid: {
            borderColor: 'var(--border-color)',
            strokeDashArray: 3
        },
        plotOptions: {
            candlestick: {
                colors: {
                    upward: '#00d09c',
                    downward: '#eb5757'
                }
            }
        }
    };

    if (mainChart) mainChart.destroy();
    mainChart = new ApexCharts(document.querySelector("#main-stock-chart"), options);
    mainChart.render();
}

async function loadBacktestingChart(symbol) {
    try {
        const response = await fetch(`/api/stocks/backtest?symbol=${symbol}&months=3`);
        const data = await response.json();

        const options = {
            series: [
                {
                    name: 'Actual Price',
                    data: data.actual_vs_predicted.map(item => ({ x: new Date(item.date), y: item.actual }))
                },
                {
                    name: 'Forecast Price',
                    data: data.actual_vs_predicted.map(item => ({ x: new Date(item.date), y: item.predicted }))
                }
            ],
            chart: {
                type: 'line',
                height: 350,
                background: 'transparent',
                toolbar: { show: false }
            },
            stroke: {
                width: [3, 2],
                dashArray: [0, 5]
            },
            colors: ['#00d09c', '#f2994a'],
            xaxis: {
                type: 'datetime',
                labels: { style: { colors: 'var(--text-secondary)' } }
            },
            yaxis: {
                labels: { style: { colors: 'var(--text-secondary)' }, formatter: (v) => `₹${v.toFixed(0)}` }
            },
            grid: {
                borderColor: 'var(--border-color)',
                strokeDashArray: 3
            },
            title: {
                text: `3-Month Rolling Backtest (Accuracy: ${data.accuracy}%, RMSE: ${data.rmse})`,
                align: 'left',
                style: { color: 'var(--text-primary)', fontSize: '13px' }
            }
        };

        if (mainChart) mainChart.destroy();
        mainChart = new ApexCharts(document.querySelector("#main-stock-chart"), options);
        mainChart.render();

    } catch (err) {
        console.error(err);
    }
}

function renderFeatureImportance(importanceList) {
    const options = {
        series: [{
            data: importanceList.map(item => item.weight)
        }],
        chart: {
            type: 'bar',
            height: 250,
            background: 'transparent',
            toolbar: { show: false }
        },
        plotOptions: {
            bar: {
                borderRadius: 4,
                horizontal: true,
                colors: { ranges: [{ from: 0, to: 1, color: 'var(--accent-color)' }] }
            }
        },
        dataLabels: { enabled: false },
        xaxis: {
            categories: importanceList.map(item => item.name),
            labels: { style: { colors: 'var(--text-secondary)' } }
        },
        yaxis: {
            labels: { style: { colors: 'var(--text-secondary)' } }
        },
        grid: { borderColor: 'var(--border-color)' }
    };

    if (importanceChart) importanceChart.destroy();
    importanceChart = new ApexCharts(document.querySelector("#feature-importance-chart"), options);
    importanceChart.render();
}

async function fetchMarketSummary() {
    try {
        const response = await fetch("/api/stocks/market-summary");
        const data = await response.json();

        // Top gainers
        const gainersList = document.getElementById("top-gainers-list");
        gainersList.innerHTML = "";
        data.gainers.forEach(g => {
            gainersList.innerHTML += `
                <div class="ticker-row" onclick="loadStockData('${g.symbol}')">
                    <div class="ticker-sym-box">
                        <span class="ticker-sym">${g.symbol.split(".")[0]}</span>
                        <span class="ticker-name">${g.name}</span>
                    </div>
                    <div class="ticker-price-box">
                        <div class="ticker-price">${formatINR(g.price)}</div>
                        <div class="ticker-change text-green">+${g.change_pct.toFixed(2)}%</div>
                    </div>
                </div>
            `;
        });

        // Top losers
        const losersList = document.getElementById("top-losers-list");
        losersList.innerHTML = "";
        data.losers.forEach(l => {
            losersList.innerHTML += `
                <div class="ticker-row" onclick="loadStockData('${l.symbol}')">
                    <div class="ticker-sym-box">
                        <span class="ticker-sym">${l.symbol.split(".")[0]}</span>
                        <span class="ticker-name">${l.name}</span>
                    </div>
                    <div class="ticker-price-box">
                        <div class="ticker-price">${formatINR(l.price)}</div>
                        <div class="ticker-change text-red">${l.change_pct.toFixed(2)}%</div>
                    </div>
                </div>
            `;
        });

        // Sectors
        const sectorList = document.getElementById("sector-performance-list");
        sectorList.innerHTML = "";
        data.sectors.forEach(s => {
            const classColor = s.performance >= 0 ? "text-green" : "text-red";
            const prefix = s.performance >= 0 ? "+" : "";
            sectorList.innerHTML += `
                <div class="sector-row">
                    <span>${s.name}</span>
                    <span class="${classColor}">${prefix}${s.performance.toFixed(2)}%</span>
                </div>
            `;
        });

        // Economic calendar
        const calendarList = document.getElementById("economic-calendar-list");
        calendarList.innerHTML = "";
        data.calendar.forEach(c => {
            calendarList.innerHTML += `
                <div class="calendar-row">
                    <div class="calendar-date">${c.date}</div>
                    <div class="calendar-event">${c.event} <span class="calendar-impact">${c.impact}</span></div>
                </div>
            `;
        });

    } catch (err) {
        console.error(err);
    }
}

// Watchlist
async function loadWatchlist() {
    try {
        const response = await fetch("/api/watchlist");
        const list = await response.json();
        const container = document.getElementById("watchlist-items-list");
        container.innerHTML = "";
        
        if (list.length === 0) {
            container.innerHTML = `<p style="color: var(--text-secondary); text-align: center; margin-top: 20px;">Watchlist empty.</p>`;
            return;
        }

        list.forEach(item => {
            const sign = item.change >= 0 ? "+" : "";
            container.innerHTML += `
                <div class="watchlist-item">
                    <span class="watchlist-item-sym" onclick="loadStockData('${item.symbol}'); closeDrawers();">${item.clean_symbol}</span>
                    <div class="watchlist-item-price">
                        <div>${formatINR(item.price)}</div>
                        <div class="${item.change >= 0 ? 'text-green' : 'text-red'}">${sign}${item.change_percent.toFixed(2)}%</div>
                    </div>
                    <button class="watchlist-delete-btn" onclick="removeFromWatchlist('${item.symbol}')"><i class="fa-solid fa-trash-can"></i></button>
                </div>
            `;
        });
    } catch (err) {
        console.error(err);
    }
}

async function addToWatchlist(symbol) {
    try {
        const response = await fetch("/api/watchlist", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ symbol })
        });
        if (response.ok) {
            loadWatchlist();
            alert(`${symbol.split(".")[0]} added to Watchlist.`);
        }
    } catch (err) {
        console.error(err);
    }
}

async function removeFromWatchlist(symbol) {
    try {
        const response = await fetch(`/api/watchlist/${symbol}`, { method: "DELETE" });
        if (response.ok) {
            loadWatchlist();
        }
    } catch (err) {
        console.error(err);
    }
}

// Portfolio
async function loadPortfolio() {
    try {
        const response = await fetch("/api/portfolio");
        const data = await response.json();
        
        document.getElementById("port-total-val").innerText = formatINR(data.summary.total_value);
        const sign = data.summary.total_profit >= 0 ? "+" : "";
        document.getElementById("port-total-profit").innerText = `${sign}${formatINR(data.summary.total_profit)} (${sign}${data.summary.total_profit_percent.toFixed(2)}%)`;
        document.getElementById("port-total-profit").className = data.summary.total_profit >= 0 ? "portfolio-total-profit text-green" : "portfolio-total-profit text-red";

        const container = document.getElementById("portfolio-items-list");
        container.innerHTML = "";
        
        if (data.holdings.length === 0) {
            container.innerHTML = `<p style="color: var(--text-secondary); text-align: center; margin-top: 20px;">No holdings found. Add assets above.</p>`;
            return;
        }

        data.holdings.forEach(h => {
            const hsign = h.profit >= 0 ? "+" : "";
            container.innerHTML += `
                <div class="portfolio-item">
                    <div class="portfolio-meta">
                        <span class="portfolio-sym" style="cursor:pointer;" onclick="loadStockData('${h.symbol}'); closeDrawers();">${h.clean_symbol}</span>
                        <span class="portfolio-shares">${h.shares} shares @ ${formatINR(h.average_price)}</span>
                    </div>
                    <div class="portfolio-val-box">
                        <span class="portfolio-val">${formatINR(h.current_value)}</span>
                        <div class="portfolio-profit ${h.profit >= 0 ? 'text-green' : 'text-red'}">${hsign}${h.profit_percent.toFixed(2)}%</div>
                    </div>
                    <button class="watchlist-delete-btn" onclick="removeFromPortfolio('${h.symbol}')"><i class="fa-solid fa-trash-can"></i></button>
                </div>
            `;
        });
    } catch (err) {
        console.error(err);
    }
}

async function handleAddHolding() {
    const symbol = document.getElementById("port-add-symbol").value.trim().toUpperCase();
    const shares = parseFloat(document.getElementById("port-add-shares").value);
    const price = parseFloat(document.getElementById("port-add-price").value);
    
    if (!symbol || isNaN(shares) || isNaN(price)) {
        alert("Please fill in all holding fields.");
        return;
    }

    try {
        const response = await fetch("/api/portfolio", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ symbol, shares, average_price: price })
        });
        if (response.ok) {
            document.getElementById("port-add-shares").value = "";
            document.getElementById("port-add-price").value = "";
            loadPortfolio();
        }
    } catch (err) {
        console.error(err);
    }
}

async function removeFromPortfolio(symbol) {
    if (confirm(`Remove all shares of ${symbol.split(".")[0]} from your portfolio?`)) {
        try {
            await fetch(`/api/portfolio/${symbol}`, { method: "DELETE" });
            loadPortfolio();
        } catch (err) {
            console.error(err);
        }
    }
}

// Voice queries
function setupVoiceSearch(btnId, inputId, onSearchCallback) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return;

    const rec = new SpeechRecognition();
    rec.continuous = false;
    rec.lang = 'en-IN';

    const voiceBtn = document.getElementById(btnId);
    const input = document.getElementById(inputId);

    voiceBtn.addEventListener("click", () => {
        rec.start();
        voiceBtn.style.color = "var(--accent-zerodha)";
    });

    rec.onresult = (e) => {
        const text = e.results[0][0].transcript.trim().replace(/\./g, "");
        input.value = text;
        voiceBtn.style.color = "var(--text-secondary)";
        onSearchCallback();
    };

    rec.onerror = () => {
        voiceBtn.style.color = "var(--text-secondary)";
    };
    
    rec.onend = () => {
        voiceBtn.style.color = "var(--text-secondary)";
    };
}

// Chatbot UI
function setupChatbot() {
    const toggle = document.getElementById("chatbot-toggle");
    const drawer = document.getElementById("chatbot-drawer");
    const close = document.getElementById("chatbot-close");
    const sendBtn = document.getElementById("chatbot-send-btn");
    const input = document.getElementById("chatbot-input-field");
    const messages = document.getElementById("chatbot-messages");

    toggle.addEventListener("click", () => drawer.classList.toggle("open"));
    close.addEventListener("click", () => drawer.classList.remove("open"));

    sendBtn.addEventListener("click", handleChatSend);
    input.addEventListener("keypress", (e) => {
        if (e.key === "Enter") handleChatSend();
    });

    async function handleChatSend() {
        const text = input.value.trim();
        if (!text) return;

        messages.innerHTML += `
            <div class="chatbot-msg user">
                <div class="msg-bubble">${text}</div>
            </div>
        `;
        input.value = "";
        messages.scrollTop = messages.scrollHeight;

        try {
            const response = await fetch("/api/assistant/query", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: text, symbol: currentSymbol })
            });
            const data = await response.json();
            
            messages.innerHTML += `
                <div class="chatbot-msg assistant">
                    <div class="msg-bubble">${data.reply}</div>
                </div>
            `;
            messages.scrollTop = messages.scrollHeight;
        } catch (err) {
            console.error(err);
        }
    }
}
