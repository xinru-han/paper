RESEARCH ARTICLE

# Regional Differentiation of Agricultural Land-Service Scale Coupling and Grain Yield in the Beijing-Tianjin-Hebei Region

Xinyan Wang   Lifu Zheng  Shuying Zhang  Chengbin Xi  Yunlu Zhang

School of Landscape Architecture, Beijing Forestry University, Beijing, China

Correspondence: Lifu Zheng (zhenglifu22@mails.ucas.ac.cn) | Yunlu Zhang (zhangyunlu@bjfu.edu.cn)

Received: 7 August 2025 | Revised: 27 October 2025 | Accepted: 1 November 2025

Funding: This work was supported by the Fundamental Research Funds for the Central Universities (QNTD202503) and National Key Research and Development Program of China (Program No. 2024YFD2200900).

Keywords: agricultural service scaling | coupling coordination | land degradation risk | land fragmentation | nonlinear yield response spatial heterogeneity | sustainable intensification

## ABSTRACT

Addressing the risks of land degradation from farmland fragmentation and misaligned inputs, this study examines the coordination between land consolidation and agricultural service systems in the Beijing-Tianjin-Hebei (BTH) region. Historically, asynchronous development between these systems has created structural mismatches, raising the risk of underutilization, ecological inefficiency, and yield decline. Land-service coordination and its nonlinear relationship with grain yield are evaluated to inform region-specific strategies for sustainable land use. The farmland landscape pattern (FLP) index and a TOPSIS-based service index capture land and service scaling. The coupling coordination degree (CCD) model measures land-service synergy, while a generalized additive model (GAM) reveals a threshold effect: yields remain limited at low-to-moderate coordination but rise sharply once CCD exceeds \~0.8. Fixed-input and fixed-FLP analyses indicate that consolidation is a prerequisite for service expansion to effectively enhance yields. k-Means clustering identifies three main agricultural systems: (1) low-coordination, low-yield zones in ecologically sensitive areas; (2) high-coordination, high-yield peri-urban zones; and (3) moderate-to-high coordination, lower-yield traditional farming regions. Within each cluster, XGBoost-SHAP reveals heterogeneous marginal effects of irrigation, labor, fertilizer, protected agriculture, and FLP. A secondary clustering delineates finer subtypes, enabling county-level, precision management. Overall, intensification under weak structural coordination is inefficient and heightens degradation risk; productivity gains depend more on optimizing land structure and aligning services than on input volume. By integrating coordination metrics with interpretable machine learning, the study advances a hierarchical typology—spanning macro-regional systems and intra-cluster subtypes—to guide spatially targeted, sustainability-oriented land governance in the BTH region.

## 1 | Introduction

According to the Global Report on Food Crises 2024, jointly released by FAO and other international agencies, approximately 218.6 million people worldwide are currently experiencing severe food insecurity (Mohammed et al. 2025). As one of the most populous nations, China must feed nearly 20% of the global population with less than 9% of the world's cultivated land, creating sustained pressure on its agricultural resources (Ghose 2014). China's agricultural trajectory is shaped by its evolving land-tenure system (Sun et al. 2018). Since the 1978 Reform and Opening-Up, the Household Responsibility System granted farmers individual land-use rights, greatly boosting productivity and easing food shortages (Hao et al. 2023). However, this reform also led to widespread land fragmentation, with farmers managing multiple scattered plots. Fragmentation remains a major barrier to agricultural modernization, limiting mechanization and increasing labor and production costs. It also contributes to functional land degradation by reducing land-use efficiency, complicating field operations, and increasing risks of land abandonment, especially in marginal or aging farming communities. Land consolidation is widely seen as a key solution (Zhou et al. 2020). Where consolidation is slow or constrained by institutional and physical limitations, alternative mechanisms have emerged: agricultural service organizations increasingly provide specialized and integrated services that enhance production efficiency (Veeck et al. 2020). Yet the asynchronous development of these two approaches has created mismatches within China's agricultural system.

Given the structural complexity of Chinese agriculture, “agricultural scale management" has come to encompass more than land expansion (Min et al. 2023). Scholars increasingly distinguish two dimensions: land scale and agricultural service scale. This distinction is vital, as land area alone cannot fully capture modernization dynamics (Huttunen 2019). Ideally, modern agriculture is practiced on consolidated land—large, contiguous, regularly shaped plots that enhance input efficiency and sustainability. In contrast, unconsolidated land presents structural barriers to modernization and reflects a fundamentally different spatial configuration (Ntihinyurwa and de Vries 2021) Meanwhile, service scaling refers to specialized, outsourced operations—such as mechanization, irrigation, fertilization, protected agriculture, and skilled labor—that allow smallholders to access economies of scale without altering land tenure (Niroula and Thapa 2005). Policymakers increasingly view service-system expansion as key to integrating smallholders into modern agriculture (Ren et al. 2023). However, greater land or service scale is not inherently better; outcomes depend on local context and adaptation. Fragmentation can be beneficial in specific socio-ecological settings—such as densely populated or mountainous areas—where it supports crop diversity and ecological resilience (Jackson et al. 2012). At the same time, persistent issues like nonpoint source pollution and soil compaction suggest that overapplication of inputs remains a problem, revealing inefficiencies in resource allocation.

In theory, land consolidation and agricultural service scaling should proceed in coordination, forming an integrated system to boost efficiency, reduce costs, and raise yields. However, prior evidence reveals a paradox: stronger coupling between land and services does not always lead to higher productivity (Zhong et al. 2020). This divergence points to a structural mismatch namely, the asynchrony between land consolidation and service expansion. Despite national efforts, land fragmentation persists in many areas, undermining the effectiveness of mechanized services (Luo et al. 2024). Scattered, irregular plots often compel reliance on manual labor, increasing costs and limiting operational efficiency (Mead 2005). In addition, large-scale farming without localized green technologies and precision inputs often results in inefficient resource use. In underdeveloped regions, even where land restructuring has enabled physical scale, weak infrastructure and insufficient service systems suppress productivity (Tripp 2006), contributing to land abandonment and other forms of underutilization (Sun et al. 2025). Addressing these mismatches—whether due to inadequate services or poor alignment between land structure and delivery—is essential for improving resource efficiency and unlocking the potential of integrated agricultural scaling.

