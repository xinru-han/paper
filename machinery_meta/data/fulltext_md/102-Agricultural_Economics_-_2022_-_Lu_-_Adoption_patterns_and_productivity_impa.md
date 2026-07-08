ORIGINAL ARTICLE

AGRICULTURAL   
ECONOMICS   
The Journal of the International Association of Agricultural Economists

WILEY

# Adoption patterns and productivity impacts of agricultural mechanization services

Qinan Lu¹  Xiaodong Du¹  Huanguang Qiu²

1Department of Agricultural and Applied Economics, University of   
Wisconsin-Madison, Madison, Wisconsin, USA

2School of Agricultural Economics and Rural Development, Renmin University of China, Beijing, China

Correspondence

Qinan Lu, Department of Agricultural and Applied Economics, University of Wisconsin-Madison, Madison, WI, USA Email: qinan.lu@wisc.edu

## Abstract

Agricultural mechanization services (AMS) have emerged as a viable and effective solution for helping farmers gain access to machinery equipment in developing countries. This study investigates the simultaneous decision-making regarding multiple mechanization services and the causal impacts of the AMS on land productivity among Chinese smallholders. We find that: (i) The ratio of offfarm wage to AMS price, or the wage-rent ratio, has a significant positive effect on AMS adoption; the sequential adoption of AMS starts with power-intensive followed by control-intensive production tasks, (ii) Switching to AMS in plowing, transplanting, and harvesting increases rice yield by 48.0 kg, 23.7 kg, and 7.9 kg, respectively, and (iii) The AMS of pesticide spraying significantly decreases yield but the negative effect can be mitigated with professional service providers and effective labor monitoring, highlighting potential moral hazards associated with AMS when monitoring is costly. Simulation illustrates that increased AMS adoption can significantly enhance food security in China.

KEYWORDS

food security, garden variety 3SLS, multivariate probit, outsourcing

JEL CLASSIFICATION Q12, Q16, Q15, O3, D13

## 1  INTRODUCTION

It is well recognized that transforming agriculture through affordable mechanization is a powerful engine for poverty alleviation and long-run development in developing countries (Carillo, 2021; Duarte & Restuccia, 2010; Johnston & Mellor, 1961; Matsuyama, 1992; Schultz, 1953). A major risk facing smallholders in developing countries is not being able to complete agricultural production tasks on time and with high quality in the busy farming seasons. For example, deficient land plowing can be detrimental to soil drainage and crop root growth and, more importantly, limit field availability for later tasks such as transplanting and pest control (Kumar & Kalita, 2017). Meanwhile, the absence of harvesting capacity may delay a harvest until its optimal timing has passed and thus cause great losses. With appropriate access to agricultural machines, farmers can promptly complete operational tasks, and thus significantly intensify agricultural production and secure the food supply. However, smallholders in developing countries cannot afford a considerable amount of investment in agricultural machines.

Agricultural mechanization services (AMS) have emerged as a viable and effective solution for helping farmers gain access to machinery equipment in past decades (Biggs & Justice, 2015; Caunedo & Kala, 2021; Houssou et al., 2013; Van Loon et al., 2020; Yang et al., 2013). By aggregating the demand of smallholders, AMS enables service providers to achieve economies of scale and therefore overcome the barrier of high initial investment. AMS providers include professional farmers, cooperatives, and agricultural companies, etc. AMS comprise in-demand agricultural production tasks, such as land plowing, transplanting, pesticide spraying, and harvesting, and may vary by location. An increasing number of small farmers choose to adopt and pay for AMS for one or more tasks.

Although significant efforts have been made by governments and non-governmental organizations (NGOs) to champion the development of AMS, some developing countries have historically failed to popularize AMS (Adu-Baffour et al., 2019; Pingali, 2007; Sheahan & Barrett, 2017). For instance, African governments and some international NGOs have attempted to promote AMS in the past few decades, but African agriculture still relies heavily on animal and human muscle power (Diao et al., 2016; Houssou et al., 2013). Potential explanations for this failure include (i) insufficient demand for agricultural services due to the low income of farmers (Sheahan & Barrett, 2017); (ii) relatively high rent for agricultural machines, largely because equipment in Africa is almost completely imported (World Bank, 2014); and (iii) difficulties governments and NGOs face in predicting and capturing sequential demand for agricultural machines given the significant spatial variations and different stages of regional development (Daum & Birner, 2017).1

However, AMS has developed rapidly in China over the last 20 years (Yang et al., 2013; Zhang et al., 2017). Taking rice production as an example, the average expenditure of Chinese farmers for AMS rose from 73.11 CNY (Chinese yuan) in 2003 to 287.35 CNY per mu in 2018, and AMS expenditure as a proportion of total production cost increased from 33.22% in 2005 to 49.02% in 2018.2

A better understanding of China's successful experience with AMS is helpful for other developing countries to realize agricultural mechanization or even broader economic development. We observed several factors contributing to AMS development in China, which notably contrast with the reasons inhibiting the AMS development in Africa. First, the off-farm income of Chinese farmers increased dramatically from 2000 to 2020. Second, with the growing capabilities in agricultural equipment sectors, many agricultural machines in China are now manufactured domestically; this has decreased AMS costs. Third, with relatively mature AMS markets in China, private sectors are more responsive and sensitive to the dynamic sequential demand for mechanization services (Diao et al., 2014).

To investigate the AMS development in China, we took rice as a case study and conducted a rural household survey in 12 counties in 2018. The survey collected detailed records of off-farm jobs and wages for individual family members. We also collected the AMS-related prices of various operational tasks executed by different types of machines, such as stretcher sprayers versus T-tank sprayers for pesticide spraying. To capture the sequential demand of AMS, we selected the four most important operational tasks of rice production: plowing, transplanting, pesticide spraying, and harvesting. Complete input and output data measuring the impact of AMS on productivity were obtained.

Agricultural mechanization services may influence crop yields in two opposite directions. With skilled and proficient providers, AMS is expected to increase land productivity (Cortes & Salvatori, 2019; Mugera et al., 2016; Zhang et al., 2017). Conversely, the moral hazard problem that widely exists in principal-agent relationships is likely to occur in AMS (At &. Thomas, 2019; Dubois, 2002; Ghatak & Pandey, 2000). For instance, the task of pesticide spraying is less mechanical and the outcome is more difficult to observe than the other tasks, which potentially result in moral hazard problems and drag down land productivity. Therefore, the total yield effect of AMS is ambiguous a priori and needs to be empirically determined. If the total impact is negative, the development of AMS is not sustainable overall and, more importantly, will endanger food security given the rigid land constraint in China. Furthermore, AMS's potential negative impact on yield may result in a remarkable increase in grain prices in the global market; this has been recognized as the economic root of violent conflicts in Africa (McGuirk & Burke, 2020).

The study quantifies the effect of wage-rent ratios on farmers' AMS adoption decisions and the corresponding productivity impacts. To do so, we integrate the multivariate probit (MVP) model with the instrumental variable (IV) method under the framework of the three-stage least squares (3SLS) to deal with both endogeneity and simultaneity. Based on empirical estimates, we simulate the yield, the increase in total rice output in China, and the number of people fed in low, medium, and high AMS adoption scenarios. Finally, we discuss the implications for policy design, potential extensions, and limitations of the research.

We find that the wage-rent ratio has a significant and positive effect on AMS adoption in all modeled tasks, with the probability of AMS adoption decreasing with the sequential order of harvesting, plowing, transplanting, and pesticide spraying. Switching to AMS for plowing, transplanting, and harvesting increases rice yields by 48.0 kg, 23.7 kg, and 7.9 kg, respectively. Interestingly, the magnitude of the yield effect is consistent with the sequential nature of production tasks dictated by the biological rule of crops, with relatively larger effects for tasks executed earlier in the growing season. Using AMS to spray pesticides proves to significantly decrease (i.e., by 21.3 kg) rice yields. In a subsample with only professional service providers, the negative effect slightly declines, and further turns positive with effective labor supervision; thus, there is a moral hazard with AMS when monitoring is costly. Furthermore, simulation results show that increasing the AMS adoption rate for plowing alone by 20 percentage points increases total rice output in China by 3.79 billion kg; this shift would provide cereal grain for an additional 32 million people per year.

This study contributes to the literature in four aspects. First, our findings add evidence to the literature on AMS by summarizing the successful experience of AMS development in China. While the rise in off-farm wages and the decrease in AMS prices promote the adoption of AMS, the positive effects of three out of four market-based AMS on rice yields in China suggest that market-based service providers may be better at meeting the sequential demand for agricultural mechanization. Chen and Lan (2020) document the patterns of agricultural mechanization in China after the Household Responsibility System (HRS) reform from 1976 to 1988, which we term the “Phase I" story of China's agricultural mechanization. Our study tells the more recent “Phase II" story.

Second, to the best of our knowledge, this article is the first study to quantify the causal effects of AMS on crop yields after addressing two challenging empirical issues. The first issue is omitted variable bias (OVB) resulting from unobserved factors that influence both crop yield and farm households' adoption decisions. To address OVB, we employ wage-rent ratios as instrument variables for AMS adoption decisions since the market-oriented rental prices are closely related to farmers' decisions but do not influence crop yield directly after controlling for potential confounding factors. We expect the exclusion restriction should be satisfied. Second, farmers make decisions concerning AMS for multiple production tasks simultaneously. Unobserved factors such as farmers' personal preferences for leisure influence AMS adoption for multiple tasks, which results in highly correlated adoption decisions. Conventional approaches model decisions separately (e.g., probit or logit model) or in a simplified way (Wu & Babcock, 1998). Accounting for the correlation yields us better predicted probabilities of AMS and further attenuates the estimation bias in 3SLS. To realize this, we estimate a multivariate probit model where multiple binary choices of AMS are simultaneously estimated as a system with a correlated error structure.

