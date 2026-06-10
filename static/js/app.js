/**
 * app.js — EcoTrace India
 * Frontend logic: calculator form, API calls, chart rendering, localStorage.
 */

// ============================================================
// Emission factors (client-side for real-time running total)
// Must match data/emission_factors.json exactly
// ============================================================

const EMISSION_FACTORS = {
  energy: {
    electricity_kwh: 0.75,
    lpg_per_cylinder: 37.68,
  },
  transport: {
    petrol_car_per_km: 0.171,
    two_wheeler_per_km: 0.089,
    train_per_km: 0.011,
    domestic_flight_per_km: 0.255,
  },
  diet: {
    vegan: 1500,
    vegetarian: 1700,
    non_vegetarian: 2500,
    heavy_meat: 3300,
  },
  waste: {
    landfill_per_kg: 0.5,
    recycled_reduction: 0.3,
    composting_reduction: 0.4,
  },
};

// ============================================================
// Utility helpers
// ============================================================

function $(selector) {
  return document.querySelector(selector);
}
function $$(selector) {
  return document.querySelectorAll(selector);
}

/** Animate a number counting up from 0 to target */
function animateCounter(element, target, duration = 1500, suffix = '') {
  const start = performance.now();
  const startVal = 0;
  function tick(now) {
    const elapsed = now - start;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
    const current = startVal + (target - startVal) * eased;
    element.textContent = current.toFixed(2) + suffix;
    if (progress < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

/** Show a toast notification */
function showToast(message, duration = 3000) {
  let toast = document.getElementById('toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'toast';
    toast.className = 'toast';
    document.body.appendChild(toast);
  }
  toast.textContent = message;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), duration);
}

// ============================================================
// Mobile nav toggle
// ============================================================

document.addEventListener('DOMContentLoaded', () => {
  const toggle = document.getElementById('nav-toggle');
  const nav = document.getElementById('navbar-nav');
  if (toggle && nav) {
    toggle.addEventListener('click', () => {
      nav.classList.toggle('open');
    });
  }
});

// ============================================================
// Calculator — Multi-step form
// ============================================================

let currentStep = 1;
const totalSteps = 4;

/** Get all form values as an object */
function getFormData() {
  return {
    electricity_kwh: parseFloat($('#electricity_kwh')?.value) || 0,
    lpg_cylinders: parseFloat($('#lpg_cylinders')?.value) || 0,
    petrol_car_km: parseFloat($('#petrol_car_km')?.value) || 0,
    two_wheeler_km: parseFloat($('#two_wheeler_km')?.value) || 0,
    train_km: parseFloat($('#train_km')?.value) || 0,
    flight_km: parseFloat($('#flight_km')?.value) || 0,
    diet_type: document.querySelector('input[name="diet_type"]:checked')?.value || 'vegetarian',
    waste_kg: parseFloat($('#waste_kg')?.value) || 0,
    recycles: $('#recycles')?.checked || false,
    composts: $('#composts')?.checked || false,
    city_tier: $('#city_tier')?.value || 'metro',
    language: 'English',
  };
}

/** Calculate running total client-side (same formula as calculator.py) */
function calculateRunningTotal() {
  const data = getFormData();
  const ef = EMISSION_FACTORS;

  const energy = (
    (data.electricity_kwh * 12 * ef.energy.electricity_kwh) +
    (data.lpg_cylinders * 12 * ef.energy.lpg_per_cylinder)
  ) / 1000;

  const transport = (
    (data.petrol_car_km * ef.transport.petrol_car_per_km * 12) +
    (data.two_wheeler_km * ef.transport.two_wheeler_per_km * 12) +
    (data.train_km * ef.transport.train_per_km * 12) +
    (data.flight_km * ef.transport.domestic_flight_per_km * 12)
  ) / 1000;

  const diet = (ef.diet[data.diet_type] || ef.diet.vegetarian) / 1000;

  let waste = (data.waste_kg * 12 * ef.waste.landfill_per_kg) / 1000;
  if (data.recycles) waste *= (1 - ef.waste.recycled_reduction);
  if (data.composts) waste *= (1 - ef.waste.composting_reduction);

  return energy + transport + diet + waste;
}

/** Update the running total display */
function updateRunningTotal() {
  const totalEl = document.getElementById('running-total-value');
  if (totalEl) {
    const total = calculateRunningTotal();
    totalEl.textContent = total.toFixed(2);
  }
}

/** Navigate to a specific step */
function goToStep(step) {
  if (step < 1 || step > totalSteps) return;
  currentStep = step;

  // Update step visibility
  $$('.form-step').forEach((el, i) => {
    el.classList.toggle('active', i + 1 === step);
  });

  // Update step indicators
  $$('.step-indicator').forEach((el, i) => {
    el.classList.remove('active', 'completed');
    if (i + 1 === step) el.classList.add('active');
    else if (i + 1 < step) el.classList.add('completed');
  });

  // Update progress bar
  const progressFill = $('.progress-fill');
  if (progressFill) {
    progressFill.style.width = `${(step / totalSteps) * 100}%`;
  }

  // Update nav buttons
  const prevBtn = document.getElementById('btn-prev');
  const nextBtn = document.getElementById('btn-next');
  const calcBtn = document.getElementById('btn-calculate');

  if (prevBtn) prevBtn.style.display = step === 1 ? 'none' : 'inline-flex';
  if (nextBtn) nextBtn.style.display = step === totalSteps ? 'none' : 'inline-flex';
  if (calcBtn) calcBtn.style.display = step === totalSteps ? 'inline-flex' : 'none';

  updateRunningTotal();
}

/** Initialize calculator event listeners */
function initCalculator() {
  const form = document.getElementById('calculator-form');
  if (!form) return;

  // Nav buttons
  document.getElementById('btn-next')?.addEventListener('click', () => goToStep(currentStep + 1));
  document.getElementById('btn-prev')?.addEventListener('click', () => goToStep(currentStep - 1));

  // Real-time running total on all inputs
  form.querySelectorAll('input, select').forEach(input => {
    input.addEventListener('input', updateRunningTotal);
    input.addEventListener('change', updateRunningTotal);
  });

  // Calculate button
  document.getElementById('btn-calculate')?.addEventListener('click', submitCalculation);

  // Initialize first step
  goToStep(1);
}

/** Submit calculation to backend */
async function submitCalculation() {
  const calcBtn = document.getElementById('btn-calculate');
  if (calcBtn) {
    calcBtn.disabled = true;
    calcBtn.innerHTML = '<span class="loading-spinner"></span> Calculating...';
  }

  const data = getFormData();

  try {
    const response = await fetch('/api/calculate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.error || 'Calculation failed');
    }

    const result = await response.json();

    // Store result in localStorage for the results page
    localStorage.setItem('ecotrace_result', JSON.stringify(result));
    localStorage.setItem('ecotrace_form_data', JSON.stringify(data));

    // Navigate to results
    window.location.href = '/results';
  } catch (error) {
    showToast('❌ ' + error.message);
    if (calcBtn) {
      calcBtn.disabled = false;
      calcBtn.innerHTML = '🌍 Calculate My Footprint';
    }
  }
}

// ============================================================
// Results page
// ============================================================

function initResults() {
  const container = document.getElementById('results-container');
  if (!container) return;

  const stored = localStorage.getItem('ecotrace_result');
  if (!stored) {
    window.location.href = '/calculator';
    return;
  }

  const result = JSON.parse(stored);
  renderResults(result);
  fetchInsights(result);

  const btnShare = document.getElementById('btn-share-badge');
  if (btnShare) {
    btnShare.addEventListener('click', () => shareScore(result));
  }
}

/** Share the user's score */
function shareScore(result) {
  const grade = result.eco_score.grade;
  const tonnes = result.total.toFixed(2);
  const text = `🌱 I just checked my carbon footprint on EcoTrace India!\n\nMy Eco Score: ${grade}\nMy Footprint: ${tonnes} tonnes CO₂e/year.\n\nFind out your score and get an AI action plan at EcoTrace India! 🌍`;
  
  if (navigator.share) {
    navigator.share({
      title: 'My EcoTrace Score',
      text: text,
    }).catch(console.error);
  } else {
    navigator.clipboard.writeText(text).then(() => {
      showToast('✅ Score copied to clipboard!');
    }).catch(() => {
      alert('Could not copy to clipboard. Please copy manually:\n\n' + text);
    });
  }
}

/** Render all result sections */
function renderResults(result) {
  // Eco Score Badge
  renderEcoScore(result.eco_score);

  // Total footprint with counter animation
  const totalEl = document.getElementById('footprint-number');
  if (totalEl) {
    animateCounter(totalEl, result.total, 1500);
  }

  // Benchmark comparison
  renderBenchmarks(result);

  // Category breakdown
  renderBreakdown(result.breakdown, result.total);

  // Tree offset
  renderTreeOffset(result.tree_offset);
}

/** Render the eco score badge */
function renderEcoScore(ecoScore) {
  const gradeEl = document.getElementById('eco-grade');
  const labelEl = document.getElementById('eco-label');
  const circleEl = document.getElementById('eco-circle');

  if (gradeEl) gradeEl.textContent = ecoScore.grade;
  if (labelEl) labelEl.textContent = ecoScore.label;
  if (circleEl) circleEl.style.color = ecoScore.color;

  // Confetti for A+ or A
  if (ecoScore.grade === 'A+' || ecoScore.grade === 'A') {
    triggerConfetti();
  }
}

/** Simple confetti effect */
function triggerConfetti() {
  const canvas = document.getElementById('confetti-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;

  const particles = [];
  const colors = ['#00C853', '#43A047', '#FDD835', '#FF9933', '#1976D2', '#E53935'];

  for (let i = 0; i < 120; i++) {
    particles.push({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height - canvas.height,
      w: Math.random() * 8 + 4,
      h: Math.random() * 6 + 3,
      color: colors[Math.floor(Math.random() * colors.length)],
      vy: Math.random() * 3 + 2,
      vx: (Math.random() - 0.5) * 2,
      rot: Math.random() * 360,
      rv: (Math.random() - 0.5) * 8,
    });
  }

  let frame = 0;
  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    let alive = false;
    particles.forEach(p => {
      if (p.y < canvas.height + 20) {
        alive = true;
        p.y += p.vy;
        p.x += p.vx;
        p.rot += p.rv;
        ctx.save();
        ctx.translate(p.x, p.y);
        ctx.rotate((p.rot * Math.PI) / 180);
        ctx.fillStyle = p.color;
        ctx.fillRect(-p.w / 2, -p.h / 2, p.w, p.h);
        ctx.restore();
      }
    });
    frame++;
    if (alive && frame < 300) requestAnimationFrame(draw);
    else ctx.clearRect(0, 0, canvas.width, canvas.height);
  }
  requestAnimationFrame(draw);
}

/** Render benchmark comparison bars */
function renderBenchmarks(result) {
  const container = document.getElementById('benchmark-bars');
  if (!container) return;

  const benchmarks = result.benchmarks;
  const userTotal = result.total;

  // Find max value for scaling
  const maxVal = Math.max(userTotal, benchmarks.india_urban, benchmarks.global, 8);

  const items = [
    { label: '🇮🇳 You', value: userTotal, isUser: true },
    { label: 'India National', value: benchmarks.india_national },
    { label: 'India Urban', value: benchmarks.india_urban },
    { label: '🌍 Global', value: benchmarks.global },
    { label: '🎯 2050 Target', value: benchmarks.target_2050 },
  ];

  container.innerHTML = items.map(item => {
    const width = (item.value / maxVal) * 100;
    const color = getScoreColor(item.value);
    return `
      <div class="benchmark-item ${item.isUser ? 'user-benchmark' : ''}">
        <span class="benchmark-label">${item.label}</span>
        <div class="benchmark-track">
          <div class="benchmark-fill" style="width: ${width}%; background: ${color};"></div>
        </div>
        <span class="benchmark-value" style="color: ${color}">${item.value.toFixed(1)}t</span>
      </div>
    `;
  }).join('');
}

/** Get color based on footprint value */
function getScoreColor(value) {
  if (value <= 2.0) return '#00C853';
  if (value <= 3.5) return '#43A047';
  if (value <= 5.0) return '#FDD835';
  if (value <= 7.0) return '#FB8C00';
  return '#E53935';
}

/** Render category breakdown stacked bar + legend */
function renderBreakdown(breakdown, total) {
  const barContainer = document.getElementById('stacked-bar');
  const legendContainer = document.getElementById('breakdown-legend');
  if (!barContainer) return;

  const categories = [
    { key: 'energy', label: 'Energy', color: 'var(--cat-energy)', icon: '⚡' },
    { key: 'transport', label: 'Transport', color: 'var(--cat-transport)', icon: '🚗' },
    { key: 'diet', label: 'Diet', color: 'var(--cat-diet)', icon: '🍽️' },
    { key: 'waste', label: 'Waste', color: 'var(--cat-waste)', icon: '🗑️' },
  ];

  barContainer.innerHTML = categories.map(cat => {
    const value = breakdown[cat.key];
    const pct = total > 0 ? (value / total) * 100 : 0;
    return `
      <div class="stacked-bar-segment" data-category="${cat.key}"
           style="width: ${pct}%"
           title="${cat.label}: ${value.toFixed(2)}t (${pct.toFixed(0)}%)">
        ${pct > 10 ? pct.toFixed(0) + '%' : ''}
      </div>
    `;
  }).join('');

  if (legendContainer) {
    legendContainer.innerHTML = categories.map(cat => {
      const value = breakdown[cat.key];
      const pct = total > 0 ? ((value / total) * 100).toFixed(0) : 0;
      return `
        <div class="legend-item">
          <span class="legend-dot" style="background: ${cat.color}"></span>
          ${cat.icon} ${cat.label}: ${value.toFixed(2)}t (${pct}%)
        </div>
      `;
    }).join('');
  }

  // Also render Chart.js doughnut if canvas exists
  renderDoughnutChart(breakdown);
}

/** Render a Chart.js doughnut chart */
function renderDoughnutChart(breakdown) {
  const canvas = document.getElementById('breakdown-chart');
  if (!canvas || typeof Chart === 'undefined') return;

  new Chart(canvas, {
    type: 'doughnut',
    data: {
      labels: ['Energy', 'Transport', 'Diet', 'Waste'],
      datasets: [{
        data: [breakdown.energy, breakdown.transport, breakdown.diet, breakdown.waste],
        backgroundColor: ['#1976D2', '#F57C00', '#388E3C', '#757575'],
        borderColor: '#152416',
        borderWidth: 3,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: {
          display: false,
        },
        tooltip: {
          callbacks: {
            label: (context) => {
              const val = context.parsed;
              return ` ${context.label}: ${val.toFixed(2)} tonnes`;
            },
          },
        },
      },
      cutout: '65%',
    },
  });
}

/** Render tree offset cards */
function renderTreeOffset(treeOffset) {
  const treesEl = document.getElementById('offset-trees');
  const carEl = document.getElementById('offset-car');
  const solarEl = document.getElementById('offset-solar');

  if (treesEl) treesEl.textContent = treeOffset.trees_needed.toLocaleString();
  if (carEl) carEl.textContent = treeOffset.equivalent_car_km.toLocaleString();
  if (solarEl) solarEl.textContent = treeOffset.solar_panels_kw;
}

/** Fetch AI insights from /api/insights */
async function fetchInsights(result) {
  const container = document.getElementById('insights-container');
  if (!container) return;

  // Show loading
  container.innerHTML = `
    <div class="insights-loading">
      <span class="loading-spinner"></span>
      <p>EcoBot is analyzing your footprint...</p>
    </div>
  `;

  try {
    const response = await fetch('/api/insights', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(result),
    });

    if (!response.ok) throw new Error('Failed to get insights');

    const data = await response.json();
    renderInsights(data);
  } catch (error) {
    container.innerHTML = `
      <div class="error-message">
        Unable to load AI insights. Please refresh the page to try again.
      </div>
    `;
  }
}

/** Render the 3 insight cards */
function renderInsights(data) {
  const container = document.getElementById('insights-container');
  if (!container || !data.insights) return;

  const cardsHtml = data.insights.map(insight => `
    <div class="insight-card" data-category="${insight.category}">
      <div class="insight-header">
        <span class="insight-category">${insight.category}</span>
        <span class="difficulty-badge difficulty-${insight.difficulty}">${insight.difficulty}</span>
      </div>
      <p class="insight-tip">${insight.tip}</p>
      <div class="insight-savings">
        🌱 Saves ~${insight.co2_saved_kg} kg CO₂/year
      </div>
      ${insight.india_context ? `<p class="insight-context">🇮🇳 ${insight.india_context}</p>` : ''}
    </div>
  `).join('');

  container.innerHTML = `<div class="insights-grid">${cardsHtml}</div>`;

  // Motivational message
  if (data.motivational_message) {
    const msgEl = document.getElementById('motivational-message');
    if (msgEl) {
      msgEl.textContent = data.motivational_message;
      msgEl.style.display = 'block';
    }
  }

  // Populate top tip in Eco Badge
  if (data.insights && data.insights.length > 0) {
    const topTipEl = document.getElementById('badge-top-tip');
    if (topTipEl) {
      topTipEl.textContent = `💡 Top Tip: ${data.insights[0].tip}`;
    }
  }
}

// ============================================================
// 30-Day Action Plan
// ============================================================

function initActionPlan() {
  const container = document.getElementById('action-plan-container');
  if (!container) return;

  const stored = localStorage.getItem('ecotrace_result');
  const generateBtn = document.getElementById('btn-generate-plan');
  const calculateBtn = document.getElementById('btn-calculate-first');
  const statusText = document.getElementById('action-plan-status-text');

  if (stored) {
    // User has a result — show Generate button
    if (generateBtn) generateBtn.style.display = 'inline-flex';
    if (calculateBtn) calculateBtn.style.display = 'none';
    if (statusText) statusText.textContent = 'Your footprint data is ready. Click below to generate your personalized 30-day plan!';

    generateBtn?.addEventListener('click', () => fetchActionPlan(JSON.parse(stored)));
  }

  // Copy plan button
  document.getElementById('btn-copy-plan')?.addEventListener('click', copyActionPlan);
}

/** Fetch action plan from /api/action-plan */
async function fetchActionPlan(result) {
  const emptyEl = document.getElementById('action-plan-empty');
  const loadingEl = document.getElementById('action-plan-loading');
  const contentEl = document.getElementById('action-plan-content');

  if (emptyEl) emptyEl.style.display = 'none';
  if (loadingEl) loadingEl.style.display = 'block';

  try {
    const response = await fetch('/api/action-plan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(result),
    });

    if (!response.ok) throw new Error('Failed to generate plan');

    const plan = await response.json();
    localStorage.setItem('ecotrace_action_plan', JSON.stringify(plan));
    renderActionPlan(plan);
  } catch (error) {
    if (loadingEl) loadingEl.style.display = 'none';
    if (emptyEl) emptyEl.style.display = 'block';
    showToast('❌ Failed to generate action plan. Please try again.');
  }
}

