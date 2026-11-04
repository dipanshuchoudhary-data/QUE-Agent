# Chunk size benchmark (floor = join pieces below it; ceiling = split above it)

Same rows, top-k 2, pool 4, judged retriever eval (production mode). One judge run per variant, so differences under about 0.02 are noise.

| variant | floor | ceiling | chunks | median chars | chunks <400 | recall | precision | relevancy | average | recall<=0.5 | injected chars |
|---|---|---|---|---|---|---|---|---|---|---|---|
| f0_m900 | 0 | 900 | 510 | 482 | 204 | 0.856 | 0.905 | 0.901 | 0.887 | 3 | 1296 |
| f400_m900 | 400 | 900 | 397 | 693 | 50 | 0.850 | 0.889 | 0.888 | 0.876 | 3 | 1488 |
| f400_m700 | 400 | 700 | 493 | 545 | 99 | 0.782 | 0.841 | 0.864 | 0.829 | 6 | 1187 |
| f400_m1200 | 400 | 1200 | 331 | 781 | 15 | 0.870 | 0.894 | 0.904 | 0.889 | 3 | 1767 |
| f600_m900 | 600 | 900 | 389 | 708 | 53 | 0.846 | 0.865 | 0.886 | 0.866 | 3 | 1522 |
