#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ofis Gözlem Paneli (Ofis Dashboard)
-----------------------------------
Ofis Ajan Şirketi'nden tamamen bağımsız, yalnızca salt-okunur (read-only)
durum, rapor ve logları görselleştiren hafif yerel web arayüzü.

Çalıştırma:
    py -3 bin/panel.py
    (veya port belirterek: py -3 bin/panel.py --port 8080)
"""

import sys
import os
import json
import glob
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path

# Proje Kök Dizini (c:\Alper\Ofis)
BASE_DIR = Path(__file__).resolve().parent.parent

BIRIMLER = [
    {"id": "dekan", "ad": "Dekan", "rol": "Ana Orkestratör & Alper Muhatabı", "ikon": "🏛️"},
    {"id": "dekan-sekreteri", "ad": "Dekan Sekreteri", "rol": "Mevzuat Derleme & Kural İndeksi", "ikon": "📋"},
    {"id": "staj-burosu", "ad": "Staj Bürosu", "rol": "Atomik 1 Öğrenci Staj İnceleme & Sicil İmza", "ikon": "🎓"},
    {"id": "postaci", "ad": "Postacı", "rol": "E-Posta & Telegram Dinleyici / İletişim", "ikon": "📬"},
    {"id": "memur", "ad": "Memur", "rol": "MÜDEK & Komisyon İdari Yazışma", "ikon": "🗂️"},
    {"id": "ik-memuru", "ad": "İK Memuru", "rol": "Ajan Kadrosu, Prompt & Skill Yöneticisi", "ikon": "👥"},
    {"id": "bilgi-islem", "ad": "Bilgi İşlem", "rol": "Python Araçları & Birim Testleri", "ikon": "💻"},
    {"id": "mufettis", "ad": "Müfettiş", "rol": "Bağımsız Denetçi (KVKK, Barkod, T.C. Mod-10)", "ikon": "🔍"}
]

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>YTÜ GMİM • Ofis Ajan Şirketi Canlı Paneli</title>
  <!-- Marked.js for fast client-side Markdown rendering -->
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <style>
    :root {
      --bg: #0f172a;
      --card-bg: #1e293b;
      --card-border: #334155;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --accent: #38bdf8;
      --accent-hover: #0ea5e9;
      --success: #22c55e;
      --warning: #f59e0b;
      --danger: #ef4444;
      --info: #a855f7;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
      padding: 20px;
    }

    /* Üst Bar */
    header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 18px;
      margin-bottom: 24px;
      border-bottom: 1px solid var(--card-border);
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .brand h1 {
      font-size: 1.35rem;
      font-weight: 700;
      letter-spacing: -0.02em;
      color: #fff;
    }
    .brand p {
      font-size: 0.85rem;
      color: var(--text-muted);
    }
    .header-actions {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .refresh-badge {
      font-size: 0.75rem;
      background: #1e293b;
      color: var(--accent);
      padding: 6px 12px;
      border-radius: 9999px;
      border: 1px solid var(--card-border);
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .live-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--success);
      box-shadow: 0 0 8px var(--success);
      animation: pulse 2s infinite;
    }
    @keyframes pulse {
      0%, 100% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.4; transform: scale(0.85); }
    }

    /* Grid Düzeni */
    .dashboard-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }

    .unit-card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 16px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      transition: all 0.2s ease;
      cursor: pointer;
      position: relative;
      overflow: hidden;
    }
    .unit-card:hover {
      border-color: var(--accent);
      transform: translateY(-2px);
      box-shadow: 0 8px 24px rgba(0,0,0,0.3);
    }
    .unit-card.active {
      border-color: var(--accent);
      box-shadow: 0 0 0 2px var(--accent);
    }

    .card-top {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 12px;
    }
    .unit-meta {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .unit-icon {
      font-size: 1.6rem;
      background: #0f172a;
      width: 44px;
      height: 44px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 10px;
      border: 1px solid var(--card-border);
    }
    .unit-names h3 {
      font-size: 1rem;
      font-weight: 600;
    }
    .unit-names span {
      font-size: 0.75rem;
      color: var(--text-muted);
    }

    .status-pill {
      font-size: 0.7rem;
      font-weight: 600;
      text-transform: uppercase;
      padding: 4px 8px;
      border-radius: 6px;
      letter-spacing: 0.05em;
    }
    .status-bosta { background: rgba(34, 197, 94, 0.15); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.3); }
    .status-mesaide { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }
    .status-bekliyor { background: rgba(56, 189, 248, 0.15); color: #7dd3fc; border: 1px solid rgba(56, 189, 248, 0.3); }

    .card-body {
      margin-bottom: 12px;
    }
    .last-result {
      font-size: 0.8rem;
      color: #cbd5e1;
      background: #0f172a;
      padding: 8px 10px;
      border-radius: 6px;
      border: 1px solid #1e293b;
      margin-bottom: 10px;
      max-height: 48px;
      overflow: hidden;
      text-overflow: ellipsis;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
    }
    .queue-preview {
      display: flex;
      justify-content: space-between;
      font-size: 0.75rem;
      color: var(--text-muted);
    }
    .queue-preview b {
      color: var(--accent);
    }

    .card-footer {
      font-size: 0.7rem;
      color: var(--text-muted);
      border-top: 1px solid #334155;
      padding-top: 8px;
      display: flex;
      justify-content: space-between;
    }

    /* Alt Detay Alanı (Tablar & Rapor Görüntüleyici) */
    .detail-section {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      overflow: hidden;
    }
    .nav-tabs {
      display: flex;
      background: #0f172a;
      border-bottom: 1px solid var(--card-border);
      overflow-x: auto;
    }
    .nav-tab {
      padding: 12px 20px;
      font-size: 0.85rem;
      font-weight: 500;
      color: var(--text-muted);
      background: none;
      border: none;
      border-bottom: 2px solid transparent;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 8px;
      white-space: nowrap;
    }
    .nav-tab:hover {
      color: #fff;
    }
    .nav-tab.active {
      color: var(--accent);
      border-bottom-color: var(--accent);
      background: rgba(56, 189, 248, 0.05);
    }

    .tab-content {
      padding: 24px;
      min-height: 350px;
    }

    /* Markdown Rapor Stilleri */
    .markdown-body {
      color: #cbd5e1;
      font-size: 0.92rem;
      line-height: 1.65;
    }
    .markdown-body h1, .markdown-body h2, .markdown-body h3 {
      color: #fff;
      margin-top: 18px;
      margin-bottom: 10px;
      border-bottom: 1px solid #334155;
      padding-bottom: 6px;
    }
    .markdown-body h1 { font-size: 1.35rem; color: var(--accent); }
    .markdown-body h2 { font-size: 1.15rem; }
    .markdown-body h3 { font-size: 1rem; }
    .markdown-body p { margin-bottom: 12px; }
    .markdown-body blockquote {
      border-left: 3px solid var(--accent);
      background: rgba(56, 189, 248, 0.08);
      padding: 8px 14px;
      border-radius: 0 6px 6px 0;
      margin: 12px 0;
      color: #94a3b8;
    }
    .markdown-body table {
      width: 100%;
      border-collapse: collapse;
      margin: 16px 0;
      font-size: 0.85rem;
    }
    .markdown-body th, .markdown-body td {
      border: 1px solid var(--card-border);
      padding: 8px 12px;
      text-align: left;
    }
    .markdown-body th {
      background: #0f172a;
      color: var(--accent);
    }
    .markdown-body tr:nth-child(even) {
      background: rgba(255,255,255,0.02);
    }
    .markdown-body code {
      background: #0f172a;
      padding: 2px 6px;
      border-radius: 4px;
      font-size: 0.82rem;
      color: #e2e8f0;
      border: 1px solid #334155;
    }
    .markdown-body pre {
      background: #0b1120;
      padding: 12px;
      border-radius: 8px;
      border: 1px solid #334155;
      overflow-x: auto;
      margin: 12px 0;
    }
    .markdown-body pre code {
      border: none;
      background: transparent;
      padding: 0;
    }

    /* Dosya Seçim Listesi */
    .file-picker {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 16px;
      padding-bottom: 14px;
      border-bottom: 1px solid var(--card-border);
    }
    .file-btn {
      background: #0f172a;
      color: var(--text-muted);
      border: 1px solid var(--card-border);
      padding: 6px 12px;
      border-radius: 6px;
      font-size: 0.8rem;
      cursor: pointer;
      transition: all 0.15s ease;
    }
    .file-btn:hover {
      color: #fff;
      border-color: var(--accent);
    }
    .file-btn.active {
      background: var(--accent);
      color: #0f172a;
      font-weight: 600;
      border-color: var(--accent);
    }

    /* Kuyruk Listesi Stili */
    .queue-item {
      background: #0f172a;
      border: 1px solid var(--card-border);
      border-radius: 8px;
      padding: 12px;
      margin-bottom: 10px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .queue-title {
      font-size: 0.85rem;
      color: #f1f5f9;
      font-weight: 500;
    }
    .queue-meta {
      font-size: 0.75rem;
      color: var(--text-muted);
      margin-top: 4px;
    }
  </style>
</head>
<body>

  <header>
    <div class="brand">
      <div style="font-size: 2rem;">⚓</div>
      <div>
        <h1>YTÜ GİDF • Ofis Ajan Şirketi Paneli</h1>
        <p>GMİM Bölüm Staj Değerlendirme & İdari Yönetim Göstergesi (Read-Only)</p>
      </div>
    </div>
    <div class="header-actions">
      <div class="refresh-badge">
        <span class="live-dot"></span>
        <span id="sync-status">Canlı (Her 5s)</span>
      </div>
    </div>
  </header>

  <!-- 8 Birim Kartı -->
  <div class="dashboard-grid" id="units-grid">
    <!-- JS ile doldurulacak -->
  </div>

  <!-- Detay Alanı (Tablar) -->
  <div class="detail-section">
    <div class="nav-tabs">
      <button class="nav-tab active" onclick="switchTab('gundem')">🏛️ Birleşik Dekan Gündemi</button>
      <button class="nav-tab" onclick="switchTab('raporlar')">📑 Birim Çıktıları & Raporlar</button>
      <button class="nav-tab" onclick="switchTab('kuyruk')">📋 Görev Kuyruğu & Yapılanlar</button>
      <button class="nav-tab" onclick="switchTab('ogrenciler')">🎓 Öğrenci Profil Kartları</button>
      <button class="nav-tab" onclick="switchTab('defterler')">📓 Ajan Tecrübe Defterleri</button>
    </div>

    <div class="tab-content" id="tab-container">
      <div id="content-area" class="markdown-body">
        Yükleniyor...
      </div>
    </div>
  </div>

  <script>
    let currentTab = 'gundem';
    let selectedUnit = null;
    let dashboardData = null;

    async function loadData() {
      try {
        const resp = await fetch('/api/state');
        if (!resp.ok) throw new Error("Ağ hatası");
        dashboardData = await resp.json();
        renderUnits(dashboardData.birimler);
        renderCurrentTab();
        document.getElementById('sync-status').textContent = 'Senkronize: ' + new Date().toLocaleTimeString();
      } catch (err) {
        console.error("Yükleme hatası:", err);
        document.getElementById('sync-status').textContent = 'Bağlantı kesildi';
      }
    }

    function renderUnits(units) {
      const grid = document.getElementById('units-grid');
      grid.innerHTML = '';

      units.forEach(u => {
        const d = u.durum_json || {};
        const state = d.durum || 'bosta';
        const queueLen = (d.kuyruk || []).length;
        const lastResult = d.son_sonuc || 'Beklemede';
        const lastRun = d.son_kosu ? d.son_kosu.replace('T', ' ').substring(0, 16) : '-';

        const card = document.createElement('div');
        card.className = `unit-card ${selectedUnit === u.id ? 'active' : ''}`;
        card.onclick = () => selectUnit(u.id);

        card.innerHTML = `
          <div class="card-top">
            <div class="unit-meta">
              <div class="unit-icon">${u.ikon}</div>
              <div class="unit-names">
                <h3>${u.ad}</h3>
                <span>${u.rol}</span>
              </div>
            </div>
            <span class="status-pill status-${state}">${state}</span>
          </div>

          <div class="card-body">
            <div class="last-result" title="${lastResult}">${lastResult}</div>
            <div class="queue-preview">
              <span>Kuyruk: <b>${queueLen} görev</b></span>
              <span>Müfettiş: <b>${d.mufettis?.son_karar || 'ONAY'}</b></span>
            </div>
          </div>

          <div class="card-footer">
            <span>Son Koşu: ${lastRun}</span>
            <span>Detay gör →</span>
          </div>
        `;
        grid.appendChild(card);
      });
    }

    function selectUnit(unitId) {
      selectedUnit = (selectedUnit === unitId) ? null : unitId;
      renderUnits(dashboardData.birimler);
      if (selectedUnit) {
        switchTab('raporlar');
      }
    }

    function switchTab(tabId) {
      currentTab = tabId;
      document.querySelectorAll('.nav-tab').forEach(b => {
        b.classList.toggle('active', b.getAttribute('onclick').includes(tabId));
      });
      renderCurrentTab();
    }

    async function renderCurrentTab() {
      if (!dashboardData) return;
      const area = document.getElementById('content-area');

      if (currentTab === 'gundem') {
        if (!dashboardData.gundem) {
          area.innerHTML = '<blockquote>Henüz üretilmiş bir Birleşik Dekan Gündemi bulunmuyor.</blockquote>';
          return;
        }
        area.innerHTML = marked.parse(dashboardData.gundem);
      }
      else if (currentTab === 'raporlar') {
        const files = dashboardData.ciktilar || [];
        if (files.length === 0) {
          area.innerHTML = '<blockquote>Henüz oluşturulmuş rapor/çıktı dosyası bulunmuyor.</blockquote>';
          return;
        }

        // Filtre: Eğer seçili birim varsa ona göre filtrele
        const filtered = selectedUnit 
          ? files.filter(f => f.birim === selectedUnit)
          : files;

        let pickerHtml = '<div class="file-picker">';
        if (selectedUnit) {
          pickerHtml += `<button class="file-btn" onclick="selectedUnit=null; renderUnits(dashboardData.birimler); renderCurrentTab();">✕ ${selectedUnit} Filtresini Kaldır</button>`;
        }
        filtered.forEach((f, idx) => {
          pickerHtml += `<button class="file-btn ${idx===0 ? 'active':''}" onclick="loadFileContent('${f.path}', this)">${f.birim}: ${f.ad}</button>`;
        });
        pickerHtml += '</div><div id="file-body">Yükleniyor...</div>';
        area.innerHTML = pickerHtml;

        if (filtered.length > 0) {
          loadFileContent(filtered[0].path);
        } else {
          document.getElementById('file-body').innerHTML = `<blockquote>${selectedUnit} birimine ait henüz bir rapor bulunmuyor.</blockquote>`;
        }
      }
      else if (currentTab === 'kuyruk') {
        let qHtml = '<h2>Tüm Birimlerin Görev Kuyrukları</h2><p style="color: var(--text-muted); margin-bottom: 16px;">Bekleyen, tamamlanan ve denetlenen iş akışı:</p>';
        dashboardData.birimler.forEach(u => {
          const queue = u.durum_json?.kuyruk || [];
          if (queue.length > 0) {
            qHtml += `<h3 style="margin-top: 14px; font-size: 0.95rem;">${u.ikon} ${u.ad} (${queue.length} Görev)</h3>`;
            queue.forEach(item => {
              const statusBadge = item.durum === 'tamam' 
                ? '<span style="color:#4ade80; font-weight:600;">✓ Tamamlandı</span>' 
                : '<span style="color:#7dd3fc; font-weight:600;">⏳ Bekliyor</span>';
              qHtml += `
                <div class="queue-item">
                  <div>
                    <div class="queue-title">${item.id} — ${item.baslik || item.not || ''}</div>
                    <div class="queue-meta">${item.zaman || ''}</div>
                  </div>
                  <div>${statusBadge}</div>
                </div>
              `;
            });
          }
        });
        area.innerHTML = qHtml;
      }
      else if (currentTab === 'ogrenciler') {
        const ogrenciler = dashboardData.ogrenciler || [];
        if (ogrenciler.length === 0) {
          area.innerHTML = '<blockquote>Arşivde kayıtlı öğrenci profil kartı bulunmuyor.</blockquote>';
          return;
        }
        let pickerHtml = '<div class="file-picker">';
        ogrenciler.forEach((og, idx) => {
          pickerHtml += `<button class="file-btn ${idx===0 ? 'active':''}" onclick="loadFileContent('${og.path}', this)">🎓 ${og.no}</button>`;
        });
        pickerHtml += '</div><div id="file-body">Yükleniyor...</div>';
        area.innerHTML = pickerHtml;
        loadFileContent(ogrenciler[0].path);
      }
      else if (currentTab === 'defterler') {
        const defterler = dashboardData.defterler || [];
        let pickerHtml = '<div class="file-picker">';
        defterler.forEach((d, idx) => {
          pickerHtml += `<button class="file-btn ${idx===0 ? 'active':''}" onclick="loadFileContent('${d.path}', this)">📓 ${d.birim}</button>`;
        });
        pickerHtml += '</div><div id="file-body">Yükleniyor...</div>';
        area.innerHTML = pickerHtml;
        if (defterler.length > 0) loadFileContent(defterler[0].path);
      }
    }

    async function loadFileContent(path, btnElem) {
      if (btnElem) {
        document.querySelectorAll('.file-btn').forEach(b => b.classList.remove('active'));
        btnElem.classList.add('active');
      }
      const body = document.getElementById('file-body');
      if (!body) return;
      body.innerHTML = 'Yükleniyor...';
      try {
        const resp = await fetch(`/api/file?path=${encodeURIComponent(path)}`);
        const data = await resp.json();
        body.innerHTML = marked.parse(data.content);
      } catch (err) {
        body.innerHTML = '<blockquote>Dosya yüklenemedi.</blockquote>';
      }
    }

    // İlk yükleme ve 5 saniyede bir otomatik polling
    loadData();
    setInterval(loadData, 5000);
  </script>
</body>
</html>
"""

class OfisPanelHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Konsolu kirletmemek için HTTP istek loglarını sessize al
        return

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))
            return

        if path == "/api/state":
            data = self.collect_state()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
            return

        if path == "/api/file":
            qs = parse_qs(parsed.query)
            file_path = qs.get("path", [None])[0]
            content = ""
            if file_path:
                try:
                    target = BASE_DIR / file_path
                    if target.exists() and target.is_file():
                        content = target.read_text(encoding="utf-8")
                    else:
                        content = f"Dosya bulunamadı: {file_path}"
                except Exception as e:
                    content = f"Dosya okuma hatası: {str(e)}"

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"content": content}, ensure_ascii=False).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

    def collect_state(self):
        units_data = []
        for b in BIRIMLER:
            unit_id = b["id"]
            durum_file = BASE_DIR / "takimlar" / unit_id / "durum.json"
            durum_json = {}
            if durum_file.exists():
                try:
                    durum_json = json.loads(durum_file.read_text(encoding="utf-8"))
                except Exception:
                    pass
            units_data.append({
                "id": unit_id,
                "ad": b["ad"],
                "rol": b["rol"],
                "ikon": b["ikon"],
                "durum_json": durum_json
            })

        # Son Dekan Gündemi
        gundem_text = ""
        gundem_files = sorted(glob.glob(str(BASE_DIR / "takimlar" / "dekan" / "cikti" / "*-gundem.md")), reverse=True)
        if gundem_files:
            try:
                gundem_text = Path(gundem_files[0]).read_text(encoding="utf-8")
            except Exception:
                pass

        # Çıktı Dosyaları
        ciktilar = []
        for p in sorted(glob.glob(str(BASE_DIR / "takimlar" / "*" / "cikti" / "*.md")), reverse=True):
            p_obj = Path(p)
            birim_name = p_obj.parent.parent.name
            rel_path = str(p_obj.relative_to(BASE_DIR)).replace("\\", "/")
            ciktilar.append({
                "birim": birim_name,
                "ad": p_obj.name,
                "path": rel_path
            })

        # Öğrenci Profil Kartları
        ogrenciler = []
        for p in sorted(glob.glob(str(BASE_DIR / "sirket" / "arsiv" / "ogrenciler" / "*.md"))):
            p_obj = Path(p)
            rel_path = str(p_obj.relative_to(BASE_DIR)).replace("\\", "/")
            ogrenciler.append({
                "no": p_obj.stem,
                "path": rel_path
            })

        # Defterler
        defterler = []
        for b in BIRIMLER:
            d_path = BASE_DIR / "takimlar" / b["id"] / "defter.md"
            if d_path.exists():
                defterler.append({
                    "birim": b["ad"],
                    "path": str(d_path.relative_to(BASE_DIR)).replace("\\", "/")
                })

        return {
            "birimler": units_data,
            "gundem": gundem_text,
            "ciktilar": ciktilar,
            "ogrenciler": ogrenciler,
            "defterler": defterler
        }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Ofis Ajan Şirketi Canlı Gözlem Paneli")
    parser.add_argument("--port", type=int, default=8765, help="Web sunucu portu (Varsayılan: 8765)")
    parser.add_argument("--no-browser", action="store_true", help="Tarayıcıyı otomatik açma")
    args = parser.parse_args()

    port = args.port
    server = HTTPServer(("127.0.0.1", port), OfisPanelHandler)
    url = f"http://127.0.0.1:{port}"

    print("=" * 60)
    print(f"⚓ YTÜ GMİM • Ofis Ajan Şirketi Paneli Başlatıldı")
    print(f"🌐 Panel Adresi: {url}")
    print(f"ℹ️  Mod: Salt Okunur (Read-Only) / 5 sn otomatik yenileme")
    print("=" * 60)
    print("Kapatmak için Ctrl+C tuşlayabilirsiniz.\n")

    if not args.no_browser:
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nPanel durduruldu.")
        sys.exit(0)


if __name__ == "__main__":
    main()