/** Render the 4-week action plan */
function renderActionPlan(plan) {
  const loadingEl = document.getElementById('action-plan-loading');
  const contentEl = document.getElementById('action-plan-content');
  const savingBanner = document.getElementById('saving-banner');
  const ctasEl = document.getElementById('action-plan-ctas');

  if (loadingEl) loadingEl.style.display = 'none';
  if (contentEl) contentEl.style.display = 'block';
  if (ctasEl) ctasEl.style.display = 'flex';

  // Saving banner
  if (savingBanner && plan.estimated_annual_saving_tonnes) {
    document.getElementById('saving-amount').textContent = plan.estimated_annual_saving_tonnes;
    savingBanner.style.display = 'flex';
  }

  // Build accordion
  const weekIcons = ['🚀', '🔧', '🍃', '🏆'];
  const weeksHtml = (plan.weeks || []).map((week, idx) => {
    const actionsHtml = (week.actions || []).map(action => `
      <div class="action-item">
        <div class="action-day">${action.day_range}</div>
        <div class="action-details">
          <p class="action-text">${action.action}</p>
          <div class="action-meta">
            <span class="action-impact">🌱 ${action.impact}</span>
            <span class="action-time">⏱️ ${action.time_needed}</span>
          </div>
        </div>
      </div>
    `).join('');

    return `
      <div class="accordion-card ${idx === 0 ? 'open' : ''}">
        <button class="accordion-header" aria-expanded="${idx === 0}" data-week="${week.week}">
          <span class="accordion-icon">${weekIcons[idx] || '📋'}</span>
          <span class="accordion-title">Week ${week.week}: ${week.theme}</span>
          <span class="accordion-chevron">▾</span>
        </button>
        <div class="accordion-body" ${idx === 0 ? '' : 'style="display: none;"'}>
          ${actionsHtml}
        </div>
      </div>
    `;
  }).join('');

  contentEl.innerHTML = weeksHtml;

  // Accordion toggle listeners
  contentEl.querySelectorAll('.accordion-header').forEach(header => {
    header.addEventListener('click', () => {
      const card = header.parentElement;
      const body = card.querySelector('.accordion-body');
      const isOpen = card.classList.contains('open');

      card.classList.toggle('open');
      header.setAttribute('aria-expanded', !isOpen);
      body.style.display = isOpen ? 'none' : 'block';
    });
  });
}

