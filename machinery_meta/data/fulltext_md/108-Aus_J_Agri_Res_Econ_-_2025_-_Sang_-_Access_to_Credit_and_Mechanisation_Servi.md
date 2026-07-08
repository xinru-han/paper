# Access to Credit and Mechanisation Service Expenditure: An Analysis Considering Access, Sources, Purposes and Amounts of Credit

Xiance Sang1 Wanglin Ma² Aya Suzuki³ Hepei Zhang4

1College of Economics and Management, Huazhong Agricultural University, Wuhan, China | 2Department of Global Value Chains and Trade, Faculty of Agribusiness and Commerce, Lincoln University, Christchurch, Lincoln, New Zealand | 3Department of International Studies, Graduate School of Frontier Sciences, The University of Tokyo, Kashiwa-Shi, Chiba, Japan | 4School of Economics and Management, Gannan University of Science and Technology, Ganzhou, China

Correspondence: Hepei Zhang (Hepei.Zhang@outlook.com)

Received: 6 December 2024 | Revised: 28 September 2025 | Accepted: 7 October 2025

Funding: The authors received no specific funding for this work.

Keywords: access to credit | conditional mixed process | formal and informal credit | mechanisation service expenditure

## ABSTRACT

This study estimates the impact of access to credit on mechanisation service expenditure by considering farmers' binary credit access decisions and distinguishing between formal and informal credit access. We employ a conditional mixed process model to address selection bias issues and use open-access data from the Rural Development Institute at the Chinese Academy of Social Sciences (Beijing, China) through the 2020 China Rural Revitalization Survey. The theoretical analyses suggest that relaxing credit constraints enables farmers to achieve higher net returns by increasing all variable inputs, including farm machines, until they achieve the expected optimal level. The empirical results reveal that access to credit significantly increases mechanisation service expenditure by 115.5 yuan/mu, and the impact is larger on farmers cultivating small- and medium-sized farms and those residing in the less developed central and western regions. Access to formal and informal credit affects mechanisation service expenditure differently. Specifically, accessing credit from formal sources (e.g., banks) significantly increases mechanisation service expenditure by 44.7 yuan/mu, while accessing credit from informal sources (e.g., friends and relatives) has no statistically significant effect on mechanisation service expenditure. Moreover, credit primarily intended for financing agricultural production significantly increases mechanisation service expenditure by 83.5 yuan/mu, whereas credit used mainly for nonagricultural purposes significantly reduces such expenditure by 25.5 yuan/mu. These findings are further verified by estimating the effects of loan amounts on mechanisation service expenditure. Finally, we also investigate the nexus between mechanisation service adoption and farm performance, revealing that mechanisation service adoption increases crop yield by 12.6% and commercialisation by 77.4%, respectively.

JEL Classification: C21, G21, G23, Q12, Q14

## 1 | Introduction

Agriculture is the “pillar of support" for the economy in developing countries because it provides raw materials for the industrial sectors, raises incomes and employment, reduces poverty and ensures national and global food and nutrition security (FAO 2022; Sher et al. 2023). Nevertheless, the sustainability of agricultural production has been challenged by several barriers, such as labour shortages due to rural-urban migration, rising labour costs and climate change. These barriers reduce crop yields, exacerbating food insecurity (OECD and FAO 2023).

Agricultural mechanisation has the potential to overcome barriers facing smallholder farm production because it can substitute for farm labourers, eliminate drudgery, improve production efficiency and boost farmers' adoption of climate change adaptation strategies (Li et al. 2023; Afridi et al. 2023; Daum 2023; Ma et al. 2024). Farmers can get machines by purchasing, renting or outsourcing services (Ma, Renwick, and Grafton 2018). Purchasing machines is sometimes costly, especially for smallscale farming households. Renting machines requires technical know-how, which involves risks (e.g., risks caused by misoperation) for renters. In comparison, buying outsourcing services enables farmers to overcome the limitations of the other two options. Consequently, outsourcing machinery services has become an optimal option for many smallholder farming households, and it has been increasingly promoted as an indispensable part of inclusive agricultural transformation (Zhang et al. 2017; Tufa et al. 2023).

Some studies have shown that the use of outsourced mechanisation services helps improve production efficiency (Benin 2015; Huan et al. 2022), raise the economies of scope (Takeshima 2017; Qian et al. 2022) and increase farm income (Adu-Baffour et al. 2019; Mottaleb et al. 2017). For example, Takeshima (2017) found that using tractor services significantly increases the returns to scale of agricultural production for farmers who do not own tractors in Nepal. Adu-Baffour et al. (2019) showed that using tractor services improves rural households' farm income and crop yield in Zambia. In China, Huan et al. (2022) found that mechanisation services significantly improve the technical efficiency of maize production in China.

Despite the significant benefits of outsourcing mechanisation services, high service prices and insufficient income have impeded some credit-constrained farmers from benefiting from these services (Lu et al. 2022; Qiu et al. 2021). Access to credit has the potential to help farmers ease liquidity constraints and remove barriers to purchasing mechanisation services. However, farm households, especially those without sufficient collateral, usually cannot access credit or the required amount. They are often excluded from formal financial markets and services due to higher transaction costs associated with credit market access and imperfect information (Belissa et al. 2019; Nakano and Magezi 2020). As a result, credit-constrained farmers cannot purchase needed agricultural inputs such as farm machines, resulting in lower farm productivity and income (Jimi et al. 2019).

To date, it remains unclear whether and to what extent access to credit affects mechanisation service expenditure. Besides, in practice, farmers can seek formal or informal credit. Formal credit refers to the loans provided by formal financial institutions such as banks, credit unions and credit cooperatives, regulated by government law. Informal credit refers to the loan an individual obtains from friends, neighbours and relatives on a reliable and trustworthy basis. Because credit from formal and informal sources differs in terms of conditions, size and coverage and screening and enforcement mechanisms (Regassa et al. 2023), farmers receiving formal and informal credit may behave differently in farm investments. However, the impact of access to formal and informal credit on mechanisation service expenditure has been neglected in the literature.

This study aims to explore six research objectives: (a) to estimate the impact of access to credit on mechanisation service expenditure; (b) to assess the impact of access to formal and informal credit on mechanisation service expenditure; (c) to assess the impact of access to agricultural and non-agricultural credit on mechanisation service expenditure; (d) to explore how loan amount affects mechanisation service expenditure; (e) to estimate the impact of formal and informal loan amount on mechanisation service expenditure and (f) to investigate the nexus between mechanisation service adoption and farm performance, measured by crop yields and commercialisation. These are important issues to be explored. Insights obtained from this study would not only help expand our understanding of the nexus between access to credit and mechanisation service expenditure but also provide evidence that helps the government design appropriate policy instruments that further develop credit markets to ease farmers' access, accelerate agricultural mechanisation and promote rural and agricultural development sustainably.

We make three significant contributions to the literature. First, this study attempts to link farmers' credit access with their expenditure on mechanisation services. It considers farmers' binary credit access decisions, the sources of credit (formal and informal sources), the primary purposes of credit use (agricultural and non-agricultural) and loan amounts. Second, we explore the heterogeneous effects of access to credit on mechanisation service expenditure by farm size and geographical locations. This issue has been neglected in the literature despite evidence indicating that farm size (Li and Huo 2021; Mohammed et al. 2023) and geographical location (Zhou et al. 2020; Ma et al. 2023) determine farmers' access to credit and machinery use. Third, we employ the conditional mixed process (CMP) model to address selection bias issues. Farmers make their own decisions (selfselection) on whether to access credit, which source to obtain it from (i.e., formal or informal), whether they should acquire credit, the primary intended use of the credit (i.e., agricultural or non-agricultural) and the loan amount they seek, depending on their financial and other socioeconomic factors. These facts suggest that credit variables are endogenous, induced by selection bias issues. Failure to account for selection bias and endogeneity issues would lead to biased and inconsistent estimates. The CMP model can control for selection bias from observed and unobserved factors.

The importance of credit in improving farm investments and household welfare has been well documented in the literature. A growing number of studies have shown that improving farmers' access to credit can stimulate agricultural investments (Hossain et al. 2019; Carrer et al. 2020; Harou et al. 2022), improve farm performance (Kassouri and Kacou 2022; Hutchins 2023; Sher et al. 2023), alleviate rural poverty (Kumar et al. 2020; Felkner et al. 2022) and enhance food security (Fink et al. 2020; Le Cotty et al. 2023). For example, the analysis for Bangladesh by Hossain et al. (2019) found that access to credit encourages tenant farmers to adopt modern varieties and improve rice yield. In Zambia, Fink et al. (2020) found that providing small loans during the lean season can improve food security and raise average agricultural output

Sher et al. (2023) revealed that interest-free and village-level credit density promote farmers' market participation and increase their product prices in Pakistan. Therefore, analysing the nexus between access to credit and mechanisation service expenditure helps add new insights in this field.

This study estimates the open-access 2020 China Rural Revitalization Survey (CRRS) data. In China, the rapid development of the agricultural mechanisation service market plays a crucial role in the progress of agricultural mechanisation. Attributed to the Chinese government's financial and policy support, the number of agricultural mechanisation service organisations experienced significant growth, increasing from 165,636 in 2008 to 193,408 in 2021 (Figure 1). The share of mechanisation service organisations with agricultural machinery valued at 500,000 yuan and above in total mechanisation service organisations grew steadily, increasing from 5% in 2008 to 32% in 2021. During this period, the revenue from mechanisation services also showed considerable expansion, from 346.65 billion yuan in 2008 to 481.65 billion yuan in 2021. According to the 2022 National Statistical Bulletin on Agricultural Mechanisation Development, approximately 49.60 million individuals in China were engaged in mechanisation services. The total service area of agricultural machinery operations, including ploughing, sowing, harvesting, electrically powered irrigation and plant protection, reached 7.36 billion mu in 2022.

At the same time, China's rural financial environment has improved significantly following financial system reforms. The previously limited coverage of financial institutions, inadequate financial supply and lack of market competition in rural areas have undergone substantial changes. As of 2023, banking financial institutions covered 97.93% of townships nationwide, with an average of three banking outlets per township, and basic financial services had reached all administrative villages (Zhang et al. 2024). The rapid expansion of rural financial infrastructure has significantly enhanced credit accessibility for rural households, better meeting their financial service needs and providing critical support for purchasing mechanisation services and other productive inputs.

The rest of this paper is organised as follows. Section 2presents the theoretical framework. Section 3 details the estimation strategy in the study. Section 4 introduces the data and descriptive statistics. The results are presented and discussed in Section 5. The final section draws conclusions and policy implications.

## 2 | Theoretical Framework

The theoretical framework of this study is adapted from Mukasa (2017), who constructed a theoretical model linking farmers' optimisation behaviour to credit markets. We assume that farmers maximise the utility of net returns from a single agricultural output. The net returns (NR) of the farmer can be expressed as:

![](images/6e4e5fbaf8ab51a64341917ada8c66fcb5f431f18738f57e29601f56ac9d51c8.jpg)

(1)

where P is the output price; f(M,X, Z) is the farm production function and f(·) is strictly concave; M is the total area of land (fixed in the short run); X represents an aggregate of non-land variable inputs (e.g., labour and machinery); Z is a vector of production shifters capturing farmer- and farm-level characteristics (e.g., age, gender and irrigation ratio); and W is the price of the non-land variable inputs.