In recent years, cultivated land in China has shifted northward, forming a pattern of "north-to-south grain transfer," with northern China contributing an increasing share of national grain supply (Yougui et al. 2016). As a major urban cluster, the Beijing-Tianjin-Hebei (BTH) region exemplifies the challenge of coupling land consolidation with the scaling of agricultural services while facing multiple land-use pressures. Rapid urbanization nearly doubled urban land from \~3574 to \~6829 km² between 2000 and 2015, driving cropland loss, fragmentation, and conversion to artificial land (Tang et al. 2021; Xu et al. 2023), which in turn has accelerated cropland abandonment (Zhang, Yang, et al. 2024). Groundwater storage in the North China Plain declined at \~2.2cm/year during 2003-2010 (Feng et al. 2013), and under combined agricultural and urban demand, BTH has become one of the areas most severely affected by ecological water risks (Du et al. 2024). Falling groundwater levels and intensified evaporation have also aggravated soil salinization, posing serious threats to productivity and ecosystem stability (Zhao et al. 2022). These compounded pressures underscore the limits of simply expanding acreage or intensifying inputs amid rapid urbanization and escalating ecological risks (Bao et al. 2021). Stark intra-regional disparities in development, resources, infrastructure, and governance create highly uneven demand for agricultural services (Wang and Kuang 2023). Mismatches between service provision and local needs can result in over- or under-scaling, causing efficiency losses, ecological harm, and inequality (Cardenas et al. 2002). Additional barriers—weak land tenure, low willingness to transfer land, rural aging, limited policy awareness, and inconsistent reform enforcement—further impede effective coupling. With little room for land expansion, improving landuse efficiency while maintaining appropriate operational scales is essential for sustainable grain production in BTH (Sharma et al. 2023). Key questions thus arise: how to evaluate land-service scaling adequacy across counties; whether further consolidation is needed; whether inputs are excessive or insufficient; and, crucially, how land-service coupling translates into yield performance. Addressing these issues is vital for targeted, county-level governance in this complex transitional region.

To address these questions, the analysis focuses on 2000-2022, a critical period for farmland consolidation and service scaling in China. This timeframe encompasses major reforms—such as the abolition of the agricultural tax, adjustments to grain procurement and storage, and the institutionalization of land transfer and moderate-scale management—capturing both the evolution and drivers of consolidation (Zhang, Tsai, and Chung 2024). Data availability is also favorable, with statistical records and remote-sensing products remaining consistent and allowing robust cross-validation. Within this context, the study quantitatively examines county-level relationships between land consolidation, service scaling, and grain yield in the

![](images/eb1722673f7c60ca19d4c643d46af70f89796659c0b53cee154b03598d67f028.jpg)  
FIGURE 1 | Study area location. Wiley acknowledges that the borders within the figure are subject to multiple territorial claims. [Colour figure can be viewed at wileyonlinelibrary.com]

BTH region, and provides targeted policy recommendations for region-specific agricultural development. The specific objectives are as follows: (1) to measure the degree of land consolidation—represented by indicators of land fragmentation—and the level of agricultural service scaling, quantified using the Technique for Order Preference by Similarity to Ideal Solution (TOPSIS) based on key inputs (irrigation, fertilizer use, mechanization, labor, and protected agriculture); (2) to examine the coupling-yield relationship using generalized additive models (GAMs) to capture potential nonlinear patterns; (3) to classify the study area by coupling and yield using k-means clustering, identifying three types: low-coordination, low-yield zones in ecologically sensitive areas; high-coordination, high-yield periurban zones; and moderate-to-high coordination, lower-yield traditional farming regions; (4) within each type, to apply GAMs to characterize nonlinear yield responses to irrigation, fertilizer, mechanization, labor, protected agriculture, and farmland landscape pattern (FLP), and to use XGBoost with SHAP to quantify each factor's relative importance; and (5) to conduct a second k-means based on input variables and fragmentation metrics to reveal finer-grained subtypes that support precision, contextspecific policy design.

## 2 | Methods

## 2.1 | Study Area and Data Sources

This study examines the BTH region, a core urban agglomeration and major grain-producing area in China undergoing rapid urbanization and rural transformation. It includes Beijing, Tianjin, and Hebei Province, covering 198 county-level divisions (Figure 1). As counties are the basic units of agricultural governance and policy implementation, a county-scale analysis helps reveal spatial heterogeneity in land use and input coordination, providing a basis for targeted policy strategies.

Multiple data sources were integrated to capture both land characteristics and agricultural socioeconomic conditions. Land use data and administrative boundaries were obtained from the Resource and Environmental Science Data Center of Wuhan University and the Chinese Academy of Sciences (https://www. resdc.cn/DataSearch.aspx). Agricultural inputs and grain yield data—including irrigation, fertilizer use, mechanization, and rural labor—were compiled from the official Statistical Yearbooks of Beijing, Tianjin, and Hebei (https://www.stats.gov.cn/sj/ndsj/).

## 2.2 | Analytical Methods

## 2.2.1 | Land Scaling and Agricultural Service Scaling

2.2.1.1 | FLP Index and Weight Assignment. Farmland fragmentation and consolidation were assessed using six landscape metrics (Xu et al. 2023) (Table 1): Number of patches (NP; Equation 1), largest patch index (LPI; Equation 2), landscape shape index (LSI; Equation 3), area-weighted mean shape index (AWMSI; Equation 4), patch density (PD; Equation 5), and aggregation index (AI; Equation 6). Indicators were calculated at the county level with the landscapemetrics package in R (v4.3.3).

To integrate these indicators into a composite index, principal components analysis (PCA) was applied after direction alignment and standardization. Two principal components (eigenvalue >1) explained 86.2% of the total variance. The FLP index was then constructed as a variance-weighted composite and rescaled to [0,1], where higher values indicate greater fragmentation.

Agricultural service scaling was quantified using a dual-ideal TOPSIS based on five standardized input ratios: irrigation, fertilizer, mechanization, rural labor, and protected agriculture.

al     n   ces  le.
<table><tr><td>Target level</td><td>Indicator category</td><td>Indicator name</td><td>Calculation formula</td><td>Equation number</td><td>Index direction</td></tr><tr><td rowspan="6">Fragmentation of the agricultural landscape</td><td>Patch proportion</td><td>NP</td><td>Total number of patches</td><td>(1)</td><td>+</td></tr><tr><td></td><td>LPI</td><td>LPI = Area of the largest patch × 100 Total landscape area</td><td>(2)</td><td></td></tr><tr><td>Regularity of shape</td><td>LSI</td><td>LSI = Total edge lenght 2√π×Total patch area</td><td>(3)</td><td>+</td></tr><tr><td></td><td>AWMSI</td><td>AWMSI = Σ Patch area × Shape index of each patch) Total landscape area</td><td>(4)</td><td>+</td></tr><tr><td>Spatial distribution</td><td>PD</td><td>PD = Number of patches × 10,000 (patches per 100 ha) Total landscape area</td><td>(5)</td><td>+</td></tr><tr><td></td><td>AI</td><td>Number of adjacent edges between patches of the same class ×100 Maximum possible adjacent edges</td><td>(6)</td><td>一</td></tr></table>

Each year, the top and bottom 10% of counties (by 3-year rolling mean yield) defined the ideal and anti-ideal reference sets. County scores were computed from Euclidean distances to these vectors, yielding a 0-1 index representing closeness to high-yield input configurations (Abdolalizadeh et al. 2025). Provincespecific reference sets were used to reduce heterogeneity.

2.2.1.2 | Coupling Coordination Between Land and Service Scaling. Coupling coordination between land and service scaling was assessed using the coupling coordination degree (CCD) model (Pan et al. 2024).

![](images/a840db4e6678577d0a5a1adf943484587d3a139743989f2f43f7efa68c350c48.jpg)

where C is the coupling degree, T the comprehensive development level, and D the CCD. Equal weights (α = 0.5) were assigned to the two subsystems to reflect their comparable importance in agricultural modernization.

## 2.2.2  Modeling the Nonlinear Effects of Coordination and Input Factors on Grain Yield

