version 17
args requested_reps
do "/root/data/Paper/食物消费数据/paper0-EASI/easi_total_anomaly_rebuild/code/00_config.do"
use "$AR_DATA/total_anomaly_analysis.dta", clear
keep if sample_model

estimates use "$AR_OUT/easi_gmm.ster"
matrix AR_BOOT_START = e(b)
local easi_order = e(fooddem_order)

capture program drop _ar_reference
program define _ar_reference, rclass
    version 17
    local prices "lnp1 lnp2 lnp3 lnp4 lnp5 lnp6"
    local shares "s1 s2 s3 s4 s5 s6"
    local quantities "qt1 qt2 qt3 qt4 qt5 qt6"
    local core "hhsize child_ratio elderly_ratio female_head head_no_education head_primary_education age_missing female_head_missing education_missing"
    quietly ds province_*, has(type numeric)
    local demos "`core' `r(varlist)'"
    capture confirm variable boot_cluster
    if _rc local cl "village_cluster"
    else local cl "boot_cluster"

    quietly fooddem, model(easi) order($AR_BOOT_ORDER) shares(`shares') ///
        prices(`prices') expenditure(ln_foodexp) estimator(gmm) ///
        demographics(`demos') quantities(`quantities') selection(sy) ///
        endogeneity(iv) instruments(ln_income inv_income) cluster(`cl') ///
        gmmsteps(2) from(AR_BOOT_START) iterate(120) tolerance(1e-5)
    quietly ar_reference_point
    forvalues g = 1/6 {
        local exp`g' = r(exp`g')
        local mar`g' = r(mar`g')
        local hic`g' = r(hic`g')
    }
    forvalues g = 1/6 {
        return scalar exp`g' = `exp`g''
        return scalar mar`g' = `mar`g''
        return scalar hic`g' = `hic`g''
    }
end

global AR_BOOT_ORDER `easi_order'
local reps = 199
if "`requested_reps'" != "" local reps = real("`requested_reps'")
if "$AR_BOOT_REPS" != "" local reps = real("$AR_BOOT_REPS")
bootstrap exp1=r(exp1) exp2=r(exp2) exp3=r(exp3) exp4=r(exp4) ///
    exp5=r(exp5) exp6=r(exp6) mar1=r(mar1) mar2=r(mar2) ///
    mar3=r(mar3) mar4=r(mar4) mar5=r(mar5) mar6=r(mar6) ///
    hic1=r(hic1) hic2=r(hic2) hic3=r(hic3) hic4=r(hic4) ///
    hic5=r(hic5) hic6=r(hic6), reps(`reps') seed(20260716) ///
    cluster(village_cluster) idcluster(boot_cluster) nodots ///
    saving("$AR_OUT/easi_reference_bootstrap_replicates.dta", replace): ///
    _ar_reference

shell /usr/bin/python3 "$AR_CODE/compile_bootstrap.py"
capture confirm file "$AR_OUT/easi_reference_bootstrap.csv"
if _rc {
    di as error "bootstrap result compiler failed"
    exit 601
}