The third contribution is that we apply the garden variety 2SLS in Angrist and Pischke (2008) to analyze the effects of agents' simultaneous decisions on the outcomes by organically integrating the MVP and IV methods under the frame of the three-stage least squares. The integrated model accounts for simultaneity and endogeneity and can be readily applied to many other settings. For example, the model can help analyze the effects of stockholders' simultaneous choices of highly correlated stocks on their performance after accounting for the endogeneity caused by unobserved risk preference.

Finally, the study adds new evidence to the literature on the problem of moral hazard. We find moral hazard in the use of AMS for pesticide spraying, which is the most difficult task requiring labor supervision among the modeled production tasks. The empirical results show that adopting AMS for pesticide spraying has a negative effect on crop yield and, more interestingly, that effective labor supervision can eliminate the negative effect.

## 2  BACKGROUND

In China, the main agricultural operators are farm households that rent a small piece of land from the local rural community. In 2017, small farmers operating about 70% of total arable land accounted for more than 98% of main agricultural operators. Approximately 91% of the rural households have farmlands less than 10 mu (.67 ha),3 and small farmers have fewer financial resources than large farmers and benefit less from economies of scale. Therefore, small farmers are unwilling to purchase large agricultural machines. When a small farm does own machines, most of these are often outdated and inefficient (Sheng et al., 2017). These obstacles constrain productivity growth in China.

Aging and outflow of agricultural labor are factors that hinder agricultural productivity. The percentage of the population aged 65 and above in China increased from 6.81% in 2000 to 11.47% in 2019,4 and the percentage of the elderly is much higher for agricultural labor. Compared to young labor, older operators generally have less human capital, such as physical strength and education; a lower ability to access information technology; and a lower willingness to adopt new technology. Rapid urbanization and industrialization have caused a large-scale outflow of agricultural labor, which decreased from 360.4 million in 2000 to 202.6 million in 2018.⁵ Lack of quantity and quality of agricultural labor hurts agricultural production in China.

Although enlarging farm size can overcome the barriers of low and inefficient capital investment and lack of agricultural labor, increasing operational scale through widescale land consolidation is unrealistic in China given the current Household Responsibility System (HRS), under which the village collective owns the land while farm households only have contract rights. Since 1978, the arable land in China has been contracted to individual farm households in a rural collective according to the size of a household. A household is restricted to the number of acres it was initially allocated as contract rights are generally not transferable between farm households. The average acre of farmlands those farm households contracted from the rural collective is only approximately .65 ha in 2016.6

To encourage land transfer, the Rural Land Contract Law, officially announced in 2003, has formalized land leasing rights, and the law provides legal security to both lease-in and lease-out parties (Chari et al., 2021).7 Land operations rights were formally separated from land contract rights in the 2019 Amendment of RLCL,8 which legally secures the contract rights of farm households who lease out their operation rights. However, Huang et al. (2012) found that the majority of such transfers were between relatives or friends within a village. High transaction costs (Kimura et al., 2011) and the expectation of land price appreciation (Carter & Yao, 2002; Jin & Deininger, 2009) hinder land transfer. Even if the land were transferred and consolidated to some extent in the future, farm sizes would still remain small in China. Farmers with more land would still be unable to afford efficient but expensive machines.

In recent years, AMS has emerged as an effective solution to overcome the capital and labor constraints faced by China's agricultural industry. As part of the production decision, farm operators with land operation rights can choose not to execute all production tasks by themselves, but to adopt AMS and pay service providers for one or more tasks. Aggregating demand from smallholder farmers, AMS providers can afford to buy large agricultural machines. Adopting AMS allows smallholder farmers to approach the economies of scale and capital intensity of large farms and thus reduce the productivity gap.

The Chinese government has issued policies to support and facilitate the development of AMS, including (i) extending AMS from tasks that are suitable for machinery use, such as harvesting and plowing, to all tasks such as transplanting/seeding and plant protection; (ii) expanding from grain crops (e.g., rice, maize, and corn) to cash crops (e.g., sugarcane, cotton, and beetroot); (iii) piloting on a small scale and then promoting the experience nationwide; and (iv) enlarging the AMS market by cultivating more service providers.º

Considering the extensive geographical coverage and rapidly increasing expenditure share of AMS, analyzing the patterns of AMS adoption will provide insights into the future development of AMS. More importantly, investigating the effect of AMS on land productivity has significant implications for food security in China and grain prices in the global market.

## 3  EMPIRICAL MODEL

This section starts with the analysis of farmers' AMS choices for four tasks in rice production, including plowing (hereafter denoted by P), transplanting (T), pesticide spraying (S), and harvesting (H), using a multivariate probit model. First, we look into the AMS adoption decisions of the four tasks. For doing so, we focus on the driving effect of the wage-rent ratio on AMS decisions for two reasons: (i) variation in the wage-rent ratio accounts for the remarkable differences in observed AMS adoption in the four tasks, and (ii) wage-rent ratio is proven to be a valid instrumental variable for farmers' AMS decisions for estimating productivity impact. We rationalize how the wage-rent ratio influences farmers' AMS decisions and the decisions' impacts on crop yields in a theoretical model in Appendix B. In the second part of this section, we apply a garden variety 3SLS method to estimate the individual effects of AMS on rice yield using the wage-rent ratio as the IV in each task. Doing so allows us to account for both endogeneity and simultaneity related to AMS adoption decisions.

## 3.1  AMS decisions on production tasks

A farm household faces a binary choice, adopting AMS or not, in each of the four tasks of rice production. latent variable that is proportional to the level of AMS demand of household i for production task j. The level of

![](images/033d5acfeb653b64b31222e8e5381eb42487abdfaf8387c20815cb9d0b544165.jpg)

(1)

where Ratioj represents the wage-rent ratio; Z is a vector of control variables including, farm household characteristics, land characteristics, and social capital of the farm household; and εj is the error term. Xj combines Ratioj and Z′i, that is, X′ij ≡ (Ratioj, Z′ j), and γj consists of αj and βj (i.e., γ′i ≡ (αj, β′)). Depending on the sign of DS\*i ij' we map Equation (1) to the observed binary choice variable DSij:

![](images/749b882105b0863ec0c9b12f26a80b8de05d1806cc37fec16c6e799b1448890e.jpg)

(2)

If we assume that ε′ s are i.i.d. and normally distributed, Equation (2) represents four independent univariate probit models (UVPs) for the four AMS decisions. However, the i.i.d. assumption implies that all the unobserved factors that influence the AMS choice in one task are not correlated with those of all other tasks. This is a strong and potentially implausible assumption. For example, a farm household's unobserved characteristics, such as preference for leisure and social connections, could affect its AMS decisions regarding multiple tasks in a similar way and thus lead to correlated choices.

In this study, we allow for correlations across the AMS choices of all four tasks by utilizing a multivariate probit model. The multivariate probit model is generalized from the bivariate probit model and has been applied to many settings (e.g., Atamanov & Van den Berg, 2012; Bontemps & Nauges, 2016; Chrisendo et al., 2021; Ma et al., 2018; Magrini et al., 2017). For a recent review of multivariate probit/logit model see Bel et al. (2018). The MVP model assumes that the residual terms ε (note that we drop the household subscript i till Equation (6) for simplicity) in Equation (1) jointly conform to a multivariate normal distribution:

![](images/7e0774c49873cd5e951290369e2832188b674e580fd986dc6ab762b996c00c80.jpg)

(3)

where ρjk,j,k ∈ {P,T,S,H} and j ≠ k denote the correlation coefficients of ε and εk, and are assumed to be symmetric, that is, ρjk = ρkj. The UVP model is a special case of MVP when the correlation coefficient ρjk = 0 for j, k ∈ {P, T, S, H}. Equations (1)–(3) define the multivariate probit model. The marginal probability of adopting AMS for an individual task is

![](images/8e3a40f654a58d51148a8803eff59d8297024edb0c179c979c1dfe3dc8307ec4.jpg)

(4)

Referring to Ramful and Zhao (2009) and Li et al. (2019), we predict the joint and conditional probabilities based on the estimates of the MVP model. Our model extends the calculations of these probabilities to four binary choices associated with higher computational complexities. There are 16( = 24) joint probabilities for the four binary choices in the MVP model. Below we list some of interest:

![](images/2debfb8df3c282f9a7decf68dcb912de21dea9416e6b5a1379c0c017ebb972ed.jpg)

![](images/e510c18ac2dc03ea8e99860d2101af48fe206f32e3d5dc64ccfb26f42956ec61.jpg)

![](images/ad8dca5c3b1792fc6cd923661918b150e1003825cda91280011273ce88df7744.jpg)

![](images/40fc7c657791babdc92cc4024d2da9ceaa5355f917d92a482d185687b7704aa1.jpg)

![](images/d603f8a5cb61f3f53aee71c069196b88506dfb1420c0d7ad796cd57b02d0028b.jpg)

where Φ4(·) represents the cumulative distribution function (CDF) of the standard normal distribution with four dimensions. Hereafter Φ(·) denotes the CDF of the standard normal distribution with j dimensions. The above five sub-equations in Equation (5) represent the probability of adopting AMS in task(s) of none, harvesting, harvesting and plowing, all four tasks except pesticide spraying, and all four tasks, respectively, which are determined by the control variables, X, and the correlations between the corresponding choices ρjk.

We also derive conditional probabilities of interest. For example, the respective probabilities of plowing, transplanting, and pesticide spraying conditional on harvesting, and the respective probabilities of transplanting and pesticide spraying conditional on harvesting and plowing are as follows:

![](images/f73e46c1492939c365171d3a06715b7994e7c7fa285e1428f03a7ede488df2c4.jpg)

![](images/c3cbba2dc1aec9529a5c2e4b0e8619d87b73ea236632a4124f4d57043786bec9.jpg)

(6)

Finally, the log-likelihood function of the MVP model for an i.i.d. sample of N farm households is given by

![](images/885fe2ff98eded925e41db2cfa38c85f2694d8d99e68b72004f6714ea849b77c.jpg)

(7)

## 3.2 | Causal effects of AMS on land productivity