To investigate how resource coordination affects agricultural productivity, a multistep analytical framework combining GAM and k-means clustering was employed, with XGBoost used as an auxiliary exploratory tool to verify nonlinear patterns. The GAM was first applied to standardized annual panel data (2000-2022) to capture the nonlinear relationship between the CCD and grain yield. All variables were Z-score normalized for comparability. The model was implemented in R using the mgcv package, and smooth terms were selected via generalized cross-validation. Subsequently, k-means clustering based on standardized CCD and unit yield was used to identify three dominant agricultural systems representing distinct coordination-productivity configurations. This clustering provided the analytical basis for subsequent within-cluster modeling.

## 2.2.3 | Regional Typology and Yield Drivers Based on Coordination and Input Structure

Within each primary cluster identified from the CCD-yield classification, GAMs were first fitted to capture the nonlinear effects of agricultural inputs—irrigation, fertilizer, mechanization, rural labor, protected agriculture, and FLP—on grain yield. All variables were standardized, and smooth terms were selected via generalized cross-validation. Subsequently, XGBoost was used to evaluate the relative contribution and direction of these input variables, and the resulting SHAP values provided interpretable measures of marginal effects and variable importance across counties. Finally, a secondary k-means clustering using the same standardized indicators was conducted within each cluster to identify finer-scale subtypes that reflect internal variation in input configuration and fragmentation. The elbow method determined the optimal number of subclusters. This integrated procedure—GAM modeling, XGBoost-SHAP interpretation, and secondary clustering—combines statistical modeling with interpretable machine learning to reveal heterogeneous yield mechanisms within each agricultural system.

![](images/cc21c58e0e35d53b25fb938ef3b1db6d28d3031509cc5a17744222fb32b53f0e.jpg)  
(a)  
(b)  
FIGURE 2 | (A) Evolution of land scaling level in counties of the BTH region, 2000–2022. (b) Evolution of agricultural service scaling (TOPSIS) in counties of the BTH region, 2000-2022. [Colour figure can be viewed at wileyonlinelibrary.com]

## 2.3 | Statistical Analysis

All analyses were conducted in R (v4.3.3) and ArcGIS Pro 3.2. Quantitative variables were standardized (Z-score) for comparability. Temporal trends in FLP, service scaling (TOPSIS), and the CCD were assessed using annual boxplots and Mann-Kendall and Sen's slope tests on county-level means (2000-2022). Significance was set at p <0.05 with 95% confidence intervals for slope estimates. Model validation involved multiple checks. For GAMs, smooth terms were selected via generalized crossvalidation, and residuals were tested for normality, heteroscedasticity, and spatial autocorrelation (Moran's I). For XGBoost, parameters were tuned to minimize RMSE and stabilize SHAP distributions, ensuring consistent nonlinear estimates. k-Means clustering robustness was evaluated through repeated initialization (nstart=50) and Silhouette analysis (mean=0.509), indicating acceptable compactness and separation. Sensitivity tests on coupling weight (α=0.4-0.6) and TOPSIS thresholds (5%-15%) confirmed stability (ρ> 0.9). All maps used the Albers equal-area projection (WGS 84). Unless stated otherwise, tests were two-tailed with p < 0.05.

## 3 | Results

## 3.1 | Spatial Evolution of Land and Service Scaling in the BTH Region

Figure 2 illustrates the spatial evolution of FLP and agricultural service scaling (TOPSIS index) in the BTH region from 2000 to 2022. Both dimensions show distinct trajectories and spatial heterogeneity, yet reflect a shared pattern of gradual systematization. Northwestern Hebei has consistently maintained low fragmentation, shaping a stable northwest-southeast gradient. From 2000 to 2010, mean FLP declined and localized consolidation appeared in parts of central-southern Hebei, while urban peripheries remained relatively integrated. After 2010, FLP rebounded, increasing disparities as many central-southern counties became more fragmented. Service scaling displays a northwest-southeast contrast, lower in the northwest and higher in the southeast. Before 2010, scaling remained modest, though early clusters emerged in south-central and southeastern Hebei. After 2015, rapid growth occurred in central-southern Hebei, though the regional gradient persisted.

![](images/0599547ee6061bee6b501b55deb5fef9c30eb1feb571560444d3286a11243151.jpg)  
FIGURE 3 | Coupling coordination between land consolidation and agricultural service scaling in the BTH region (2000-2022). [Colour figure can be viewed at wileyonlinelibrary.com]

![](images/8ca207f1e5aedd98448a4e038f1de61da14624967dc030eaa2dff153725877a8.jpg)  
FIGURE 4 | Nonlinear relationship between coupling coordination degree and grain yield estimated via GAM.

![](images/e02f08aa9d78fd2d5fb712c8402ba735778c56bdb6747153689a594f1a8e2111.jpg)

![](images/65ab08d77ed6800d810009f422755dc85189d1511f0906f57554315a3bc70917.jpg)  
FIGURE 5 | Spatial and feature-space distribution of the three agricultural clusters based on coupling degree and grain yield. [Colour figure can be viewed at wileyonlinelibrary.com]

## 3.2 | Relationship Between Agricultural Scaling and Grain Yield in the BTH Region

Figure 3 shows a persistent south-high/north-low gradient, evolving from scattered low-moderate patches to a continuous improvement belt. A high-CCD corridor centered on Xingtai-Handan-Hengshui-southern Cangzhou has expanded to adjacent counties, while the northern mountains and the Beijing-Tianjin periphery remain weak. Overall, the pattern shifted from fragmented coordination to structural integration, while retaining a south-strong/north-weak contrast (Figure 3).

To quantify the CCD-yield relationship (Figure 4), a GAM was fitted. The smooth effect of CCD is significant and nonlinear (effective degrees of freedom [edf] = 8.06, F= 172.2, p < 0.001), explaining 26.8% of the deviance (adjusted R²=0.267; Figure 4). Correlation diagnostics also indicate a positive association (Pearson r= 0.384; Spearman ρ = 0.603; both p < 0.001). The partial-effect curve shows modest gains at low-mid CCD but sharp acceleration beyond \~0.8, with no downturn.

k-Means clustering on standardized county-level CCD and unit yield identifies three groups (Figure 5): Cluster 1 (low coordination-lowest yield), concentrated in northern/mountainous belts with high fragmentation and resource constraints; Cluster 2 (high coordination-high yield), scattered in transition/periurban zones where balanced input and favorable conditions convert coordination into superior outcomes; and Cluster 3 (moderate coordination-lower yield), forming a central-southern corridor (Xingtai-Handan-Hengshui-southern Cangzhou), indicating that structural alignment alone does not translate into high productivity.

Overall, gains depend less on scaling land or services in isolation than on context-specific co-scaling of land structure and service provision. Single-factor expansion delivers limited, often diminishing, returns, whereas joint advancement that elevates CCD into a high-coordination range (\~0.8) aligns with accelerated yield improvements—supporting policies that prioritize coordinated scaling and precise input configuration to sustain productivity growth.

## 3.3 | Cluster-Based Analysis of Agricultural Inputs and Grain Yield Using k-Means

## 3.3.1 | Cluster 1: Low Coupling-Low Yield

