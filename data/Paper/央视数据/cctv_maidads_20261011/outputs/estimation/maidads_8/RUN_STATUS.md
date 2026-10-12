# Interrupted First-Pass Fit

The old-kernel 3-start job was deliberately interrupted with exit code 130 after
more than 35 minutes. Starts 1 and 2 were completed and their raw parameter
CSVs remain intact. Start 3 did not complete. There is no completed model summary
and this directory is not a qualified final fit. New numerical-initialization
runs are stored separately; incomplete candidates are not silently discarded.