To evaluate the causal effects of the hired AMS on rice yields, we employ a three-stage least squares method. As described in 3.1, we use the MVP model in the first stage to account for the simultaneous choices of AMS:

![](images/b51cf6429dc4b9ce3433622e6309f6dc43d7ca4e619180d36e57f228798a4da2.jpg)

(8)

where the wage-rent ratio (Ratio) is the instrumental variable for the AMS choice of task j (DSij). The control variables in Zi are defined as in Equation (1). As the endogenous variable (DS) is a dummy variable here, the underlying conditional expectation function (CEF) for Equation (8) can be nonlinear. However, the first stage of the usual two-stage least squares (2SLS) is a linear approximation of the CEF function, E(DSj|Ratioj, Z). This is another reason we use MVP in the first stage to obtain the fitted values of DSij,p.

The specification of the second stage is:

![](images/4aa0375dc85a1458e6948ecee6c41b5b55ab146722856c87d43c245af5beaa6c.jpg)

(9)

where Y is the rice yield of farm household i. The parameter γ is of interest.

However, if we substitute DSij,p for DSij directly in Equation (9), another problem arises: only the ordinary least squares (OLS) estimation of Equation (8) guarantees that the first stage residuals (ε) are uncorrelated with the predicted values DS and the covariates in Z. Hausman (1975) terms this problem Forbidden Regression, and Angrist and Pischke (2008) proposed an approach called the garden variety 2SLS to solve the problem. Namely, we use the predicted probability ÁŠij,p as the instrumental variable for DS in Equation (8).10 Therefore, we add one more step before the second stage:

![](images/da7c3c60bfe49134d1e2f12db59e9dfb0b5bf3fd52cf77fd601fa5637f9bed7b.jpg)

(10)

Therefore, the estimation system includes Equation (8) as the first stage, Equation (10) the second stage, and Equation (9) the third stage. The three-equation system is estimated using the reg3 (Three-stage estimation for systems of simultaneous equations) command in STATA."1

The IV estimators remain valid in the system. Two assumptions guarantee the wage-rent ratios as valid instruments. The first assumption is:Cov(Ratioij, DSij) ≠ 0, which ensures that Ratio captures at least some variation in DSj. This can be tested by the significance of Ratioj s’coefficients in the MVP model. The second assumption is the exclusion restriction, that is, Cov(Ratioj, ej) = 0, which implies that Ratioij is uncorrelated with eij. The wage-rent ratio is constructed as the ratio of a farm household head's off-farm wage to local AMS price. With appropriate control variables that we discuss in a later section, we assume that both off-farm wage and AMS prices are not correlated with the unobserved factors that influence the farm's rice yield.12

## 4  DATA

## 4.1  Sampling

We conducted a rural survey on AMS in the major rice production regions of China in the summer of 2018. The survey collected detailed microdata of AMS adoption in individual production tasks, inputs and outputs, farm-level off-farm wage, and village-level prices of AMS using different types of machines for each task, and farm household and land characteristics.

The survey utilized a stratified random sampling method to select farm households in three steps. First, we chose Heilongjiang, Zhejiang, and Sichuan Provinces from each of the three major rice production regions of Northeast, East, and Southeast China, respectively. More than 90% of farmlands in these three provinces produce rice in at least one growing season. Second, we randomly chose four counties in each province and two towns in every county with a total of 24 towns in the sample. Third, within every town, we randomly selected approximately 18 farm households. After eliminating observations with incomplete information, 404 farm households remained in the final dataset. Although the sample size was not large, we consider it representative of rice production in China. Figure A1 shows the geographical distribution of rice production¹³ and the locations of the 12 counties studied.

## 4.2 Variable definition and choices

This section introduces choices and definitions of variables in our empirical analysis. We measure agricultural productivity by rice yields, that is, total rice output divided by farm size with unit “kg/mu". Two other important variables in this study are wage-rent ratios and the AMS decisions on four tasks in rice production. We define the W   
wage-rent ratio as Ratio =   
wage measured by the hourly off-farm wage of the farm household head (CNY/h), and Ris the farm-specific AMS

price of a certain task in the market (CNY/h).14 For example, if the AMS price of harvesting is 80 CNY/mu, a farmer needs to spend 8 h on one mu harvest unaided, and their hourly off-farm wage is 30 CNY/h, then the AMS rent is ten CNY/h and the wage-rent ratio is three. The definition implies that the higher the wage-rent ratio, the higher the opportunity cost for a farmer to operate the task unaided. Another important variable is AMS choice. We define the AMS choice (DS) as a dummy variable equal to one if a farm household chooses not to operate the task i unaided but to buy the AMS from the market, and zero otherwise.

The control variables are categorized into the following four groups: (i) The characteristics of the head of a farm household, including gender, age, education, whether engage in an off-farm occupation¹5, whether have a religious belief, and risk preference. Following the method of Holt & Laury (2002), we designed an experiment to measure the risk attitude of the head of a farm household. We obtained an index ranging from zero (extreme risk-averse) to one (extreme risk-loving) to represent the individual risk preference; (ii) Land characteristics, including planting area, number of plots, and plot fertility; (iii) Farm household characteristics, including whether a family member belongs to the Chinese Communist Party (CCP), is a village committee member, is a villager representative; and (iv) A proxy variable for the village location and market access. Market access may be associated with village-level rent and influence crop yields. To control the confounding effect of market access, we use “the distance from village to the nearest town" as the proxy.16 We also included county dummies to control unobserved characteristics at the county level. The summary statistics for these variables are summarized in Table 1.

## 4.3 Descriptive statistics

In Figure 1, we plot the estimated kernel densities of the wage-rent ratios of the four tasks for the AMS (the blue dashed lines) and non-AMS groups (the red solid lines).17 Compared to the AMS group, the density of the non-AMS group is skewed more to the left, which means that the non-adoption group has a relatively lower wage-rent ratio with a higher probability. All four panels in Figure 1 indicate that the wage-rent ratios of both groups are right or positively skewed, that is, the mean of the wage-rent ratio is higher than its median. For the AMS prices of the four tasks, the means and medians are quite similar, as reported in Table 1. Therefore, their densities are likely to be close to the normal distribution.18 The positive skewness of the wage-rent ratio implies the positive skewness of the hourly off-farm wages and is consistent with the results of the Chinese General Social Survey (CGSS).19

TA BL E 1 Summary statistics
<table><tr><td></td><td>Mean</td><td>Min</td><td>Median</td><td>Max</td></tr><tr><td>Panel A: AMS related characteristics</td><td></td><td></td><td></td><td></td></tr><tr><td>Plowing choice (P)</td><td>.48</td><td>.00</td><td>.00</td><td>1.00</td></tr><tr><td>Transplanting choice (T)</td><td>.27</td><td>.00</td><td>.00</td><td>1.00</td></tr><tr><td>Pesticide spraying choice (S)</td><td>.09</td><td>.00</td><td>.00</td><td>1.00</td></tr><tr><td>Harvesting choice (H)</td><td>.81</td><td>.00</td><td>1.00</td><td>1.00</td></tr><tr><td>Off-farm wage (yuan/day)</td><td>179.07</td><td>.00</td><td>90.00</td><td>595.00</td></tr><tr><td>Wage-rent ratio (P)</td><td>2.27</td><td>.00</td><td>1.00</td><td>31.19</td></tr><tr><td>Wage-rent ratio (T)</td><td>1.09</td><td>.00</td><td>.40</td><td>21.32</td></tr><tr><td>Wage-rent ratio (S)</td><td>.78</td><td>.00</td><td>.28</td><td>15.59</td></tr><tr><td>Wage-rent ratio (H)</td><td>4.23</td><td>.00</td><td>1.50</td><td>71.29</td></tr><tr><td>Plowing price (yuan/mu)</td><td>109.22</td><td>30.00</td><td>100.00</td><td>200.00</td></tr><tr><td>Transplanting price (yuan/mu)</td><td>82.72</td><td>25.00</td><td>85.00</td><td>140.00</td></tr><tr><td>Pesticide spraying price (yuan/mu)</td><td>21.88</td><td>5.00</td><td>21.00</td><td>100.00</td></tr><tr><td>Harvesting price (yuan/mu)</td><td>115.55</td><td>60.00</td><td>100.00</td><td>300.00</td></tr><tr><td>Panel B: Household head Characteristics</td><td></td><td></td><td></td><td></td></tr><tr><td>Gender (1 = male)</td><td>.97</td><td>.00</td><td>1.00</td><td>1.00</td></tr><tr><td>Age</td><td>58.64</td><td>36.00</td><td>60.00</td><td>85.00</td></tr><tr><td>Years of education</td><td>6.42</td><td>.00</td><td>6.00</td><td>16.00</td></tr><tr><td>Off-farm occupation (1 = yes)</td><td>.41</td><td>.00</td><td>.00</td><td>1.00</td></tr><tr><td>Risk preference</td><td>.45</td><td>.00</td><td>.40</td><td>1.00</td></tr><tr><td>Religion belief (1 = yes)</td><td>.08</td><td>.00</td><td>.00</td><td>1.00</td></tr><tr><td>Panel C: Land characteristics</td><td></td><td></td><td></td><td></td></tr><tr><td>Rice yield (kg/mu)1</td><td>539.21</td><td>50.00</td><td>500.00</td><td>1050.00</td></tr><tr><td>Planting area (mu)</td><td>40.88</td><td>1.38</td><td>14.00</td><td>232.50</td></tr><tr><td>Number of plots</td><td>12.61</td><td>1.00</td><td>8.00</td><td>50.00</td></tr><tr><td>Land fertility (1 = yes)</td><td>.57</td><td>.00</td><td>1.00</td><td>1.00</td></tr><tr><td>Plain (1 = yes)</td><td>.91</td><td>.00</td><td>1.00</td><td>1.00</td></tr><tr><td>Panel D: Household characteristics</td><td></td><td></td><td></td><td></td></tr><tr><td>CPC member (1 = yes)</td><td>.29</td><td>.00</td><td>.00</td><td>1.00</td></tr><tr><td>Village representatives (1 = yes)</td><td>.32</td><td>.00</td><td>.00</td><td>1.00</td></tr><tr><td>Village committee member (1 = yes)</td><td>.23</td><td>.00</td><td>.00</td><td>1.00</td></tr><tr><td>Panel E: Proxy for location/market access</td><td></td><td></td><td></td><td></td></tr><tr><td>Distance from village to nearest town (km)</td><td>4.66</td><td>.10</td><td>4.00</td><td>45.00</td></tr></table>

