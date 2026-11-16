# Downloads and parses the real public CSA bundle into caiq/data/*.json (gitignored).
# Run this before anything else in caiq/.
from __future__ import annotations

from caiq.extract import build

if __name__ == "__main__":
    n_questions, n_controls = build()
    print(f"{n_questions} real CAIQ v4.0.3 questions, {n_controls} real CCM v4.1.1 control objectives")