GAM results for Cluster 1 (adjusted R²=0.41; all smooth terms p <0.01) reveal significant nonlinear effects of agricultural inputs on yield (Figure 6). Irrigation promotes yield up to moderate levels but declines beyond \~40 units, suggesting water stress or inefficiency. Mechanization exhibits irregular responses under fragmented, resource-constrained conditions. Excessive labor input markedly reduces efficiency, likely due to diminishing marginal returns. Protected agriculture shows mixed effects: moderate expansion enhances yield, whereas overuse (>0.07) negatively affects productivity, implying structural or management bottlenecks. Fertilizer input demonstrates a nonlinear effect, with positive responses at moderate levels but diminishing returns and volatility at higher intensities. The FLP index consistently exerts a strong negative effect (edf≈ 3.0, p < 0.001), emphasizing that fragmentation constrains effective input integration.

In Cluster 1, SHAP-based importance ranking for grain yield (Figure 7) is: Irrigation> Protected agriculture> Mechanization > FLP> Fertilizer> Labor. The right panel indicates effect magnitudes rather than directions. Directionally, irrigation suppresses yield at high intensities; FLP is consistently negative; protected agriculture exhibits dual effects, with moderate expansion improving yield but overexpansion reducing it; fertilizer is generally positive at moderate levels but becomes negative at higher intensities; and labor and mechanization exert weaker and unstable influences. The SHAP waterfall plot illustrates a low-yield case where excessive irrigation and land fragmentation drive predictions below the baseline, while other factors play relatively minor roles.

![](images/0c9f1319fccfc6304953a0cfb18b6f08a6ee060fee90f92c06109c6c0998d310.jpg)

![](images/8943561a46d8b4aadc7864085f1131cfb110761751e12fe2aceb46b07aa559d0.jpg)

![](images/73eace92da870b25338f7a15b1dc0cdb8b35c16e0b7fe9ace6fb4b71b1498770.jpg)

![](images/ee5e0bd8c74271f5431f4ea617b1bdef6a277b358b6f698594e121dde007f316.jpg)

![](images/9ab7ec120e3a51aa59369ebc4e891c6cca95adb910da14d5aa9d41cb18a8c13f.jpg)

![](images/0293e063478b5d33dac0b20e2a719772638032e9d7287afac60dc11f7fc7012b.jpg)

![](images/efeb0dd6580037267a07064a78f7a55b5f51bdb7c308c9a523ffa2db9a469781.jpg)  
FIGURE 6 | Nonlinear effects of agricultural inputs on yield in Cluster 1 based on the GAM model.

FIGURE 7 | SHAP-based feature importance and interpretation of yield drivers in Cluster 1. [Colour figure can be viewed at wileyonlinelibrary. com]  
![](images/f19bc8ebe58af4092e48ff29b1bec1ef083ed46cf09f58cc218b669b5b8bdc06.jpg)  
FIGURE 8 | Subgroup typology within Cluster 1 based on input structure and SHAP analysis. [Colour figure can be viewed at wileyonlinelibrary. com]

Secondary clustering further highlights the internal heterogeneity (Figure 8). Subtype A (fragmentation-constrained) has the highest FLP and uniformly high-input levels (n =138, 10.9%).

Consistent with the significant negative effect of FLP in the GAM (edf≈ 3.0, p <0.001), yield in these regions is constrained more by spatial fragmentation than by resource scarcity. Subtype

B (moderate-input) shows intermediate FLP and input levels (n = 966, 76.4%), where low yield suggests that moderate investment or structural alignment alone does not lead to substantial productivity gains. Subtype C (low-input basic) features the lowest FLP and input intensity (n = 161, 12.7%). Here, low yield primarily reflects insufficient resource endowment, although the GAM indicates that irrigation, moderate fertilizer use, and limited facility expansion within low-mid ranges generate clear positive marginal returns.

## 3.3.2 | Cluster 2—Moderate Coupling and High Yield

In Cluster 2, the GAM explained 27.5% of yield variation (Figure 9). Three factors showed significant nonlinear relationships with yield. Mechanization had the strongest effect (edf≈8.6, p <0.001), showing unstable responses at higher intensities. Irrigation was also significant (edf≈7.4, p <0.001), where excessive input (>60%) reduced productivity. FLP exerted a consistently negative effect (edf≈ 3.1, p <0.01), highlighting the persistent constraint of land fragmentation on efficiency. By contrast, fertilizer input, labor, and protected agriculture had limited or insignificant effects.

The SHAP analysis (Figure 10) supported these findings. Mechanization and irrigation emerged as the dominant drivers of yield variation, while FLP also played a nonnegligible negative role. In contrast, fertilizer, labor, and protected agriculture contributed minimally. The waterfall plots further emphasized that excessive mechanization suppressed yield most strongly whereas moderate irrigation provided compensatory benefits.

Secondary clustering identified three distinct subtypes within Cluster 2 (Figure 11). Subtype A (fertilizer-driven and fragmented systems) is characterized by the highest fertilizer input alongside a pronounced FLP effect; although yields remain high, overfertilization and spatial fragmentation undermine efficiency and sustainability. Subtype B (labor-intensive systems) relies most heavily on rural labor, with relatively low mechanization and facility input, reflecting smallholder-dominated, laborcoordinated production. Subtype C (facility-dominated systems) depends on protected agriculture, indicating a capital-intensive, technology-oriented pattern with limited marginal gains. Together, these subtypes demonstrate that while Cluster 2 sustains high yields under moderate coupling, productivity pathways diverge, and risks arise from labor dependence, structural inefficiencies, or input over-intensification.

![](images/cd8655afb5a60274fa6d6ca541b93f459342476f32e7c81d2a6f2025a36d22ea.jpg)

![](images/4f8bb5da41fae45a589239e52feccbd122d9ecd15699a6086b7c5c02b0e45618.jpg)

![](images/2ee39f463fdefb2011527a47982e59c9dea89d8183facad57ba2174b76e1a744.jpg)

![](images/860c7e5055608a85057a89882e1c98bceca370a84cc1ce812705005e79ff72d9.jpg)

![](images/29099504bbb9ead3e1611d7d795ff2442a2703a5fec6b11ba8399e2a6071eaf9.jpg)

![](images/ac1a286ff9f3e2e2a621c210c28266ca8f726d669be5d75442e386683c7b0c4e.jpg)  
FIGURE 9| Nonlinear effects of agricultural inputs on yield in Cluster 2 based on the GAM model.

![](images/44b1c4b4e3ec66388476cdf3b729030bb448befa3023b7888095ae5c2d9d8c7b.jpg)

![](images/79c286e4446ec624036d1707013c13ed860f2f19a5ded4c9863cea7e414757df.jpg)  
FIGURE 10 | SHAP-based feature importance and interpretation of yield drivers in Cluster 2. [Colour figure can be viewed at wileyonlinelibrary. com]

## 3.3.3  Cluster 3: High Coupling With Relatively Low Yield

Cluster 3, concentrated in central and southern Hebei, shows high coordination but only moderate yields. The GAM (Figure 12; adjusted R²=0.17, deviance explained =18.5%) reveals marked nonlinearities. Irrigation improves yield at \~40%-80% and \~100% but declines locally, indicating inefficiency (edf≈8.2, p <0.001). Mechanization has little effect at low levels but boosts yield beyond 2.5kW/ha, with irregular responses (edf≈ 7.5, p <0.001). Labor raises yield between 20 and 60 people/ha and continues to increase slightly beyond that range (edf≈8.5, p <0.001). Protected agriculture contributes negatively (edf≈ 8.1, p <0.001). Fertilizer follows an inverted-U, peaking at \~3-5tons/ha then declining (edf≈6.2, p <0.001). FLP has a consistently negative effect (edf≈ 7.2, p < 0.001), with yields dropping steeply once fragmentation exceeds \~20.