/** Copy action plan text to clipboard */
function copyActionPlan() {
  const plan = JSON.parse(localStorage.getItem('ecotrace_action_plan') || '{}');
  if (!plan.weeks) return;

  let text = '🌱 My 30-Day Eco Action Plan — EcoTrace India\n\n';
  if (plan.estimated_annual_saving_tonnes) {
    text += `Estimated annual saving: ${plan.estimated_annual_saving_tonnes} tonnes CO₂e\n\n`;
  }

  plan.weeks.forEach(week => {
    text += `=== Week ${week.week}: ${week.theme} ===\n`;
    week.actions.forEach(action => {
      text += `${action.day_range}: ${action.action}\n  Impact: ${action.impact} | Time: ${action.time_needed}\n`;
    });
    text += '\n';
  });

  text += 'Generated by EcoTrace India — ecotrace-india.onrender.com';

  navigator.clipboard.writeText(text).then(() => {
    showToast('✅ Plan copied to clipboard!');
  }).catch(() => {
    showToast('❌ Could not copy. Try selecting the text manually.');
  });
}

// ============================================================
// AI Chat
// ============================================================

let chatHistory = [];

function initChat() {
  const container = document.getElementById('chat-container');
  if (!container) return;

  const form = document.getElementById('chat-form');
  const input = document.getElementById('chat-input');

  form?.addEventListener('submit', (e) => {
    e.preventDefault();
    const message = input.value.trim();
    if (message) {
      sendChatMessage(message);
      input.value = '';
    }
  });

  // Suggestion chips
  document.querySelectorAll('.suggestion-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      const message = chip.dataset.message;
      if (message) {
        sendChatMessage(message);
        // Hide suggestions after first click
        const suggestionsEl = document.getElementById('chat-suggestions');
        if (suggestionsEl) suggestionsEl.style.display = 'none';
      }
    });
  });
}