Note: 11 mu = 666.67 m².

Panel A of Table 2 presents the observed joint probabilities of choosing AMS for the four tasks. Some joint probabilities, such as Cases 3, 6, and 8, are small or even zero. Thus, we focus on cases with relatively high joint probabilities. The marginal probabilities of choosing AMS for the four tasks are presented in the first row of Panel B, which are remarkably different. Specifically, the probability of using AMS for harvesting is the highest (81.5%)

![](images/986be719ab89b5e7f0a9df595916362d9d8dfea94025796caa9603cda8130b3f.jpg)

![](images/55123089624e0d043e9dbe3a34f49f1f4cb4b758aefeee84ade205b470929ed7.jpg)

![](images/ac5f0b3940b085b7fd3c63d19343c0d937db911a28ceb5bf1e4a003cd55a6cd2.jpg)

![](images/5b52bcf20270212d4cb2cb800644014099a0b5e5a19859d3dd2956e6dc272786.jpg)  
FIG U R E 1 Comparison of density in non-AMS and AMS groups. Note: The figure represents the Epanechnikov kernel densities of wage-rent ratios in four tasks. The blue dashed line and red solid line represent the density of the non-AMS and AMS groups, respectively Compared to the AMS group, the density of the non-AMS group skewed more to the left, signifying that the non-AMS group has a relatively lower wage-rent ratio with a higher probability.

among the four tasks, followed by plowing and transplanting at 48.5% and 26.5%, respectively, while the probability for pesticide spraying is the lowest (9.3%).

Panel B of Table 2 illustrates that the AMS choices of the four tasks are highly correlated. For example, among farm households who adopt AMS for harvesting, plowing, and transplanting, 33.3% choose to hire the service for pesticide spraying, while the corresponding unconditional probability is only 9.3% for the whole sample. Among those households who hire AMS for harvesting, 57.7% also choose the service for plowing. Hence, if a farm household adopts AMS for one task, it is more likely to adopt AMS for another particular task. We will revisit conditional probabilities after estimating the MVP model.

## 5  ADOPTION PATTERNS OF AMS

## 5.1  Regression results: MVP versus UVP

To compare with the MVP model, we estimate the AMS adoption equations for four tasks separately using the UVP. The MVP model is preferred as it jointly estimates the AMS decisions after accounting for cross-equation correlations.

The estimation results of the MVP and UVP models are presented in Table 3, Columns 1–4 and 5–8, respectively. Comparing the two sets of results, we find that the standard errors of the MVP model are smaller than those of the UVP, implying that the MVP estimates are more efficient. In Panel B of Table 3, we report the estimated correlation coefficients: ρ(i, j = T, P, S, H; i ≠ j), which are jointly significant at the 1% level, with four significantly different from zero. This indicates strong correlations among the AMS choices of the same farm household, which can be induced by unobserved factors such as farmer's preference for leisure. Therefore, the MVP model is more suitable in this setting, and we will focus on its results next.

The marginal effects (MEs) of the explanatory variables on unconditional probabilities in the MVP model are reported in Table A2. All MEs are evaluated at the sample means of the other variables. All wage-rent ratios have significant and positive effects on the AMS choices of the four tasks. Specifically, a one-unit increase in the wagerent ratio results in a 1.2%, 2.9%, 3.9%, and 3.0% rise in the probability of plowing, transplanting, pesticide spraying, and harvesting, respectively.

The effect of the age of household head also provides insights into the adoption of AMS. Age has a significant positive effect on the choice of plowing and harvesting, but does not significantly influence the choices of transplanting and spraying. This is probably because harvesting and plowing are highly demanding of physical strength compared with tasks such as pesticide spraying. The probability of using AMS increases with age, with an average 1.2% and .8% annual increase for harvesting and plowing, respectively.

TA BL E 2 Observed probabilities of using AMS  
Panel A: Observed joint probability of using AMS
<table><tr><td>Case</td><td>Plowing</td><td>Transplanting</td><td>Spraying</td><td>Harvesting</td><td>Probability</td></tr><tr><td>1</td><td>Yes</td><td>No</td><td>No</td><td>No</td><td>.010</td></tr><tr><td>2</td><td>No</td><td>Yes</td><td>No</td><td>No</td><td>.030</td></tr><tr><td>3</td><td>No</td><td>No</td><td>Yes</td><td>No</td><td>.000</td></tr><tr><td>4</td><td>No</td><td>No</td><td>No</td><td>Yes</td><td>.263</td></tr><tr><td>5</td><td>Yes</td><td>Yes</td><td>No</td><td>No</td><td>.005</td></tr><tr><td>6</td><td>Yes</td><td>No</td><td>Yes</td><td>No</td><td>.000</td></tr><tr><td>7</td><td>Yes</td><td>No</td><td>No</td><td>Yes</td><td>.288</td></tr><tr><td>8</td><td>No</td><td>Yes</td><td>Yes</td><td>No</td><td>.000</td></tr><tr><td>9</td><td>No</td><td>Yes</td><td>No</td><td>Yes</td><td>.068</td></tr><tr><td>10</td><td>No</td><td>No</td><td>Yes</td><td>Yes</td><td>.010</td></tr><tr><td>11</td><td>Yes</td><td>Yes</td><td>Yes</td><td>No</td><td>.000</td></tr><tr><td>12</td><td>Yes</td><td>Yes</td><td>No</td><td>Yes</td><td>.105</td></tr><tr><td>13</td><td>Yes</td><td>No</td><td>Yes</td><td>Yes</td><td>.025</td></tr><tr><td>14</td><td>No</td><td>Yes</td><td>Yes</td><td>Yes</td><td>.005</td></tr><tr><td>15</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td><td>.053</td></tr><tr><td>16</td><td>No</td><td>No</td><td>No</td><td>No</td><td>.140</td></tr><tr><td>Total</td><td></td><td></td><td></td><td></td><td>1.000</td></tr><tr><td colspan="6">Panel B: Selected (un)conditional probabilities of using AMS</td></tr><tr><td>Case</td><td></td><td>Plowing</td><td>Transplanting</td><td>Spraying</td><td>Harvesting</td></tr><tr><td>1 Pr(·)</td><td></td><td>.485</td><td>.265</td><td>.093</td><td>.815</td></tr><tr><td>2</td><td>Pr(·|H = 1)</td><td>.577</td><td>.282</td><td>.134</td><td>1.000</td></tr><tr><td>3</td><td>Pr(·|H = 1, P = 1)</td><td>1.000</td><td>.335</td><td>.165</td><td>1.000</td></tr><tr><td>4</td><td>Pr(·|H = 1, P = 1, T = 1)</td><td>1.000</td><td>1.000</td><td>.333</td><td>1.000</td></tr></table>

Note: Panel A presents the observed joint probabilities of adopting AMS in 16 cases. Panel B presents four selected (un)conditional probabilities. Pr(H)is the highest probability among the four tasks, so we pick harvesting as the condition. We choose (harvesting and plowing) and (harvesting, plowing, and transplanting) as the conditions following the same logic.

## 5.2 Prediction of the probabilities of AMS adoption

Based on the estimation results of the MVP model, we calculate the conditional and unconditional probabilities of adopting AMS in this section. For comparison, we also calculate the conditional and unconditional probabilities using the UVP model. Specifically, we employ the UVP-Exogenous model to estimate a separate UVP model for each of the four tasks with the dummies of the other three tasks on the right-hand side.

In Table 4, we report the predicted (un)conditional probabilities using the MVP and UVP-Exogenous models with all predicted probabilities evaluated at the sample means of the covariates.20 Consistent with our expectation, there exist remarkable differences between the predicted probabilities calculated using MVP and UVP-Exogenous. For example, for a farm household that adopts AMS for harvesting, the predicted probability of adopting AMS for transplanting is 14.8% using the MVP model, but 24.2% with the UVP-Exogenous model.

Standard errors of the predicted (un)conditional probabilities in Table 4 are calculated using simulations. First, we simulate the coefficients 3000 times based on the estimated coefficients, standard errors, and correlation coefficients. Second, we multiply the matrix by the vector of the sample means of all covariates. Finally, we obtain 3000 sets of simulated probabilities, from which we compute the sample standard errors.