In this cluster, SHAP analysis (Figure 13) highlights FLP, protected agriculture, and labor as the main constraints. FLP is consistently negative, and both protected agriculture and labor suppress yield when overused. Irrigation and mechanization contribute little and remain unstable, while fertilizer is positive at moderate but negative at high intensities. The waterfall plot shows that excessive facilities, labor, and fragmentation drive yield losses, with moderate fertilizer offering limited compensation.

Secondary clustering highlighted three distinct subtypes within this group (Figure 14). Subtype A (input-constrained): most

![](images/c41a18a10be1f5c10824edbc81598d2a76992eed88b2db6ff2e9cb8487c7e118.jpg)  
FIGURE 11 | Typology of Cluster 2 subgroups based on dominant input structure and SHAP explanations. [Colour figure can be viewed at wileyonlinelibrary.com]

![](images/511eceb2fa1ed9c5f1ea5811365583aaf9169a115625c47efb9a57c487187e45.jpg)  
FIGURE 12 | Partial dependence plots from GAMs showing nonlinear effects of input variables on grain yield in Cluster 3.

![](images/91bf3b332891a5b2851fb24958dc9302e6040e2ec84e82ea767bf5ac9dfb2528.jpg)  
FIGURE 13 | SHAP-based feature importance and representative waterfall plot for yield prediction in Cluster 3. [Colour figure can be viewed at wileyonlinelibrary.com]

![](images/f066463ebfde1f44e6f99ec9aae5c8e0fdc1a971543abda905de47020c328663.jpg)  
FIGURE 14 | Typology of Cluster 3 subgroups based on dominant input structure and SHAP-based interpretation. [Colour figure can be viewed at wileyonlinelibrary.com]

inputs contribute little, with only moderate fertilizer and protected agriculture effects. Subtype B (intensively coordinated): all inputs are influential, but high FLP signals persistent structural constraints. Subtype C (labor-mechanization dominant): characterized by strong effects of mechanization and labor with moderate irrigation, while fertilizer, protected agriculture, and FLP play minimal roles, despite FLP's overall negative impact at the cluster level.

Overall, these subtypes confirm that higher fragmentation consistently limits the translation of resource coordination into yield advantages, while localized imbalances in labor and facility inputs also contribute to moderate performance in this otherwise highly coupled region.

## 4  Discussion

## 4.1 | Agricultural Coupling in the BTH Region: Policy Drivers and Resource Reallocation

Spatially, the study covers the BTH region (Figure 1), encompassing 198 counties. Spatial heterogeneity in land and service scaling (Figures 2 and 3) reveals a persistent north-south contrast, with urbanized plains showing higher coordination than mountainous areas. The coordinated advancement of land consolidation and agricultural service systems has been central to shaping large-scale agricultural development in the region. Although both dimensions have progressed in parallel, service scaling has consistently lagged behind land consolidation due to institutional and infrastructural inertia. As shown in Figure 15, scaling declined in the early 2000s, rebounded after 2010, weakened during 2010–2015, and stabilized following the post-2015 policy reforms. These fluctuations mirror the national transition from “expansion" to "optimization,"highlighting the structural inertia inherent in service provision compared with the steadier progress of land integration (Wang et al. 2020).

The evolution of scaling reflects a policy-led transformation shaped by both land-use regulation and service system development. Land consolidation advanced steadily under continuous institutional support—such as the farmland “red line" policy, the Urban and Rural Planning Law, and the High-Standard Farmland Construction Guidelines—while service scaling was more volatile, constrained by labor shortages and fragmented institutions (Liu et al. 2017; Zhang et al. 2017; Zhou et al. 2020). Since 2015, environmental regulations such as the “Zero Growth Action"for fertilizers and the amended Land Administration Law, together with smart agriculture initiatives, have revitalized idle land and reoriented service provision toward efficiency and sustainability (van Loon et al. 2020; Charania and Li 2020).

![](images/5957bb1a8cbd093d2e51273550ae0e2df3c86fd823eac4ba09c593a1f39d9012.jpg)

![](images/0153717376022499629f176a521cc29b61ed3687ebe1b2ef54a53a31312ca77b.jpg)  
Year

![](images/7e59d8fbe502f3aec2de344a0e44a6726f20d839bf24ea0c3eed5db579b4f94f.jpg)  
FIGURE 15 | Temporal evolution of land fragmentation (FLP), service scaling (TOPSIS index), and agricultural coupling degree in the BTH region, 2000-2022. [Colour figure can be viewed at wileyonlinelibrary.com]

Overall, these dynamics underscore that agricultural modernization in the BTH region has stemmed less from market expansion than from institutional alignment. Land and service systems have advanced not independently but through policy regimes that synchronized their development and redirected resources toward sustainable intensification.

## 4.2 | Excessive Resource Inputs and Poor Land Integration as Key Constraints on Yield Improvement

As shown in Figures 4 and 5, the nonlinear CCD-yield relationship exhibits a clear threshold effect—yield rises sharply once coordination exceeds \~0.8. The three identified clusters further delineate distinct coordination-yield regimes across the BTH region, revealing that yield limitations primarily stem from mismatches between land structure and service inputs.

Cluster 1, concentrated in northern Hebei, the Taihang Mountains, and surrounding hills, combines low coupling with low yields. Natural barriers—cold climates, short frost-free periods, and rugged terrain—impede farmland consolidation. High fragmentation undermines modern inputs: despite relatively high irrigation and fertilizer use, yields remain low due to spatial inefficiency and ecological stress. In such fragile systems, mismanagement can trigger erosion, groundwater depletion, or salinization (Hossain et al. 2020). While protected agriculture offers adaptive potential, expansion often reduces arable land and aggravates fragmentation, further suppressing output. Thus, weak land integration and inefficient input use are the core constraints in these underdeveloped zones. Nonlinear and SHAP analyses (Figures 6-8) further confirm that yield stagnation stems from input saturation and imbalance under fragmented land structures.

Cluster 2, located in the fertile North China Plain, represents structurally optimized, high-yield systems. Consolidated land patterns enable efficient mechanization, irrigation, and labor deployment. Evidence from the GAM and SHAP analyses (Figures 9 and 10) confirms that mechanization and irrigation are the dominant yield drivers, though both exhibit diminishing marginal effects at high intensities. SHAP and GAM results identify mechanization and irrigation as the most influential inputs, though with diminishing returns at high intensities. This suggests the system is approaching saturation, where further gains rely on balancing inputs rather than intensification. Sustaining productivity requires maintaining synergy between land structure and service scaling to avoid environmental stress. The refined subtypes (Figure 11) reveal alternative high-yield pathways—mechanization-based, labor-intensive, and facilitydriven—highlighting that balanced land-service synergy, rather than uniform input expansion, underpins sustainable productivity.