We further assume that a farmer has a fixed income I at the beginning of the crop production process and allocates C to household consumption goods with a unit price J. If I > JC + WX, the farmer can self-finance his household consumption and crop production to maximise net returns. However, in most developing countries, some farmers cannot sufficiently afford household consumption and farm investment expenditures with their fixed income, I (Balana et al. 2022; Li et al. 2020; Mishra et al. 2018). Suppose income-constrained households prioritise household income for consumption expenditures to satisfy the basic needs of life. In that case, they must seek credit for farm investment, such as purchasing production inputs, to maintain or enhance farm productivity.

![](images/834903be4b4b61de041a1f2f435946c2928fa79ebc023bd94beec6c9e810403c.jpg)  
Share of mechanisation service organisations with agricultural machinery valued at 500,000 Yuan and above  
FIGURE 1 | Changes in the number of agricultural mechanisation service organisations and the share of mechanisation service organisations with agricultural machinery valued at 500,000 yuan and above. China Agricultural Machinery Industry Yearbook (2009–2022).

To facilitate our settings, we assume that a farmer can only afford a fraction s of variable input expenditure and he must acquire credit to pay a fraction 1 – s of variable input expenditure.1 The lender determines the loan amount K and the interest rate r. Thus, the problem of maximising the utility of net returns is as follows:

![](images/25c7e23d9c180e2b7924d5fe069acc7a0d937c0899a0789012652b1f36f99fec.jpg)

(2)

subject to:

![](images/461668933dec3c66f33a72e123d2b5f581ede061784c2e930b5ad0b19788fed9.jpg)

(2a)

![](images/70821f1aa9cca321a8dc17fc48ba63378399eb3419a0d4639f8f02feeac8bc1e.jpg)

(2b)

where sWX refers to household expenditure on variable inputs paid through self-financing and (1 – s)WX refers to expenditure on variable inputs paid through loans (i.e., credit). Equation (2a) shows that expenditure on variable inputs X is constrained by income I, consumption expenditure JC and the credit limit K(Z,Zc). The maximum loan amount available depends on the production shifter, Z (e.g., farm size), and the consumption shifter, ZC (e.g., household size). Equation (2b) reveals that the loan amount is determined by the value of total land owned γM, where γ is the land price.

The Lagrangian function for this problem is given by:

![](images/a8e763e05233d198c1f4a942de851cf1a6bc29da0ae91c6078f6240105171a4a.jpg)

(3)

where λ and µ are the shadow prices of credit constraints and loan limits, respectively. The Kuhn-Tucker conditions for this problem are as follows:

![](images/3661d564bba7d1d698d6cd11e805b809b45c081318bfe7e1215961e797e77f7b.jpg)

(3a)

![](images/d0682a7a48a9eb218a4479f243e229352f7c20b0444bbb29eb15343e509a898d.jpg)

(3b)

![](images/29fb43cae81c621ca7bd17c75f443fed09f604961c93b773f00b88ce17d6cdcd.jpg)

(3c)

If the credit constraint is not binding (i.e., λ = 0), the maximum quantity of variable inputs X corresponds to the level that equates its marginal value product Pfx(·) to its marginal cost W. However, when the credit constraint becomes binding, as λ and U'(·) are strictl positive, we can obtain Pfx(·) = W[1 + ν(] This suggests that the marginal value product Pfx(·) of variable inputs is higher than their marginal cost. Therefore, due to credit constraints, farmers may use sub-optimal levels of variable inputs. In other words, credit-constrained farmers tend to use production inputs that are less than the optimal level they expect.

The above theoretical analyses suggest that relaxing credit constraints enables farmers to achieve higher net returns by increasing all variable inputs (e.g., fertilisers, pesticides, improved seeds and farm machines) until they achieve the expected optimal level. Some studies have found that access to credit increases farmers' adoption and intensity of use of agricultural inputs, such as hybrid maize (Simtowe and Zeller 2006) and chemical fertilisers (Regassa et al. 2023). This study extends our understanding by exploring how credit access among rural households affects their farm investments, considering mechanisation service investment as a production input. In addition, farmers have different motivations and capabilities for obtaining credit from formal and informal sources (Parappurathu et al. 2019; Chandio et al. 2021), resulting in different impacts on farm investment and performance. Therefore, we also investigate whether access to formal and informal credit makes a difference in determining mechanisation service expenditure and how loan amounts influence it.

## 3 | Estimation Strategy

## 3.1 | CMP Model

The first objective of this study is to estimate the impact of access to credit on mechanisation service expenditure. In this study, access to credit is measured as a binary variable. Mechanisation service expenditure is a variable left-censored at zero because not all farming households have purchased the mechanisation services. Although the instrumental variable-based two-stage least squares (IV-2SLS) regression model (Bayramoglu et al. 2023; Gallea 2023) and the IV-based Tobit (IV-Tobit) model (Kharel et al. 2022; Saroj and Paltasingh 2024) have been used to address endogeneity, they are inappropriate when the treatment variable is binary. In our case, an appropriate model should allow the estimation of the impact of a binary treatment variable on a censored dependent variable and the conditional mixed process (CMP) model is the appropriate one.

The CMP model relaxes the restrictions on the distributions of the selected variables, allowing us to estimate different types of econometric models (e.g., probit and Tobit regressions) jointly (Elmallakh and Wahba 2022; Li and Ma 2023; Zheng and Ma 2022). Besides, the CMP model can address the selection bias arising from observed and unobserved factors and improve estimation efficiency by jointly estimating two or more equations with correlated error terms (Daoud et al. 2020; Martey 2022; Nnaji et al. 2022). Specifically, we jointly estimate the access to credit equation using the probit model and the mechanisation service expenditure equation using the Tobit model. They are specified as follows:

Access to credit equation (probit model):

![](images/0eb43c5a1416c91ce442a118872f1be5cafa561c19ca6e3f4124d9fe4a239663.jpg)

(4)

Mechanisation service expenditure equation (Tobit model):

![](images/1cfd978070aec9472a440af21e657de0341283ffdcbb7c3919d58c4ed3d05257.jpg)

(5)

where C\* is a latent variable denoting the propensity that household i chooses to access credit, which can be identified by a binary observable variable C (1 for credit users and 0 for non-users); E, is a continuous latent variable representing the mechanisation service expenditure by household i; E is the observed mechanisation service expenditure obtained by censoring the latent expenditure at 0. X is a vector of exogenous variables; IV1 represents the instrumental variable for CMP model identification. α1, α2, α3 and α are parameters to be estimated; ε and µ denote the error terms.

The second objective of this study is to examine the differentiated effects of access to formal and informal credit on mechanisation service expenditure. Following Nnaji et al. (2022), we specify a simultaneous equation system within the framework of the CMP model. Specifically, the CMP model jointly estimates one probit model for the access to formal credit equation, one probit model for the access to informal credit equation and one Tobit model for the mechanisation service expenditure equation as follows:

Access to formal credit equation (probit model):

![](images/b0d8b0acc154523c5040b075f1a70aac4bee2d5c53ba5c7e39d35719dd7b58dd.jpg)

(6)

Access to informal credit equation (probit model):

![](images/c36b5cc1c43befa0ae097d11a34cb0ce25a24d507cb8efed04148c52a4d9f07e.jpg)

(7)

Mechanisation service expenditure equation (Tobit model):

![](images/2793d477071122919ac2552a121f07f3f5ce0390b548b8125084a53388ff19b6.jpg)

(8)

where FC is a latent variable denoting the propensity that household i chooses to access formal credit, which can be identified by a binary observable variable FC (1 for formal credit users and 0 for non-users); IC\* is a latent variable denoting the propensity that household i chooses to access informal credit, which can be identified by a binary observable variable IC (1 for informal credit users and 0 for non-users); IV1 and IV₂ indicate the selected instrumental variables. E\*, E and X are as defined earlier. β1, β2, β3, β4, β5, β6 and β7 are parameters to be estimated; µ1i, µ2 and µ₃ are the error terms.

The third objective of this study is to examine the heterogeneous effects of access to agricultural and non-agricultural credit on mechanisation service expenditure. Similarly, we specify a system of simultaneous equations within the CMP framework. In particular, the CMP model jointly estimates one probit model for the access to agricultural credit equation, one probit model for access to non-agricultural credit equation, and one Tobit model for the mechanisation service expenditure equation as follows:

Access to agricultural credit equation (probit model):

![](images/ab6f9f68fd55efe2aa5ef964bb0ab6be5a780c4fba8860b7dc01b6daeee414cc.jpg)

(9)

Access to non-agricultural credit equation (probit model):

![](images/f9895bdf53695285ee1a577eb217c3f0484b943788facb1288c304e5df64e511.jpg)

(10)

Mechanisation service expenditure equation (Tobit model):

![](images/80d7d09eab7fbad68209172bdda7749ef8e4b39ec961b85bf2498c5c5d3559f2.jpg)

(11)

where AC\* is a latent variable representing the propensity that household i obtains credit for agricultural purposes, which can be identified by a binary observable variable AC (1 for agricultural credit users and 0 for non-users); NC\* is a latent variable representing the propensity that household i obtains credit for non-agricultural purposes, which can be identified by a binary observable variable NC (1 for non-agricultural credit users and 0 for non-users); E\*, Ei, Xi, IV1 and IV2 are the same as defined earlier. γ1, γ2, γ3, γ4, γ 5, γ6 and γ7 are parameters to be estimated; ω1i, ω2 and ω3i are the error terms.

Following the fourth research objective, this study further examines the impact of total loan amount on mechanisation service expenditure. Given the censored nature of the total loan amount and mechanisation service expenditure variables, we use the CMP model to estimate two Tobit models as follows jointly:

Total loan amount equation (Tobit model):

![](images/65bd0e1f5d88892807673b7d5f08bb2f211959d50f1040a98153a46d768425d8.jpg)

(12)

Mechanisation service expenditure equation (Tobit model):

![](images/091352b5ecae92e2c95930fd2c5bb641c5494e4213e7716469c76590117bb19c.jpg)

(13)

where A\* is a continuous latent variable representing the total loan amount received by household i; A is the observed total loan amount obtained by censoring the latent expenditure at 0. E, Ei, X and IV1 are the same as defined earlier. θ1, θ2, θ3 and θ4 are parameters to be estimated; φ1 and φ2 are the error terms.

This study also examines the differences in the impact of the formal and informal loan amounts on mechanisation service expenditure as the fifth objective. The CMP model jointly estimates three Tobit models for the formal loan amount equation, informal loan amount equation and mechanisation service expenditure equation as follows:

Formal loan amount equation (Tobit model):

![](images/265f5346600d07313484d1e5a2c42f0a2189b2e3bbdb2c96c9f580d4db310fea.jpg)

(14)

Informal loan amount equation (Tobit model):

![](images/db6a0ca743b95a7709dbdc632351a13419dadbcf11c4e36a6555827e5e06ccc5.jpg)

(15)

Mechanisation service expenditure equation (Tobit model):

![](images/8370e071da8dd8cdd00517f5db20c3bece28e8606a860f8736c746950d72654f.jpg)

(16)

