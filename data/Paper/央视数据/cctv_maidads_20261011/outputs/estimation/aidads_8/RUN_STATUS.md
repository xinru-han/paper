# Interrupted First-Pass Fit

The old-kernel 3-start job was deliberately interrupted with exit code 130 after
more than 35 minutes. Starts 1 and 2 were completed and their raw parameter
CSVs remain intact. Start 3 did not complete. There is no completed model summary
and this directory is not a qualified final fit. The separately retained
`aidads_8_warm` run completed all three starts and failed the stationarity gate.