/** Send a message to /api/chat */
async function sendChatMessage(message) {
  const messagesEl = document.getElementById('chat-messages');
  const sendBtn = document.getElementById('chat-send-btn');

  // Render user message
  renderChatMessage('user', message);
  chatHistory.push({ role: 'user', text: message });

  // Show typing indicator
  const typingId = 'typing-' + Date.now();
  messagesEl.insertAdjacentHTML('beforeend', `
    <div class="chat-message bot-message" id="${typingId}">
      <div class="message-avatar">🌱</div>
      <div class="message-bubble typing-indicator">
        <span></span><span></span><span></span>
      </div>
    </div>
  `);
  messagesEl.scrollTop = messagesEl.scrollHeight;

  if (sendBtn) sendBtn.disabled = true;

  // Get footprint data for context
  const footprintData = JSON.parse(localStorage.getItem('ecotrace_result') || 'null');

  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: message,
        chat_history: chatHistory.slice(-10),
        footprint_data: footprintData,
        language: 'English',
      }),
    });

    // Remove typing indicator
    document.getElementById(typingId)?.remove();

    if (!response.ok) throw new Error('Failed to get response');

    const data = await response.json();
    renderChatMessage('bot', data.response);
    chatHistory.push({ role: 'bot', text: data.response });
  } catch (error) {
    document.getElementById(typingId)?.remove();
    renderChatMessage('bot', "I'm having trouble connecting. Please try again in a moment! 🌱");
  }

  if (sendBtn) sendBtn.disabled = false;
  document.getElementById('chat-input')?.focus();
}