E s s sd  o s -s TAA
<table><tr><td colspan="9">Panel A: Regression Results of the MVP and UVP Models (2)</td></tr><tr><td>Dependent variable:</td><td>(1)</td><td></td><td>(3)</td><td>(4) Using AMS (1 = yes)</td><td>(5)</td><td>(6)</td><td>(7)</td><td>(8)</td></tr><tr><td>Model:</td><td colspan="9">MVP</td></tr><tr><td>Task:</td><td>Plowing</td><td>Transplanting</td><td>Spraying</td><td>Harvesting</td><td>Plowing</td><td>UVP Transplanting</td><td>Spraying</td><td>Harvesting</td></tr><tr><td>Wage-rent ratio (P)</td><td>.042**</td><td></td><td></td><td></td><td>.045*</td><td></td><td></td><td></td></tr><tr><td>(.021)</td><td></td><td></td><td></td><td></td><td>(.024)</td><td></td><td></td><td></td></tr><tr><td></td><td>.141**</td><td></td><td></td><td></td><td></td><td>.141**</td><td></td><td></td></tr><tr><td>Wage-rent ratio (T)</td><td></td><td>(.061)</td><td></td><td></td><td></td><td>(.066)</td><td></td><td></td></tr><tr><td>Wage-rent ratio (S)</td><td></td><td></td><td>.229***</td><td></td><td></td><td></td><td>.274***</td><td></td></tr><tr><td></td><td></td><td></td><td>(.068)</td><td></td><td></td><td></td><td>(.069)</td><td></td></tr><tr><td>Wage-rent ratio (H)</td><td></td><td></td><td></td><td>.137***</td><td></td><td></td><td></td><td>.170***</td></tr><tr><td></td><td></td><td></td><td></td><td>(.040)</td><td></td><td></td><td></td><td>(.047)</td></tr><tr><td>Household head char.</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td></tr><tr><td>Land char.</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td></tr><tr><td>Household char.</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td></tr><tr><td>Proxy for location</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td></tr><tr><td>County dummies</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td></tr><tr><td>Observations</td><td></td><td>399</td><td></td><td></td><td>398</td><td>362</td><td>398</td><td>398</td></tr><tr><td>Wald chi2</td><td></td><td>3064.54</td><td></td><td></td><td>134.73</td><td>121.21</td><td>35.55</td><td>97.51</td></tr><tr><td colspan="9">Panel B: Regression results of the MVP and UVP Models</td></tr><tr><td>PPT</td><td>.019</td><td>(.114)</td><td>PTS</td><td>.472***</td><td>(.098)</td><td>PTH</td><td>-.031</td><td>(.125)</td></tr><tr><td>PPS Likelihood ratio test of ρTp = ρTs = ρτH = ρps = ρpµ = ρsH = 0: Chi2(6) = 68.13, Prob. &gt; chi2 = .00.</td><td>.591***</td><td>(.083)</td><td>ρPH</td><td>.541***</td><td>(.087)</td><td>PSH</td><td>.387***</td><td>(.093)</td></tr></table>

t rt -  o  o ts e- t  e t o   s s t  t t st er    td  e e rs    \*     te oe s  a e o o xod  s o  e o o     o    st  -   o  t   oed coud  e  se  s  t   oa  t s    -  o   del.

TA B L E4 Predicted probabilities of using AMS via simulation
<table><tr><td colspan="3">MVP</td><td colspan="2">UVP-exogenous</td></tr><tr><td>Unconditional probability of AMS</td><td></td><td></td><td></td><td></td></tr><tr><td>Pr(P = 1|X)</td><td>.451</td><td>(.030)</td><td>.419</td><td>(.032)</td></tr><tr><td>Pr(T = 1|X)</td><td>.149</td><td>(.018)</td><td>.244</td><td>(.028)</td></tr><tr><td>Pr(S = 1|X)</td><td>.073</td><td>(.014)</td><td>.053</td><td>(.017)</td></tr><tr><td>Pr(H = 1|X)</td><td>.934</td><td>(.018)</td><td>.938</td><td>(.020)</td></tr><tr><td colspan="3">Probability of AMS conditional on harvesting</td><td></td><td></td></tr><tr><td>Pr(P = 1|H = 1, X)</td><td>.476</td><td>(.031)</td><td>.491</td><td>(.033)</td></tr><tr><td>Pr(T = 1|H = 1, X)</td><td>.148</td><td>(.019)</td><td>.242</td><td>(.031)</td></tr><tr><td>Pr(S = 1|H = 1,X)</td><td>.078</td><td>(.015)</td><td>.053</td><td>(.017)</td></tr><tr><td colspan="3">Probability of AMS conditional on harvesting and plowing</td><td></td><td></td></tr><tr><td>Pr(T = 1|H = 1, P = 1, X)</td><td>.152</td><td>(.029)</td><td>.225</td><td>(.047)</td></tr><tr><td>Pr(S = 1|H = 1, P = 1, X)</td><td>.144</td><td>(.025)</td><td>.162</td><td>(.034)</td></tr></table>

Note: The table reports the predicted probabilities of AMS adoption based on the estimates obtained from the MVP model and compares them with the predictions based on the UVP model. Probabilities are calculated at the sample means of the explanatory variables. Standard errors are in parentheses. Standard errors are calculated using simulations. First, we simulate the coefficients 3000 times based on the estimated coefficients, standard errors, and correlation coefficients. Second, we multiply the matrix by the vector of the sample means of all covariates. Finally, we obtain 3000 sets of simulated probabilities. Sample standard errors are calculated based on the simulation results.

Although we cannot observe the order in which households adopt different AMS without household-level panel data, the un(conditional) probabilities in Table 4 enable us to infer the sequential order of AMS adoption across tasks. Predicted unconditional probabilities in Table 4 show that harvesting demonstrates the highest adoption probability of 93.4%. For households who have adopted AMS for harvesting, the second task most likely to be adopted is plowing, with a conditional probability of 47.6%, followed by transplanting and pesticide spraying.

The predicted order is consistent with the sequence of demand for agricultural mechanization postulated by Pingali (2007). The author argues that demand for agricultural mechanization in power-intensive tasks, such as harvesting and plowing, occurs first, while that for control-intensive tasks, such as transplanting, and weeding/pesticide spraying, follows later and is highly correlated with wage rate. Our study provides empirical evidence that the sequential adoption of AMS indeed starts with power-intensive tasks followed by control-intensive tasks, and the order within each group also follows the wage rate relative to the price of AMS. As a result of the sequential pattern of AMS adoption, the demand for AMS can exhibit great spatial differences. Therefore, programs led by the government or NGOs that aim to promote AMS adoption may find it difficult to capture the sequence and spatial distribution of AMS demand, while market-based private sectors may be more sensitive and responsive to the spontaneous demand for AMS.

## 6  PRODUCTIVITY IMPACT OF AMS

## 6.1  Baseline regression results: Garden variety 3SLS versus OLS

Based on the predicted value of DSj,p, we use the garden variety 3SLS approach to estimate the causal effect of AMS choices on rice yields, as specified in Equations (9) and (10). To account for the simultaneous decisions of AMS and the OVB when evaluating the yield effect, we compare the results obtained from the garden variety 3SLS (Columns 1–4) and OLS (Columns 5–8) in Table 5. Although the estimates have the same signs, the estimates of OLS are less efficient than those of the 3SLS model because the single equation OLS method overlooks the correlations between AMS choices of the four tasks. Therefore, in the following discussion, we focus on the results of the garden variety 3SLS, the coefficients of which are plotted in Panel A of Figure 2.

AMS adoption is found to have a significant and positive effect on rice yield in transplanting, plowing, and harvesting. The garden variety 3SLS results show that changing from self-operation to AMS increases the yield by about 48.0 kg, 23.7 kg, and 7.9 kg for plowing, transplanting, and harvesting, respectively.21 Adopting AMS in plowing contributes the most to rice yield, which may result from the fact that insufficient soil plowing hinders crop root growth and reduces soil drainage (Diao et al., 2016). An interesting finding is that adopting AMS for the tasks performed earlier in the growing season has a larger positive yield effect.

E y Vs        y s TA
<table><tr><td rowspan="3">Dependent var.: Model:</td><td>(1)</td><td>(2)</td><td>(3)</td><td>(4)</td><td>(5)</td><td>(6)</td><td>(7)</td><td>(8)</td></tr><tr><td colspan="3">Garden variety 3SLS</td><td colspan="2">Rice Yield (kg/mu)</td><td colspan="3">OLS</td></tr><tr><td>Plowing</td><td>Transplanting</td><td>Spraying</td><td>Harvesting</td><td>Plowing</td><td>Transplanting</td><td>Spraying</td><td>Harvesting</td></tr><tr><td>AMS (P)</td><td>47.973***</td><td></td><td></td><td></td><td>15.459</td><td></td><td></td><td></td></tr><tr><td></td><td>(11.443)</td><td></td><td></td><td></td><td>(12.768)</td><td></td><td></td><td></td></tr><tr><td></td><td>23.715***</td><td></td><td></td><td></td><td></td><td>9.377</td><td></td><td></td></tr><tr><td>AMS (T)</td><td></td><td>(2.927)</td><td></td><td></td><td></td><td>(16.650)</td><td></td><td></td></tr><tr><td>AMS (S)</td><td></td><td></td><td>-21.259***</td><td></td><td></td><td></td><td>-3.941</td><td></td></tr><tr><td></td><td></td><td></td><td>(4.630)</td><td></td><td></td><td></td><td>(18.834)</td><td></td></tr><tr><td>AMS (H)</td><td></td><td></td><td></td><td>7.879*</td><td></td><td></td><td></td><td>8.209</td></tr><tr><td></td><td></td><td></td><td></td><td>(4.667)</td><td></td><td></td><td></td><td>(15.966)</td></tr><tr><td>Household head char.</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td></tr><tr><td>Land char.</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td></tr><tr><td>Household char.</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td></tr><tr><td>Proxy for location</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td></tr><tr><td>County dummies</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td></tr><tr><td>R-squared</td><td>.232</td><td>.241</td><td>.240</td><td>.242</td><td>.245</td><td>.243</td><td>.242</td><td>.242</td></tr><tr><td>Chi2</td><td>137.00</td><td>191.14</td><td>146.32</td><td>127.56</td><td>一</td><td></td><td></td><td></td></tr><tr><td>F-stat</td><td>一</td><td>一</td><td>一</td><td></td><td>4.99</td><td>4.92</td><td>4.91</td><td>4.92</td></tr><tr><td>Observations</td><td>394</td><td>394</td><td>394</td><td>394</td><td>394</td><td>394</td><td>394</td><td>394</td></tr></table>

ot  t o t t  t   o  t  t   it o   o ee t erd t   st e ae e r    o   o   ty oeo o oo     os  oa er ot o xod  os oso a  oo o     (- o)  a (- o) ies count -tcs

![](images/873806e280ee1d04e53b380162d354a9d55037c595a712b7c625a40eba08de57.jpg)

![](images/0c89e102f4ede3ef5c0614bca66026725ed52186ac403a439a492f6f66f3f49c.jpg)  
FI G U R E 2 Estimated effects of AMS on rice yield. Note: Panel A presents the effect of AMS on rice yield in the four tasks, respectively (based on the estimation results of the garden variety 3SLS model in Table 5). Panel B presents the effect of the pesticide spraying service on rice yields in the three subsamples in Table 6: (i) samples in which all service providers are professional, (ii) samples in which farmers have labor supervision on the spraying service, and (iii) the intersection of samples in (i) and (ii)

