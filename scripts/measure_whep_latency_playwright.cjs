const { chromium } = require('../web/node_modules/playwright-core');
const http = require('http');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const REPO_ROOT = path.resolve(__dirname, '..');
const FFMPEG_BIN = path.join(REPO_ROOT, 'tools', 'ffmpeg', 'bin', 'ffmpeg.exe');

async function getJwtToken() {
  // Jalankan python inline untuk generate valid JWT dari secret di .env
  return new Promise((resolve, reject) => {
    const py = spawn('server/.venv/Scripts/python.exe', ['-c', `
import jwt, time, sys
from server.app.core.config import settings
payload = {"sub": "1", "role": "admin", "exp": int(time.time()) + 3600}
token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
sys.stdout.write(token)
`], { cwd: REPO_ROOT });
    let token = '';
    py.stdout.on('data', d => token += d.toString());
    py.on('close', code => {
      if (code === 0 && token.trim()) resolve(token.trim());
      else reject(new Error('Gagal generate JWT: ' + code));
    });
  });
}

async function run() {
  console.log("==================================================================");
  console.log("PENGUKURAN LATENSI LIVE VIEW WHEP SUNGGUHAN (PLAYWRIGHT CHROMIUM)");
  console.log("==================================================================");

  let jwtToken;
  try {
    jwtToken = await getJwtToken();
    console.log(`[+] JWT Token berhasil digenerate: ${jwtToken.substring(0, 20)}...`);
  } catch (e) {
    console.error("[-] Gagal membuat JWT token:", e.message);
    process.exit(1);
  }

  // Siapkan HTML runner untuk RTCPeerConnection WHEP di browser
  const htmlContent = `
<!DOCTYPE html>
<html>
<head><title>WHEP Latency Benchmark</title></head>
<body>
  <video id="v" autoplay playsinline muted style="width:640px;height:480px;"></video>
  <canvas id="c" width="640" height="480" style="display:none;"></canvas>
  <div id="status">INIT</div>
  <script>
    async function startWhep(whepUrl, token) {
      document.getElementById('status').innerText = 'CONNECTING';
      const pc = new RTCPeerConnection({
        iceServers: [{ urls: 'stun:stun.l.google.com:19302' }],
        bundlePolicy: 'max-bundle'
      });
      
      const v = document.getElementById('v');
      pc.ontrack = (evt) => {
        console.log('[JS] ontrack event fired, streams:', evt.streams.length);
        if (evt.streams && evt.streams[0]) {
          v.srcObject = evt.streams[0];
          document.getElementById('status').innerText = 'TRACK_RECEIVED';
          v.play().catch(e => console.log('[JS] play err:', e));
        }
      };

      pc.oniceconnectionstatechange = () => {
        console.log('[JS] ICE connection state:', pc.iceConnectionState);
      };
      pc.onconnectionstatechange = () => {
        console.log('[JS] Connection state:', pc.connectionState);
      };

      pc.addTransceiver('video', { direction: 'recvonly' });
      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);

      // Tunggu hingga ICE gathering selesai (Vanilla ICE) agar candidates lengkap di SDP
      await new Promise(resolve => {
        if (pc.iceGatheringState === 'complete') {
          resolve();
        } else {
          const check = () => {
            if (pc.iceGatheringState === 'complete') {
              pc.removeEventListener('icegatheringstatechange', check);
              resolve();
            }
          };
          pc.addEventListener('icegatheringstatechange', check);
          setTimeout(resolve, 1500);
        }
      });

      console.log('[JS] Sending WHEP offer, SDP length:', pc.localDescription.sdp.length);
      const resp = await fetch(whepUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/sdp',
          'Authorization': 'Bearer ' + token
        },
        body: pc.localDescription.sdp
      });

      if (!resp.ok) {
        document.getElementById('status').innerText = 'HTTP_ERR_' + resp.status;
        throw new Error('WHEP HTTP Error: ' + resp.status);
      }

      const answerSdp = await resp.text();
      console.log('[JS] Received WHEP answer, SDP length:', answerSdp.length);
      await pc.setRemoteDescription({ type: 'answer', sdp: answerSdp });
      document.getElementById('status').innerText = 'CONNECTED';

      // Monitor pulsa video
      const canvas = document.getElementById('c');
      const ctx = canvas.getContext('2d');
      let wasPulse = false;

      function checkFrame() {
        if (v.readyState >= 2) {
          ctx.drawImage(v, 0, 0, 640, 480);
          const p = ctx.getImageData(300, 220, 40, 40).data;
          let sum = 0;
          for (let i = 0; i < p.length; i += 4) {
            sum += p[i]; // Red channel
          }
          const avg = sum / (p.length / 4);
          const isPulse = avg > 180;

          if (isPulse && !wasPulse) {
            wasPulse = true;
            if (window.onBrowserPulse) {
              window.onBrowserPulse(Date.now());
            }
          } else if (!isPulse) {
            wasPulse = false;
          }
        }
      }

      setInterval(() => {
        console.log('[JS] video state:', 'readyState=' + v.readyState, 'paused=' + v.paused, 'videoWidth=' + v.videoWidth, 'curTime=' + v.currentTime);
      }, 1000);

      setInterval(() => {
        checkFrame();
      }, 10);
    }
  </script>
</body>
</html>
  `;

  // Serve file HTML via local http server
  const server = http.createServer((req, res) => {
    res.writeHead(200, { 'Content-Type': 'text/html' });
    res.end(htmlContent);
  });
  await new Promise(r => server.listen(8999, '127.0.0.1', r));
  console.log("[+] Test runner HTTP server listening on http://127.0.0.1:8999");

  // Jalankan publisher FFmpeg dengan pulsa optik
  const width = 640, height = 480, fps = 20;
  const frameBytes = width * height * 3;
  const camId = "bench_cam_1";
  const rtspUrl = `rtsp://bench_cam_1:bench_token_1@127.0.0.1:8554/${camId}`;

  console.log("[+] Menjalankan FFmpeg publisher untuk stream RTSP -> MediaMTX...");
  const pubFfmpeg = spawn(FFMPEG_BIN, [
    "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", `${width}x${height}`, "-r", `${fps}`,
    "-i", "pipe:0",
    "-c:v", "libx264", "-preset", "ultrafast", "-tune", "zerolatency", "-b:v", "800k",
    "-f", "rtsp", "-rtsp_transport", "tcp", rtspUrl
  ], { stdio: ['pipe', 'ignore', 'ignore'] });

  const pulseSentTimes = [];
  let frameCount = 0;
  const stopFeeding = { val: false };

  // Feed frame
  const bgFrame = Buffer.alloc(frameBytes, 30);
  const pulseFrame = Buffer.alloc(frameBytes, 255);

  const feedInterval = setInterval(() => {
    if (stopFeeding.val || pubFfmpeg.stdin.destroyed) return;
    frameCount++;
    const isPulse = (frameCount % 10 === 0);
    const now = Date.now();
    if (isPulse) {
      pulseSentTimes.push({ frame: frameCount, time: now });
      try { pubFfmpeg.stdin.write(pulseFrame); } catch(e) {}
    } else {
      try { pubFfmpeg.stdin.write(bgFrame); } catch(e) {}
    }
  }, 1000 / fps);

  // Berikan waktu 2 detik agar publisher stream aktif di MediaMTX
  await new Promise(r => setTimeout(r, 2000));

  // Launch Chromium
  console.log("[+] Membuka Chromium headless dengan Playwright...");
  let browser;
  try {
    browser = await chromium.launch({
      channel: 'chrome',
      headless: true,
      args: ['--use-fake-ui-for-media-stream', '--no-sandbox']
    });
  } catch (e) {
    console.log("[!] Coba fallback ke msedge...");
    browser = await chromium.launch({
      channel: 'msedge',
      headless: true,
      args: ['--use-fake-ui-for-media-stream', '--no-sandbox']
    });
  }

  const page = await browser.newPage();
  page.on('console', msg => console.log('PAGE LOG:', msg.text()));
  page.on('pageerror', err => console.log('PAGE ERR:', err.message));
  const samples = [];

  await page.exposeFunction('onBrowserPulse', (recvTime) => {
    // Cari pulseSentTime terdekat sebelum recvTime
    const validSent = pulseSentTimes.filter(p => p.time <= recvTime);
    if (validSent.length > 0) {
      const closest = validSent[validSent.length - 1];
      const lat = recvTime - closest.time;
      if (lat >= 20 && lat <= 1200) {
        samples.push(lat);
        console.log(`  [WHEP Sample #${samples.length}] Latensi = ${lat} ms (Sent: ${closest.time}, Recv: ${recvTime})`);
      }
    }
  });

  await page.goto('http://127.0.0.1:8999');
  console.log("[+] Memulai koneksi RTCPeerConnection WHEP ke MediaMTX...");
  
  try {
    await page.evaluate(async ({ whepUrl, token }) => {
      await window.startWhep(whepUrl, token);
    }, {
      whepUrl: `http://127.0.0.1:8889/${camId}/whep?token=${encodeURIComponent(jwtToken)}`,
      token: jwtToken
    });

    console.log("[+] Menunggu 15 detik pengumpulan sampel latensi WHEP...");
    const startCollect = Date.now();
    while (samples.length < 10 && (Date.now() - startCollect < 15000)) {
      await new Promise(r => setTimeout(r, 500));
      const status = await page.evaluate(() => document.getElementById('status').innerText);
      if (status.startsWith('HTTP_ERR')) {
        console.log("[-] WHEP HTTP Error:", status);
        break;
      }
    }
  } catch (err) {
    console.error("[-] Gagal WHEP Playwright:", err.message);
  }

  // Cleanup
  stopFeeding.val = true;
  clearInterval(feedInterval);
  try { pubFfmpeg.stdin.end(); pubFfmpeg.kill(); } catch(e) {}
  await browser.close();
  server.close();

  console.log("\n" + "=" * 65);
  console.log("HASIL PENGUKURAN LATENSI LIVE VIEW WHEP:");
  console.log("==================================================================");
  if (samples.length >= 10) {
    samples.sort((a, b) => a - b);
    const mean = samples.reduce((a, b) => a + b, 0) / samples.length;
    const median = samples[Math.floor(samples.length / 2)];
    const p95 = samples[Math.min(samples.length - 1, Math.floor(samples.length * 0.95))];

    console.log(`Jumlah Sampel: ${samples.length}`);
    console.log(`10 Sampel Mentah: ${samples.slice(0, 10).join(', ')} ms`);
    console.log(`Rata-rata (Mean) : ${mean.toFixed(2)} ms`);
    console.log(`Median           : ${median.toFixed(2)} ms`);
    console.log(`P95              : ${p95.toFixed(2)} ms`);
  } else if (samples.length > 0) {
    console.log(`Hanya terkumpul ${samples.length} sampel: ${samples.join(', ')} ms`);
  } else {
    console.log("STATUS: TIDAK DIUKUR / GAGAL MENERIMA PULSA OPTIK WHEP");
  }
  console.log("==================================================================");
}

run().catch(console.error);