where FA\* is a continuous latent variable representing the formal loan amount received by household i; IA\* is a continuous latent variable representing the informal loan amount by household i; FA‡ and IA are observed by FA and IAi, respectively. E\*, Ei, Xi, IV1 and IV2 are the same as defined earlier. δ1, δ2, δ3, δ4, δ5, δ6 and δ7 are parameters to be estimated; τ1i, τ2 and τ3 denote the error terms.

## 3.2 | Instrumental Variable Identification

For the CMP model to be correctly specified, it is essential to identify valid instrumental variables that are correlated with the endogenous key explanatory variables but uncorrelated with mechanisation service expenditure. This study used a dummy variable indicating whether farmers receive a line of credit from a bank as IV, in Equations (4), (6), (9), (12) and (14). A line of credit is an arrangement between a bank and a customer establishing a preset borrowing limit that can be drawn on repeatedly. A credit line authorised by financial institutions is an essential prerequisite for customers to access credit, especially formal credit, and the credit amount a customer can receive (Swaminathan et al. 2010). The validity of IV, hinges on the assumption that access to a credit line affects mechanisation service expenditure only through its impact on actual credit access. This assumption is plausible because the approval of credit lines is primarily governed by institutional and structural factors, such as rural financial infrastructure, local banking regulations and government-backed lending programmes, rather than by unobservable household characteristics. Credit line eligibility is typically based on standardised, externally verifiable criteria, including documented land tenure, formal credit history and participation in agricultural support schemes. These factors are exogenous to farm-level managerial ability, production efficiency or mechanisation preferences, thereby supporting the exogeneity of IV1.

In addition, we employ a dummy variable reflecting whether a farmer can borrow money from relatives or friends, as IV, in Equations (7), (10) and (15). Access to informal credit often depends on personal social networks, and farmers who borrow from friends or relatives are more likely to obtain informal credit (Cull et al. 2019). We argue that this variable satisfies the exclusion restriction because it primarily reflects a farmer's access to informal sources of liquidity rather than factors that directly influence mechanisation service expenditure. While social ties may provide access to information or support, the expenditure on mechanisation services is mainly driven by household labour availability, financial capacity and farm size—all of which are explicitly controlled for in our empirical model. Moreover, we include covariates like education, village cadre and cooperative membership to capture variation in social capital and information access, mitigating concerns about potential omitted variable bias.

Following previous studies (Ma et al. 2022; Vatsa et al. 2023), we performed a falsification test proposed by Di Falco et al. (2011) to verify the validity of the selected IVs statistically. The results are presented in Appendix Table A1 in Supporting Information. The results show that the chosen IVs affect farmers' credit access decisions and loan amounts, but do not affect the mechanisation service expenditure variable. These findings suggest that IV, and IV, fulfil the conditions of correlation and exogeneity (Geffersa and Tabe-Ojong 2023). Thus, they are valid instruments.

## 3.3 | IPWRA Estimator

The last research objective of this study is to investigate the impact ofmechanisation service adoption on farm performance, measured by crop yields and commercialisation. Since farmers self-select to adopt mechanisation services, potential selection bias must be addressed. We could not identify valid instrumental variables for these outcome variables that satisfy the exclusion restriction. Therefore, we employ the inverse probability weighted regression adjustment (IPWRA) estimator to correct for self-selection bias. Unlike propensity score matching (PSM), which requires correct specification of the treatment model, IPWRA is doubly robust and yields consistent estimates if either the treatment or the outcome model is correctly specified (Zhang et al. 2025; Li et al. 2025). This property makes IPWRA particularly appropriate for our analysis, allowing us to obtain reliable estimates of the effects of mechanisation service adoption on farm performance.

The IPWRA estimator specifies the treatment and outcome models as follows:

![](images/1a86ad6033bdb4a3590868d7b76ae8e63cb00e18fdf82aa3c8d3432b121e190d.jpg)

(17a)

![](images/b1065a770f12dba447a767f6cb4fefba6cb20e759c3fe1e4a97871283ce702e6.jpg)

(17b)

where Pr (Ai = 1) refers to the probability that a household adopts mechanisation services in agricultural production. Y refers to the farm performance variable (i.e., crop yield or commercialisation); X refers to the vectors of covariates that affect the treatment assignment and outcome variable; ρ and η are the corresponding parameters; g(Xi, ρ) refers to regression specification of determinants of mechanisation service adoption; f(Xi, η) refers to the regression specification of determinants of farm performance; v and κ, are the random error terms.

Under the analytical framework of potential outcomes, we can estimate the average treatment effects (ATE) of mechanisation service adoption on farm performance as follows:

![](images/afff01de879724d3c7d738a607b5e4199d9bb92ed41fd085f23fce19e63941cb.jpg)

(18)

The IPWRA estimator calculates the predicted outcomes and contrasts their means to obtain the ATE using the inverse of estimated treatment probability weights (Cattaneo 2010).

## 4 | Data and Descriptive Statistics

## 4.1 | Data

This study uses open-access data from the Rural Development Institute at the Chinese Academy of Social Sciences (Beijing, China) through the 2020 China Rural Revitalization Survey (CRRS). The survey collected information on agricultural production in 2019. A multi-stage probability proportional to size (PPS) sampling technique was utilised to collect data. In the first stage, ten provinces were selected based on their geographical location and economic development levels. These include Guangdong, Zhejiang and Shandong from eastern China, Anhui, Henan and Heilongjiang from central China and Guizhou, Sichuan, Ningxia and Shanxi from western China. In the second stage, five counties were selected from each province based on their economic development levels. In the third stage, three towns were randomly selected in each county, and two villages were then randomly selected in each town chosen. In the final stage, around 12-14 households were randomly selected from each selected village and household heads were invited for face-to-face interviews, resulting in a total sample of 3833 rural households.

A pre-tested and well-structured questionnaire was used for data collection. The questionnaire comprised individual characteristics (e.g., age, gender and education), household- and farm-level characteristics (e.g., household size, child ratio, elderly ratio, village cadre, cooperative membership, household income, agricultural machinery, number of grain types, farm size, number of plots, irrigation ratio and natural shocks), village-level characteristics (road condition, distance to town and distance to county), credit access status, loan amounts and expenditure on mechanisation services.

We focus on maize, wheat and rice because these are China's three primary grain crops, forming the backbone of national food production. These crops benefit from well-established mechanisation technologies and mature service markets, with comprehensive mechanisation rates in 2022 reaching 90.60% for maize, 97.55% for wheat and 86.86% for rice. In contrast, crops such as vegetables, fruits and cash crops tend to exhibit lower and more variable mechanisation rates due to greater production heterogeneity and the lack of standardised mechanisation processes. Restricting the analysis to these grain crops enhances comparability across households by focusing on production systems with similar mechanisation contexts. This approach reduces potential confounding factors and improves the internal validity of our findings. It is also consistent with the methodology of recent studies (Wang et al. 2024; Ma et al. 2025). We define “grain-producing households" as cultivating at least one of the three major grain crops, regardless of whether they also grow other crops. After excluding observations with missing values for key variables, the final sample includes 1819 households, of which 1037 grow a single grain crop and 782 cultivate two or more.

We acknowledge that limiting the sample to grain-producing households may reduce generalizability to farms specialising in non-grain crops. However, given that grain production remains a national priority and is at the centre of China's rural development and mechanisation policies, our findings offer relevant and actionable insights for most Chinese farming households engaged in staple crop production. To address potential concerns regarding crop diversity, we have included a control variable capturing the number of grain crop types grown by each household. This adjustment accounts for differences in crop portfolios and their possible influence on mechanisation service expenditures, further enhancing the robustness of our results.

## 4.2 | Descriptive Statistics

Table 1 presents the definitions and descriptive statistics of the selected variables. Agricultural mechanisation services refer to machinery-based operations, such as ploughing, sowing, pesticide spraying, fertiliser application, irrigation and harvesting, provided by specialised service providers or individual operators. This study focuses on household expenditures on such services in grain production. On average, sample households spend approximately 117 yuan/mu on mechanisation services. Figure 2 depicts the proportional distributions of mechanisation service adoption by production tasks. The figure reveals that most farmers adopted mechanisation services for harvesting, with a percentage of 57%, followed by ploughing and sowing at 51% and 26%, respectively. In addition, about 10%, 10% and 8% of farmers adopted mechanisation services for pesticide spraying, irrigation and fertiliser application, respectively.

Table 1 also shows that around 46% of farm households have accessed credit from formal sources (e.g., banks and credit unions) or informal sources (e.g., relatives and friends). Specifically, about 21% of the farm households received credit from formal sources, while about 25% received credit from informal sources. Approximately 18% of farmers have obtained credit primarily for agricultural production, whereas 28% have used it mainly for non-agricultural purposes such as off-farm businesses, daily consumption and housing. The average total loan amount was 46,300 yuan and the average loan amounts from formal and informal sources were 32,600 yuan and 13,700 yuan, respectively.

Regarding the control variables, on average, the surveyed household heads were 51years old and 76% were male. Respondents received an average of about 8years of school education. The surveyed households had around four members on average. The mean child and elderly ratios were 0.22 and 0.20, respectively. The average annual per capita household income is 16,900 yuan and approximately 45% of farming households own agricultural machinery. The mean farm size was 30.43 mu and the average number of plots cultivated by farm households was 7.31. Around 32% experienced natural shocks (e.g., drought, flooding or insects) in crop production in 2019.

Table 2 reports the mean differences between credit users and non-users in the selected variables. It shows that credit users spend, on average, 27 yuan/mu less than non-users and the mean difference is statistically significant at the 1% level. This finding indicates that access to credit is potentially associated with mechanisation service expenditure. However, the mean differences cannot be used to capture the effect of access to credit on mechanisation service expenditure because it does not account for other confounding factors that jointly influence farmers' credit access decisions and mechanisation service expenditure. In addition, Table 2 also indicates a significant difference between credit users and non-users in terms of age, education, household size, child ratio, elderly ratio, village cadre, household income, number of grain types, farm size, number of plots, irrigation ratio, natural shocks, road conditions, distance to town, distance to county and regional dummies. These systematic differences between credit users and non-users imply the existence of potential self-selection issues. Therefore, it is necessary to address the endogeneity associated with access to credit using rigorous econometric approaches such as the CMP model.