Specifically, as field plowing, transplanting, and harvesting are performed sequentially, the corresponding yields resulting from AMS adoption are 48.0 kg, 23.7 kg, and 7.9 kg, respectively. The reason may be that inadequate or untimely completion of tasks limits the availability of the field for later production tasks.

Existing literature on AMS in agriculture and outsourcing in other industries also offers evidence of productivityenhancing effects (Paul & Yasar, 2009; Picazo-Tadeo & Reig-Martínez, 2006; Sheng et al., 2017). In our case, the positive yield effect may result from the specialization of service providers, who are generally more proficient and professional in executing production tasks. These positive effects relieve the food insecurity possibly associated with AMS and prove that adopting AMS for production tasks is a feasible and efficient way to improve agricultural production in China.

However, using AMS for pesticide spraying has a negative effect on rice yield. A change from self-operation to AMS significantly decreases the rice yield by 21.3 kg.22 Two reasons may account for the negative effect. First, pesticide spraying is harder to monitor compared to other tasks, and without effective supervision it may lead to a moral hazard problem. Second, a relatively larger percentage of non-professional service providers offer pesticide spraying because of its low barriers to entry. Although the magnitude of the negative effect is smaller than the positive effects of transplanting and plowing, this effect is still worth exploring further.

## 6.2 Heterogeneity and robustness

We explore the impact heterogeneity across farmer groups. For doing so, we divide the sample into two subsamples, one with farm household heads who have some off-farm occupation and the other with farm household heads who do not, and conduct the regression analysis separately. The estimated yield effects are summarized in Table A4 in the Appendix. We find that productivity impact varies across groups. The adoption of AMS in plowing, transplanting, and harvesting has larger positive productivity impacts for household heads who do not have an off-farm occupation. One possible explanation is that farm households who do not hire out labor may not suffer or suffer less from agency costs.23 However, the results also show that they suffer more losses in pesticide spraying. It is possible that they may adopt more traditional pesticide spraying services which are more likely to involve moral hazards.

We further check whether there exist heterogeneous effects in terms of farm size.24 We define the subsamples based on farm size, including, less than 15 mu, less than 20 mu, less than 25 mu, less than 50 mu and then compare the results of subsamples with the whole sample. As reported in Table A5 in the Appendix, the results remain robust in terms of sign and magnitude. But we do not find strong evidence of the heterogeneity of productivity impacts across farm sizes. One possible explanation is farmland fragmentation in China. Even if some farm households have larger farms, the farmlands can be located in different regions within a village and are not connected physically to each other (Lu et al., 2013; Wang et al., 2014; Yang et al., 2013), which hinders the realization of scale economy (Jia & Petrick, 2014).

Rice production in Heilongjiang is expected to be different from that in the other two provinces especially considering the geographical latitude and topography, so we exclude Heilongjiang from our sample to test the robustness of the empirical results.25 The empirical results are summarized in Table A6, which shows that the results are largely consistent with the results in Columns 1-4 in Table 5. Next, we will explore the mitigation of the negative effects of pesticide spraying services.

## 6.3  Mitigation of the negative effects of pesticide spraying

Investigating the negative yield effect of AMS for pesticide spraying sheds light on potential ways to mitigate the related yield loss. Compared to the other three tasks, pesticide spraying has three distinct characteristics. First, while other tasks, such as plowing and harvesting, require large agricultural machines, traditional pesticide spraying in China is achieved with a manual pesticide sprayer with a low value (i.e., approximately 15 USD). This leads to many non-professional service providers entering the market. The second characteristic is related to performance monitoring. It is relatively easy to observe the outcomes of tasks other than pesticide spraying. For example, farm households can directly observe the number of rice ears wasted in the field during harvesting. However, it is hard to monitor the performance of pesticide spraying because pesticide does not immediately influence the crop, leading to a potential moral hazard problem. Third, pesticide spraying is executed approximately four times on average in China while the other tasks are only executed once. Considering that pesticide spraying needs to be executed multiple times, executing it proficiently may greatly increase the yield of rice crops that typically suffer from pests and diseases; otherwise, pesticide spraying may have a negative effect. Therefore, we seek to further investigate the yield effect of AMS for pesticide spraying using the subsamples constructed according to the first two characteristics discussed above.

First, we restrict our analysis to the samples in which all service providers of pesticide spraying are professional. We define pesticide spraying providers as professional service providers if they use more advanced spraying machines than traditional hand-operated sprayers (e.g. stretcher sprayers powered by gas or electricity, T-tank sprayers, and air-carrier sprayers). See Figure A2 for more details on spraying machines. The results in Table 6 show that the negative yield effect of AMS for pesticide spraying slightly changes from -21.3 kg to -19.1 kg for the restricted samples (Column 2), implying that the negative effect can be mitigated by adopting more advanced and specialized pesticide sprayers. Service providers outside local communities generally possess more advanced agricultural machinery (Yang et al., 2013), so an important policy implication is that reducing barriers to entry in local AMS markets will likely mitigate the negative yield effect.

Second, we restrict our analysis to the samples of households that can supervise service providers. The results show that the yield effect changes from negative to positive (Column 3) and indicates that the AMS for pesticide spraying can increase rice yield by 43.1 kg with labor supervision. Even though supervision can relieve the concern about the negative effect on yield, its related cost is high. However, our results show that moral hazard does exist in the AMS for pesticide spraying. With the rapid development of agricultural informatization in China, we expect a significant decrease in supervision cost that can potentially solve the moral hazard problem of AMS.

Finally, we further restrict our analysis to the samples of professional providers and farmers with labor supervision. Unsurprisingly, the yield effect of the spraying service is further improved from 43.1 kg to 99.7 kg (Column 4). Therefore, contingent on the specialization of AMS and informatization of agriculture in China, the negative effect of the pesticide spraying service can be fully mitigated or even becomes positive. We plot the coefficient estimates obtained from the whole sample and these three subsamples in Panel B of Figure 2 for comparison.

For each of the three subsample regressions, we test the significance of the difference between the coefficients obtained in a subsample and in the whole sample using the Fisher Permutation Test.26 The null hypothesis is that the absolute value of the difference is zero. We simulate the empirical samples 3000 times and reject all the null hypotheses with p-values smaller than .10, that is, the differences of the coefficients in the subsamples are significant at the 10% level.

TA BL E6 Effect of pesticide spraying service on rice yield in subsamples
<table><tr><td rowspan="3">Dependent var.: Model: Task:</td><td>(1)</td><td>(2)</td><td>(3) Rice yield (kg/mu)</td><td>(4)</td></tr><tr><td colspan="4">The garden variety 3SLS</td></tr><tr><td colspan="4">Pesticide spraying</td></tr><tr><td>Sample:</td><td></td><td>Only professional</td><td>Only with</td><td>Professional service+supervision</td></tr><tr><td>AMS (S)</td><td>All -21.259***</td><td>service -19.123***</td><td>supervision 43.120***</td><td>99.740***</td></tr><tr><td></td><td>(4.630)</td><td>(3.694)</td><td>(2.789)</td><td>(13.850)</td></tr><tr><td>Household head char.</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td></tr><tr><td>Land char.</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td></tr><tr><td>Household char.</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td></tr><tr><td>Proxy for location</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td></tr><tr><td>County dummies</td><td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td></tr><tr><td>Fisher permutation test</td><td></td><td>.063</td><td>.000</td><td>.000</td></tr><tr><td>R-squared</td><td>.240</td><td>.257</td><td>.230</td><td>.224</td></tr><tr><td>Chi2</td><td>146.32</td><td>149.38</td><td>358.07</td><td>163.16</td></tr></table>

Note: \*\*\*P < .01,\*\* P < .05,\* P < .1. Standard errors are in parentheses. The table presents the effect of AMS on rice yield in the subsamples. Column 2 is for the subsample in which all the service providers are professional; Column 3 is for the subsample in which farmers have labor supervision of spraying service, and Column 4 is for the intersection of the two subsamples in Columns 2 and 3. The null hypothesis of the Fisher Permutation Test is that the absolute value of the difference between the AMS coefficient in a subsample and that of the whole sample is zero.

To better understand the negative productivity effects of the pesticide spraying service, we look into the size of the farms who adopt the service.27 The average and median acres of farm households who adopted pesticide spraying services are approximately 57.1 mu and 27.0 mu, while the numbers for households who did not adopt are approximately 39.2 mu and 13.0 mu. Two possible explanations for the negative yield effects are both related to monitoring cost: (i) it might be more difficult for large farms to monitor service providers' task operation, and (ii) more workers may involve in the services for larger farms, which in turn increases difficulties of distinguishing performance of individual workers and result in moral hazards.

## 6.4  Simulation

In this section, we simulate the effect of AMS on rice yield in three scenarios based on the estimates we obtained from the garden variety 3SLS model. In the tasks of transplanting, plowing, and spraying, we define low, medium, and high-level AMS adoption as an increase of 10, 20, and 30 percentage points, respectively. In the task of harvesting, we set the increases as 5, 10, and 15 percentage points as adoption will be higher than 100% with increments of 10 percentage points. For each scenario of an individual task, we run the simulation 500 times. Table 7 reports the simulation results with Column 1 reporting the actual level of AMS adoption.

Using the medium level of AMS adoption (Column 3) as an example, the simulation results show that a medium level increase of AMS adoption for plowing, transplanting, and harvesting increases the average rice yield by 9.61 kg to 549.38 kg, by 4.70 kg to 544.88 kg, and by .77 kg to 540.62 kg, respectively. By contrast, a medium-level adoption of AMS for pesticide spraying decreases the average rice yield by 4.26 kg to 535.60 kg.

