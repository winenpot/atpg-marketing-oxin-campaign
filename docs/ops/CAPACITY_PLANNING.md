# Capacity planning: production sizing cheatsheet

Goal: decide between 1, 2 or 3 domestic servers using measurements, not guesses.
Target: 40,000 registered users, 10,000 active at a spike.
The starting estimate (to be confirmed or rejected by this process):

| Item | Estimate |
|---|---|
| Spike load | 1,000 req/s worst case (10k players, 1 request every ~10 s), typical peak 100–300 req/s |
| Writes | 20–40k redemptions/day (hard max 200k); 100–200k ledger rows/day |
| App server | 4 vCPU / 8 GB |
| DB server | 4 vCPU / 16 GB / 100–200 GB NVMe |
| Backups | Continuous WAL archive off-site |

## Roadmap

| Step | When | Output | Decision it feeds |
|---|---|---|---|
| 1. Inventory | Day 1, 30 min per server | Filled "Server facts" table | Is the hardware in the right class at all? |
| 2. Benchmarks | Day 1, 1 h per server, off-hours | fio + pgbench numbers | Can the disk run Postgres? |
| 3. Monitoring | Days 1–5 (include a weekend) | Daily peaks of CPU, RAM, disk, steal, network | How much headroom other projects leave |
| 4. Traffic model | Day 2 | Filled "Traffic model" table, agreed with Mehdi/Arman | Target req/s and writes |
| 5. Load test | After the API (redemption, games, boards) runs on staging | k6 results at 250/500/1,000 req/s | Real capacity per server |
| 6. Failure drill | Before launch | Restore from backup, timed | 2 vs 3 servers (is the restore time acceptable?) |
| 7. Decision | After 5 and 6 | One ADR (0010) with the numbers | Final topology |

Decision rule (step 7):
- p95 latency < 300 ms and error rate < 0.5% at 1,000 req/s, with CPU < 70% and
  DB disk await < 10 ms: the chosen servers are enough.
- If one server passes on its own **and** a restore takes under 1–2 hours **and** the
  business accepts that downtime: 1 server is acceptable.
- If the restore is slower than the business accepts during the prize phase: add a
  standby (3 servers).

## Step 1: inventory (run on each server)

```bash
hostnamectl; uptime
lscpu | grep -E 'Model name|^CPU\(s\)|Thread|MHz|Hypervisor'
free -h
lsblk -o NAME,SIZE,ROTA,TYPE,MOUNTPOINT,MODEL     # ROTA=0 means SSD/NVMe
df -h /var/lib/docker /var/lib/postgresql 2>/dev/null
cat /sys/block/*/queue/scheduler 2>/dev/null
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}'   # who else lives here
docker stats --no-stream
ss -tlnp                                           # listening ports (exposure check)
ip -br addr                                        # private network between servers?
```

Server facts (fill in):

| | App server | DB server |
|---|---|---|
| vCPU / model | | |
| RAM | | |
| Disk type / size / free | | |
| VM or bare metal (Hypervisor line) | | |
| Other projects on it | | |
| Private link between them? Latency (`ping -c 20 <other>`) | | |
| Provider / datacenter | | |

## Step 2: benchmarks (off-hours; they load the machine)

Disk: Postgres cares about small random writes and fsync latency, not MB/s.

```bash
sudo apt install -y fio
# 4k random write with fsync, like Postgres WAL commits
fio --name=walsync --filename=/var/tmp/fio.test --size=1G --bs=4k --rw=randwrite \
    --ioengine=libaio --direct=1 --fsync=1 --runtime=60 --time_based --group_reporting
# mixed random read/write, like table pages
fio --name=mixed --filename=/var/tmp/fio.test --size=4G --bs=8k --rw=randrw --rwmixread=70 \
    --ioengine=libaio --direct=1 --iodepth=32 --runtime=60 --time_based --group_reporting
rm /var/tmp/fio.test
```

Rough reading: fsync'd 4k writes > 2,000 IOPS with latency in the low milliseconds is
fine for this load. Below ~500 IOPS, or tens of milliseconds, the disk is network or HDD
storage and will be the bottleneck.

Postgres (in a throwaway container on the DB server, never the live DB):

```bash
docker run -d --name pgb -e POSTGRES_PASSWORD=x -p 127.0.0.1:55432:5432 postgres:16
docker exec pgb pgbench -U postgres -i -s 50 postgres
docker exec pgb pgbench -U postgres -c 32 -j 4 -T 120 postgres      # report tps + latency
docker rm -f pgb
```

Our heaviest transaction (a redemption) is a few inserts and updates, close to pgbench's
TPC-B. Several thousand tps here means the DB has well over 10x headroom for the
expected redemption rate.

## Step 3: monitoring over several days

Option A (lightest): sysstat, one sample per minute, keeps 7+ days.

```bash
sudo apt install -y sysstat
sudo sed -i 's/^ENABLED=.*/ENABLED="true"/' /etc/default/sysstat
sudo systemctl enable --now sysstat
# change the interval to 1 minute
sudo systemctl edit sysstat-collect.timer   # [Timer] OnCalendar= / OnCalendar=*:*:00
# read later (sa<DD> = day of month)
sar -u -f /var/log/sysstat/sa$(date +%d)    # CPU incl. %steal
sar -r                                      # memory
sar -d -p                                   # disk await, %util
sar -n DEV                                  # network
sar -q                                      # load average, run queue
```

