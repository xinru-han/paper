# Paper 9 script 94: quality response matrix Psi^M -> Psi^H, quality-corrected
# price elasticities, heatmap (F2) and homogeneity figure (F3).
source("/root/data/Paper/央视数据/paper9-easiq/code/00_setup.R")
suppressPackageStartupMessages(library(ggplot2))

ps <- fread(file.path(DIR_TAB, "t3b_stageB_price_coefs.csv"), encoding = "UTF-8")
sa <- readRDS(file.path(DIR_INT, "stageA.rds"))
pe <- readRDS(file.path(DIR_INT, "price_elasticities.rds"))
th <- fread(file.path(DIR_TAB, "t3_theta.csv"), encoding = "UTF-8")[eval_at == "mean"]

## Psi^M: 13 x 14 from the price-version Stage B
PsiM <- matrix(NA_real_, 13, 14, dimnames = list(PK13, G14))
for (cc in PK13) {
  sub <- ps[category == cc & grepl("^lnp_", term)]
  PsiM[cc, as.integer(sub("lnp_", "", sub$term))] <- sub$est
}
thx <- ps[term == "ln_x", .(category, theta_x = est)]   # theta in the price spec
PsiH <- PsiM + outer(thx$theta_x[match(PK13, thx$category)], sa$wbar)
fwrite(as.data.table(PsiM, keep.rownames = "category"), file.path(DIR_TAB, "t6_psiM_matrix.csv"))
fwrite(as.data.table(PsiH, keep.rownames = "category"), file.path(DIR_TAB, "t6a_psiH_matrix.csv"))

## quality-corrected quantity price elasticities: eps_q = eM - PsiM
epsq <- pe$eM - PsiM
fwrite(as.data.table(epsq, keep.rownames = "category"), file.path(DIR_TAB, "t6c_eps_quality_corrected.csv"))
own <- data.table(category = PK13, eM_own = diag(pe$eM[, 1:13]),
                  psiM_own = diag(PsiM[, 1:13]), epsq_own = diag(epsq[, 1:13]))
fwrite(own, file.path(DIR_TAB, "t6d_ownprice_before_after.csv"))
logmsg("94: own-price psi mean = ", round(mean(own$psiM_own, na.rm = TRUE), 3))

## F2 heatmap
ml <- melt(as.data.table(PsiM, keep.rownames = "g"), id.vars = "g",
           variable.name = "k", value.name = "psi")
ggsave(file.path(DIR_FIG, "fig2_psi_heatmap.png"), width = 9, height = 6, dpi = 150,
  plot = ggplot(ml, aes(k, g, fill = pmax(pmin(psi, .5), -.5))) + geom_tile() +
    scale_fill_gradient2(low = "#b2182b", mid = "white", high = "#2166ac", name = "psi^M") +
    labs(x = "price of k", y = "quality of g",
         title = "Quality response matrix Psi^M (winsorized at ±0.5)") +
    theme_minimal(base_size = 10) + theme(axis.text.x = element_text(angle = 60, hjust = 1)))

## F3 homogeneity test figure
hb <- fread(file.path(DIR_TAB, "t6b_homogeneity_test.csv"), encoding = "UTF-8")
ggsave(file.path(DIR_FIG, "fig3_homogeneity.png"), width = 8, height = 5, dpi = 150,
  plot = ggplot(hb, aes(reorder(category, sum_psi_plus_theta), sum_psi_plus_theta)) +
    geom_col(fill = "steelblue") +
    geom_errorbar(aes(ymin = sum_psi_plus_theta - 1.96 * se,
                      ymax = sum_psi_plus_theta + 1.96 * se), width = .25) +
    geom_hline(yintercept = 0, linetype = 2) + coord_flip() +
    labs(x = NULL, y = "sum_k psi_gk + theta_g (0 under homogeneity)",
         title = "Zero-degree homogeneity of quality choice") +
    theme_minimal(base_size = 11))
logmsg("94: done")