Cluster 3, also in the North China Plain, exhibits relatively high coordination but only moderate yields. SHAP analyses show persistent fragmentation constrains returns even under developed services. Most inputs (irrigation, fertilizer, protected agriculture) follow inverted U-shaped responses, reflecting overuse beyond effective thresholds. Labor and mechanization partly compensate but cannot offset structural inefficiencies. This “high-input yet underperforming" configuration illustrates the risk of concentrating resources without spatial restructuring (Tittonell et al. 2007). As shown in Figures 12-14, most inputs in Cluster 3 exhibit inverted-U responses, indicating overuse beyond optimal thresholds; subtype comparisons further confirm that, under similar service intensities, higher fragmentation results in less balanced input structures, emphasizing the dominant role of spatial configuration over input magnitude in determining performance.

These cluster-level patterns point to a common conclusion: structural integration is the critical precondition for translating inputs into yield gains. To test this mechanism more directly, we conducted fixed-input and fixed-FLP analyses. The fixed-input results (Figure 16a) reveal a pronounced threshold effect: yields remain nearly stagnant at low to moderate integration levels but rise sharply once land integration surpasses \~0.8. The fixed-FLP analysis (Figure 16b) provides complementary evidence. When land is highly consolidated, rising TOPSIS scores translate into substantial yield gains, whereas under medium or high fragmentation, the TOPSIS-yield curves remain flat, showing that additional service inputs bring little benefit. These findings align with broader empirical evidence: land consolidation projects in China have been shown to enhance production efficiency and ecological resilience by reducing fragmentation and enabling more effective use of agricultural services (Gao et al. 2024; Jin et al. 2017). Other studies further indicate that consolidation strengthens mechanization efficiency and fertilizer use, laying the foundation for sustainable intensification (Duan et al. 2021). Taken together, the results confirm that spatial restructuring is not a substitute for input scaling but rather a necessary foundation for unlocking its productivity potential.

![](images/ac457ecbee46c8663d2d6731f0da393c7172df96c821306db3af2f40f509c5d0.jpg)

In summary, yield improvements in BTH cannot rely solely on intensification (Zeng et al. 2025). Structural integration—especially moderate land consolidation combined with efficient service deployment—is essential. Future strategies should emphasize spatial optimization, precision agriculture, and sustainable input management to mitigate ecological risks and secure long-term productivity.

## 4.3 | Agricultural Resource Optimization Based on Cluster Characteristics

Based on the integrated SHAP and GAM results, Figure 17 delineates secondary agricultural zones reflecting clusterspecific optimization strategies. XGBoost-SHAP analysis identified distinct yield drivers across the three clusters, underscoring the need for differentiated strategies. Targeting key constraints—including irrigation intensity, labor allocation, protected agriculture, and land fragmentation—allows resource optimization to be tailored to local conditions in the BTH region (Figure 17).

## 4.3.1 | Type I: Resource Restructuring Zones

4.3.1.1 | I-A: Fragmentation-Constrained Systems. Fragmentation is the main constraint, with scarce inputs and low yields. Policies should prioritize land consolidation and spatial coordination, supported by ecological restoration on sloping lands. Enhancing spatial efficiency is essential for irrigation and fertilizer investments to be effective (Hao et al. 2023).

4.3.1.2 | I-B: High-Intensity but Inefficient Systems. This subtype has the highest inputs and yields, yet irrigation and fertilizer exhibit sharply diminishing or even negative returns. Strategies should shift from intensification to efficiency, emphasizing precision fertilization, integrated water-nutrient management, and eco-friendly practices to mitigate environmental stress (van Wesenbeeck et al. 2021).

![](images/b1340d197c6334eb8c2a4d305e5589f2d306f8cae67e446a8d817a40bb51a71f.jpg)  
(a)

![](images/de9b928593ee1d507a533b57925969e1d7d5f61064d34ead328cf0d247b7b9b6.jpg)  
(b)  
FIGURE 16 | Partial dependence of land integration (FLP\_int) on predicted yield. (b) Predicted yield by service scale (TOPSIS), FLP fixed. [Colour figure can be viewed at wileyonlinelibrary.com]

![](images/b1c71b9f6bfd3e61be8760f6b82654b5fbdd91d41c37fc6ee8b0bf1dae2634c3.jpg)  
FIGURE 17 | Spatial distribution of secondary agricultural zones based on cluster-specific resource optimization strategies. [Colour figure can be viewed at wileyonlinelibrary.com]

4.3.1.3  I-C: Low-Input Basic Systems. This subtype is the largest group, characterized by uniformly low inputs constrained by weak endowments rather than fragmentation. Gradual improvements in irrigation, moderate fertilizer use, and small-scale protected agriculture can yield clear marginal gains and foster more stable productivity.

## 4.3.2 | Type II: High-Performance Agricultural Leading Zones

Clusters in this category demonstrate high levels of resource coordination and productivity, serving as benchmarks for modern agriculture.

4.3.2.1 | II-A: Labor-Intensive Systems. Promote mechanization services and digital technologies to reduce dependence on manual labor while maintaining high productivity (Wu et al. 2005).

4.3.2.2  II-B:Fertilizer-DrivenandFragmentedSystems. Implement precision fertilization,land consolidation, and eco-friendly input substitution to curb overuse, address fragmentation, and sustain yields (Yang et al. 2024).

4.3.2.3 | II-C: Irrigation-Dominated Systems. Adopt precision irrigation and integrated water-nutrient management to mitigate diminishing returns and ensure sustainable output (Cai et al. 2025).

## 4.3.3 | Type III: Agricultural Optimization and Transition Zones

Although located in traditional farming regions, these areas remain in transition, and their sustainable productivity depends on targeted, context-specific strategies.

4.3.3.1 | III-A: Low-Input, Moderate-Yield Systems. These counties maintain moderate yields with minimal inputs. Rather than intensification, strategies should focus on improving spatial coordination, piloting adaptive crop rotations, and developing scalable “low-input, high-efficiency" models suited to local contexts (Shi 2003).

4.3.3.2 | III-B: Intensively Coordinated but Structurally Constrained Zones. Characterized by strong irrigation and protected agriculture but limited chemical reliance, these areas are well-positioned for ecological intensification. Policies should promote organic fertilizers, biological pest control, and precision water management, while scaling sustainable land use and farming practices.

4.3.3.3 | III-C: Transitional Mechanized Systems. Excessive dependence on labor, fertilizers, and machinery, combined with weak irrigation and facility support, creates efficiency bottlenecks. Transition strategies should include fertilizer reduction, water-saving technologies, and cropping system restructuring aligned with ecological capacity. Differentiated subsidies and performance-based assessments can guide a shift toward more efficient and greener systems (Zheng et al. 2023).

## 4.4 | Limitations and Future Directions

This study primarily focused on cultivated land inputs, unit grain yield, and land fragmentation, without fully accounting for natural factors such as climate variability, crop types, and cropping systems. As a result, the current analysis may not capture the full complexity of agricultural efficiency or the deeper mechanisms underlying land-input coordination. Future research should adopt more comprehensive modeling approaches—such as spatial panel models, generalized additive mixed models, or spatial econometric frameworks—to better account for spatiotemporal heterogeneity, nonlinear transitions, and potential threshold effects in the couplingyield relationship at the county level (Zhao and Feng 2024; Awokuse et al. 2024).

