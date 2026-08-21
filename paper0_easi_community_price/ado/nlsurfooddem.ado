*! fooddem NLSUR evaluator 1.0.0  12jul2026
program define nlsurfooddem
    version 17
    syntax varlist if, at(name)
    global FD_PRED 1
    fooddem_gmm `varlist' `if', at(`at')
    global FD_PRED 0
end
