// tab 切换与滑杆值显示
document.querySelectorAll('nav button[data-p]').forEach(b => b.onclick = () => {
  document.querySelectorAll('nav button').forEach(x => x.classList.remove('active'));
  b.classList.add('active');
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.getElementById('p-' + b.dataset.p).classList.add('active');
});
document.querySelectorAll('input[type=range]').forEach(r => {
  const v = document.getElementById('v-' + r.id.replace('m2X','m2X').replace('m5X','m5X'));
  const show = document.getElementById('v-' + r.id);
  if (show) r.oninput = () => show.textContent = r.value;
});

const charts = {};
function mkChart(id, cfg) {
  if (charts[id]) charts[id].destroy();
  charts[id] = new Chart(document.getElementById(id), cfg);
}
function kpis(el, items) {
  document.getElementById(el).innerHTML = items.map(([n, l]) =>
    `<div class="kpi"><div class="n">${n}</div><div class="l">${l}</div></div>`).join('');
}
async function post(url, body, spin) {
  const s = document.getElementById(spin);
  if (s) s.style.display = 'inline';
  try {
    const r = await fetch(url, {method: 'POST', headers: {'Content-Type': 'application/json'},
                               body: JSON.stringify(body)});
    if (!r.ok) throw new Error(await r.text());
    return await r.json();
  } finally { if (s) s.style.display = 'none'; }
}
const gv = id => parseFloat(document.getElementById(id).value);

async function runM1() {
  const d = await post('/api/m1', {
    pi: gv('pi'), kappa: gv('kappa'), chi: gv('chi'), reserve_X: gv('reserve_X'),
    beta: gv('beta'), vy: gv('vy'), rho_scale: gv('rho_scale'),
    pbar_shift: gv('pbar_shift'), D_shift: gv('D_shift')}, 's-m1');
  kpis('m1-kpis', [[d.Y_star, 'Y* 最优国产规模(万吨)'], [d.M_star, 'M* 进口(万吨)'],
                   [d.Z_star, 'Z* 替代蛋白(万吨)'], [d.MC_at_Y, '影子价格(元/吨)'],
                   [d.welfare, '规划福利(亿元)']]);
  mkChart('m1-chart', {type: 'line', data: {labels: d.curve.y,
    datasets: [{label: '优序供给 MC(Y) 元/吨', data: d.curve.mc, borderColor: '#8c1f28', pointRadius: 0}]},
    options: {plugins: {annotation: undefined, title: {display: true,
      text: `优序供给曲线 — Y*=${d.Y_star} 万吨`}}, scales: {x: {title: {display: true, text: '累计产量(万吨)'},
      ticks: {maxTicksLimit: 10}}, y: {title: {display: true, text: '元/吨'}}}}});
  const P = d.parts;
  document.getElementById('m1-parts').innerHTML = '<table class="kv">' +
    Object.entries({供给成本: -P.supply_cost, 进口支出: -P.import_cost, 中断风险: -P.risk_R,
      安全价值B: P.B_security, 质量价值: P.quality_V, 链条价值Φ: P.Phi_G,
      投资成本F: -P.F_invest, 替代成本CZ: -P.C_Z}).map(([k, v]) =>
      `<tr><td>${k}</td><td style="color:${v < 0 ? '#8c1f28' : '#2b6a99'}">${v.toFixed(1)}</td></tr>`).join('') + '</table>';
}

async function runM2() {
  const d = await post('/api/m2', {M: gv('M'), reserve_X: gv('m2X'),
    prob_scale: gv('prob_scale'), ell_scale: gv('ell_scale')}, 's-m2');
  kpis('m2-kpis', [[d.cost_yi, '期望采购成本(亿元)'],
                   [d.scenarios[0].cvar5, '基线 CVaR₅%(亿元)'],
                   [d.scenarios[3].cvar5, 'C3 双重冲击 CVaR₅%']]);
  mkChart('m2-shares', {type: 'bar', data: {labels: d.sources, datasets: [
    {label: '带约束最优份额', data: d.shares_capped, backgroundColor: '#2b6a99'},
    {label: '无约束解析解(定理6.1)', data: d.shares_analytic, backgroundColor: '#c07a26'}]},
    options: {plugins: {title: {display: true, text: '进口来源组合'}}}});
  mkChart('m2-scen', {type: 'bar', data: {labels: d.scenarios.map(s => s.scenario),
    datasets: [{label: 'CVaR₅% 损失(亿元)', data: d.scenarios.map(s => s.cvar5), backgroundColor: '#8c1f28'},
               {label: '平均短缺(万吨)', data: d.scenarios.map(s => s.mean_short), backgroundColor: '#999'}]},
    options: {plugins: {title: {display: true, text: '中断情景'}}}});
}

async function runM3() {
  const d = await post('/api/m3', {shock_pct: gv('shock')}, null);
  kpis('m3-kpis', [[d.food_index_pct + '%', '消费价格指数响应'],
                   [d.dlnp_pct[1] + '%', '压榨部门价格响应'],
                   [d.dlnp_pct[3] + '%', '牲畜养殖价格响应']]);
  mkChart('m3-chart', {type: 'bar', data: {labels: d.labels,
    datasets: [{label: '价格响应 %', data: d.dlnp_pct, backgroundColor: '#8c1f28'}]},
    options: {indexAxis: 'y', plugins: {title: {display: true,
      text: `大豆供给冲击 ${gv('shock')}% 的产业链传导 (2023 IO表)`}}}});
}

async function runM5() {
  const d = await post('/api/m5', {sub_area: gv('sub_area'), price_floor: gv('price_floor'),
    theta: gv('theta'), reserve_X: gv('m5X'),
    targeted: document.getElementById('targeted').checked}, 's-m5');
  kpis('m5-kpis', [[Math.round(d.Y.reduce((a, b) => a + b) / d.Y.length), '平均产量(万吨)'],
                   [(d.selfsuff * 100).toFixed(1) + '%', '自给率'],
                   [d.fiscal, '财政支出(亿元/年)'], [d.gini, '农户收入基尼']]);
  mkChart('m5-chart', {type: 'line', data: {labels: d.years, datasets: [
    {label: '国产产量(万吨)', data: d.Y, borderColor: '#8c1f28', yAxisID: 'y'},
    {label: '进口(万吨)', data: d.M, borderColor: '#2b6a99', yAxisID: 'y'},
    {label: '短缺(万吨)', data: d.short, borderColor: '#c07a26', yAxisID: 'y'}]},
    options: {plugins: {title: {display: true, text: '供给结构演化 2026–2032'}}}});
  mkChart('m5-income', {type: 'line', data: {labels: d.years, datasets: [
    {label: '种豆净收益(元/亩)', data: d.income, borderColor: '#2b6a99'},
    {label: '平均质量 q̄ (×1000)', data: d.q_bar.map(v => v * 1000), borderColor: '#8c1f28'}]},
    options: {plugins: {title: {display: true, text: '农户收入与质量'}}}});
}
