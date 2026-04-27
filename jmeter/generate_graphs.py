import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from collections import defaultdict

# ---------------------------------------------------------------------------
# Load data — read per-level files directly so concurrency is unambiguous
# ---------------------------------------------------------------------------
BINS = [100, 200, 300, 400, 500]

ENDPOINT_MAP = {
    "POST /auth/login":         "Login (POST /auth/login)",
    "GET /restaurants?q=ramen": "Search (GET /restaurants)",
    "POST /reviews/":           "Review (POST /reviews/)",
}

data  = defaultdict(lambda: defaultdict(list))
errs  = defaultdict(lambda: defaultdict(int))
total = defaultdict(lambda: defaultdict(int))

for conc in BINS:
    path = f"tmp_results_{conc}.csv"
    try:
        with open(path) as f:
            for row in csv.DictReader(f):
                label = row["label"]
                if label not in ENDPOINT_MAP:
                    continue
                elapsed = int(row["elapsed"])
                success = row["success"].strip().lower() == "true"
                data[label][conc].append(elapsed)
                total[label][conc] += 1
                if not success:
                    errs[label][conc] += 1
    except FileNotFoundError:
        print(f"Warning: {path} not found, skipping")

# ---------------------------------------------------------------------------
# Build summary arrays
# ---------------------------------------------------------------------------
summary = {}
for label in ENDPOINT_MAP:
    avg_rt, p95_rt, err_pct, tput = [], [], [], []
    for conc in BINS:
        times = data[label][conc]
        if not times:
            avg_rt.append(0); p95_rt.append(0); err_pct.append(0); tput.append(0)
            continue
        arr = np.array(times)
        avg_rt.append(np.mean(arr))
        p95_rt.append(np.percentile(arr, 95))
        n = total[label][conc]
        e = errs[label][conc]
        err_pct.append(100 * e / n if n else 0)
        # throughput: requests per second (rough — use window of allThreads)
        tput.append(n / max(1, (max(arr) / 1000)))  # simple estimate
    summary[label] = dict(avg=avg_rt, p95=p95_rt, err=err_pct, tput=tput)

# ---------------------------------------------------------------------------
# Color scheme
# ---------------------------------------------------------------------------
COLORS = {
    "POST /auth/login":         "#4CAF50",
    "GET /restaurants?q=ramen": "#2196F3",
    "POST /reviews/":           "#FF9800",
}
MARKERS = {
    "POST /auth/login":         "o",
    "GET /restaurants?q=ramen": "s",
    "POST /reviews/":           "^",
}

# ---------------------------------------------------------------------------
# Figure 1 — Avg Response Time vs Concurrency
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 6))
fig.patch.set_facecolor("#1a1a2e")
ax.set_facecolor("#16213e")

for label, name in ENDPOINT_MAP.items():
    ax.plot(BINS, summary[label]["avg"],
            color=COLORS[label], marker=MARKERS[label],
            linewidth=2.5, markersize=8, label=name)

ax.set_xlabel("Concurrent Users", color="white", fontsize=13)
ax.set_ylabel("Avg Response Time (ms)", color="white", fontsize=13)
ax.set_title("Response Time vs Concurrent Users", color="white", fontsize=15, fontweight="bold")
ax.set_xticks(BINS)
ax.tick_params(colors="white")
ax.spines[:].set_color("#444")
ax.grid(True, color="#333", linestyle="--", alpha=0.7)
ax.legend(facecolor="#0f3460", labelcolor="white", fontsize=11)
plt.tight_layout()
plt.savefig("graph_response_time.png", dpi=150, bbox_inches="tight", facecolor="#1a1a2e")
plt.close()
print("Saved graph_response_time.png")

# ---------------------------------------------------------------------------
# Figure 2 — Error Rate vs Concurrency
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 6))
fig.patch.set_facecolor("#1a1a2e")
ax.set_facecolor("#16213e")

x = np.arange(len(BINS))
width = 0.25
labels_list = list(ENDPOINT_MAP.keys())
for i, label in enumerate(labels_list):
    ax.bar(x + i * width, summary[label]["err"],
           width=width, color=COLORS[label],
           label=ENDPOINT_MAP[label], alpha=0.85)

ax.set_xlabel("Concurrent Users", color="white", fontsize=13)
ax.set_ylabel("Error Rate (%)", color="white", fontsize=13)
ax.set_title("Error Rate vs Concurrent Users", color="white", fontsize=15, fontweight="bold")
ax.set_xticks(x + width)
ax.set_xticklabels(BINS)
ax.tick_params(colors="white")
ax.spines[:].set_color("#444")
ax.grid(True, color="#333", linestyle="--", alpha=0.7, axis="y")
ax.legend(facecolor="#0f3460", labelcolor="white", fontsize=11)
plt.tight_layout()
plt.savefig("graph_error_rate.png", dpi=150, bbox_inches="tight", facecolor="#1a1a2e")
plt.close()
print("Saved graph_error_rate.png")

# ---------------------------------------------------------------------------
# Figure 3 — P95 Response Time vs Concurrency
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 6))
fig.patch.set_facecolor("#1a1a2e")
ax.set_facecolor("#16213e")

for label, name in ENDPOINT_MAP.items():
    ax.plot(BINS, summary[label]["p95"],
            color=COLORS[label], marker=MARKERS[label],
            linewidth=2.5, markersize=8, linestyle="--", label=name)