/** Render a chat message bubble */
function renderChatMessage(role, text) {
  const messagesEl = document.getElementById('chat-messages');
  if (!messagesEl) return;

  const isBot = role === 'bot';
  const avatar = isBot ? '🌱' : '👤';
  const className = isBot ? 'bot-message' : 'user-message';

  // Simple markdown-ish formatting for bot messages
  let formattedText = text;
  if (isBot) {
    formattedText = text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n/g, '<br>');
  }

  const messageHtml = `
    <div class="chat-message ${className}">
      <div class="message-avatar">${avatar}</div>
      <div class="message-bubble">${formattedText}</div>
    </div>
  `;

  messagesEl.insertAdjacentHTML('beforeend', messageHtml);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

// ============================================================
// Monthly Progress Tracker
// ============================================================

function initTracker() {
  const container = document.getElementById('tracker-container');
  if (!container) return;

  const history = JSON.parse(localStorage.getItem('ecotrace_history') || '[]');

  if (history.length === 0) {
    document.getElementById('tracker-empty').style.display = 'block';
    document.getElementById('tracker-content').style.display = 'none';
    return;
  }

  document.getElementById('tracker-empty').style.display = 'none';
  document.getElementById('tracker-content').style.display = 'block';

  renderTrackerChange(history);
  renderTrackerChart(history);
  renderTrackerTable(history);

  // Clear history button
  document.getElementById('btn-clear-history')?.addEventListener('click', () => {
    if (confirm('Are you sure you want to clear all tracker history?')) {
      localStorage.removeItem('ecotrace_history');
      window.location.reload();
    }
  });
}

