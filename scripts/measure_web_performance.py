#!/usr/bin/env python3
"""
scripts/measure_web_performance.py — Mengukur waktu muat awal web dashboard
Menggunakan Playwright (Microsoft Edge headless) untuk mengambil metrik Navigation Timing API.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

JS_MEASURE_SCRIPT = """
import { chromium } from '@playwright/test';

async function measure() {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  
  const startTime = Date.now();
  await page.goto('http://127.0.0.1:8000/login', { waitUntil: 'networkidle' });
  const totalElapsed = Date.now() - startTime;
  
  const timing = await page.evaluate(() => {
    const entry = performance.getEntriesByType('navigation')[0];
    if (!entry) return null;
    return {
      dns_time_ms: Math.round(entry.domainLookupEnd - entry.domainLookupStart),
      tcp_connect_ms: Math.round(entry.connectEnd - entry.connectStart),
      ttfb_ms: Math.round(entry.responseStart - entry.requestStart),
      response_time_ms: Math.round(entry.responseEnd - entry.responseStart),
      dom_interactive_ms: Math.round(entry.domInteractive - entry.startTime),
      dom_content_loaded_ms: Math.round(entry.domContentLoadedEventEnd - entry.startTime),
      load_complete_ms: Math.round(entry.loadEventEnd - entry.startTime),
    };
  });
  
  await browser.close();
  console.log(JSON.stringify({ total_elapsed_ms: totalElapsed, timing }));
}

measure().catch(err => {
  console.error(err);
  process.exit(1);
});
"""

def main():
    measure_file = ROOT / "web" / "measure_temp.mjs"
    measure_file.write_text(JS_MEASURE_SCRIPT, encoding="utf-8")
    try:
        res = subprocess.run(
            ["node", str(measure_file)],
            cwd=str(ROOT / "web"),
            capture_output=True,
            text=True,
            check=True
        )
        data = json.loads(res.stdout.strip())
        print("=== Pengukuran Waktu Muat Awal Web Dashboard 'Rumah' ===")
        print(f"URL Diuji            : http://127.0.0.1:8000/login")
        print(f"Total Waktu Muat     : {data['total_elapsed_ms']} ms")
        if data.get('timing'):
            t = data['timing']
            print(f"TTFB                 : {t['ttfb_ms']} ms")
            print(f"DOM Content Loaded   : {t['dom_content_loaded_ms']} ms")
            print(f"Load Complete        : {t['load_complete_ms']} ms")
        else:
            print("Navigation timing API tidak tersedia.")
    finally:
        if measure_file.exists():
            measure_file.unlink()

if __name__ == "__main__":
    main()