ax.set_xlabel("Concurrent Users", color="white", fontsize=13)
ax.set_ylabel("P95 Response Time (ms)", color="white", fontsize=13)
ax.set_title("P95 Response Time vs Concurrent Users", color="white", fontsize=15, fontweight="bold")
ax.set_xticks(BINS)
ax.tick_params(colors="white")
ax.spines[:].set_color("#444")
ax.grid(True, color="#333", linestyle="--", alpha=0.7)
ax.legend(facecolor="#0f3460", labelcolor="white", fontsize=11)
plt.tight_layout()
plt.savefig("graph_p95_response_time.png", dpi=150, bbox_inches="tight", facecolor="#1a1a2e")
plt.close()
print("Saved graph_p95_response_time.png")

# ---------------------------------------------------------------------------
# Figure 4 — Combined Dashboard (2x2)
# ---------------------------------------------------------------------------
fig, axes = plt.subplots(2, 2, figsize=(16, 10))
fig.patch.set_facecolor("#1a1a2e")
fig.suptitle("JMeter Load Test Results — Yelp Clone API", color="white",
             fontsize=16, fontweight="bold", y=0.98)

# Top-left: Avg response time
ax = axes[0][0]
ax.set_facecolor("#16213e")
for label, name in ENDPOINT_MAP.items():
    ax.plot(BINS, summary[label]["avg"], color=COLORS[label],
            marker=MARKERS[label], linewidth=2.5, markersize=7, label=name)
ax.set_title("Avg Response Time (ms)", color="white", fontsize=12)
ax.set_xlabel("Concurrent Users", color="white"); ax.set_ylabel("ms", color="white")
ax.set_xticks(BINS); ax.tick_params(colors="white")
ax.spines[:].set_color("#444"); ax.grid(True, color="#333", linestyle="--", alpha=0.6)
ax.legend(facecolor="#0f3460", labelcolor="white", fontsize=9)

# Top-right: P95 response time
ax = axes[0][1]
ax.set_facecolor("#16213e")
for label, name in ENDPOINT_MAP.items():
    ax.plot(BINS, summary[label]["p95"], color=COLORS[label],
            marker=MARKERS[label], linewidth=2.5, markersize=7, linestyle="--", label=name)
ax.set_title("P95 Response Time (ms)", color="white", fontsize=12)
ax.set_xlabel("Concurrent Users", color="white"); ax.set_ylabel("ms", color="white")
ax.set_xticks(BINS); ax.tick_params(colors="white")
ax.spines[:].set_color("#444"); ax.grid(True, color="#333", linestyle="--", alpha=0.6)
ax.legend(facecolor="#0f3460", labelcolor="white", fontsize=9)

# Bottom-left: Error rate bars
ax = axes[1][0]
ax.set_facecolor("#16213e")
x = np.arange(len(BINS))
width = 0.25
for i, label in enumerate(labels_list):
    ax.bar(x + i * width, summary[label]["err"], width=width,
           color=COLORS[label], label=ENDPOINT_MAP[label], alpha=0.85)
ax.set_title("Error Rate (%)", color="white", fontsize=12)
ax.set_xlabel("Concurrent Users", color="white"); ax.set_ylabel("%", color="white")
ax.set_xticks(x + width); ax.set_xticklabels(BINS)
ax.tick_params(colors="white"); ax.spines[:].set_color("#444")
ax.grid(True, color="#333", linestyle="--", alpha=0.6, axis="y")
ax.legend(facecolor="#0f3460", labelcolor="white", fontsize=9)

# Bottom-right: Summary stats table
ax = axes[1][1]
ax.set_facecolor("#16213e")
ax.axis("off")
table_data = [["Users", "Login Avg", "Search Avg", "Review Avg", "Login Err%"]]
for i, conc in enumerate(BINS):
    row = [
        str(conc),
        f"{summary['POST /auth/login']['avg'][i]:.1f}ms",
        f"{summary['GET /restaurants?q=ramen']['avg'][i]:.1f}ms",
        f"{summary['POST /reviews/']['avg'][i]:.1f}ms",
        f"{summary['POST /auth/login']['err'][i]:.1f}%",
    ]
    table_data.append(row)

tbl = ax.table(cellText=table_data[1:], colLabels=table_data[0],
               cellLoc="center", loc="center",
               bbox=[0, 0.1, 1, 0.85])
tbl.auto_set_font_size(False)
tbl.set_fontsize(10)
for (r, c), cell in tbl.get_celld().items():
    cell.set_facecolor("#0f3460" if r == 0 else "#1a1a2e")
    cell.set_text_props(color="white")
    cell.set_edgecolor("#444")
ax.set_title("Summary Table", color="white", fontsize=12)

plt.tight_layout()
plt.savefig("graph_dashboard.png", dpi=150, bbox_inches="tight", facecolor="#1a1a2e")
plt.close()
print("Saved graph_dashboard.png")

# ---------------------------------------------------------------------------
# Print summary stats to console
# ---------------------------------------------------------------------------
print("\n=== SUMMARY STATS ===")
for label, name in ENDPOINT_MAP.items():
    print(f"\n{name}")
    for i, conc in enumerate(BINS):
        print(f"  {conc} users: avg={summary[label]['avg'][i]:.1f}ms  p95={summary[label]['p95'][i]:.1f}ms  err={summary[label]['err'][i]:.2f}%")
