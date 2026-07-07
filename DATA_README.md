# Data placement
`syfi_coding_trace.jsonl.gz` (TraceLab coding-agent corpus, CC-BY; 53,601,226 bytes;
sha256 below) is NOT committed to git. Place it here (or pass --trace) to regenerate every
analysis/*.txt via the .py generators:
  python3 analysis/measurement_v2.py --trace data/syfi_coding_trace.jsonl.gz --csv-dir analysis/csv
  python3 analysis/friction_rent.py  --trace data/syfi_coding_trace.jsonl.gz
  python3 analysis/theorem_maps.py   --trace data/syfi_coding_trace.jsonl.gz
  python3 analysis/skirental_robust.py --trace data/syfi_coding_trace.jsonl.gz
  python3 analysis/breakpoints.py    --trace data/syfi_coding_trace.jsonl.gz
9d265eae69a31cae203848bea936f018148eed7ca8bf56050c5abe96da0b4e6b  data/syfi_coding_trace.jsonl.gz
