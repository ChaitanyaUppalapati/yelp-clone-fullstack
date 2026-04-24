#!/bin/bash
# Run JMeter load tests at increasing concurrency levels.
# Usage: ./jmeter/run-tests.sh [jmeter-path]
#   e.g. ./jmeter/run-tests.sh /opt/homebrew/bin/jmeter

JMETER=${1:-jmeter}
PLAN="jmeter/yelp-test-plan.jmx"
RESULTS_DIR="jmeter/results"
mkdir -p "$RESULTS_DIR"

for THREADS in 100 200 300 400 500; do
  echo "=============================="
  echo "Running with THREADS=$THREADS"
  echo "=============================="
  "$JMETER" -n \
    -t "$PLAN" \
    -l "$RESULTS_DIR/results_${THREADS}.csv" \
    -e -o "$RESULTS_DIR/report_${THREADS}" \
    -JTHREADS="$THREADS" \
    -JRAMP_UP=30 \
    -JDURATION=120
  echo "Done for THREADS=$THREADS — report at $RESULTS_DIR/report_${THREADS}/index.html"
done

echo "All load tests complete."