Based on the simulations of rice yields in the three scenarios, we further predict the total rice output in China and the resulting number of additional people that can be fed. In 2017, total rice production in China was 212.67 billion kg according to the National Bureau of Statistics of China. Using this statistic and the simulated rice yield, we estimate total rice production in the three scenarios for each task. Average rice consumption per capita in China reached approximately 117 kg in 2017 in China according to the Food and Agriculture Organization (FAO), 28 enabling us to calculate the number of additional people that can be fed as a result of AMS development.

Simulation results show that the plowing service contributes most to the increase in rice output, while pesticide spraying slightly reduces the output. In the medium scenario, a 20 percentage-point increase in plowing service increases total rice production by roughly 3.79 billion kg, providing staple food to approximately 32 million people (roughly the total population of Malaysia). In the high scenario, increased rice production can feed an additional 49 million people (the approximate total population of Spain). Although the decreased output caused by pesticide spraying service is relatively low (-1.68 billion kg in the medium scenario) compared to the increased output of AMS for plowing and transplanting (3.79 and 1.85 billion kg, respectively), the importance of specialization and informatization in mitigating the negative effect of pesticide spraying service is emphasized.

TA BL E7 Simulation of rice yield and total rice output in China under three scenarios
<table><tr><td>Scenario</td><td>(1) Actual</td><td>(2) Low</td><td>(3) Medium</td><td>(4) High</td></tr><tr><td>Panel A: Plowing</td><td></td><td></td><td></td><td></td></tr><tr><td>AMS rate</td><td>.48</td><td>.58</td><td>.68</td><td>.78</td></tr><tr><td>Predicted yield (kg/mu)</td><td>539.77</td><td>544.46</td><td>549.38</td><td>554.20</td></tr><tr><td>Yield growth rate</td><td></td><td>.87%</td><td>1.78%</td><td>2.67%</td></tr><tr><td>Predicted total rice output, China (Billion Kg)</td><td>212.67</td><td>214.52</td><td>216.46</td><td>218.36</td></tr><tr><td>Increased total rice output, China (Billion Kg)</td><td>一</td><td>1.85</td><td>3.79</td><td>5.69</td></tr><tr><td>Additional population being fed (Million)</td><td></td><td>15.79</td><td>32.36</td><td>48.59</td></tr><tr><td>Panel B: Transplanting</td><td></td><td></td><td></td><td></td></tr><tr><td>AMS rate</td><td>.27</td><td>.37</td><td>.47</td><td>.57</td></tr><tr><td>Predicted yield (kg/mu)</td><td>540.18</td><td>542.56</td><td>544.88</td><td>547.32</td></tr><tr><td>Yield growth rate</td><td></td><td>.44%</td><td>.87%</td><td>1.32%</td></tr><tr><td>Predicted total rice output, China (Billion Kg)</td><td>212.67</td><td>213.61</td><td>214.52</td><td>215.49</td></tr><tr><td>Increased total rice output, China (Billion Kg)</td><td>一</td><td>.94</td><td>1.85</td><td>2.81</td></tr><tr><td>Additional population being fed (Million)</td><td></td><td>8.01</td><td>15.82</td><td>24.03</td></tr><tr><td>Panel C: Spraying</td><td></td><td></td><td></td><td></td></tr><tr><td>AMS rate</td><td>.09</td><td>.19</td><td>.29</td><td>.39</td></tr><tr><td>Predicted yield (kg/mu)</td><td>539.86</td><td>537.73</td><td>535.60</td><td>533.52</td></tr><tr><td>Yield growth rate</td><td></td><td>-.39%</td><td>-.79%</td><td>-1.17%</td></tr><tr><td>Predicted total rice output, China (Billion Kg)</td><td>212.67</td><td>211.83</td><td>211.00</td><td>210.18</td></tr><tr><td>Increased total rice output, China (Billion Kg)</td><td></td><td>-.84</td><td>-1.68</td><td>-2.50</td></tr><tr><td>Additional population being fed (Million)</td><td>一</td><td>-7.17</td><td>-14.34</td><td>-21.35</td></tr><tr><td>Panel D: Harvesting</td><td></td><td></td><td></td><td></td></tr><tr><td>AMS rate</td><td>.81</td><td>.86</td><td>.91</td><td>.96</td></tr><tr><td>Predicted yield (kg/mu)</td><td>539.85</td><td>540.22</td><td>540.62</td><td>541.02</td></tr><tr><td>Yield growth rate</td><td>一</td><td>.07%</td><td>.14%</td><td>.22%</td></tr><tr><td>Predicted total rice output, China (Billion Kg)</td><td>212.67</td><td>212.82</td><td>212.98</td><td>213.13</td></tr><tr><td>Increased total rice output, China (Billion Kg)</td><td>一</td><td>.15</td><td>.30</td><td>.46</td></tr><tr><td>Additional population being fed (Million)</td><td>一</td><td>1.25</td><td>2.59</td><td>3.94</td></tr></table>

Note: The table reports simulation results for predicted rice yield, actual total (and increased) rice output, and additional population fed in three scenarios based on the estimates obtained from the garden variety 3SLS model. In harvesting, we set an increment of 5 percentage points (the other three tasks are 10) since it will be higher than 100%, with increments of 10 percentage points in the high scenario. NBSC provides actual total rice output in 2017. FAO statistic is used for the average rice consumption per capita per year in China (117 kg); we estimated the additional population that can be fed based on these data.

## 7  CONCLUSION

Individual countries should choose a realistic route of agricultural mechanization that suits their agricultural resources, stage of development, and institutional background. Agricultural mechanization services have been and will continue to be an effective and efficient way to help China achieve agricultural mechanization. The market effectively matches the current affordable agricultural technology with the sequential demand for agricultural mechanization, which is determined by the ratio of the offfarm wage to the price of service in China. Furthermore, the positive productivity impact of AMS ensures it is a sustainable approach that farmers will continue to adopt in the future.

These empirical results support a facilitative and supportive role for the government. First, facilitating the development of AMS should follow the sequential order of AMS demand to avoid waste of resources and to increase effectiveness. Second, removing distortionary policies such as reducing entry barriers in local AMS markets can promote the application of advanced agricultural technology, which can mitigate the negative effect of a spraying service. Finally, promoting agricultural informatization can reduce labor supervision costs and further solve the related moral hazard problem.

We predict that AMS will rapidly develop in the near future in China. Rising off-farm wages and decreases in farm machinery costs will increase the demand for AMS, while the increasing use of professional equipment and the development of agricultural informatization will mitigate concerns related to AMS adoption. The further development of AMS will consequently enhance food security in China.

China's experience of realizing agricultural mechanization through AMS will provide insights for other Southeastern and South Asian developing countries that are experiencing rapid urbanization and increasing opportunities from off-farm employment. For some African countries, especially those in the Sub-Saharan area, attempts to promote the development of AMS through state-led or NGO-supported services are beneficial but not sufficient. Increasing off-farm income by broadening off-farm employment opportunities is also needed and can promote farmers' spontaneous demand for AMS. AMS development can act as an effective substitute for farmers' own labor and can compensate for labor shortages in the busy farming seasons, which in turn would result in yield improvement, enhanced food security, and less dependence by a large and fast-growing population on the global grain market.

We conclude with a discussion of some study limitations. First, although we conducted a detailed input-output survey of rice farmers in China, our sample size was restricted by survey costs. A larger scale survey covering more crops (e.g., wheat, maize, and potato) is required to evaluate the comprehensive effects of AMS on crop yield. Second, we did not distinguish rice farmers who do not use AMS. As agricultural operators without the use of AMS in China become more diversified, we will emphasize their heterogeneity in future research. Last, we acknowledge that although we have carefully dealt with the endogeneity of the adoption of AMS and attenuated the endogeneity bias, we cannot rule out the possibility that some unobserved factors may associate with the instrumental variable given the cross-sectional data we have. To better control for unobservable time-invariant factors, a follow-up survey is on our future research agenda.

## ACKNOWLEDGMENTS

We appreciate Prof. Abdulai and the two anonymous referees for their constructive comments and suggestions. Qinan Lu thanks Guanming Shi and workshop participants at the University of Wisconsin-Madison. Xiaodong Du thanks the workshop participants at the Center for Quantitative Economics of Jilin University. All errors are our own.

## REFERENCES

Adu-Baffour, F., Daum, T., & Birner, R. (2019). Can small farms benefit from big companies' initiatives to promote mechanization in Africa? A case study from Zambia. Food Policy, 84, 133–145. https://doi.org/10.1016/j.foodpol.2019.03.007

Angrist, J. D., & Pischke, J.-S. (2008). Mostly harmless econometrics: An empiricist's companion. Princeton, N.J: Princeton University Press.

At, C., & Thomas, L. (2019). Optimal tenurial contracts under both moral hazard and adverse selection. American Journal of Agricultural Economics, 101(3), 941–959. https://doi.org/10.1093/ajae/ aay049

Atamanov, A., & Van den Berg, M. (2012). Participation and returns in rural nonfarm activities: Evidence from the Kyrgyz Republic. Agricultural Economics, 43(4), 459–471. https://doi.org/10.1111/j.1574- 0862.2012.00596.x

Bel, K., Fok, D., & Paap, R. (2018). Parameter estimation in multivariate logit models with many binary choices. Econometric Reviews, 37(5),534–550. https://doi.org/10.1080/07474938.2015.1093780

Biggs, S., & Justice, S. (2015). Rural and agricultural mechanization: A history of the spread of small engines in selected Asian countries. IFPRI Discussion Paper 01443, International Food Policy Research Institute (IFPRI), Available at: https://tinyurl.com/y2zm7ffz

Bontemps, C., & Nauges, C. (2016). The impact of perceptions in averting-decision models: An application of the special regressor method to drinking water choices. American Journal of Agricultural Economics, 98(1), 297–313. https://doi.org/10.1093/ajae/ aav046

Carillo, M. F. (2021). Agricultural policy and long-run development: Evidence from Mussolini's Battle for Grain. The Economic Journal, 131(634), 566-597. https://doi.org/10.1093/ej/ueaa060

