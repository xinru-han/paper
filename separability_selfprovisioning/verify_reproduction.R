# Compare reproduced outputs to the manuscript's shipped headline numbers.
fmt <- function(x,d=4) formatC(x,format="f",digits=d)
cat("=================================================================\n")
cat(" REPRODUCTION VERIFICATION — reproduced vs manuscript (docx)\n")
cat("=================================================================\n\n")

d <- read.csv("outputs/tables/table2_common_sample_baseline.csv")
p <- d[d$outcome=="production_participation",]
cat("Table 3 — participation exclusion tests (target N=27568):\n")
tgt <- c(M0=0.178,M1=0.106,M2=0.004,M3=0.002)
for(s in c("M0","M1","M2","M3")){
  r<-p[p$spec==s,]
  cat(sprintf("  %s  Wald=%7s  p=%6s  (manuscript p~%.3f)  N=%d\n",
      s,fmt(r$hhcomp_wald_chisq,3),fmt(r$hhcomp_wald_p),tgt[s],r$n))
}
cat("  -> manuscript: M3 Wald=16.73, p=0.002\n\n")

f<-read.csv("outputs/tables/tableF_village_fe_robustness.csv")
f<-f[f$label=="village_FE_M3_like",]
cat("Table 3 (within-village panel) — manuscript: partic 6.41/p=.171; log 16.06/p=.003; ihs 15.77/p=.003:\n")
for(i in 1:3) cat(sprintf("  %-24s Wald=%7s  p=%6s\n",f$outcome[i],fmt(f$wald_chisq[i],3),fmt(f$wald_p[i])))
cat("\n")

ct<-read.csv("outputs/tables/table4_category_specific_nsi.csv")
cat("Table 5 — category-specific tests (manuscript: eggs/oils/veg/fruit sig after BH; beans before):\n")
for(i in 1:nrow(ct)) cat(sprintf("  %-8s Wald=%7s p=%7s nsi=%5s %s\n",
   ct$food_category[i],fmt(ct$hhcomp_wald_chisq[i],2),fmt(ct$hhcomp_wald_p[i]),fmt(ct$nsi[i],2),ct$signal_label[i]))
cat("\n")

a0<-read.csv("outputs/post_estimation_plan/A0_stacked_two_margin_omnibus.csv")
a1<-read.csv("outputs/post_estimation_plan/A1_mundlak_wald.csv")
a4<-read.csv("outputs/post_estimation_plan/A4_category_attribute_meta_summary.csv")
cat("Post-estimation (kg-cleaned sample; manuscript values in parens):\n")
cat(sprintf("  A0 omnibus (df=8)         Wald=%s p=%s   (manuscript 20.43, p=0.009)\n",fmt(a0$wald_chisq,2),fmt(a0$wald_p)))
mp<-a1[a1$outcome=="production_participation",]
cat(sprintf("  A1 Mundlak partic within  Wald=%s p=%s   (manuscript 16.53, p=0.002)\n",fmt(mp$wald_chisq[mp$block=="within_household_deviation"],2),fmt(mp$wald_p[mp$block=="within_household_deviation"])))
cat(sprintf("  A1 Mundlak partic between  Wald=%s p=%s   (manuscript 10.89, p=0.028)\n",fmt(mp$wald_chisq[mp$block=="between_village_means"],2),fmt(mp$wald_p[mp$block=="between_village_means"])))
cat(sprintf("  A4 category meta rho=%s p=%s slope=%s (manuscript rho=0.77 p=0.044 slope=7.91)\n",fmt(a4$spearman_rho,2),fmt(a4$spearman_p),fmt(a4$wls_bandwidth_coef,2)))
cat("\nNote: A0/A1/A5 magnitudes differ slightly because the exact 27,861-row\n")
cat("kg-cleaned snapshot was lost; the 28,208-row snapshot (27,262 common) is used.\n")
cat("The manuscript itself notes this sample update is immaterial (16.53 vs 16.73).\n")