TABLE 1 | Variable definitions and summary statistics.
<table><tr><td>Variables</td><td>Definitions</td><td>Mean (S.D.)</td></tr><tr><td>Dependent variable</td><td></td><td></td></tr><tr><td>Mechanisation service expenditure</td><td>Expenditure on mechanisation services (100 yuan/mu)a</td><td>1.17 (1.44)</td></tr><tr><td>Key explanatory variables Access to credit</td><td>1 if a household has access to credit from formal</td><td>0.46 (0.50)</td></tr><tr><td></td><td>sources (e.g., banks and credit unions) or informal sources (e.g., relatives and friends), 0 otherwise</td><td></td></tr><tr><td>Access to formal credit</td><td>1 if a household has access to credit from formal sources, 0 otherwise</td><td>0.21 (0.41)</td></tr><tr><td>Access to informal credit</td><td>1 if a household has access to credit from informal sources, 0 otherwise</td><td>0.25 (0.43)</td></tr><tr><td>Access to agricultural credit</td><td>1 if a household has access to credit for agricultural production, 0 otherwise</td><td>0.18 (0.38)</td></tr><tr><td>Access to non-agricultural credit</td><td>1 if a household has access to credit for non- agricultural activities, 0 otherwise</td><td>0.28 (0.45)</td></tr><tr><td>Total loan amount</td><td>Total loan amount from formal or informal sources (10,000 yuan)</td><td>4.63 (9.49)</td></tr><tr><td>Formal loan amount</td><td>Loan amount from formal sources (10,000 yuan)</td><td>3.26 (8.22)</td></tr><tr><td>Informal loan amount</td><td>Loan amount from informal sources (10,000 yuan)</td><td>1.37 (4.09)</td></tr><tr><td>Control variables</td><td></td><td></td></tr><tr><td>Age</td><td>Age of household head (HH) in years</td><td>51.26 (15.09)</td></tr><tr><td>Gender</td><td>1 if the HH is male, 0 otherwise</td><td>0.76 (0.43)</td></tr><tr><td>Education</td><td>Education level of HH (years)</td><td>7.68 (3.46)</td></tr><tr><td>Household size</td><td>Number of members in a household (persons)</td><td>4.19 (1.52)</td></tr><tr><td>Child ratio</td><td>Ratio of children (14years or younger) to the number of family members between 15 to 64years old</td><td>0.22 (0.34)</td></tr><tr><td>Elderly ratio</td><td>Ratio of elder (65 years or older) to the number of family members between 15 to 64years old</td><td>0.20 (0.41)</td></tr><tr><td>Village cadre</td><td>1 if any household member is a village cadre, 0 otherwise</td><td>0.16 (0.37)</td></tr><tr><td>Cooperative membership</td><td>1 if any household member is a member of an agricultural cooperative, 0 otherwise</td><td>0.23 (0.42)</td></tr><tr><td>Household income</td><td>Total household income (10,000 yuan/capita)</td><td>1.69 (2.01)</td></tr><tr><td>Agricultural machinery</td><td>1 if household owns agricultural machinery, 0 otherwise</td><td>0.45 (0.50)</td></tr><tr><td>Number of grain types</td><td>Number of grain types grown in a household</td><td>1.43 (0.50)</td></tr><tr><td>Farm size</td><td>Total farm size (mu)</td><td>30.43 (89.68)</td></tr><tr><td>Number of plots</td><td>Number of land parcels</td><td>7.31 (7.83)</td></tr><tr><td>Irrigation ratio</td><td>Ratio of irrigated land to total cultivated land</td><td>0.61 (0.48)</td></tr><tr><td>Natural shocks</td><td>1 if a household experienced natural shocks (e.g., drought, flooding or insects)</td><td>0.32 (0.47)</td></tr><tr><td>Road condition</td><td>1 if the road from village to the local transportation is good, 0 otherwise</td><td>0.77 (0.42)</td></tr><tr><td>Distance to town</td><td>Distance from village to the nearest town (km)</td><td>5.86 (5.84)</td></tr><tr><td>Distance to county</td><td>Distance from village to the nearest county (km)</td><td>23.31 (15.63)</td></tr><tr><td>Eastern</td><td>1 if household resides in eastern region, 0 otherwise</td><td>0.17 (0.37)</td></tr><tr><td>Central</td><td>1 if household resides in central region, 0 otherwise</td><td>0.37 (0.48)</td></tr><tr><td>Western</td><td>1 if household resides in western region, 0 otherwise</td><td>0.46 (0.50)</td></tr><tr><td>IV1</td><td>1 if a household has received a line of credit from a bank, 0 otherwise</td><td>0.34 (0.47)</td></tr><tr><td>IV2</td><td>1 if a household has relatives and friends who can borrow money, 0 otherwise</td><td>0.84 (0.37)</td></tr><tr><td>Observations</td><td></td><td>1819</td></tr></table>

Note: SD refers to the standard deviation.  
aYuan is the Chinese currency (1 USD = 6.90 yuan in 2019); 1 mu =1/15 ha.

![](images/9f3e9f8586e1751a9a84a01996944527e4c19ee05303e327c0aaf9131feddf99.jpg)  
FIGURE 2 | Proportional distributions of mechanisation service adoption.

Figures 3 and 4 illustrate the mean differences in mechanisation service expenditure between credit users and non-users by farm size and geographical locations, respectively. Figure 3 demonstrates that credit users and non-users cultivating small-sized land (≤ 5 mu) spend the highest on mechanisation services, while their counterparts cultivating large-sized farms (> 30 mu) pay the lowest on the same. Figure 4 shows that credit users and non-users living in the Eastern part of China spend the most on mechanisation services, while those in the Western part spend the least. These findings suggest the potential heterogeneous effects of access to credit on mechanisation service expenditure across farm sizes and geographical locations.

Figure 5 illustrates the means of mechanisation service expenditure for farmers choosing different credit sources. Non-users of credit report the highest mechanisation service expenditure relative to formal and informal credit users. The expenditure on mechanisation services reported by the informal credit users is higher than that reported by the formal credit users. These findings suggest that formal and informal credit may impact mechanisation service expenditure differently.

## 5| Results and Discussion

## 5.1 | Impact of Access to Credit on Mechanisation Service Expenditure

## 5.1.1 | Determinants of Access to Credit

Table 3 presents the results obtained from the CMP model, jointly estimated by Equations (4) and (5). The results in the lower part of Table 3 reveal that the correlation coefficient of the error terms, Pε1 ε2, is significant and negative, indicating the presence of negative selection bias due to unobserved factors (Baum 2016). The negative selection bias implies that farmers with higher credit access probability have lower mechanisation service expenditure. Therefore, if we do not use the CMP model to account for the selection bias issues, the impact of access to credit on mechanisation service expenditure would be underestimated.

The second and third columns in Table 3 show the factors influencing farmers' decisions regarding credit access. Although the estimated coefficients help understand the direction of the control variables and farmers' decisions to access credit, they cannot be used to explain the magnitudes of the influence. We therefore calculate the marginal effects, which are presented in the third column of Table 3. The marginal effect of the age variable is significantly negative, indicating that a 1-year increase in age decreases the probability of accessing credit by 0.1%. The finding aligns with the results of Kumar et al. (2020) for India and Chandio et al. (2021) for Pakistan. Compared with younger farmers, older ones are risk-averse and are less capable of paying debt; thus, they are reluctant to seek credit (Ojo and Baiyegunhi 2020). The marginal effect of the education variable is negative and significant, suggesting that the probability of accessing credit could fall by 1.1% with every additional year of schooling. Better-educated farmers are more productive and receive higher incomes than their counterparts with lower education levels, and thus, the former are less likely to be credit-constrained (Chandio and Jiang 2018).

As shown in the third column of Table 3, the elderly ratio variable has a negative and significant marginal effect, indicating that rural households with more elderly members are 8.5% less likely to access credit. Rural households with a high proportion of older people are relatively less productive, and their solvency is also relatively weak (Ojo and Baiyegunhi 2020). Because solvency is an essential factor that credit institutions refer to before granting credit, households with a high proportion of older people are less likely to get credit. The marginal effect of the farm size variable is positive and significant, indicating that rural households with larger farm sizes are 0.1% more likely to access credit. This finding is consistent with Akhtar et al. (2019), who showed that the probability of using credit as a risk management strategy is higher for large farmers compared to small farmers in Pakistan.

The natural shocks variable shows a positive and significant marginal effect in the third column of Table 3, indicating that farmers who experience natural shocks (e.g., drought, flooding or insects) are 7.9% more likely to access credit. Experiencing natural shocks brings higher production losses and reduced incomes, driving farmers to access credit to support household farms and non-farm businesses (Ahmad and Afzal 2022). The marginal effects of the location variables suggest that farmers living in the eastern and central regions are 16.7% and 10.2% less likely to access credit than those living in the western region (the reference region). China's eastern and central parts are more developed and have better economic conditions than the Western ones. Thus, the farmers in the eastern and central regions are less likely to be capital-constrained than those in the western region. These findings confirm location-fixed effects that affect farmers' decisions to access credit. The marginal effect of IV, is positive and statistically significant, suggesting that farmers to whom the bank has granted a credit line are 15.0% more likely to access credit.

TABLE 2 | Mean difference in the selected variable between credit users and non-users.
<table><tr><td>Variables</td><td>Credit users</td><td>Non-users</td><td>Mean difference</td><td>t</td></tr><tr><td>Mechanisation service expenditure</td><td>1.02 (0.05)</td><td>1.29 (0.05)</td><td>-0.27***</td><td>-3.09</td></tr><tr><td>Age</td><td>52.59 (0.49)</td><td>49.71 (0.51)</td><td>-2.89***</td><td>-4.08</td></tr><tr><td>Gender</td><td>0.95 (0.01)</td><td>0.96 (0.01)</td><td>-0.01</td><td>-0.17</td></tr><tr><td>Education</td><td>7.61 (0.11)</td><td>7.93 (0.10)</td><td>-0.32**</td><td>-2.24</td></tr><tr><td>Household size</td><td>4.28 (0.05)</td><td>4.13 (0.05)</td><td>0.15**</td><td>2.08</td></tr><tr><td>Child ratio</td><td>0.24 (0.01)</td><td>0.20 (0.01)</td><td>0.04**</td><td>2.21</td></tr><tr><td>Elderly ratio</td><td>0.15 (0.01)</td><td>0.23 (0.01)</td><td>-0.08***</td><td>-3.97</td></tr><tr><td>Village cadre</td><td>0.14 (0.01)</td><td>0.18 (0.01)</td><td>-0.04**</td><td>-2.29</td></tr><tr><td>Cooperative membership</td><td>0.23 (0.01)</td><td>0.24 (0.01)</td><td>-0.01</td><td>0.54</td></tr><tr><td>Household income</td><td>1.83 (0.07)</td><td>1.57 (0.06)</td><td>0.26**</td><td>2.77</td></tr><tr><td>Agricultural machinery</td><td>0.46 (0.02)</td><td>0.44 (0.02)</td><td>0.02</td><td>0.89</td></tr><tr><td>Number of grain types</td><td>1.38 (0.02)</td><td>1.48 (0.02)</td><td>-0.10***</td><td>-4.16</td></tr><tr><td>Farm size</td><td>44.19 (4.16)</td><td>18.68 (1.51)</td><td>25.51***</td><td>6.11</td></tr><tr><td>Number of plots</td><td>7.93 (0.30)</td><td>6.77 (0.23)</td><td>1.16***</td><td>3.14</td></tr><tr><td>Irrigation ratio</td><td>0.59 (0.02)</td><td>0.64 (0.02)</td><td>-0.05**</td><td>-2.15</td></tr><tr><td>Natural shocks</td><td>0.34 (0.02)</td><td>0.27 (0.01)</td><td>0.07***</td><td>4.44</td></tr><tr><td>Road condition</td><td>0.74 (0.02)</td><td>0.79 (0.01)</td><td>-0.05***</td><td>-3.48</td></tr><tr><td>Distance to town</td><td>6.34 (0.24)</td><td>5.44 (0.15)</td><td>0.90***</td><td>3.28</td></tr><tr><td>Distance to county</td><td>24.03 (0.55)</td><td>22.69 (0.49)</td><td>1.34*</td><td>1.82</td></tr><tr><td>Eastern</td><td>0.11 (0.01)</td><td>0.22 (0.01)</td><td>−0.11***</td><td>-6.40</td></tr><tr><td>Central</td><td>0.37 (0.02)</td><td>0.38 (0.02)</td><td>-0.01</td><td>-0.38</td></tr><tr><td>Western</td><td>0.53 (0.02)</td><td>0.41 (0.02)</td><td>0.12***</td><td>5.13</td></tr><tr><td>IV1</td><td>0.45 (0.02)</td><td>0.24 (0.01)</td><td>0.21***</td><td>9.59</td></tr><tr><td>IV2</td><td>0.87 (0.01)</td><td>0.81 (0.01)</td><td>0.07***</td><td>3.85</td></tr><tr><td>Observations</td><td>838</td><td>981</td><td></td><td></td></tr></table>

