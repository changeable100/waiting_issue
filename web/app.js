'use strict';
const $ = id => document.getElementById(id);
const fmt = value => value == null ? '无样本' : value.toFixed(2);
let latest = null;
let scenarios = new Set();
const ns = 'http://www.w3.org/2000/svg';
function node(tag, attrs = {}, text) {
  const el = document.createElementNS(ns, tag);
  Object.entries(attrs).forEach(([key, value]) => el.setAttribute(key, value));
  if (text != null) el.textContent = text;
  return el;
}
function drawOccupancy(run, capacity) {
  const width = 760, height = 235, left = 38, right = 18, top = 20, bottom = 34;
  const end = Math.max(run.horizon_min, run.drain_complete_min, 1);
  const x = t => left + t / end * (width - left - right);
  const y = n => height - bottom - n / capacity * (height - top - bottom);
  const svg = node('svg', {viewBox: `0 0 ${width} ${height}`, role: 'img', 'aria-labelledby': 'trace-title trace-desc'});
  svg.append(node('title', {id: 'trace-title'}, '外卖柜格口占用随时间变化'));
  svg.append(node('desc', {id: 'trace-desc'}, `容量每柜${capacity}格，观测窗口${run.horizon_min}分钟，运行至${run.drain_complete_min.toFixed(1)}分钟。`));
  for (let i = 0; i <= 4; i++) {
    const n = capacity * i / 4;
    svg.append(node('line', {x1: left, y1: y(n), x2: width - right, y2: y(n), stroke: '#e9efeb'}));
    svg.append(node('text', {x: left - 8, y: y(n) + 3, 'text-anchor': 'end'}, Number.isInteger(n) ? n : n.toFixed(1)));
    const t = end * i / 4;
    svg.append(node('text', {x: x(t), y: height - 14, 'text-anchor': 'middle'}, t.toFixed(0)));
  }
  svg.append(node('text', {x: left, y: 10}, '格口数'));
  svg.append(node('text', {x: width - right, y: height - 1, 'text-anchor': 'end'}, '相对时间 / 分钟'));
  svg.append(node('line', {x1: x(run.horizon_min), x2: x(run.horizon_min), y1: top, y2: height - bottom, stroke: '#acbcb7', 'stroke-dasharray': '4 4'}));
  svg.append(node('line', {x1: left, x2: width - right, y1: y(capacity), y2: y(capacity), stroke: '#cf9b47', 'stroke-dasharray': '5 4'}));
  const colors = ['#16796c', '#719cd0', '#b57d4f', '#9b7bc1'];
  run.lockers.forEach((bank, index) => {
    const points = run.trace.filter(p => p.locker_id === bank.locker_id);
    let path = `M ${x(0)} ${y(0)}`;
    points.forEach(p => {path += ` H ${x(p.time_min)} V ${y(p.occupied)}`;});
    path += ` H ${x(end)}`;
    svg.append(node('path', {d: path, fill: 'none', stroke: colors[index % colors.length], 'stroke-width': 2, 'stroke-linejoin': 'round'}));
  });
  $('occupancy-chart').replaceChildren(svg);
  $('trace-context').textContent = `种子 ${run.seed} · 首轮 ${run.orders.length} 单 · 窗口 ${run.horizon_min} 分钟 · 全部取走于第 ${run.drain_complete_min.toFixed(1)} 分钟`;
}
function showResult(result) {
  const {settings: s, prediction: p, single_run: run} = result;
  $('deposit').textContent = fmt(p.metrics.deposit_wait_min.mean);
  $('pickup').textContent = fmt(p.metrics.student_queue_wait_min.mean);
  $('total').textContent = fmt(p.metrics.arrival_to_pickup_min.mean);
  $('result-context').textContent = `${s.scenario_label} ｜ 每柜 ${s.capacity} 格 ｜ ${s.replications} 次重复 ｜ 种子 ${s.seed} ｜ ${p.source_kind === 'synthetic' ? '合成数据' : p.source_kind}`;
  drawOccupancy(run, s.capacity);
  const rows = [['投递等待', p.metrics.deposit_wait_min], ['取餐排队', p.metrics.student_queue_wait_min], ['两类排队合计', p.metrics.total_queue_wait_min]];
  const max = Math.max(...rows.map(([, d]) => d.p90 ?? 0), 0.01);
  $('wait-chart').replaceChildren();
  rows.forEach(([label, d]) => {
    const row = document.createElement('div'); row.className = 'wait-row';
    const header = document.createElement('div'); header.className = 'wait-label';
    const name = document.createElement('span'); name.textContent = label;
    const value = document.createElement('span'); value.textContent = `P90 ${fmt(d.p90)} 分钟`;
    header.append(name, value);
    const track = document.createElement('div'); track.className = 'bar-track';
    const bar = document.createElement('div'); bar.className = 'bar-fill'; bar.style.width = `${(d.p90 ?? 0) / max * 100}%`;
    track.append(bar);
    const detail = document.createElement('div'); detail.className = 'dist-detail'; detail.textContent = `平均 ${fmt(d.mean)} · P50 ${fmt(d.p50)} · P95 ${fmt(d.p95)} 分钟`;
    row.append(header, track, detail); $('wait-chart').append(row);
  });
  $('pressure').replaceChildren();
  p.lockers.forEach(bank => {
    const section = document.createElement('div'); section.className = 'pressure-item';
    const title = document.createElement('p'); title.className = 'pressure-title'; title.textContent = `外卖柜 ${bank.locker_id} · ${s.capacity} 格`;
    section.append(title);
    [['平均格口占用率', bank.utilization], ['满柜时间占比', bank.full_time_fraction]].forEach(([label, value]) => {
      const row = document.createElement('div'); row.className = 'pressure-row';
      const name = document.createElement('span'); name.textContent = label;
      const strong = document.createElement('strong'); strong.textContent = `${(value * 100).toFixed(1)}%`;
      row.append(name, strong); section.append(row);
    });
    $('pressure').append(section);
  });
  $('provenance').textContent = `参数来源：${p.provenance}。${p.warnings.join(' ')}`;
  $('download').disabled = false;
}
async function execute(event) {
  event?.preventDefault();
  if (!$('simulation-form').reportValidity()) return;
  const scenario_id = ['day', 'weather', 'period', 'week'].map(id => $(id).value).join('_');
  $('error').hidden = true;
  if (!scenarios.has(scenario_id)) { $('error').textContent = '此场景没有可用参数'; $('error').hidden = false; return; }
  const payload = {scenario_id, capacity: Number($('capacity').value), replications: Number($('replications').value), seed: Number($('seed').value)};
  $('fields').disabled = true; $('download').disabled = true;
  $('results').setAttribute('aria-busy', 'true'); $('run-button').textContent = '正在运行…';
  $('status').textContent = '正在调用本地模型计算，请稍候…';
  try {
    const response = await fetch('/api/simulate', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)});
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || '仿真请求未完成');
    showResult(result); latest = result;
    $('status').textContent = '仿真已完成，右侧为本次运行结果。';
  } catch (err) {
    $('error').textContent = `运行失败：${err.message}。请确认本地服务仍在运行。`;
    $('error').hidden = false; $('status').textContent = latest ? '保留上次成功运行的结果。' : '暂无仿真结果，请重试。';
    $('download').disabled = !latest;
  } finally {
    $('fields').disabled = false; $('results').setAttribute('aria-busy', 'false'); $('run-button').textContent = '运行仿真 ↗';
  }
}
$('simulation-form').addEventListener('submit', execute);
$('simulation-form').addEventListener('input', () => { if (latest) $('status').textContent = '条件已修改，点击运行以更新结果。右侧仍为上次结果。'; });
$('download').addEventListener('click', () => {
  if (!latest) return;
  const blob = new Blob([JSON.stringify(latest, null, 2)], {type: 'application/json;charset=utf-8'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a'); a.href = url; a.download = `locker-${latest.settings.scenario_id}-${latest.settings.capacity}.json`;
  a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
});
(async () => {
  try {
    const response = await fetch('/api/scenarios');
    if (!response.ok) throw new Error('无法载入场景');
    const data = await response.json(); scenarios = new Set(data.scenarios.map(s => s.id));
    await execute();
  } catch (err) {
    $('status').textContent = '本地服务未连接'; $('error').textContent = `${err.message}，请启动 web_server.py 后刷新页面。`;
    $('error').hidden = false; $('results').setAttribute('aria-busy', 'false');
  }
})();
