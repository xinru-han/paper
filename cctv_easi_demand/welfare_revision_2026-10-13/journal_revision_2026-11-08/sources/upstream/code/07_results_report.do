version 17
clear all
set more off
set type double
global ROOT "/root/data/Paper/央视数据/Paper1-EASI/meat_merge_trial_2026-10-11"
global OLD "/root/data/Paper/央视数据/Paper1-EASI/stata_rebuild_2026-10-10"
log using "$ROOT/logs/07_results_report.log",text replace
clear
input byte good str20 good_name
1 "主食"
2 "食用油"
3 "蔬菜"
4 "水果"
5 "猪肉"
6 "其他肉类"
7 "水产品"
8 "乳制品"
end
tempfile labels sy before exactown
save `labels',replace
use "$ROOT/outputs/exact/elasticities_common_full.dta",clear
merge m:1 good using `labels',assert(match) nogen
order model good good_name
save "$ROOT/outputs/comparison/eight_group_exact.dta",replace
export delimited using "$ROOT/outputs/comparison/eight_group_exact.csv",replace
export excel using "$ROOT/outputs/meat_merge_results.xlsx",sheet("Exact elasticities") firstrow(variables) replace
quietly summarize N,meanonly
local exact_N=r(mean)
quietly summarize common_support_rate,meanonly
local exact_support=r(mean)
keep good model marshallian_own
reshape wide marshallian_own,i(good) j(model) string
rename marshallian_ownaids AIDS
rename marshallian_ownquaids QUAIDS
rename marshallian_owneasi EASI
save `exactown',replace
import delimited using "$ROOT/outputs/demand/elasticities_main.csv",clear varnames(1)
keep if margin=="unconditional" & sample=="common_positive" & subgroup=="all" & type=="marshallian" & good==shock
rename elasticity SY_EASI
keep good SY_EASI n support_rate
save `sy',replace
use `exactown',clear
merge 1:1 good using `sy',assert(match) nogen
merge 1:1 good using `labels',assert(match) nogen
rename n N_SY_EASI
rename support_rate support_SY_EASI
gen long N_exact=`exact_N'
gen double support_exact=`exact_support'
order good good_name AIDS QUAIDS EASI SY_EASI N_exact support_exact N_SY_EASI support_SY_EASI
format AIDS QUAIDS EASI SY_EASI %9.4f
save "$ROOT/outputs/comparison/own_price_all_models.dta",replace
export delimited using "$ROOT/outputs/comparison/own_price_all_models.csv",replace
export excel using "$ROOT/outputs/meat_merge_results.xlsx",sheet("Own price all models") firstrow(variables) sheetreplace
list good_name AIDS QUAIDS EASI SY_EASI,noobs
putdocx begin,font("Noto Sans CJK SC",10)
putdocx paragraph,style(Title)
putdocx text ("禽肉与牛羊肉合并：八类食品 Stata 重估结果")
putdocx paragraph
putdocx text ("2026年10月11日。此文件仅为模型试验结果报告，未修改论文。原禽肉组（含原其他肉类）与牛羊肉组合并为“其他肉类”，其余品类保留。样本仍为583,668个家庭月、27,638户家庭、24个省份，覆盖2020—2022年。")
putdocx paragraph
putdocx text ("合并后的支出、预算份额和购买指标重新计算；固定2021年外部价格篮子的品类权重重新归一化。原禽肉组权重为40.2473%，原牛羊肉组为59.7527%。价格采用加权几何指数。Stone实际支出、家庭均值和购买历史重新生成。估计、弹性、检验、表格与图全部由Stata/Mata完成。")
putdocx paragraph,style(Heading1)
putdocx text ("1. 八类食品的自身价格弹性")
putdocx table own=data(good_name AIDS QUAIDS EASI SY_EASI),varnames
putdocx table own(1,1)=("食品类别")
putdocx table own(1,2)=("AIDS")
putdocx table own(1,3)=("QUAIDS")
putdocx table own(1,4)=("精确EASI")
putdocx table own(1,5)=("SY-EASI")
putdocx paragraph
putdocx text ("表中为未补偿（Marshallian）自身价格弹性，采用与原报告一致的预测数量权重聚合。AIDS、QUAIDS、精确EASI使用三套模型共同正预测份额支持；SY-EASI使用主模型自身的共同正预测份额支持。估计本身使用全部家庭月记录，并未删除观测到的零购买；支持筛选只用于弹性报告。")
* Old versus merged group: each specification's standard reporting support.
use "$OLD/outputs/exact/elasticities_common_full.dta",clear
keep if good==6 | good==7
keep model good marshallian_own
reshape wide marshallian_own,i(model) j(good)
rename marshallian_own6 old_poultry
rename marshallian_own7 old_beef_mutton
save `before',replace
use "$ROOT/outputs/exact/elasticities_common_full.dta",clear
keep if good==6
rename marshallian_own merged_other_meat
keep model merged_other_meat hicksian_own expenditure N common_support_rate
merge 1:1 model using `before',assert(match) nogen
save `before',replace
import delimited using "$OLD/outputs/demand/elasticities_main.csv",clear
keep if margin=="unconditional" & sample=="common_positive" & subgroup=="all" & type=="marshallian" & good==shock & (good==6 | good==7)
quietly summarize elasticity if good==6,meanonly
scalar oldp=r(mean)
quietly summarize elasticity if good==7,meanonly
scalar oldb=r(mean)
import delimited using "$ROOT/outputs/demand/elasticities_main.csv",clear
keep if margin=="unconditional" & sample=="common_positive" & subgroup=="all" & good==6
quietly summarize elasticity if type=="marshallian" & shock==6,meanonly
scalar newm=r(mean)
quietly summarize elasticity if type=="expenditure",meanonly
scalar newe=r(mean)
quietly summarize n if type=="expenditure",meanonly
scalar newn=r(mean)
quietly summarize support_rate if type=="expenditure",meanonly
scalar news=r(mean)
use `before',clear
local next=_N+1
set obs `next'
replace model="sy_easi" in `next'
replace old_poultry=oldp in `next'
replace old_beef_mutton=oldb in `next'
replace merged_other_meat=newm in `next'
replace expenditure=newe in `next'
replace N=newn in `next'
replace common_support_rate=news in `next'
order model old_poultry old_beef_mutton merged_other_meat expenditure hicksian_own N common_support_rate
format old_poultry old_beef_mutton merged_other_meat expenditure hicksian_own %9.4f
save "$ROOT/outputs/comparison/meat_before_after.dta",replace
export delimited using "$ROOT/outputs/comparison/meat_before_after.csv",replace
export excel using "$ROOT/outputs/meat_merge_results.xlsx",sheet("Meat before after") firstrow(variables) sheetreplace
list,noobs
putdocx paragraph,style(Heading1)
putdocx text ("2. 合并前后肉类结果")
putdocx table meat=data(model old_poultry old_beef_mutton merged_other_meat expenditure),varnames
putdocx table meat(1,1)=("模型")
putdocx table meat(1,2)=("原禽肉")
putdocx table meat(1,3)=("原牛羊肉")
putdocx table meat(1,4)=("合并后其他肉类")
putdocx table meat(1,5)=("食品支出弹性")
putdocx paragraph
putdocx text ("原禽肉与原牛羊肉两列分别为合并前对应组别的自身价格弹性；合并后其他肉类为八类模型重新估计的自身价格弹性；食品支出弹性为合并后的估计。合并后的估计未施加弹性必须为负的限制，也未取两个旧弹性的平均值。")
graph bar old_poultry old_beef_mutton merged_other_meat,over(model) yline(0,lcolor(black)) ytitle("Own-price elasticity") legend(order(1 "Original poultry" 2 "Original beef/mutton" 3 "Merged other meat") rows(1) size(small)) graphregion(color(white)) name(meatmerge,replace)
graph export "$ROOT/outputs/comparison/meat_own_price_comparison.png",width(1800) replace
putdocx paragraph
putdocx image "$ROOT/outputs/comparison/meat_own_price_comparison.png",width(6.2)
use "$ROOT/outputs/exact/model_fit_full.dta",clear
export excel using "$ROOT/outputs/meat_merge_results.xlsx",sheet("Fit checks") firstrow(variables) sheetreplace
format criterion %10.7f
format support_rate %9.4f
putdocx paragraph,style(Heading1)
putdocx text ("3. 估计与核验")
putdocx table fit=data(model N n_parameters moment_jacobian_rank converged support_rate),varnames
putdocx table fit(1,1)=("模型")
putdocx table fit(1,2)=("估计观测数")
putdocx table fit(1,3)=("参数数")
putdocx table fit(1,4)=("矩条件导数秩")
putdocx table fit(1,5)=("收敛")
putdocx table fit(1,6)=("正份额支持率")
putdocx paragraph
putdocx text ("三套精确模型为与九类版本相同设定的一步GMM，使用同样的人口特征、宏观控制与时间变量；省级聚类协方差已保存。主模型保留SY购买选择、家庭均值控制及购买历史，并计算两步省级推断。模型收敛、参数识别秩、解析梯度、压缩矩条件与逐观测矩条件一致性、弹性解析导数均已核对。")
use "$ROOT/outputs/comparison/exact_matched_sample.dta",clear
export excel using "$ROOT/outputs/meat_merge_results.xlsx",sheet("Same sample exact") firstrow(variables) sheetreplace
keep if (grouping=="nine" & inlist(good,6,7)) | (grouping=="eight" & good==6)
format marshallian_own expenditure %9.4f
putdocx pagebreak
putdocx paragraph
putdocx text ("合并前后另取六套精确模型正预测份额支持的交集，使用完全相同的家庭月重新计算弹性（不重新估计参数），用于排查支持样本变化的影响：")
putdocx table matched=data(grouping model good N marshallian_own expenditure),varnames
putdocx table matched(1,1)=("组别")
putdocx table matched(1,2)=("模型")
putdocx table matched(1,3)=("食品编码")
putdocx table matched(1,4)=("观测数")
putdocx table matched(1,5)=("自身价格弹性")
putdocx table matched(1,6)=("支出弹性")
use "$ROOT/outputs/exact/regularity_common_full.dta",clear
export excel using "$ROOT/outputs/meat_merge_results.xlsx",sheet("Regularity") firstrow(variables) sheetreplace
format slutsky_asymmetry slutsky_max_eigenvalue %10.6g
putdocx paragraph
putdocx text ("精确模型的平均Slutsky矩阵检查如下。最大特征值大于零表示未满足该报告支持上的整体半负定性；自身价格弹性变负与整体曲率是两个不同检查。")
putdocx table reg=data(model slutsky_asymmetry slutsky_max_eigenvalue),varnames
putdocx table reg(1,1)=("模型")
putdocx table reg(1,2)=("最大不对称误差")
putdocx table reg(1,3)=("Slutsky最大特征值")
import delimited using "$ROOT/outputs/inference/other_meat_main.csv",clear varnames(1)
export excel using "$ROOT/outputs/meat_merge_results.xlsx",sheet("SY other meat inference") firstrow(variables) sheetreplace
format estimate se_province_two_step ci_lower ci_upper %9.4f
putdocx paragraph
putdocx text ("SY主模型其他肉类的省级两步delta标准误及95%区间（t临界值，自由度23）：")
replace sample=cond(sample=="raw_all","全部观测","正份额支持")
replace type=cond(type=="expenditure","食品支出弹性","自身价格弹性")
putdocx table ci=data(sample type estimate se_province_two_step ci_lower ci_upper),varnames
putdocx table ci(1,1)=("支持样本")
putdocx table ci(1,2)=("弹性类型")
putdocx table ci(1,3)=("点估计")
putdocx table ci(1,4)=("省级两步标准误")
putdocx table ci(1,5)=("区间下界")
putdocx table ci(1,6)=("区间上界")
putdocx paragraph
putdocx text ("精确模型弹性表在本次试验中报告点估计；参数省级协方差见保存的估计文件。上述支持口径和标准误定义应随结果一并解读。完整交叉价格弹性、补偿弹性、预测支持、价格权重、估计对象和运行日志均保存在本试验目录。")
putdocx save "$ROOT/outputs/meat_merge_results.docx",replace
foreach file in elasticities_full cross_price_common_full prediction_audit_full analytic_derivative_audit {
    use "$ROOT/outputs/exact/`file'.dta",clear
    export excel using "$ROOT/outputs/meat_merge_results.xlsx",sheet("`file'") firstrow(variables) sheetreplace
}
use "$ROOT/outputs/audit/descriptives.dta",clear
merge 1:1 good using `labels',assert(match) nogen
export excel using "$ROOT/outputs/meat_merge_results.xlsx",sheet("Descriptives") firstrow(variables) sheetreplace
display "MEAT_MERGE_REPORT_SUCCESS"
log close