Carter, M. R., & Yao, Y. (2002). Local versus global separability in agricultural household models: The factor price equalization effect of land transfer rights. American Journal of Agricultural Economics, 84(3), 702-715. https://doi.org/10.1111/1467-8276.00329

Caunedo, J., & Kala, N. (2021). Mechanizing agriculture. Department of Economics Working Paper, Cornell University. Available at: http://www.julietacaunedo.com/research.html

Chari, A., Liu, E. M., Wang, S.-Y., & Wang, Y. (2021). Property rights, land misallocation, and agricultural efficiency in China. The Review of Economic Studies, 88(4), 1831–1862. https://doi.org/ 10.1093/restud/rdaa072

Chen, S., & Lan, X. (2020). Tractor vs. animal: Rural reforms and technology adoption in China. Journal of Development Economics, 147, 102536. https://doi.org/10.1016/j.jdeveco.2020.102536

Chrisendo, D., Siregar, H., & Qaim, M. (2021). Oil palm and structural transformation of agriculture in Indonesia. Agricultural Economics, 52(5), 849–862. https://doi.org/10.1111/agec.12658

Cortes, G. M., & Salvatori, A. (2019). Delving into the demand side: Changes in workplace specialization and job polarization. Labour Economics, 57, 164–176. https://doi.org/10.1016/j.labeco. 2019.02.004

Daum, T., & Birner, R. (2017). The neglected governance challenges of agricultural mechanization in Africa-insights from Ghana. Food Security, 9(5), 959–979. https://doi.org/10.1007/s12571-017-0716-9

Diao, X., Cossar, F., Houssou, N., & Kolavalli, S. (2014). Mechanization in Ghana: Emerging demand, and the search for alternative supply models. Food Policy, 48, 168–181. https://doi.org/10.1016/j. foodpol.2014.05.013

Diao, X., Silver, J., & Takeshima, H. (2016). Agricultural mechanization and agricultural transformation. IFPRI Discussion Paper 01527, International Food Policy Research Institute (IFPRI). Available at: https://tinyurl.com/54xhfm5x

Duarte, M., & Restuccia, D. (2010). The role of the structural transformation in aggregate productivity. The Quarterly Journal of Economics, 125(1), 129–173. https://doi.org/10.1162/qjec.2010.125.1. 129

Dubois, P. (2002). Moral hazard, land fertility and sharecropping in a rural area of the Philippines. Journal of Development Economics, 68(1), 35-64. https://doi.org/10.1016/S0304-3878(02)00005-6

Efron, B., & Tibshirani, R. J. (1994). An introduction to the bootstrap. Boca Raton, FL: Chapman & Hall/CRC Press.

Ghatak, M., & Pandey, P. (2000). Contract choice in agriculture with joint moral hazard in effort and risk. Journal of Development Economics, 63(2), 303-326. https://doi.org/10.1016/S0304-3878(00) 00116-4

Hausman, J. A. (1975). An instrumental variable approach to full information estimators for linear and certain nonlinear econometric models. Econometrica, 43, 727–738.

Hayami, Y., & Ruttan, V. W. (1971). Induced innovation in agricultural development. Center for Economic Research, Department of Economics, University of Minnesota.

Holt, C. A., & Laury, S. K. (2002). Risk aversion and incentive effects. American economic review, 92(5), 1644–1655.

Houssou, N., Diao, X., Cossar, F., Kolavalli, K., Jimah, K., & Aboagye, P. O. (2013). Agricultural mechanization in Ghana: Is specialized agricultural mechanization service provision a viable business model? American Journal of Agricultural Economics, 95(5), 1237-1244. https://tinyurl.com/44an8sax

Huang, J., & Ding, J. (2016). Institutional innovation and policy support to facilitate small-scale farming transformation in China. Agricultural Economics, 47(S1), 227–237. https://doi.org/10.1111/ agec.12309

Huang, J., Gao, L., & Rozelle, S. (2012). The effect of off-farm employment on the decisions of households to rent out and rent in cultivated land in China. China Agricultural Economic Review, 4(1), 5–17. https://doi.org/10.1108/17561371211196748

Jia, L., & Petrick, M. (2014). How does land fragmentation affect offfarm labor supply: Panel data evidence from China. Agricultural Economics, 45(3), 369–380. https://doi.org/10.1111/agec.12071

Jin, S., & Deininger, K. (2009). Land rental markets in the process of rural structural transformation: Productivity and equity impacts from China. Journal of Comparative Economics, 37(4), 629–646. https://doi.org/10.1016/j.jce.2009.04.005

Johnston, B. F., & Mellor, J. W. (1961). The role of agriculture in economic development. The American Economic Review, 51(4), 566-593.

Kimura, S., Otsuka, K., Sonobe, T., & Rozelle, S. (2011). Efficiency of land allocation through tenancy markets: Evidence from China. Economic Development and Cultural Change, 59(3), 485-510. https://doi.org/10.1086/649639

Kumar, D., & Kalita, P. (2017). Reducing postharvest losses during storage of grain crops to strengthen food security in developing countries. Foods, 6(1), 8. https://doi.org/10.3390/foods6010008

Li, C., Poskitt, D. S., & Zhao, X. (2019). The bivariate probit model, maximum likelihood estimation, pseudo true parameters and partial identification. Journal of Econometrics, 209(1), 94–113. https:// doi.org/10.1016/j.jeconom.2018.07.009

Lu, X., Xianjin, H., Taiyang, Z., Yuntai, Z., & Yi, L. (2013). A review of farmland fragmentation in China. Journal of Resources and Ecology, 4(4), 344–352. https://doi.org/10.5814/j.issn.1674-764x.2013.04. 007

Ma, W., Abdulai, A., & Goetz, R. (2018). Agricultural cooperatives and investment in organic soil amendments and chemical fertilizer in China. American Journal of Agricultural Economics, 100(2), 502– 520. https://doi.org/10.1093/ajae/aax079

Magrini, E., Balié, J., & Morales-Opazo, C. (2017). Cereal price shocks and volatility in sub-Saharan Africa: What really matters for farmers' welfare? Agricultural Economics, 48(6), 719–729. https://doi. org/10.1111/agec.12369

Matsuyama, K. (1992). Agricultural productivity, comparative advantage, and economic growth. Journal of Economic Theory, 58(2), 317-334. https://doi.org/10.1016/0022-0531(92)90057-0

McGuirk, E., & Burke, M. (2020). The economic origins of conflict in Africa. Journal of Political Economy, 128(10), 3940–3997. https:// doi.org/10.1086/709993

Mugera, A. W., Langemeier, M. R., & Ojede, A. (2016). Contributions of productivity and relative price changes to farm-level profitability change. American Journal of Agricultural Economics, 98(4), 1210-1229. https://doi.org/10.1093/ajae/aaw029

Paul, C. J. M., & Yasar, M. (2009). Outsourcing, productivity, and input composition at the plant level. Canadian Journal of Economics, 42(2), 422-439. https://doi.org/10.1111/j.1540-5982.2009. 01514.x

Picazo-Tadeo, A. J., & Reig-Martínez, E. (2006). Outsourcing and efficiency: The case of Spanish citrus farming. Agricultural Economics, 35(2), 213–222. https://doi.org/10.1111/j.1574-0862.2006. 00154.x

Pingali, P. (2007). Agricultural mechanization: Adoption patterns and economic impact. Handbook of Agricultural Economics, 3, 2779-2805. https://doi.org/10.1016/S1574-0072(06)03054-4

Ramful, P., & Zhao, X. (2009). Participation in marijuana, cocaine and heroin consumption in Australia: A multivariate probit approach. Applied Economics, 41(4), 481–496. https://doi.org/10. 1080/00036840701522853

Schultz, T. W. (1953). The economic organization of agriculture. New York: McGraw Hill.

Sheahan, M., & Barrett, C. B. (2017). Ten striking facts about agricultural input use in Sub-Saharan Africa. Food Policy, 67, 12–25. https://doi.org/10.1016/j.foodpol.2016.09.010

Sheng, Y., Song, L., & Yi, Q. (2017). Mechanization outsourcing and agricultural productivity for small farms: implications for rural land reform in China. In: Song et al. (eds.), China's New Sources of Economic Growth. Canberra, Australian: National University Press.

Van Loon, J., Woltering, L., Krupnik, T. J., Baudron, F., Boa, M., & Govaerts, B. (2020). Scaling agricultural mechanization services in smallholder farming systems: Case studies from sub-Saharan Africa, South Asia, and Latin America. Agricultural Systems, 180, 102792. https://doi.org/10.1016/j.agsy.2020.102792

Wang, H. H., Wang, Y., & Delgado, M. S. (2014). The transition to modern agriculture: Contract farming in developing economies. American Journal of Agricultural Economics, 96(5), 1257–1271. https://doi.org/10.1093/ajae/aau036

World Bank (2014). Agribusiness indicators: Synthesis report. Agriculture Global Practice Discussion Paper 1, Washington, D.C.: WorldBank. Available at: https://tinyurl.com/4y5fnmwd

Wu, J., & Babcock, B. A. (1998). The choice of tillage, rotation, and soil testing practices: Economic and environmental implications. American Journal of Agricultural Economics, 80(3), 494–511. https://doi.org/10.2307/1244552

Yang, J., Huang, Z., Zhang, X., & Reardon, T. (2013). The rapid rise of cross-regional agricultural mechanization services in China. American Journal of Agricultural Economics, 95(5), 1245–1251. https://doi.org/10.1093/ajae/aat027

Zhang, X., Yang, J., & Thomas, R. (2017). Mechanization outsourcing clusters and division of labor in Chinese agriculture. China Economic Review, 43, 184–195. https://doi.org/10.1016/j.chieco.2017.01. 012

## SUPPORTING INFORMATION

Additional supporting information can be found online in the Supporting Information section at the end of this article.

How to cite this article: Lu, Q., Du, X., & Qiu, H. (2022). Adoption patterns and productivity impacts of agricultural mechanization services. Agricultural Economics, 53, 826–845.   
https://doi.org/10.1111/agec.12737