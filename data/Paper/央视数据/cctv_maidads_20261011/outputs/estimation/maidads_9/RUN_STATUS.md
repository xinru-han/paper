# Interrupted First-Pass Fit

The old-initialization 3-start job was deliberately interrupted with exit code
130 after approximately 30 minutes. Starts 1 and 2 were completed and their raw
parameter CSVs remain intact. Start 3 did not complete. There is no completed
model summary and this directory is not a qualified final fit. A new-kernel fit
will be recorded separately, without replacing the completed candidates.