In addition, expanding the coupling analysis beyond grain yield to incorporate other critical ecosystem services—such as biodiversity, water filtration, and carbon sequestration—would enable a more holistic evaluation of multifunctional landscapes and potential synergies (Yan et al. 2018). Integrating detailed socioeconomic indicators, including farmer income, employment, and policy implementation costs, would further support cost-benefit analyses of sustainable land management practices (Li et al. 2018). Scenario-based modeling of long-term policy impacts in the BTH region could also provide strategic foresight for adaptive governance. Together, these directions position the current study as a foundational step toward more integrated, dynamic, and policy-relevant frameworks for sustainable land system management.

## 5 | Conclusion

This study develops an integrated framework to evaluate the coordination between farmland consolidation and agricultural service scaling and examines its nonlinear relationship with grain yield in the BTH region. Using the FLP index to capture fragmentation and a TOPSIS-based composite indicator to measure service scaling, the CCD model revealed a clear threshold effect: yields remain stagnant under low-to-moderate coordination but increase sharply once land integration surpasses \~0.8. k-Means clustering further identified three dominant system types, and XGBoost-SHAP analysis exposed substantial heterogeneity in input effects. Overall, the results confirm that input intensification alone does not secure higher productivity; rather, structural alignment between land and services is essential.

These findings highlight that fragmented landscapes reduce input efficiency and heighten ecological risks such as erosion, salinization, and soil degradation. Differentiated strategies are thus required: structurally constrained regions should prioritize land integration and ecological restoration; high-performing systems should refine input use to improve marginal efficiency; and transitional zones should adopt balanced, eco-friendly intensification. By emphasizing structural coordination and ecological thresholds, this study provides a scientific basis for place-based, sustainability-oriented agricultural policies in BTH.

Future research should expand this framework by integrating broader natural and socioeconomic dimensions. Climate variability, crop diversity, and ecosystem services such as biodiversity, water regulation, and carbon sequestration should be incorporated to enable more holistic assessments. Methodological extensions including spatial panel models, generalized additive mixed models, and spatial econometric approaches could better capture spatiotemporal heterogeneity and threshold dynamics at the county level. Cluster-specific strategies should also be linked to policy pilots, scenario-based simulations, and precision interventions such as land consolidation, smart agriculture, and sustainable input management to enhance policy relevance. Taken together, these directions position the current study as a foundation for advancing resilient, efficient, and ecologically sound agricultural transformation.

## Data Availability Statement

The data that support the findings of this study are available from the corresponding author upon reasonable request.

## References

Abdolalizadeh, E., H. Bakhoda, and M. Almassi. 2025. "Optimizing Cultivation Choices Through the TOPSIS and Conceptual Models: Expert Insights on Agricultural Practices." Environmental and Sustainability Indicators 27: 100780.

Awokuse, T., S. Lim, F. Santeramo, and S. Steinbach. 2024. "Robust Policy Frameworks for Strengthening the Resilience and Sustainability of Agri-Food Global Value Chains." Food Policy 127: 102714.

Bao, W., Y. Yang, and L. Zou. 2021. "How to Reconcile Land Use Conflicts in Mega Urban Agglomeration? A Scenario-Based Study in the Beijing-Tianjin-Hebei Region, China."Journal of Environmental Management 296: 113168.

Cai, S., X. Zhao, and X. Yan. 2025. "Towards Precise Nitrogen Fertilizer Management for Sustainable Agriculture."Earth Critical Zone 2: 100026.

Cardenas, J. C., J. Stranlund, and C. Willis. 2002. "Economic Inequality and Burden-Sharing in the Provision of Local Environmental Quality." Ecological Economics 40, no. 3: 379–395.

Charania, I., and X. Li. 2020. "Smart Farming: Agriculture's Shift From a Labor Intensive to Technology Native Industry." Internet of Things 9: 100142.

Du, J., Y. Laghari, Y. C. Wei, et al. 2024. "Groundwater Depletion and Degradation in the North China Plain: Challenges and Mitigation Options." Water 16, no. 2: 354.

Duan, J., C. Ren, S. Wang, et al. 2021. "Consolidation of Agricultural Land Can Contribute to Agricultural Sustainability in China."Nature Food 2, no. 12: 1014–1022.

Feng, W., M. Zhong, J. M. Lemoine, R. Biancale, H. T. Hsu, and J. Xia. 2013. "Evaluation of Groundwater Depletion in North China Using the Gravity Recovery and Climate Experiment (GRACE) Data and Ground-Based Measurements." Water Resources Research 49, no. 4: 2110-2118.

Gao, P., C. Yang, Y. Liu, G. Xin, and R. Chen. 2024. "Evaluating the Effect of Comprehensive Land Consolidation on Spatial Reconstruction of Rural Production, Living, and Ecological Spaces." Ecological Indicators 168: 112785.

Ghose, B. 2014. "Food Security and Food Self-Sufficiency in China: From Past to 2050." Food and Energy Security 3, no. 2: 86–95.

Hao, W., X. Hu, J. Wang, Z. Zhang, Z. Shi, and H. Zhou. 2023. "The Impact of Farmland Fragmentation in China on Agricultural Productivity."Journal of Cleaner Production 425: 138962.

Hossain, A., T. J. Krupnik, J. Timsina, et al. 2020. "Agricultural Land Degradation: Processes and Problems Undermining Future Food Security." In Environment, Climate, Plant and Vegetation Growth, edited by S. Fahad, M. Hasanuzzaman, M. Alam, et al., 17–61. Springer International Publishing.

Huttunen, S. 2019.“Revisiting Agricultural Modernisation: Interconnected Farming Practices Driving Rural Development at the Farm Level." Journal of Rural Studies 71: 36–45.

Jackson, L. E., M. M. Pulleman, L. Brussaard, et al. 2012. "Social-Ecological and Regional Adaptation of Agrobiodiversity Management Across a Global Set of Research Regions." Global Environmental Change 22, no. 3: 623–639.

Jin, X., Y. Shao, Z. Zhang, et al. 2017. "The Evaluation of Land Consolidation Policy in Improving Agricultural Productivity in China." Scientific Reports 7, no. 1: 2792.

Li, Y., W. Wu, and Y. Liu. 2018. "Land Consolidation for Rural Sustainability in China: Practical Reflections and Policy Implications." Land Use Policy 74: 137–141.

Liu, X., C. Zhao, and W. Song. 2017. “Review of the Evolution of Cultivated Land Protection Policies in the Period Following China's Reform and Liberalization."Land Use Policy 67: 660–669.

Luo, X., X. Jin, X. Liu, B. Hong, and Y. Zhou. 2024. "Examining the Pathway and Mechanism of Comprehensive Land Consolidation Through the Lens of Rural Neo-Endogenous Development." Journal of Geographical Sciences 34, no. 9: 1739–1760.

Mead, D. J. 2005. "Opportunities for Improving Plantation Productivity. How Much? How Quickly? How Realistic?" Biomass and Bioenergy 28, no. 2: 249–266.

Min, M., H. Li, T. Ma, and C. Miao. 2023. "Will Agricultural Land Scale Management Aggravate Non-Point Source Pollution?-Chaohu Lake Basin, China as a Case Study." Applied Geography 158: 103056.