Note: \*\*\*p < 0.01, \*\*p <0.05, \*p < 0.10; Standard deviation is presented in parentheses.

![](images/2d4dfed58c21f681352a4ee79f315f6f82a01965638ec5092b04b06761bf9265.jpg)  
FIGURE 3 | Means of mechanisation service expenditure by credit access status and farm sizes.

![](images/d6f6c4f5b0eaa0f38ffefee699650d694268c916aeeea47c8748db7adc887810.jpg)  
FIGURE 4 | Means of mechanisation service expenditure by credit access status and geographical locations.

## 5.1.2 | Determinants of Mechanisation Service Expenditure

The last two columns in Table 3 report the determinants of mechanisation service expenditure. As the magnitudes of the Tobit coefficients are difficult to interpret, we compute the marginal effects of variables and present the results in the final column. Notably, the marginal effect of the key variable, access to credit, is significantly positive. This finding indicates that access to credit significantly increases mechanisation service expenditure by 115.5 yuan/mu. Access to credit alleviates the production investment constraints of farmers, allowing them to purchase mechanisation services (Mottaleb et al. 2017). For comparison purposes, we also estimate the impact of access to credit on mechanisation service expenditure using a simple Tobit model and present the results in Appendix Table A2 in Supporting Information. The marginal effect of access to credit is 0.084, which is much smaller than that (1.155) observed in the CMP model. The results show that the simple Tobit model tends to underestimate the impact of access to credit on mechanisation service expenditure. This is because the Tobit model treats all explanatory variables as exogenous variables and cannot address the selection bias associated with access to credit. Thus, the CMP model estimation provides more reliable results.

![](images/34f1c4784340dd228009ced41df2fb44c2d849b1159da2d47e6064b165ef70ab.jpg)  
FIGURE 5 | Means of mechanisation service expenditure by credit sources.

As reported in the final column of Table 3, the marginal effects of several control variables are statistically significant. The marginal effect of the elderly ratio variable is positive and statistically significant. The finding suggests that rural households with many older members are more likely to increase mechanisation service expenditure by 17.8 yuan/mu. Although a higher elder ratio is associated with a lower labour endowment, mechanisation services can compensate for the household labour shortage. The farm size variable's significant and negative marginal effect suggests a negative relationship between farm size and mechanisation service expenditure. Large-scale farmers tend to invest in their machinery assets (Qiu and Luo 2021), reducing their dependence and expenditure on mechanisation services. The marginal effect of the number of plots variable is statistically negative, indicating that an increased plot number would decrease mechanisation service expenditure by 2.0 yuan/ mu. The finding is consistent with Wang et al. (2020), who found that the number of plots increases the transaction costs of using machines, thus constraining farm mechanisation adoption.

The marginal effect of the irrigation ratio variable is statistically positive, indicating that each 1% increase in irrigation ratio increases mechanisation service expenditure by 0.6 yuan/mu. Farmland with irrigation conditions usually has a flatter terrain, a prerequisite for agricultural machinery use (Chen et al. 2022). Among the regional variables, the marginal effects of both eastern and central regions are significantly positive, indicating that mechanisation service expenditure is higher in eastern and central regions than in western regions. Zheng et al. (2022) showed that topography and economic conditions are important determinants of mechanised services. China's eastern and central regions generally have flatter topographic conditions and better economic conditions, and these conditions allow farmers to achieve relatively higher economies of scale by adopting mechanisation services, which also increase expenditures.

## 5.1.3  Heterogeneous Effects of Access to Credit Across Farm Sizes and Geographical Locations

The results in Table 3 only reveal a homogeneous effect of access to credit on mechanisation service expenditure. Besides,

TABLE 3 | Impact of access to credit on mechanisation service expenditure: CMP model estimates.
<table><tr><td rowspan="3">Variables</td><td colspan="2">Probit model</td><td colspan="2">Tobit model</td></tr><tr><td colspan="2">Access to credit</td><td colspan="2">Mechanisation service expenditure</td></tr><tr><td>Coefficients</td><td>Marginal effects</td><td>Coefficients</td><td>Marginal effects</td></tr><tr><td>Access to credit</td><td></td><td></td><td>1.759 (0.376)***</td><td>1.155 (0.240)***</td></tr><tr><td>Age</td><td>–0.004 (0.002)*</td><td>–0.001 (0.001)*</td><td>-0.001 (0.003)</td><td>–0.001 (0.002)</td></tr><tr><td>Gender</td><td>-0.049 (0.075)</td><td>-0.018 (0.027)</td><td>0.114 (0.103)</td><td>0.075 (0.068)</td></tr><tr><td>Education</td><td>−0.029 (0.009)***</td><td>-0.011 (0.003)***</td><td>0.018 (0.013)</td><td>0.012 (0.009)</td></tr><tr><td>Household size</td><td>0.026 (0.023)</td><td>0.009 (0.008)</td><td>0.002 (0.032)</td><td>0.001 (0.021)</td></tr><tr><td>Child ratio</td><td>0.157 (0.099)</td><td>0.057 (0.036)</td><td>-0.266 (0.125)**</td><td>-0.175 (0.082)**</td></tr><tr><td>Elderly ratio</td><td>-0.235 (0.085)***</td><td>-0.085 (0.030)***</td><td>0.271 (0.115)**</td><td>0.178 (0.075)**</td></tr><tr><td>Village cadre</td><td>-0.227 (0.088)***</td><td>-0.082 (0.031)***</td><td>0.036 (0.117)</td><td>0.024 (0.077)</td></tr><tr><td>Cooperative membership</td><td>−0.069 (0.075)</td><td>-0.025 (0.027)</td><td>−0.114 (0.102)</td><td>-0.075 (0.067)</td></tr><tr><td>Household income</td><td>0.008 (0.018)</td><td>0.003 (0.006)</td><td>0.010 (0.025)</td><td>0.007 (0.016)</td></tr><tr><td>Agricultural machinery</td><td>-0.024 (0.065)</td><td>-0.009 (0.023)</td><td>-0.473 (0.087)***</td><td>-0.310 (0.057)***</td></tr><tr><td>Number of grain types</td><td>−0.169 (0.069)**</td><td>-0.061 (0.025)**</td><td>1.059 (0.097)***</td><td>0.695 (0.062)***</td></tr><tr><td>Farm size</td><td>0.003 (0.001)***</td><td>0.001 (0.000)***</td><td>−0.002 (0.001)***</td><td>-0.001 (0.000)***</td></tr><tr><td>Number of plots</td><td>−0.002 (0.004)</td><td>-0.001 (0.002)</td><td>-0.030 (0.006)***</td><td>-0.020 (0.004)***</td></tr><tr><td>Irrigation ratio</td><td>0.026 (0.068)</td><td>0.010 (0.025)</td><td>0.853 (0.093)***</td><td>0.560 (0.061)***</td></tr><tr><td>Natural shocks</td><td>0.219 (0.070)***</td><td>0.079 (0.025)***</td><td>-0.148 (0.096)</td><td>–0.097 (0.063)</td></tr><tr><td>Road condition</td><td>-0.206 (0.072)***</td><td>-0.074 (0.026)***</td><td>0.143 (0.104)</td><td>0.094 (0.068)</td></tr><tr><td>Distance to town</td><td>0.006 (0.005)</td><td>0.002 (0.002)</td><td>−0.020 (0.006)***</td><td>−0.013 (0.004)***</td></tr><tr><td>Distance to county</td><td>−0.003 (0.002)</td><td>-0.001 (0.001)</td><td>0.003 (0.003)</td><td>0.002 (0.002)</td></tr><tr><td>Eastern</td><td>-0.461 (0.095)***</td><td>-0.167 (0.034)***</td><td>1.583 (0.151)***</td><td>1.039 (0.095)***</td></tr><tr><td>Central</td><td>−0.282 (0.076)***</td><td>−0.102 (0.027)***</td><td>1.216 (0.117)***</td><td>0.798 (0.074)***</td></tr><tr><td>IV1</td><td>0.413 (0.084)***</td><td>0.150 (0.029)***</td><td></td><td></td></tr><tr><td>Constant</td><td></td><td></td><td></td><td></td></tr><tr><td>ρεli ε2i</td><td>0.611 (0.240)**</td><td>-0.628 (0.121)***</td><td>-2.405 (0.483)***</td><td></td></tr><tr><td colspan="5">Observations</td></tr></table>

Note: \*\*\*p <0.01, \*\*p <0.05, \*p <0.10; Robust standard errors are presented in parentheses; The reference region is the western region.

Figures 6 and 7 suggest the potential heterogeneous effects of access to credit on mechanisation service expenditure across farm sizes and geographical locations. We provide empirical evidence here by performing the subsample estimations. To provide an intuitive understanding, we only present the marginal effects and corresponding standard errors of the access to credit variable graphically.

Figure 6 presents the disaggregated effects of access to credit by farm size. The results show that the marginal effects of access to credit on mechanisation service expenditure decrease monotonically with increasing farm sizes from small (≤ 5 mu) to medium (5-30 mu) and then to large (> 30 mu). Specifically, access to credit increases mechanisation service expenditure by 151.2 yuan/mu for small-scale farmers and 90.0 yuan/mu for medium-scale farmers. In contrast, the effect of credit access is not statistically significant for large-scale farmers. Compared to small and medium-scale farmers, large-scale farmers tend to invest in self-owned farm machinery (Qiu and Luo 2021). Therefore, the findings suggest that small- and medium-scale farmers are more likely to increase their expenditure on mechanisation services in response to credit access than large-scale farmers.

Figure 7 presents the disaggregated effects of access to credit by geographical locations. The results indicate significant regional heterogeneity in the effect of access to credit on mechanisation service expenditure. Specifically, access to credit increases mechanisation service expenditure by 123.9 yuan/mu in the central region and 101.7 yuan/mu in the western region. At the same time, the effect is statistically insignificant in the eastern region. This regional heterogeneity likely reflects underlying differences in economic development and mechanisation levels across regions. In the eastern region, where economic development is more advanced, many farmers have already widely adopted mechanised farming practices (Song et al. 2025). As a result, credit access has limited additional effect on their mechanisation service expenditure, as such services are already part of routine agricultural operations.

![](images/12575ab53a15544c23d6520706662ef7bf51159c99e86c177f2ac561172622cc.jpg)  
FIGURE 6 | Disaggregated effects by farm sizes. \*\*\*p < 0.01 and \*\*p < 0.05; Robust standard errors are presented in parentheses. The sample sizes of farmers with small, medium and large-sized farms are 632, 853 and 334, respectively.