Option B (graphs): Netdata (one command install, web UI) or node_exporter +
Prometheus + Grafana (what production will use anyway; `docker compose` with the
"Node Exporter Full" dashboard, id 1860). Bind the UIs to 127.0.0.1 and use
`ssh -L`, per the server-exposure rule.

Write down for each day: peak CPU %, peak %steal, min free RAM (excluding cache),
peak disk await (ms), peak network Mbit/s, and the hour these happen.

## Step 4: traffic model

Agree these numbers with Mehdi/Arman, then compute:

| Input | Value | Source |
|---|---|---|
| Registered users | 40,000 | user |
| Active at spike | 10,000 | user |
| Requests per active player per minute | 6–12 (measure: count calls in Arman's app per screen) | frontend |
| Scans per active user per day | 1–2 | marketing |
| Game rounds per active user per day | 3–5 | product |
| Spike shape | e.g. 10 min after an Instagram post, last hour before the draw | marketing |

Peak req/s = active × requests per minute / 60. With 10,000 × 6 / 60 that's 1,000
req/s. Count requests in the browser's Network tab while using the demo for 5 minutes:
this is the single number that changes the answer most.

## Step 5: load test (k6)

- Run k6 from a **different** machine than the one under test, and close to it on the
  network.
- Scenario mix close to reality: `GET /me`, `/config`, boards, `/challenges` (reads,
  ~80%); redemptions, game finish, spin, streak (writes, ~20%).
- Seed the test DB to campaign size first: 40k users, ~10M ledger rows, 1M codes.
  Empty tables give fake-good results.
- Steps: 250 → 500 → 1,000 → 1,500 req/s, 5 minutes each, plus one 30-minute soak at
  the target.
- Record p50/p95/p99 latency, error rate, and server CPU, RAM, disk await and DB
  connections at each step. The first step that fails the decision rule is the capacity.
- `pg_stat_statements` on during the test: the top 10 queries by total time are where
  indexes are missing.

## Gotchas / watch out for

- **VPS steal time.** `%steal` above ~5% means a noisy neighbour on the host takes your
  CPU. Benchmarks look fine at 3 a.m. and fall apart at 9 p.m. Monitor across days.
- **Burst credits.** Some cloud disks and CPUs are fast for minutes, then throttle.
  Run benchmarks for 10+ minutes, not 30 seconds.
- **"SSD" on network storage.** Many VPS disks are Ceph/NFS-backed: good throughput,
  bad fsync latency. The fio fsync test is what tells you.
- **Connection count.** uvicorn workers × SQLAlchemy pool size (+ overflow) must stay
  under Postgres `max_connections` (default 100). 4 workers × 20 is already 80. Use
  PgBouncer, or a small pool per worker.
- **Shared servers.** Other projects' cron jobs, backups and Docker builds create
  spikes. Look at their peaks, not their averages.
- **Swap.** Any swapping on the DB server under load is a fail. Set
  `shared_buffers` ≈ 25% RAM and `effective_cache_size` ≈ 50–75% (PGTune helps).
- **Don't send real SMS in load tests.** Use the fake SMS adapter, or the bill and the
  provider's rate limit will surprise you.
- **The throttles will fire.** The 5-scans-a-day cap and the invalid-code throttle
  will reject load-test traffic. Use many seeded users and valid codes.
- **Load generator limits.** If the k6 machine is at 100% CPU, you're measuring k6.
- **Docker bypasses ufw.** Published ports are public unless bound to 127.0.0.1.
- **Network inside Iran.** Users and SMS gateways inside Iran reach a domestic DC
  fast; test from an Iranian mobile connection, not only from the office.
- **Averages lie.** Size for the p95 and the spike minute, not the daily average.
- **Backups don't count until restored.** Time a full restore (step 6); that number
  decides whether you need the third server.

## Resources (quick reading)

- Brendan Gregg, "The USE Method" and "Linux Performance Analysis in 60,000 ms"
  (brendangregg.com; Netflix tech blog): what to look at, in what order.
- Google SRE Book, chapters on "Handling Overload" and "Load Balancing"
  (sre.google/books): headroom and spike thinking.
- PGTune (pgtune.leopard.in.ua): starting `postgresql.conf` for given RAM/CPU.
- PostgreSQL wiki, "Number Of Database Connections": why fewer connections are faster.
- Use The Index, Luke (use-the-index-luke.com): reading `EXPLAIN` and fixing slow queries.
- k6 docs (grafana.com/docs/k6): scenarios, `ramping-arrival-rate`, thresholds.
- fio docs (fio.readthedocs.io) and pgbench docs (postgresql.org/docs/16/pgbench.html).
- Grafana dashboard 1860 "Node Exporter Full"; Netdata (netdata.cloud) for a quick look.
- pgBackRest (pgbackrest.org) or WAL-G: continuous backups and timed restores.