/** Render month-over-month change banner */
function renderTrackerChange(history) {
  const bannerEl = document.getElementById('tracker-change-banner');
  const iconEl = document.getElementById('change-icon');
  const textEl = document.getElementById('change-text');
  if (!bannerEl || history.length < 2) {
    if (textEl) textEl.textContent = `You have ${history.length} month(s) logged. Keep tracking to see your trend!`;
    return;
  }

  const current = history[history.length - 1];
  const previous = history[history.length - 2];
  const change = current.total - previous.total;
  const changePct = previous.total > 0 ? ((change / previous.total) * 100).toFixed(1) : 0;

  if (change < 0) {
    if (iconEl) iconEl.textContent = '🎉';
    if (textEl) textEl.innerHTML = `Down <strong>${Math.abs(changePct)}%</strong> from last month! Your footprint decreased from ${previous.total.toFixed(2)}t to ${current.total.toFixed(2)}t.`;
    bannerEl.className = 'tracker-change-banner change-improved';
  } else if (change > 0) {
    if (iconEl) iconEl.textContent = '📈';
    if (textEl) textEl.innerHTML = `Up <strong>${changePct}%</strong> from last month. Your footprint went from ${previous.total.toFixed(2)}t to ${current.total.toFixed(2)}t.`;
    bannerEl.className = 'tracker-change-banner change-increased';
  } else {
    if (iconEl) iconEl.textContent = '➡️';
    if (textEl) textEl.textContent = `Steady at ${current.total.toFixed(2)} tonnes — same as last month.`;
  }
}