![](images/69c63a621fffdf070307a3b7ab06b21707ffdda26b063ca63f2c49d3d4004abd.jpg)  
FIGURE 7 | Disaggregated effects by geographical locations. \*\*\*p <0.01; Robust standard errors are presented in parentheses. The sample sizes of farmers in the eastern, central and western regions are 302, 677 and 840, respectively.

In contrast, farmers in the central and western regions face more severe financial constraints and operate in less mechanised agricultural environments (Xu et al. 2025). For these farmers, access to credit plays a more critical role in relaxing liquidity constraints, enabling them to invest in previously unaffordable mechanisation services. Therefore, the positive impact of access to credit on mechanisation service expenditure is more pronounced in these less developed regions. These findings underscore the need for regionally differentiated rural credit policies that account for varying levels of mechanisation development and financial access across regions.

## 5.2 | Disaggregated Estimations by Credit Sources and Credit Purpose

## 5.2.1 | Impact of Access to Formal and Informal Credit on Mechanisation Service Expenditure

Given that farmers' access to different sources of credit may have distinct impacts on mechanisation service expenditure, we analyse the impact of farmers' access to formal and informal credit on mechanisation service expenditure. The results derived from the CMP model are presented in Table 4. The significant correlation between the access to formal and informal credit equations (ρμμ) indicates that joint estimation of the probit models is appropriate.

The last column of Table 4 presents the estimated marginal effects of access to formal and informal credit on mechanisation service expenditure. The results indicate that access to formal credit significantly increases mechanisation service expenditure by 44.7 yuan/mu. In contrast, access to informal credit does not have a statistically significant effect on such expenditure. One plausible explanation is that informal credit is typically used to meet urgent and basic household needs—such as food consumption, medical care or children's tuition fees—rather than for longer-term or production-related investments like outsourcing mechanisation services (Jia et al. 2015).

Moreover, informal loans often have less favourable financial conditions, such as uncertain repayment expectations, short loan durations and limited loan amounts. These features may reduce farmers' willingness or ability to allocate informal credit toward farm production expenses. In contrast, formal credit sources are more structured, larger in scale and better suited to finance mechanisation services. This interpretation aligns with the findings of Regassa et al. (2023), who reported that formal credit had a more pronounced impact on chemical fertiliser use than informal credit in Ethiopia. The results underscore the distinct roles that formal and informal credit channels play in shaping farm investment behaviours.

I  I   o         s  ees..
<table><tr><td rowspan="2"></td><td colspan="2">Probit model</td><td colspan="2">Probit model</td><td colspan="2">Tobit model</td></tr><tr><td colspan="2">Access to formal credit</td><td colspan="2">Access to informal credit</td><td colspan="2">Mechanisation service expenditure</td></tr><tr><td>Variables</td><td>Coefficients</td><td>Marginal effects</td><td>Coefficients</td><td>Marginal effects</td><td>Coefficients</td><td>Marginal effects</td></tr><tr><td>Access to formal credit</td><td></td><td></td><td></td><td></td><td>0.659 (0.231)***</td><td>0.447 (0.155)***</td></tr><tr><td>Access to informal credit</td><td></td><td></td><td></td><td></td><td>-0.250 (0.300)</td><td>-0.169 (0.203)</td></tr><tr><td>Control variables</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td></tr><tr><td>IV1</td><td>0.966 (0.075)***</td><td>0.225 (0.015)***</td><td></td><td></td><td></td><td></td></tr><tr><td>IV2</td><td></td><td></td><td>0.227 (0.093)**</td><td>0.070 (0.028)**</td><td></td><td></td></tr><tr><td>Constant</td><td>-0.727 (0.278)***</td><td></td><td>-0.316 (0.258)</td><td></td><td>-1.206 (0.316)***</td><td></td></tr><tr><td>PμuiM2i</td><td colspan="8">-0.526 (0.034)***</td></tr><tr><td>PμiHzi</td><td colspan="8">-0.185 (0.113)</td></tr><tr><td>ρμ2iH3i</td><td colspan="8">0.123 (0.127)</td></tr><tr><td>Observations</td><td colspan="8">1819</td></tr></table>

## 5.2.2 | Impact of Access to Agricultural and Non-Agricultural Credit on Mechanisation Service Expenditure

Another source of heterogeneity in the effect of access to credit on mechanisation service expenditure lies in the intended use of credit. Following Musumba et al. (2022), we categorise credit into agricultural and non-agricultural types based on the primary purpose of the loan. We employ the CMP model to estimate the differential effects of these two credit types. The corresponding results are reported in Table 5. It is worth noting that the coefficients of ρωlω Pωuωzi and ρω1iω3i in the lower part of Table 5 are statistically significant. The findings confirm the existence of selection bias issues due to unobserved factors and the validity of estimating the CMP model.

The last column of Table 5 presents the estimated marginal effects of agricultural and non-agricultural credit on mechanisation service expenditure. The results show that access to agricultural credit significantly increases mechanisation service expenditure by 83.5 yuan/mu. In contrast, access to non-agricultural credit significantly reduces spending on mechanisation services by 25.5 yuan/mu. These findings highlight the critical role of credit purpose in influencing farm investment. Specifically, access to agricultural credit contributes to greater investment in productive inputs such as mechanisation services, likely by easing liquidity constraints and enabling the timely acquisition of mechanisation services during key agricultural seasons. Conversely, access to nonagricultural credit is associated with reduced mechanisation expenditure. This suggests that when credit is allocated for non-productive purposes, it may crowd out agricultural investment by diverting financial resources away from farm operations.

## 5.3 | Robustness Tests

To deepen our understanding and verify the robustness of the baseline results, we further examine whether mechanisation service expenditure increases with the scale of credit, measured by the total loan amount and loan amounts obtained from formal and informal sources. To simplify our discussions, we only present and discuss the findings on the loan amount.

Table 6 shows the effect of the total loan amount on mechanisation service expenditure using the CMP model. The correlation coefficient between the error terms (ρφl φ2) is insignificant, implying that no underlying shared factors influence total loan amount and mechanisation expenditure. As shown in the last column of Table 6, the marginal effect of the total loan amount is significantly positive: each additional 10,000 yuan of borrowing increases mechanisation service expenditure by 1.2 yuan per mu. Given the mean farm size of 30.43 mu (see Table 1), each 10,000 yuan increase in loan would increase mechanisation service expenditure by 36.5 yuan for an average farming household. This result reinforces our earlier finding that credit availability directly relaxes liquidity constraints and enables farmers to increase their investment in mechanisation services.

I  It  s    -    s  ts  es.
<table><tr><td></td><td colspan="2">Probit model</td><td colspan="2">Probit model</td><td colspan="2">Tobit model</td></tr><tr><td></td><td colspan="2">Access to agricultural credit</td><td colspan="2">Access to non-agricultural credit</td><td colspan="2">Mechanisation service expenditure</td></tr><tr><td>Variables</td><td>Coefficients</td><td>Marginal effects</td><td>Coefficients</td><td>Marginal effects</td><td>Coefficients</td><td>Marginal effects</td></tr><tr><td>Access to agricultural credit</td><td></td><td></td><td></td><td></td><td>1.241 (0.313)***</td><td>0.835 (0.209)***</td></tr><tr><td>Access to non-agricultural credit</td><td>Yes</td><td></td><td></td><td></td><td>-0.379 (0.187)**</td><td>-0.255 (0.126)**</td></tr><tr><td>Control variables</td><td></td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td></tr><tr><td>IV1</td><td>0.505 (0.077)***</td><td>0.113 (0.017)***</td><td></td><td></td><td></td><td></td></tr><tr><td>IV2</td><td></td><td></td><td>0.215 (0.091)**</td><td>0.070 (0.030)**</td><td></td><td></td></tr><tr><td>Constant</td><td></td><td></td><td>-0.184 (0.252)</td><td></td><td>-1.239 (0.321)***</td><td></td></tr><tr><td>ρω1ω2i</td><td colspan="6">-0.548 (0.031)***</td></tr><tr><td>ρω1iω3i</td><td colspan="6">-0.474 (0.121)***</td></tr><tr><td>ρω2ω3i</td><td colspan="6">0.262 (0.076)***</td></tr><tr><td>Observations</td><td colspan="6">1819</td></tr></table>

TABLE 6 | Impact of total loan amount on mechanisation service expenditure: CMP model estimates.
<table><tr><td rowspan="2"></td><td colspan="2">Tobit model</td><td colspan="2">Tobit model</td></tr><tr><td colspan="2">Total loan amount</td><td colspan="2">Mechanisation service expenditure</td></tr><tr><td>Variables</td><td>Coefficients</td><td>Marginal effects</td><td>Coefficients</td><td>Marginal effects</td></tr><tr><td>Total loan amount</td><td></td><td></td><td>0.018 (0.010)*</td><td>0.012 (0.007)*</td></tr><tr><td>Control variables</td><td>Yes</td><td></td><td>Yes</td><td></td></tr><tr><td>IV1</td><td>8.297 (0.737)***</td><td>4.071 (0.345)***</td><td></td><td></td></tr><tr><td>Constant</td><td>-1.962 (2.462)</td><td></td><td>-1.137 (0.305)***</td><td></td></tr><tr><td></td><td colspan="2"></td><td colspan="2">-0.063 (0.064)</td></tr><tr><td>ρφ1i φ2i Observations</td><td colspan="2"></td><td colspan="2">1819</td></tr></table>

Note: \*\*\*p <0.01 and \*p <0.10; Robust standard errors are presented in parentheses.

Table 7 reports the results for the impact of formal and informal loan amounts on mechanisation service expenditure. The statistic of ρττ3 in the lower panel is positive and significant, confirming the presence of unobserved endogeneity and supporting the use of the CMP framework. As shown in the last column of Table 7, the marginal effect of the formal loan amount is positive and significant, whereas the effect of the informal loan amount is negative and statistically insignificant. Specifically, each additional 10,000 yuan of formal borrowing increases mechanisation service expenditure by 45.6 yuan for an average household cultivating 30.43 mu. This contrast highlights that formal credit provides stable and reliable access to funds that can be directed toward mechanisation services, while informal credit lacks such reliability and therefore does not promote investment. These findings are consistent with the baseline estimates in Table 4, reinforcing the robustness of our conclusions.

## 5.4 | Impact of Mechanisation Service Adoption on Farm Performance

To enrich our understanding of the association between mechanisation services and farm performance, we employ the inverse probability weighted regression adjustment (IPWRA) estimator to estimate the impact of mechanisation service adoption on farm performance. The analysis is based on 2602 observations of grain crop production drawn from 1819 farming households. Among these observations, 1370 are related to maize, 689 to wheat and 543 to rice. Following existing studies (Ma, Abdulai, and Goetz 2018; Konja and Abdulai 2024), we use crop yield and commercialisation as proxies for farm performance. Specifically, crop yield is measured as output per unit of land (1000kg/mu) and commercialisation is defined as the ratio of the quantity sold to the total quantity produced. Mechanisation service adoption takes the value of 1 if a farmer adopts mechanisation services in crop production and 0 otherwise.

