#!/bin/bash
# Run JMeter load tests at increasing concurrency levels.
# Usage: ./jmeter/run-tests.sh [jmeter-path]
#   e.g. ./jmeter/run-tests.sh /opt/homebrew/bin/jmeter

JMETER=${1:-jmeter}
PLAN="jmeter/yelp-test-plan.jmx"
mkdir -p jmeter/results

RAMP_TIMES=(0 20 40 60 80 100)
LEVELS=(100 200 300 400 500)

for i in 0 1 2 3 4; do
  THREADS=${LEVELS[$i]}
  RAMP_UP=${RAMP_TIMES[$((i+1))]}

  echo "=============================="
  echo "Clearing load test reviews from MongoDB..."
  mongosh yelp_db --quiet --eval "db.reviews.deleteMany({comment:'Load test review'})" 2>/dev/null || \
    docker exec mongodb mongosh yelp_db --quiet --eval "db.reviews.deleteMany({comment:'Load test review'})" 2>/dev/null

  echo "Running THREADS=$THREADS  RAMP_UP=${RAMP_UP}s"
  echo "=============================="

  "$JMETER" -n \
    -t "$PLAN" \
    -l "jmeter/tmp_results_${THREADS}.csv" \
    -JTHREADS="$THREADS" \
    -JRAMP_UP="$RAMP_UP" \
    -JDURATION=60

  echo "Done for THREADS=$THREADS"
  sleep 10
done

# Merge all results into one file
echo "Merging results..."
head -1 jmeter/tmp_results_100.csv > jmeter/results.csv
for THREADS in 100 200 300 400 500; do
  tail -n +2 "jmeter/tmp_results_${THREADS}.csv" >> jmeter/results.csv
done

echo "All load tests complete. Run: python3 jmeter/generate_graphs.py"