/** Render Chart.js line chart */
function renderTrackerChart(history) {
  const canvas = document.getElementById('tracker-chart');
  if (!canvas || typeof Chart === 'undefined') return;

  const labels = history.map(e => {
    const [year, month] = e.month.split('-');
    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return `${monthNames[parseInt(month) - 1]} ${year}`;
  });

  new Chart(canvas, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Total Footprint (tonnes)',
          data: history.map(e => e.total),
          borderColor: '#43A047',
          backgroundColor: 'rgba(67, 160, 71, 0.1)',
          borderWidth: 3,
          fill: true,
          tension: 0.3,
          pointBackgroundColor: '#00C853',
          pointBorderColor: '#152416',
          pointBorderWidth: 2,
          pointRadius: 6,
          pointHoverRadius: 8,
        },
        {
          label: 'India Urban Avg (5.0t)',
          data: history.map(() => 5.0),
          borderColor: 'rgba(251, 140, 0, 0.5)',
          borderWidth: 2,
          borderDash: [8, 4],
          fill: false,
          pointRadius: 0,
        },
        {
          label: '2050 Target (2.0t)',
          data: history.map(() => 2.0),
          borderColor: 'rgba(0, 200, 83, 0.5)',
          borderWidth: 2,
          borderDash: [8, 4],
          fill: false,
          pointRadius: 0,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: {
            color: '#A5D6A7',
            font: { family: "'DM Sans', sans-serif" },
          },
        },
        tooltip: {
          callbacks: {
            label: (context) => ` ${context.dataset.label}: ${context.parsed.y.toFixed(2)}t`,
          },
        },
      },
      scales: {
        x: {
          ticks: { color: '#A5D6A7' },
          grid: { color: 'rgba(67, 160, 71, 0.1)' },
        },
        y: {
          beginAtZero: true,
          ticks: { color: '#A5D6A7' },
          grid: { color: 'rgba(67, 160, 71, 0.1)' },
        },
      },
    },
  });
}