The IPWRA estimates of the average treatment effects (ATE) of mechanisation service adoption on farm performance are reported in Appendix Table A3 in the Supporting Information. Adoption of mechanisation services significantly increases crop yield by 12.6% and commercialisation by 77.4%. These improvements suggest that mechanisation services alleviate labour bottlenecks, enhance the quality of field operations and raise production efficiency (Yi et al. 2019; Zhao et al. 2025). Beyond improving productivity, mechanisation services also generate marketable surplus, encouraging greater participation in agricultural markets (Gold and Gold 2019; da Cavalcante et al. 2025). These findings highlight the dual role of mechanisation services in strengthening farm productivity and encouraging greater market participation.

## 6 | Conclusions and Policy Implications

Credit is vital for helping smooth farm investments and improving farm performance. However, little is known about how access to credit determines mechanisation service expenditure among rural households. This study contributed to the literature by exploring how mechanisation service expenditure is determined by access to credit, the sources of credit (i.e., formal or informal credit), the primary purpose of credit use (i.e., agricultural or non-agricultural) and loan amounts. We employed the CMP model to address selection bias issues and empirically analysed the 2020 CRRS data.

The results showed that access to credit significantly increases expenditure on mechanisation services by 115.5 yuan/ mu. The farmers cultivating small- and medium-sized farms (relative to those cultivating large-sized farms) and those living in less developed central and western parts of China (relative to those living in the eastern part) benefited more from credit access in purchasing mechanisation services. We also found that age, education, elderly ratio, village cadre, number of grain types and road condition are negatively associated with farmers' decisions to access credit. Farm size and natural shocks drive farmers' decisions to access credit. Further analysis reveals that access to formal credit significantly increases mechanisation service expenditure by 44.7 yuan/mu, whereas informal credit access exerts no statistically significant effect. Regarding credit purpose, loans for agricultural production significantly increase mechanisation service expenditure by 83.5 yuan/mu. Conversely, credit primarily used