Mohammed, U. D., A. B. Berlie, and S. B. Wassie. 2025. "The Status of Food Insecurity at the Household Level in the North-Eastern Highlands of Ethiopia."Discover Food 5: 202.

Niroula, G. S., and G. B. Thapa. 2005. "Impacts and Causes of Land Fragmentation, and Lessons Learned From Land Consolidation in South Asia." Land Use Policy 22, no. 4: 358–372.

Ntihinyurwa, P. D., and W. T. de Vries. 2021. "Farmland Fragmentation, Farmland Consolidation and Food Security: Relationships, Research Lapses and Future Perspectives." Land 10, no. 2: 129.

Pan, H., Z. Du, Z. Wu, H. Zhang, and K. Ma. 2024. "Assessing the Coupling Coordination Dynamics Between Land Use Intensity and Ecosystem Services in Shanxi's Coalfields, China." Ecological Indicators 158:111321.

Ren, C., X. Zhou, C. Wang, et al. 2023. “Ageing Threatens Sustainability of Smallholder Farming in China." Nature 616, no. 7955: 96–103.

Sharma, U. C., M. Datta, and V. Sharma. 2023. "Land Use and Management."In Soils in the Hindu Kush Himalayas: Management for Agricultural Land Use, 295-462. Springer International Publishing.

Shi, T. 2003. "Moving Towards Sustainable Development: Rhetoric, Policy and Reality of Ecological Agriculture in China."International Journal of Sustainable Development and World Ecology 10, no. 3: 195-210.

Sun, Y., Y. Miao, Z. Xie, and X. Jiang. 2025. "Address the Challenge of Cultivated Land Abandonment by Cultivated Land Adoption: An Evolutionary Game Perspective." Land Use Policy 149: 107412.

Sun, Z., L. You, and D. Müller. 2018. "Synthesis of Agricultural Land System Change in China Over the Past 40Years." Journal of Land Use Science 13, no. 5: 473–479.

Tang, Z., Z. Zhang, L. Zuo, et al. 2021. "Spatial Evolution of Urban Expansion in the Beijing-Tianjin-Hebei Coordinated Development Region."Sustainability 13, no. 3: 1579.

Tittonell, P., M. T. van Wijk, M. C. Rufino, J. A. Vrugt, and K. E. Giller. 2007. "Analysing Trade-Offs in Resource and Labour Allocation by Smallholder Farmers Using Inverse Modelling Techniques: A Case-Study From Kakamega District, Western Kenya."Agricultural Systems 95, no. 1–3: 76–95.

Tripp, R. 2006. Self-Sufficient Agriculture: Labour and Knowledge in Small-Scale Farming. Routledge.

van Loon, J., L. Woltering, T. J. Krupnik, F. Baudron, M. Boa, and B. Govaerts. 2020. “Scaling Agricultural Mechanization Services in Smallholder Farming Systems: Case Studies From Sub-Saharan Africa, South Asia, and Latin America."Agricultural Systems 180: 102792.

van Wesenbeeck, C. F. A., M. A. Keyzer, W. C. M. van Veen, and H. Qiu. 2021. "Can China's Overuse of Fertilizer Be Reduced Without Threatening Food Security and Farm Incomes?"Agricultural Systems 190: 103093.

Veeck, G., A. Veeck, and H. Yu. 2020. "Challenges of Agriculture and Food Systems Issues in China and the United States." Geography and Sustainability 1, no. 2: 109–117.

Wang, Y., and Y. Kuang. 2023. "Evaluation, Regional Disparities and Driving Mechanisms of High-Quality Agricultural Development in China." Sustainability 15, no. 7: 6328.

Wang, Z., W. Li, Y. Li, C. Qin, C. Lv, and Y. Liu. 2020. "The "Three Lines One Permit" Policy: An Integrated Environmental Regulation in China." Resources, Conservation and Recycling 163: 105101.

Wu, Z., M. Liu, and J. Davis. 2005. "Land Consolidation and Productivity in Chinese Household Crop Production." China Economic Review 16, no. 1: 28–49.

Xu, M., L. Niu, X. Wang, and Z. Zhang. 2023. "Evolution of Farmland Landscape Fragmentation and Its Driving Factors in the Beijing-Tianjin-Hebei Region." Journal of Cleaner Production 418: 138031.

Yan, Y., C. Wang, Y. Quan, G. Wu, and J. Zhao. 2018. "Urban Sustainable Development Efficiency Towards the Balance Between Nature and Human Well-Being: Connotation, Measurement, and Assessment." Journal of Cleaner Production 178: 67–75.

Yang, C., W. Huang, Y. Xiao, Z. Qi, Y. Li, and K. Zhang. 2024. "Adoption of Fertilizer-Reduction and Efficiency-Increasing Technologies in China: The Role of Information Acquisition Ability."Agriculture 14, no. 8:1339.

Yougui, Z., O. Weizhong, K. Chanjuan, and J. Hongpo. 2016. "The South-To-North and North-To-South Flows of Grains and Cereals—Changes to Directions and Quantities of Flows of Grains and Cereals Between North and South in Contemporary China." In Agricultural Reform and Rural Transformation in China Since 1949, 267–286. Bril1.

Zeng, R., M. C. Abate, B. Cai, A. K. Addis, and Y. D. Dereso. 2025. "A Systematic Review of Contemporary Challenges and Debates on Chinese Food Security: Integrating Priorities, Trade-Offs, and Policy Pathways." Food 14, no. 6: 1057.

Zhang, T., J. Yang, H. Zhou, A. Dai, and D. Tan. 2024. "Abandoned Cropland Mapping and Its Influencing Factors Analysis: A Case Study in the Beijing-Tianjin-Hebei Region." Catena 239: 107876.

Zhang, X., J. Yang, and R. Thomas. 2017. "Mechanization Outsourcing Clusters and Division of Labor in Chinese Agriculture." China Economic Review 43: 184–195.

Zhang, Y., C. H. Tsai, and C. C. Chung. 2024. "Evolution of Land System Reforms in China: Dynamics of Stakeholders and Policy Transitions Toward Sustainable Farmland Use (2004-2019)."Heliyon 10, no. 17: e37471.

Zhao, H., B. Gu, D. Chen, et al. 2022. "Physicochemical Properties and Salinization Characteristics of Soils in Coastal Land Reclamation Areas: A Case Study of China-Singapore Tianjin Eco-City." Heliyon 8, no. 12: e12629.

Zhao, Y., and Q. Feng. 2024. "Identifying Spatial and Temporal Dynamics and Driving Factors of Cultivated Land Fragmentation in Shaanxi Province."Agricultural Systems 217: 103948.

Zheng, L., L. Su, and S. Jin. 2023. "Reducing Land Fragmentation to Curb Cropland Abandonment: Evidence From Rural China." Canadian Journal of Agricultural Economics/Revue Canadienne D'Agroeconomie 71, no. 3-4: 355–373.

Zhong, L., J. Wang, X. Zhang, and L. Ying. 2020. "Effects of Agricultural Land Consolidation on Ecosystem Services: Trade-Offs and Synergies." Journal of Cleaner Production 264: 121412.

Zhou, Y., Y. Li, and C. Xu. 2020. "Land Consolidation and Rural Revitalization in China: Mechanisms and Paths." Land Use Policy 91: 104379.