/** Render history table */
function renderTrackerTable(history) {
  const tbody = document.getElementById('tracker-table-body');
  if (!tbody) return;

  tbody.innerHTML = history.map((entry, idx) => {
    const [year, month] = entry.month.split('-');
    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const monthLabel = `${monthNames[parseInt(month) - 1]} ${year}`;

    let changeHtml = '—';
    if (idx > 0) {
      const prev = history[idx - 1].total;
      const diff = entry.total - prev;
      const pct = prev > 0 ? ((diff / prev) * 100).toFixed(1) : 0;
      if (diff < 0) {
        changeHtml = `<span style="color: var(--eco-excellent);">↓ ${Math.abs(pct)}%</span>`;
      } else if (diff > 0) {
        changeHtml = `<span style="color: var(--eco-danger);">↑ ${pct}%</span>`;
      } else {
        changeHtml = `<span style="color: var(--text-muted);">= 0%</span>`;
      }
    }

    const b = entry.breakdown || {};
    return `
      <tr>
        <td>${monthLabel}</td>
        <td><strong>${entry.total.toFixed(2)}</strong></td>
        <td>${(b.energy || 0).toFixed(2)}</td>
        <td>${(b.transport || 0).toFixed(2)}</td>
        <td>${(b.diet || 0).toFixed(2)}</td>
        <td>${(b.waste || 0).toFixed(2)}</td>
        <td>${changeHtml}</td>
      </tr>
    `;
  }).reverse().join('');
}

// ============================================================
// Page initialization
// ============================================================

document.addEventListener('DOMContentLoaded', () => {
  // Detect which page we're on and initialise accordingly
  if (document.getElementById('calculator-form')) {
    initCalculator();
  }
  if (document.getElementById('results-container')) {
    initResults();
  }
  if (document.getElementById('action-plan-container')) {
    initActionPlan();
  }
  if (document.getElementById('chat-container')) {
    initChat();
  }
  if (document.getElementById('tracker-container')) {
    initTracker();
  }

  // Save to tracker button
  const saveBtn = document.getElementById('btn-save-tracker');
  if (saveBtn) {
    saveBtn.addEventListener('click', saveToTracker);
  }
});