<table><tr><td rowspan="11">Mar eects Me eon smeaaue *(005 060) -001401) Tobidel Coeiints *0(.001) 0) Mar gects Inn a ount Tobi ddel Coefints Mar gects Foorm o mnnt Tobbi mddel Coeiiints Foormaa aoo amount Varbes</td><td rowspan="2">-01 052) *(09.3 (00) 1819</td><td rowspan="2">for non-agricultural purposes reduces such expenditure by 25.5 yuan/mu. Our findings were further verified by the esti- mates that the loan amount replaces the access to credit vari-</td></tr><tr><td>able in the CMP models. Our results suggest that credit policy should shift from broad expansion to targeted instruments that effectively translate lending into mechanisation service use. Priority should be given</td></tr><tr><td rowspan="8">(032)0(0*** -011 016 Yes **( (00)* 0(.059 90) **44574)* 1*5500* Yes **(*** ***(** **(*** Yes Inn a ount Cconb vbiles Constant R2</td><td rowspan="8"></td></tr><tr><td>to small- and medium-scale farms and the central and western regions, where responses are strongest. Targeting can be refined over time by monitoring uptake across regions, farm sizes and cropping systems.</td></tr><tr><td>At the instrument design level, policies should strengthen for- mal credit channels and ensure that loans are directed toward agricultural production rather than non-agricultural uses.</td></tr><tr><td>Practical measures include direct payments to service providers, disbursement upon verified completion and stricter earmarking for loan purposes to reduce fungibility and enhance the impact on mechanisation services. Access barriers remain significant for older and less-educated</td></tr><tr><td>farmers and for households in areas with weak infrastructure. Addressing these requires multi-channel delivery, includ- ing simplified procedures, agent-assisted services in remote areas and basic financial literacy support. In shock-prone set- tings, contingent credit terms such as temporary grace peri- ods or repayment deferrals can help stabilise mechanisation</td></tr><tr><td>investment. Finally, stimulating demand will be insufficient without supply- side support. Guarantee-backed working capital for provid- ers, equipment financing or leasing and digital platforms that</td></tr><tr><td>connect farmers with service providers and release funds after verified delivery can strengthen service markets. Continuous monitoring is essential to ensure that credit translates into ac- tual mechanisation service use and measurable improvements</td></tr><tr><td>in farm performance. Conflicts of Interest</td></tr><tr><td colspan="2">old  rd   prs  &gt;d &gt; d* &gt; d*** es. The authors declare no conflicts of interest. Data Availability Statement The data that support the findings of this study are available on request from the corresponding author. The data are not publicly available due to privacy or ethical restrictions. Endnotes 1If a farmer can self-finance his household consumption and crop pro- duction,s=1. References Obstvvons Adu-Baffour, F., T. Daum, and R. Birner. 2019. &quot;Can Small Farms Benefit From Big Companies&#x27; Initiatives to Promote Mechanization in Africa? A Case Study From Zambia.&quot; Food Policy 84: 133-145. P221 P2R231 Afridi, F., M. Bishnu, and K. Mahajan.2023.&quot;Genderand Mechanization:</td></tr></table>

I    s     t    s   es..

Ahmad, D., and M. Afzal. 2022. "Synchronized Agricultural Credit and Diversification Adoption to Catastrophic Risk Manage for Wheat Production in Punjab, Pakistan."Environmental Science and Pollution Research 29: 63588-63604.

Akhtar, S., G. Li, A. Nazir, et al. 2019. "Maize Production Under Risk: The Simultaneous Adoption of Off-Farm Income Diversification and Agricultural Credit to Manage Risk."Journal of Integrative Agriculture 18:460-470.

Balana, B. B., D. Mekonnen, B. Haile, F. Hagos, S. Yimam, and C. Ringler. 2022."Demand and Supply Constraints of Credit in Smallholder Farming: Evidence From Ethiopia and Tanzania." World Development 159:106033.

Baum, C. F. 2016. “Conditional Mixed-Process Models the CMP Framework."http://fmwww.bc.edu/EC-C/S2016/8823/ECON8823. S2016.nn14.slides.pdf.

Bayramoglu, B., J. F. Jacques, C. Nedoncelle, and L. Neumann-Noel. 2023. "International Climate Aid and Trade." Journal of Environmental Economics and Management 117: 102748.

Belissa, T., E. Bulte, F. Cecchi, S. Gangopadhyay, and R. Lensink. 2019. "Liquidity Constraints, Informal Institutions, and the Adoption of Weather Insurance: A Randomized Controlled Trial in Ethiopia." Journal of Development Economics 140: 269–278.

Benin, S. 2015. "Impact of Ghana's Agricultural Mechanization Services Center Program."Agricultural Economics 46: 103-117.

Carrer, M. J., A. G. Maia, M. de Mello Brandão Vinholis, and H. M. Souza Filho. 2020. “Assessing the Effectiveness of Rural Credit Policy on the Adoption of Integrated Crop-Livestock Systems in Brazil." Land Use Policy 92: 104468.

Cattaneo, M. D. 2010. "Efficient Semiparametric Estimation of Multi-Valued Treatment Effects Under Ignorability." Journal of Econometrics 155: 138–154.

Chandio, A. A., and Y. Jiang. 2018. "Determinants of Credit Constraints: Evidence From Sindh, Pakistan." Emerging Markets Finance and Trade 54: 3401-3410.

Chandio, A. A., Y. Jiang, A. Rehman, and W. Akram. 2021. "Does Formal Credit Enhance Sugarcane Productivity? A Farm-Level Study of Sindh, Pakistan." SAGE Open 11: 215824402098853.

Chen, F., W. Ma, Y. Luo, and H. Qiu. 2022. "Impacts of Plot Size on Maize Yields and Farm Profits: Implications for Sustainable Land Use and Food Security."International Journal of Sustainable Development and World Ecology 29: 888–900.

Cull, R., L. Gan, N. Gao, and L. C. Xu. 2019. "Dual Credit Markets and Household Usage to Finance: Evidence From a Representative Chinese Household Survey." Oxford Bulletin of Economics and Statistics 81: 1280-1317.

da Cavalcante, D. F. S., J. E. Cruz, G. S. da Medina, and C. N. Dias. 2025. "Determinants for Overcoming the Partial Commercialization of the Production of Family Farmers." Journal of Agricultural Education and Extension 1: 1-24.

Daoud, Y. S., S. Sarsour, R. Shanti, and S. Kamal. 2020. "Risk Tolerance, Gender, and Entrepreneurship: The Palestinian Case." Review of Development Economics 24: 766-789.

Daum, T. 2023. "Mechanization and Sustainable Agri-Food System Transformation in the Global South. A Review." Agronomy for Sustainable Development 43: 16.

Di Falco, S., M. Veronesi, and M. Yesuf. 2011. "Does Adaptation to Climate Change Provide Food Security? A Micro-Perspective From Ethiopia."American Journal of Agricultural Economics 93: 825-842.

Elmallakh, N., and J. Wahba. 2022. "Return Migrants and the Wage Premium: Does the Legal Status of Migrants Matter?" Journal of Population Economics 35: 1631-1685.

FAO. 2022. World Food and Agriculture:Statistical Yearbook 2022.

Felkner, J. S., H. Lee, S. Shaikh, A. Kolata, and M. Binford. 2022. "The Interrelated Impacts of Credit Access, Market Access and Forest Proximity on Livelihood Strategies in Cambodia." World Development 155: 105795.

Fink, G., B. K. Jack, and F. Masiye. 2020. "Seasonal Liquidity, Rural Labor Markets, and Agricultural Production." American Economic Review 110: 3351-3392.

Gallea, Q. 2023. "Weapons and War: The Effect of Arms Transfers on Internal Conflict." Journal of Development Economics 160: 103001.

Geffersa, A. G., and M. P. J. Tabe-Ojong. 2023. “Smallholder Commercialisation and Rural Household Welfare: Panel Data Evidence From Ethiopia."European Review of Agricultural Economics 51: 54-90.

Gold, A., and S. Gold. 2019. "Drivers of Farm Efficiency and Their Potential for Development in a Changing Agricultural Setting in Kerala, India."European Journal of Development Research 31: 855-880.

Harou, A. P., M. Madajewicz, H. Michelson, et al. 2022. "The Joint Effects of Information and Financing Constraints on Technology Adoption: Evidence From a Field Experiment in Rural Tanzania." Journal of Development Economics 155: 102707.

Hossain, M., M. A. Malek, M. A. Hossain, M. H. Reza, and M. S. Ahmed. 2019. "Agricultural Microcredit for Tenant Farmers: Evidence From a Field Experiment in Bangladesh." American Journal of Agricultural Economics 101: 692-709.

Huan, M., F. Dong, and L. Chi. 2022. "Mechanization Services, Factor Allocation, and Farm Efficiency: Evidence From China." Review of Development Economics 26: 1–22.

Hutchins, J. 2023. "The US Farm Credit System and Agricultural Development: Evidence From an Early Expansion, 1920-1940." American Journal of Agricultural Economics 105: 3-26.

Jia, X., H. Luan, J. Huang, and Z. Li. 2015. "A Comparative Analysis of the Use of Microfinance and Formal and Informal Credit by Farmers in Less Developed Areas of Rural China."Development and Policy Review 33:245-263.

Jimi, N. A., P. V. Nikolov, M. A. Malek, and S. Kumbhakar. 2019. "The Effects of Access to Credit on Productivity: Separating Technological Changes From Changes in Technical Efficiency."Journal ofProductivity Analysis 52: 37–55.

Kassouri, Y., and K. Y. T. Kacou. 2022. "Does the Structure of Credit Markets Affect Agricultural Development in West African Countries?" Economic Analysis and Policy 73: 588–601.

Kharel, P., J. Dávalos, and K. Dahal. 2022. "International Remittances and Nonfarm Entrepreneurship Among the Left-Behind: Evidence From Nepal."Review of Development Economics 26: 208-241.

Konja, D. T., and A. Abdulai. 2024. "Collective Market Action, Farm Performance, and Household Welfare Among Maize Farmers: The Role of Outgrower Scheme in Northern Ghana."Applied Economics 57: 1–17.

Kumar, A., A. K. Mishra, V. K. Sonkar, and S. Saroj. 2020. "Access to Credit and Economic Well-Being of Rural Households: Evidence From Eastern India."Journal of Agricultural and Resource Economics 45: 145-160.

Le Cotty, T., E. Maître d'Hôtel, and J. Subervie. 2023. "Inventory Credit to Enhance Food Security in Burkina Faso." World Development 161: 106092.

Li, C., W. Ma, A. K. Mishra, and L. Gao. 2020. "Access to Credit and Farmland Rental Market Participation: Evidence From Rural China." China Economic Review 63: 101523.

Li, J., and W. Ma. 2023. "Sharing Energy Poverty: The Nexus Between Social Interaction-Oriented Gift Expenditure and Energy Poverty in Rural China."Energy Research and Social Science 101: 103131.

Li, J., W. Ma, J. C. Botero-R, and P. Quoc Luu. 2023. "Mechanization in Land Preparation and Irrigation Water Productivity: Insights From Rice Production."International Journal of Water Resources Development 40:1-22.

Li, J., P. Vatsa, W. Ma, and P. Q. Luu. 2025. "Promoting Sustainable Agri-Food Production to Achieve Food and Nutrition Security: The Role of Soil Conservation Practices."Australian Journal of Agricultural and Resource Economics 69: 59–79.

Li, X., and X. Huo. 2021. "Impacts of Land Market Policies on Formal Credit Accessibility and Agricultural Net Income: Evidence From China's Apple Growers." Technological Forecasting and Social Change 173:121132.

Lu, Q., X. Du, and H. Qiu. 2022. "Adoption Patterns and Productivity Impacts of Agricultural Mechanization Services." Agricultural Economics 53: 826-845. https://doi.org/10.1111/agec.12737.

Ma, W., A. Abdulai, and R. Goetz. 2018. "Agricultural Cooperatives and Investment in Organic Soil Amendments and Chemical Fertilizer in China."American Journal of Agricultural Economics 100: 502–520.

Ma, W., H. Qiu, and D. B. Rahut. 2023. "Rural Development in the Digital Age: Does Information and Communication Technology Adoption Contribute to Credit Access and Income Growth in Rural China?" Review of Development Economics 27: 1421-1444.

Ma, W., A. Renwick, and Q. Grafton. 2018. "Farm Machinery Use, Off-Farm Employment and Farm Performance in China."Australian Journal of Agricultural and Resource Economics 62: 279–298.

Ma, W., H. Zheng, and P. Yuan. 2022. "Impacts of Cooperative Membership on Banana Yield and Risk Exposure: Insights From China." Journal of Agricultural Economics 73: 564–579.

Ma, W., X. Zhou, D. Boansi, G.S. A. Horlu, and V. Owusu. 2024. "Adoption and Intensity of Agricultural Mechanization and Their Impact on Non-Farm Employment of Rural Women." World Development 173: 106434.

Ma, X., X. Hou, Y. Cui, and J. Ma. 2025. "Do Socialized Agricultural Services Promote Smallholder Participation in Large Markets? Evidence From Grain Farmers in China."Agribusiness. https://doi.org/10.1002/ agr.22014.

Martey, E. 2022. “Empirical Analysis of Crop Diversification and Energy Poverty in Ghana." Energy Policy 165: 112952.

Mishra, A. K., S. Bairagi, M. L. Velasco, and S. Mohanty. 2018."Impact of Access to Capital and Abiotic Stress on Production Efficiency: Evidence From Rice Farming in Cambodia." Land Use Policy 79: 215-222.

Mohammed, K., E. Batung, S. A. Saaka, M. M. Kansanga, and I. Luginaah. 2023. "Determinants of Mechanized Technology Adoption in Smallholder Agriculture: Implications for Agricultural Policy." Land Use Policy 129: 106666.

Mottaleb, K. A., D. B. Rahut, A. Ali, B. Gérard, and O. Erenstein. 2017. "Enhancing Smallholder Access to Agricultural Machinery Services: Lessons From Bangladesh." Journal of Development Studies 53: 1502-1517.

Mukasa, A. N. 2017. "Credit Constraints and Farm Productivity: Micro-Level Evidence From Smallholder Farmers in Ethiopia." African Development Bank Group Working Paper Series No. 247.

Musumba, M., C. A. Palm, A. M. Komarek, P. K. Mutuo, and B. Kaya. 2022. "Household Livelihood Diversification in Rural Africa." Agricultural Economics (United Kingdom) 53: 1-11.

Nakano, Y., and E. F. Magezi. 2020. "The Impact of Microcredit on Agricultural Technology Adoption and Productivity: Evidence From Randomized Control Trial in Tanzania." World Development 133: 104997.

Nnaji, A., N. Ratna, A. Renwick, and W. Ma. 2022. "Risk Perception, Farmer-Herder Conflicts and Production Decisions: Evidence From Nigeria."European Review of Agricultural Economics 50: 683-716.

OECD and FAO. 2023. OECD-FAO Agricultural Outlook 2023–2032.

Ojo, T. O., and L. J. S. Baiyegunhi. 2020. "Determinants of Credit Constraints and Its Impact on the Adoption of Climate Change Adaptation Strategies Among Rice Farmers in South-West Nigeria." Journal of Economic Structures 9: 1–15.

Parappurathu, S., C. Ramachandran, K. K. Baiju, and A. K. Xavier. 2019. "Formal Versus Informal: Insights Into the Credit Transactions of Small-Scale Fishers Along the South West Coast of India."Marine Policy 103: 101–112.

Qian, L., H. Lu, Q. Gao, and H. Lu. 2022. "Household-Owned Farm Machinery vs. Outsourced Machinery Services: The Impact of Agricultural Mechanization on the Land Leasing Behavior of Relatively Large-Scale Farmers in China."Land Use Policy 115: 106008.

Qiu, T., S. T. B. Choy, Y. Li, B. Luo, and J. Li. 2021. "Farmers' Exit From Land Operation in Rural China: Does the Price of Agricultural Mechanization Services Matter?" China & World Economy 29: 99–122.

Qiu, T., and B. Luo. 2021. "Do Small Farms Prefer Agricultural Mechanization Services? Evidence From Wheat Production in China." Applied Economics 53: 2962–2973.

Regassa, M. D., M. B. Degnet, and M. B. Melesse. 2023. "Access to Credit and Heterogeneous Effects on Agricultural Technology Adoption: Evidence From Large Rural Surveys in Ethiopia." Canadian Journal of Agricultural Economics 71: 231–253.

Saroj, and K. R. Paltasingh. 2024. "What Promotes Production Contract in Indian Agriculture? Managing Market Risk Versus Profit Orientation." Agricultural Economics (United Kingdom) 55: 1-14.

Sher, A., S. Mazhar, and Y. Qiu. 2023. "Toward Sustainable Agriculture: The Impact of Interest-Free Credit on Marketing Decisions and Technological Progress in Pakistan." Sustainable Development 32, no. 1:608-616.

Simtowe, F., and M. Zeller. 2006. "The Impact of Access to Credit on the Adoption of Hybrid Maize in Malawi: An Empirical Test of an Agricultural Household Model Under Credit Market Failure."

Song, H., X. Li, L. Xin, and X. Wang. 2025. "Improving Mechanization Conditions or Encouraging Non-Grain Crop Production? Strategies for Mitigating Farmland Abandonment in China's Mountainous Areas." Land Use Policy 149: 107421.

Swaminathan, H., R. S. Du Bois, and J. L. Findeis. 2010. "Impact of Access to Credit on Labor Allocation Patterns in Malawi." World Development 38: 555-566.

Takeshima, H. 2017. "Custom-Hired Tractor Services and Returns to Scale in Smallholder Agriculture: A Production Function Approach." Agricultural Economics 48: 363-372.

Tufa, A., A. Alene, H. Ngoma, et al. 2023. "Willingness to Pay for Agricultural Mechanization Services by Smallholder Farmers in Malawi."Agribusiness 40: 248-276. https://doi.org/10.1002/agr.21841.

Vatsa, P., W. Ma, H. Zheng, and J. Li. 2023. "Climate-Smart Agricultural Practices for Promoting Sustainable Agrifood Production: Yield Impacts and Implications for Food Security."Food Policy 121: 102551.

Wang, X., Y. Song, and W. Huang. 2024. "The Effects of Agricultural Machinery Services and Land Fragmentation on Farmers' Straw Returning Behavior."Agribusiness. https://doi.org/10.1002/agr.21934.

Wang, X., F. Yamauchi, J. Huang, and S. Rozelle. 2020. "What Constrains Mechanization in Chinese Agriculture? Role of Farm Size and Fragmentation." China Economic Review 62: 101221.

Xu, G., Y. Ma, G. Qin, C. Xu, and Y. Zhu. 2025. "Why Chinese Farmers Are Reluctant to Transfer Their Land in the Context of Non-Agricultural Employment: Insights From Agricultural Mechanization."Humanities and Social Sciences Communications 12: 1-12.

Yi, Q., M. Chen, Y. Sheng, and J. Huang. 2019. "Mechanization Services, Farm Productivity and Institutional Innovation in China." China Agricultural Economic Review 11: 536-554.

Zhang, H., W. Ma, and X. Sang. 2025. “Credit Access and Sustainable Farm Investments: A Dual Perspective on Chemical and Environmentally Friendly Inputs." International Journal of Sustainable Development and World Ecology 32: 485–497.

Zhang, W., X. Xia, Y. Zhu, S. Zhao, and Z. Zhou. 2024. "Rural Financial Institutions, Access to Credit and Production Inputs of Rural Households." Finance Research Letters 70: 106298.

Zhang, X., J. Yang, and R. Thomas. 2017. "Mechanization Outsourcing Clusters and Division of Labor in Chinese Agriculture." China Economic Review 43: 184–195.

Zhao, S., J. Wu, and T. Qiu. 2025. "The Effects of Adopting Large Farms' Agricultural Mechanization Services on Agricultural Productivity." Applied Economics 1: 1-14.

Zheng, H., and W. Ma. 2022. "Scan the QR Code of Happiness: Can Mobile Payment Adoption Make People Happier?" Applied Research in Quality of Life 17: 2299–2310.

Zheng, H., W. Ma, Y. Guo, and X. Zhou. 2022. "Interactive Relationship Between Non-Farm Employment and Mechanization Service Expenditure in Rural China." China Agricultural Economic Review 14: 84-105.

Zhou, X., W. Ma, G. Li, and H. Qiu. 2020. "Farm Machinery Use and Maize Yields in China: An Analysis Accounting for Selection Bias and Heterogeneity." Australian Journal of Agricultural and Resource Economics 64: 1282-1307.

Additional supporting information can be found online in the Supporting Information section. Data S1: ajar70072-sup-0001-Tables. docx.

## Supporting Information