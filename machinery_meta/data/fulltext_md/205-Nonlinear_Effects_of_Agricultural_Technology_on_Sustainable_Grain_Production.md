# Nonlinear Effects of Agricultural Technology on Sustainable Grain Production in China

# Nieliniowy wpływ technologii rolniczej na zrównoważoną produkcję zbóż w Chinach

Bizhen Chen1, Dehong Sun²

¹School of Information Management, Minnan University of Science and Technology,

No. 1, Longjing Road, 362000, Quanzhou, China;

E-Mail (Correspondence Author): bizhen\_chen@qq.com,

ORCID: 0009-0000-8559-9996

2School of Information Management, Minnan University of Science and Technology, No. 1, Longjing Road, 362000, Quanzhou, China E-Mail: 155065349@qq.com

## Abstract

Grain production is an important element of the United Nations Sustainable Development Goals, regarding livelihoods and social stability. This article uses data on agricultural technology, social factor and grain production in China from 2011 to 2022, and uses the Generalized Additive Model (GAM) to deeply explore the nonlinear impact of agricultural technology and social factor on grain production. The results of the study show that (1) China's grain output is generally on a growing trend, but the growth rate is declining and fluctuating significantly. There is a significant difference in grain production before and after the COVID-19 epidemic. Moreover, the output in the northern region is significantly higher than that in the south. (2) Except for Consumption expenditure per capita, all other agricultural technology and social factor variables are positively correlated with grain out. (3) The impact of agricultural technology and social factor on grain output shows significant non-linear characteristics, and its impact effect varies in different intervals. Specifically, When the value of the agricultural meteorological observation service station is 20-25, the effective irrigation area is greater than 1800, consumption expenditure per capita greater than 17000 and the total sowing area of crops is 7500, it can significantly increase grain yield. On the contrary, if the emission value of chemical oxygen demand exceeds 130, it has a significant inhibitory effect on grain yield. Furthermore, the effect on grain yield peaks when the total power of agricultural machinery, GDP, and the number of unemployed people in cities approach 3000, 10000, and 20, respectively. The results of the study provide an important basis for optimizing the allocation of agricultural resources and enhancing the efficiency of grain production. Finally, some practical policy recommendations are put forward.

Key words: grain production, sustainable development, machine learning, generalized additive models, agricultural technology, social factor

## Streszczenie

Produkcja zbóż jest ważnym elementem Celów zrównoważonego rozwoju ONZ, dotyczących źródeł utrzymania i stabilności społecznej. W tym artykule przeanalizowano dane dotyczące technologii rolniczej, czynników społecznych i produkcji zbóż w Chinach w latach 2011-2022 oraz wykorzystano uogólniony model addytywny (GAM) w celu dogłębnego zbadania nieliniowego wpływu technologii rolniczej i czynnika społecznego na produkcję zbóż. Wyniki badania pokazują, że (1) produkcja zbóż w Chinach ogólnie wykazuje tendencję wzrostową, ale tempo wzrostu maleje i podlega znacznym wahaniom. Istnieje znacząca różnica w produkcji zbóż przed i po epidemii COVID-19. Co więcej, produkcja w regionie północnym jest znacznie wyższa niż na południu. (2) Z wyjątkiem wydatków konsumpcyjnych na mieszkańca, wszystkie inne zmienne związane z technologią rolniczą i czynnikami społecznymi są dodatnio skorelowane z plonami zboża. (3) Wpływ technologii rolniczej i czynnika

społecznego na wielkość plonów zboża wykazuje znaczną charakterystykę nieliniową, a efekt jego oddziaływania zmienia się w różnych przedziałach. W szczególności, gdy stacja rolniczej obserwacji meteorologicznej wynosi 20-25, efektywna powierzchnia nawadniania jest większa niż 1800, wydatki konsumpcyjne na mieszkańca są większe niż 17000, a całkowita powierzchnia zasiewów roślin wynosi 7500, może znacznie zwiększyć plon ziarna. Natomiast jeśli wartość emisji chemicznego zapotrzebowania tlenu przekracza 130, ma to istotny wpływ hamujący na plon ziarna. Co więcej, wpływ na maksymalne plony zbóż ma sytuacja, gdy całkowita moc maszyn rolniczych, PKB i liczba bezrobotnych w miastach zbliżają się odpowiednio do 3000, 10000 i 20. Wyniki badań stanowią ważną podstawę do optymalizacji alokacji zasobów rolnych i zwiększania efektywności produkcji zbóż. Przedstawiono także kilka praktycznych zaleceń politycznych.

Słowa kluczowe: produkcja zbóż, zrównoważony rozwój, uczenie maszynowe, uogólnione modele addytywne, technologia rolnicza, czynnik społeczny

## 1. Introduction

Grain production is an indispensable cornerstone of national grain security, which plays a pivotal role in maintaining national stability and promoting the sustainable development of human society. Since 2015, global hunger and food insecurity have shown an alarming increase, exacerbated by pandemics, conflict, climate change and growing inequality. Increased grain production has always been a major issue for sustainable development. United Nations Sustainable Development Goal 2 is Zero Hunger, with the ultimate aim of eradicating hunger, achieving grain security, improving nutrition and promoting sustainable agriculture.

The sustainable growth of grain production mainly relies on technological innovation to improve the yield per unit area, and agricultural technological progress is the main support for improving the comprehensive production capacity of grain (Zhang et al., 2022). Meanwhile, social factors also have a significant impact on grain production. For example, socio-economic factors, people's living standards, and social stability are closely related to sustainable grain development. With the rapid progress of technology and continuous innovation in agricultural technology, its role in improving food production efficiency, optimizing resource allocation, and reducing environmental burden is becoming increasingly prominent. At the societal level, there is a complex relationship between the socio-economy and grain production, and from the perspective of people's standard of living, human beings are both creators and consumers of grain production. However, the impact of agricultural technology and social factor on sustainable grain production is not simply linear, but involves the interweaving of numerous variables and complex mechanisms. In the face of the complex elements, determining the mechanism of the impact of grain production is an important issue facing the sustainable development of grain in China at present, and is also the starting point of this study.

Compared with the existing studies, there are three main innovations in this paper. First, the innovation of research content. Existing studies are mostly limited to a single dimension in the selection of agricultural technology indicators, lacking comprehensive consideration. From a more comprehensive perspective, this paper comprehensively examines the effects of meteorology, water quality, mechanical power and other aspects on grain yield, aiming to reveal the integrated effects of multidimensional factors of agricultural technology on grain production. In addition, based on the actual situation, this paper introduces the relevant variables at the social level in the selection of influence factors. At the same time, its impact on the sustainable development of grain is analyzed from the social level. Second, the innovation of research methods. Existing studies have mainly applied traditional models in the analysis of factors influencing grain yield, considering a single linear relationship, however, the variables are intricately related. This paper introduces the generalized additive model (GAM) in the field of machine learning to deeply explore the nonlinear impact of agricultural technology on grain yield. Compared with traditional regression models, machine learning has higher accuracy and provides a more accurate and efficient tool for analyzing the influencing factors of grain production. By introducing machine learning into the field of sustainable grain development, it can realize an important addition to the agricultural research methodology. Third, on the validity of the study's conclusions. Through the GAM in-depth exploration of the dynamic change trend of the impact effect of agricultural technology on grain production, the analysis of this change trend can provide more precise and targeted guidance for policy formulation. The conclusions of the analysis can optimize the allocation of agricultural resources, effectively avoiding the waste of resources, thus ensuring that the impact of agricultural technology on grain production is maximized.

This paper is organized into five parts. The second part reviews the literature on grain production and the impact of agricultural technology on grain production. Then, the third part describes the research design, including the research methodology, indicator selection and data sources. The fourth part describes the spatial and temporal distribution of grain production and focuses on the specific impact of agricultural technology and social factors on grain production. The fifth part mainly summarizes the conclusions and proposes some countermeasures for different factors, which provide useful references for the optimization of agricultural technology, social development and the sustainable development of grain production.

## 2. Literature review

## 2.1. Grain production

Grain production is closely related to the sustainable development of society, and the existing literature mainly focuses on the spatial pattern of grain production and its influencing factors. In terms of the spatial distribution of grain production, the axis of grain production has shifted significantly northward and crossed the Yellow River, which is the main source of irrigation water for agriculture in North China, and China has shifted its grain production to marginal areas with lower land productivity and higher natural risks (Wang et al., 2018). In addition, the COG of grain production in China has shifted to the northeast, gradually forming a spatial pattern of shifting from the northeast to the southwest (Huang et al., 2022). Yin et al. (2024) conducted a systematic assessment of China's four crop yields at the national and provincial scales by using a global lattice crop model. Li and Li (2022) used a dynamic spatial model to explore the influence mechanism and spatial spillover effects of carbon emission intensity (CEI) of food production. Global grain stability has increased in terms of global grain stock demand ratios. Among them, the stability in Asia and Africa has been enhanced (Chen et al., 2023). In addition, Yang and Li (2020) applied gray modeling techniques to the structural reform of grain supply side and used different models to predict the structural balance of supply and demand of different types of grain, Onwuchekwa-Henry et al. (2022) assessed the validity of seasonal estimation of rice yields in lowland fields in northwest Cambodia using meteorological data and vegetation cover information. Yue et al. (2021) developed a new integrated modeling framework for sustainable agriculture-energy-water-food nexus management.

Grain production is influenced by a number of factors. For example, average annual temperature plays an important role in agricultural production, but annual rainfall has little effect on agriculture (Yang et al., 2020). Land rental has a positive impact on rice acreage, especially when less labor is available for agriculture (Qiu et al., 2020). Fang et al. (2021) examined the factors contributing to geographic heterogeneity in the level of grain production in Guangdong Province, China, in terms of land, labor, and capital. In addition, there is a significant positive correlation between the part-time behavior of farm households and grain production (Ge et al., 2023), and urban expansion will continue to negatively affect regional food security in the future (Shen et al., 2023). The arrival of the information age at any time, the Internet also has a significant impact on grain production (Fu and Zhu, 2023; Zheng et al., 2022).

## 2.2. Impact of agricultural technology on grain production

Agricultural technology is an important driver of sustained grain production. Information on modern agricultural technologies and the movement of factors of production is widely disseminated and has had a significant impact on grain productivity and yields. Existing studies have identified three main ways in which agricultural technology contributes to grain production: agricultural machinery, agricultural policies and technical training for farmers. Enhancing the use of agricultural technology and promoting large-scale operations can improve national grain security (Bi et al., 2022). At the same time, an increase in the level of mechanization in one region will significantly contribute to an increase in grain production in its surrounding areas (Wu et al., 2021). In terms of agricultural technology guidance, strengthening technical guidance, training farmers, investing in machinery and equipment, and promoting the development of smart agriculture are effective means to ensure the sustainable development of grain production (Liu et al., 2021). Improving the grain supply system, strengthening the protection of arable land, improving the efficiency of fertilizer utilization, and increasing investment in agricultural science and technology can effectively mitigate the risk of grain security (Cheng and Yin, 2022).

The effects of agricultural technology are reflected in multiple aspects. Lu et al. (2019) proposed the constraints of water resource constraints on agricultural yield and planting structure. Agricultural technological innovation, policy mechanism guarantee, and increased investment in agricultural water conservancy construction can to some extent alleviate the various negative impacts of climate change on agricultural water use in China. The South-North Water Diversion Project could not resolve the conflict between limited agricultural water supply and increasing demand for irrigation. Better management of water resources and crop production is needed to achieve the UN Sustainable Development Goals (Li et al., 2023). In addition, changes in farmland area have a more pronounced impact on grain production than inputs of agricultural machinery and fertilizers (Chai et al., 2019).

In summary, grain production, as a complex systematic project, is characterized by diverse and complex influencing factors and effects. In order to more accurately grasp the dynamic changes in food production, it is necessary to comprehensively consider various factors and analyze them in depth, so as to provide strong theoretical support for the formulation of scientific agricultural production policies and measures. At the same time, it will also help to promote agricultural science and technology innovation and sustainable development, ultimately providing an important guarantee for achieving grain security and agricultural modernization

## 3. Research design

## 3.1. Research methodologies

Machine Learning (ML) is a core branch of Artificial Intelligence and is an effective solution due to its low cost, high speed and low processing difficulty (Li et al., 2023). Generalized Additive Models (GAM) are a specific type of model in the field of machine learning, GAM provide a more efficient analysis than traditional linear models (Ravindra et al., 2019) and are a strong alternative to GLM (Díaz Martínez et al., 2023).

GAM provides a framework for generalizing standard linear models in which each variable is replaced with a nonlinear function while maintaining the overall additivity of the model. Ordinary multiple linear regression modeling formula:

![](images/903861879995873df0c1523d8c239934573d26a13573651eec1e2f7efd1ef052.jpg)

(1)

where β0 is the constant term, β(i = 1,2, .., p) is the regression coefficient, and ε is the error term. The GAM replaces β with a smooth nonlinear function f(X). Therefore, the GAM is computed as:

![](images/ac55b07c820a09e6f0a708c773e2e89a0e26a567fa6be1019e6ccd6d8c0a19b1.jpg)

(2)

In this paper, the GAM is implemented in the R programming language and the GAM fitted by the gam function in the software is with smooth spline. The specific principle is to fit the model by looping through the coefficients updated sequentially for each variable and keeping the other coefficients unchanged. GAM has the following advantages.

(1) GAM allows a nonlinear function to be fitted to each X, which can model neglected nonlinear relationships.

(2) Nonlinear models predict the dependent variable more accurately.

(3) Since the model is additive, it is possible to observe the effect of each independent variable on the dependent variable individually while other variables are held constant.

## 3.2. Definition of variables

The study area of this research, i.e. the administrative divisions of China. The data were obtained from the China Statistical Yearbook and the China Agricultural Statistical Yearbook published by the National Bureau of Statistics of China, covering 31 provinces in China (excluding Hong Kong, Macao and Taiwan) from 20011 to 2022, and the type of data was panel data.

Agricultural technology is not only reflected in the total power of agricultural machinery, but also covers a variety of aspects such as water quality treatment, irrigation capacity and meteorological observation range. Considering the connotation of agricultural technology and referring to Chai et al. (2019) and Lu et al. (2019), the indicators of agricultural technology selected in this paper are: chemical oxygen demand emissions (CODE), total power of agricultural machinery (TPOAM), Agricultural meteorological observation service stations (AMOSS), effective irrigated area (EIA), and total sown area of crops (TSAOC), with grain output as the dependent variable. Regional gross domestic product (GDP), Consumption expenditure per capita (CEPC) and Number of urban registered unemployed (NURU) are selected as indicators of social level. GDP reflects the socio-economic level, CEPC is an important indicator of people's life, and NURU can measure social stability to some extent. The indicators and definitions are shown in Table 1. Table 2 shows the descriptive statistics of the variables, from Table 2, the range of values of grain output is from 28.76 to 7867.72 with a mean value of 2100.57.

Table 1. Variables and definitions, source: authors own work
<table><tr><td rowspan=1 colspan=1>Variables</td><td rowspan=1 colspan=1>Units</td><td rowspan=1 colspan=1>Definition</td></tr><tr><td rowspan=1 colspan=1>Grain output</td><td rowspan=1 colspan=1>10000 tons</td><td rowspan=1 colspan=1>The total quantity of grain produced by an agricul-tural operator during the calendar year</td></tr><tr><td rowspan=1 colspan=1>CODE</td><td rowspan=1 colspan=1>10000 tons</td><td rowspan=1 colspan=1>Chemical oxygen demand emissions</td></tr><tr><td rowspan=1 colspan=1>TPOAM</td><td rowspan=1 colspan=1>10000 kilowatts</td><td rowspan=1 colspan=1>Total power of agricultural machinery</td></tr><tr><td rowspan=1 colspan=1>AMOSS</td><td rowspan=1 colspan=1>number</td><td rowspan=1 colspan=1>Agricultural meteorological observation servicestations</td></tr><tr><td rowspan=1 colspan=1>EIA</td><td rowspan=1 colspan=1>thousand hectares</td><td rowspan=1 colspan=1>Effective irrigation area</td></tr><tr><td rowspan=1 colspan=1>TSAOC</td><td rowspan=1 colspan=1>thousand hectares</td><td rowspan=1 colspan=1>Total sowing area of crops</td></tr><tr><td rowspan=1 colspan=1>GDP</td><td rowspan=1 colspan=1>100 million CNY</td><td rowspan=1 colspan=1>Regional gross domestic product</td></tr><tr><td rowspan=1 colspan=1>CEPC</td><td rowspan=1 colspan=1>CNY</td><td rowspan=1 colspan=1>Consumption expenditure per capita</td></tr><tr><td rowspan=1 colspan=1>NURU</td><td rowspan=1 colspan=1>ten thousand people</td><td rowspan=1 colspan=1>Number of urban registered unemployed</td></tr></table>

The United Nations Sustainable SDGs set the direction for global development, with Goal 2 committing to eradicating hunger by 2030. Ensure that all people, including the poor and vulnerable, have access to safe, nutritious and sufficient food all year round. In order to achieve this goal, an increase in grain output is particularly important. Grain output, as a key indicator of the level of agricultural production, directly reflects the core requirements of Goal 2 and is closely linked to Goals 3 (Health) and 12 (Sustainable consumption and production).

Table 2. Descriptive statistics of variables, source: authors own work
<table><tr><td rowspan=1 colspan=1>Variables</td><td rowspan=1 colspan=1>Min</td><td rowspan=1 colspan=1>Q1</td><td rowspan=1 colspan=1>Median</td><td rowspan=1 colspan=1>Mean</td><td rowspan=1 colspan=1>Q3</td><td rowspan=1 colspan=1>Max</td></tr><tr><td rowspan=1 colspan=1>Grain output</td><td rowspan=1 colspan=1>28.76</td><td rowspan=1 colspan=1>531.12</td><td rowspan=1 colspan=1>1422.76</td><td rowspan=1 colspan=1>2100.57</td><td rowspan=1 colspan=1>3366.48</td><td rowspan=1 colspan=1>7867.72</td></tr><tr><td rowspan=1 colspan=1>CODE</td><td rowspan=1 colspan=1>1.76</td><td rowspan=1 colspan=1>16.83</td><td rowspan=1 colspan=1>39.42</td><td rowspan=1 colspan=1>58.83</td><td rowspan=1 colspan=1>90.68</td><td rowspan=1 colspan=1>198.25</td></tr><tr><td rowspan=1 colspan=1>TPOAM</td><td rowspan=1 colspan=1>93.97</td><td rowspan=1 colspan=1>1266.87</td><td rowspan=1 colspan=1>2552.38</td><td rowspan=1 colspan=1>3352.49</td><td rowspan=1 colspan=1>4421.38</td><td rowspan=1 colspan=1>13353.02</td></tr><tr><td rowspan=1 colspan=1>AMOSS</td><td rowspan=1 colspan=1>1.00</td><td rowspan=1 colspan=1>14.00</td><td rowspan=1 colspan=1>23.50</td><td rowspan=1 colspan=1>22.73</td><td rowspan=1 colspan=1>29.25</td><td rowspan=1 colspan=1>47.00</td></tr><tr><td rowspan=1 colspan=1>EIA</td><td rowspan=1 colspan=1>109.24</td><td rowspan=1 colspan=1>698.15</td><td rowspan=1 colspan=1>1632.52</td><td rowspan=1 colspan=1>2148.36</td><td rowspan=1 colspan=1>3175.15</td><td rowspan=1 colspan=1>6534.69</td></tr><tr><td rowspan=1 colspan=1>TSAOC</td><td rowspan=1 colspan=1>88.55</td><td rowspan=1 colspan=1>1726.26</td><td rowspan=1 colspan=1>5188.25</td><td rowspan=1 colspan=1>5347.91</td><td rowspan=1 colspan=1>8091.38</td><td rowspan=1 colspan=1>15209.41</td></tr><tr><td rowspan=1 colspan=1>GDP</td><td rowspan=1 colspan=1>611.50</td><td rowspan=1 colspan=1>11230.32</td><td rowspan=1 colspan=1>20128.50</td><td rowspan=1 colspan=1>26344.85</td><td rowspan=1 colspan=1>34675.75</td><td rowspan=1 colspan=1>129513.60</td></tr><tr><td rowspan=1 colspan=1>CEPC</td><td rowspan=1 colspan=1>5063.00</td><td rowspan=1 colspan=1>12349.75</td><td rowspan=1 colspan=1>16344.50</td><td rowspan=1 colspan=1>17748.77</td><td rowspan=1 colspan=1>20616.50</td><td rowspan=1 colspan=1>48879.00</td></tr><tr><td rowspan=1 colspan=1>NURU</td><td rowspan=1 colspan=1>1.00</td><td rowspan=1 colspan=1>14.45</td><td rowspan=1 colspan=1>25.60</td><td rowspan=1 colspan=1>26.30</td><td rowspan=1 colspan=1>37.20</td><td rowspan=1 colspan=1>82.50</td></tr></table>

At the same time, agricultural technology, as a key factor driving grain production, occupies an important position in the SDG system. Table 3 provides a detailed compendium of the intrinsic linkages between the indicators studied in this paper and the United Nations SDGs. Specifically, as an important parameter for measuring water quality, CODE is not only directly related to Goal 3 (Health), which is to ensure people's drinking water safety and prevent water related diseases, but also a necessary condition for achieving Goal 6 (Water and Sanitation). The United Nations proposes to reduce pollution, improve water quality, and ensure clean water use and good health for humans by 2030. TPOAM is an important indicator reflecting the level of agricultural technological innovation, which is highly consistent with the United Nations SDG 9 (Industry, Innovation and Infrastructure). By improving the research and application level of agricultural machinery and equipment, it can promote the modernization and intelligence of agricultural production, improve agricultural production efficiency and quality. In addition, the construction and operation of AMOSS not only reflects agro-technological innovation, but is also closely linked to Goal 13 (Climate Action). Through timely and accurate monitoring and prediction of meteorological conditions, the operational agrometeorological observation station (AMOSS) contributes to increasing the adaptability and resilience of agricultural production to climate change, and reducing the impact of climate disasters on agricultural production. EIA not only reflects the level of agricultural water management, but is also an important means of realizing Goal 6 and Goal 12 (Sustainable Consumption and Production). Through scientific planning and rational use of water resources and improved irrigation efficiency, sustainability and stability of agricultural production can be ensured. TSAOC is of great significance to the realization of Goal 2 (Zero Hunger) and Goal 12 (Sustainable consumption and production). By expanding the area sown by crops and optimizing the planting structure, the supply of grain and other agricultural products can be increased to meet the growing demand for grain. At the same time, it will promote the formation of a green, low-carbon and circular agricultural production model.

At the social level, GDP, CEPC and NURU are all closely linked to Goal 8, reflecting the importance of sustainable socio-economic development. In addition, GDP, CEPC and NURU are important elements of Goal 12, Goal 11 and Goal 1, respectively.

In summary, the indicators selected in this paper are all based on the United Nations SDGs, and the relationship between agricultural technology and food production has been studied in depth. By strengthening agricultural technology innovation, it can make a positive contribution to the realization of the sustainable development goals and promote the sustainable development of global agriculture.

Table 3. Variables and United Nations SDGs, source: authors own work
<table><tr><td rowspan=1 colspan=1>Variables</td><td rowspan=1 colspan=1>United Nations Sustainable Development Goals</td></tr><tr><td rowspan=3 colspan=1>Grain output</td><td rowspan=1 colspan=1>Goal 2: Zero Hunger</td></tr><tr><td rowspan=1 colspan=1>Goal 3: Health</td></tr><tr><td rowspan=1 colspan=1>Goal 12: Sustainable consumption and production</td></tr><tr><td rowspan=2 colspan=1>CODE</td><td rowspan=1 colspan=1>Goal 3: Health</td></tr><tr><td rowspan=1 colspan=1>Goal 6: Water and sanitation</td></tr><tr><td rowspan=1 colspan=1>TPOAM</td><td rowspan=1 colspan=1>Goal 9: Infrastructure, industrialization</td></tr><tr><td rowspan=2 colspan=1>AMOSS</td><td rowspan=1 colspan=1>Goal 9: Infrastructure, industrialization</td></tr><tr><td rowspan=1 colspan=1>Goal 13: Climate Action</td></tr><tr><td rowspan=2 colspan=1>EIA</td><td rowspan=1 colspan=1>Goal 6: Water and sanitation</td></tr><tr><td rowspan=1 colspan=1>Goal 9: Infrastructure, industrialization</td></tr><tr><td rowspan=2 colspan=1>TSAOC</td><td rowspan=1 colspan=1>Goal 2: Zero Hunger</td></tr><tr><td rowspan=1 colspan=1>Goal 12: Sustainable consumption and production</td></tr><tr><td rowspan=2 colspan=1>GDP</td><td rowspan=1 colspan=1>Goal 8: Economic growth</td></tr><tr><td rowspan=1 colspan=1>Goal 12: Sustainable consumption and production</td></tr><tr><td rowspan=2 colspan=1>CEPC</td><td rowspan=1 colspan=1>Goal 8: Economic growth</td></tr><tr><td rowspan=1 colspan=1>Goal 11: Cities</td></tr><tr><td rowspan=2 colspan=1>NURU</td><td rowspan=1 colspan=1>Goal 1: End poverty in all its forms everywhere</td></tr><tr><td rowspan=1 colspan=1>Goal 8: Economic growth</td></tr></table>

## 4. Results

## 4.1. The spatiotemporal distribution of grain production

## 4.1.1. Time series changes in grain output

Collect grain output data from China Statistical Yearbook from 2011 to 2022, and calculate the chain growth rate of Grain output based on 2011. Figure 1 shows the time evolution of grain output and its growth rate. As shown in Figure 1, grain output shows an overall growth trend. The time evolution of grain output can be mainly divided into three stages: 2011-2015, 2015-2018, 2018-2022. In the first stage, grain output showed an upward trend, while in the second stage, the change was gentle and slightly reduced. In the third stage, the trend was consistent with the first stage, and it reached its highest point during the inspection period in 2022 (68652.77), but the growth rate was lower than in the first stage.

Combined with the trend in the growth rate of grain output, it can be seen that there are fluctuations in the change of grain output. The growth rate from 2012 (4.03) to 2022 (0.54) shows a general downward trend and is negative at 2018, the lowest point in the period under examination (-0.56).

The investigation period of this article includes the global COVID-19 pandemic, and the period from 2020 to 2022 is the epidemic time of COVID-19. As shown in Figure 1, in the 2020-2022, although grain production is still increasing, the growth rate shows a pattern of first fast and then slow. The growth rate in 2022 is lower than that in 2019, and COVID-19 may lead to changes in the growth rate of grain output to some extent. In order to explore whether there is significant difference in grain yield before and after the COVID-19 epidemic, the grain yield in different periods was statistically tested. Divide the data into two groups: 2011-2020, 2020-2022, and conduct Mann Whitney U test, assuming that there is no significant difference in grain yield between the two stages. According to the calculation, the P value is 0.0091 (less than 0.05), so there is a significant difference in grain yield before and after COVID-19 (the significance level is 0.05). One possible reason is that changes in grain production are caused by social factors or agricultural production conditions. On the one hand, the COVID-19 epidemic has led to constraints on socio-economic activities globally, including limited labor mobility, disruptions in supply chains, and changes in market demand. All of these factors may have had direct or indirect impacts on agricultural production, leading to changes in food production. On the other hand, social factors may also play an important role in changes in food production. The epidemic has had a profound impact on people's lifestyles and consumption habits, which may lead to changes in the demand for food. At the same time, epidemics may also lead to an increase in the cost of agricultural production, which may affect the availability and price of grain. In summary, the significant difference in grain production before and after the COVID-19 epidemic may be the result of a combination of factors. Therefore, further exploration is needed on the impact of agricultural technology and society on sustainable grain development.

![](images/1d84d69b0bb584ab9f4d3975ac3333c7d1b7b57faa4073ae6daa7800d65608dd.jpg)  
Figure 1. Time-Series evolution of grain output and growth rate from 2011 to 2022, source: authors own work

## 4.1.2. Spatial distribution of grain output

China is a vast country with spatial heterogeneity in grain production, and Figure 2 shows the top 16 provinces in terms of total grain production in 2011-2022. As shown in Figure 2, the region with the highest grain production in China is Heilongjiang Province (87893.78), followed by Henan Province (76785.79) and Shandong Province (62466.44). The gap is smaller in Anhui Province (46555.17), Jilin Province (45958.03), Hebei Province (44082.02) and Jiangsu Province (43111.23).

From a geographical perspective, most of the regions with higher grain production in China are in the northern region, which is far ahead in grain production due to its unique geographical location. One possible reason is that the northern region, especially the Northeast Plain and North China Plain, has vast cultivated land resources, flat terrain, fertile soil, and is suitable for large-scale mechanized farming, which provides unique natural conditions for high and stable grain production. In contrast, the southern region is rich in water resources. But the terrain is complex, with more mountains and hills, and relatively limited arable land resources, which is not conducive to large-scale production of grain. In addition, the climatic conditions in the northern regions are also conducive to grain production. The temperate monsoon climate of the northeastern plains and the warm-temperate monsoon climate of the north China plains have made these areas characterized by four distinct seasons, simultaneous rainfall and heat, and abundant light, which is conducive to the growth of food crops. The southern region, on the other hand, has good heat conditions, but the seasonal distribution of precipitation is uneven, and floods and droughts are frequent, posing a threat to grain production.

![](images/0453ab9e74cce93043e576bd165f3b8c7c241ea51133ccdd5aecf0b2f14f1c19.jpg)  
Total grain output (10000 tons)  
Figure 2. Top 16 provinces in total grain production from 2011 to 2022, source: authors own work

## 4.2. GAM Evaluation

## 4.2.1. Correlation analysis

In order to explore the potential causal relationship between agricultural technology, social level, and grain production in depth, this article conducted a correlation analysis on the variables. Figure 3 demonstrates the heat map of correlation coefficients between variables, where the color shades intuitively reflect the strength of the correlation between the variables, red represents positive correlation, blue represents negative correlation. The results of the analysis showed with the exception of CEPC, all variables showed positive correlations with grain out. The strength of correlation between agricultural technology variables and grain output was, in order, TSAOC (0.95), EIA (0.89), TPOAM (0.84), AMOSS (0.62), NURU (0.59), CODE (0.50), GDP (0.27), and CEPC (-0.22).

However, it should be noted that the correlation coefficient, although it can reflect the degree of linear correlation between variables. However, its limitation is that it cannot reveal the causal relationship between the variables and the non-linear character of the relationship. Therefore, in order to explore more deeply the impact of agricultural technology on grain production and the nature of its relationship, this paper further employs regression analysis and specifically chooses GAM as the analytical tool. GAM can not only determine the causal relationship between variables, but also overcome the limitations of linear models. It can comprehensively reveal the possible nonlinear relationships between variables, providing more scientific and effective decision-making basis for the optimization of agricultural technology and the improvement of grain yield.

## 4.2.2. GAM results

Table 4 presents the GAM results. According to the p-value, all variable functions passed the significance test, confirming that all the agricultural technology indicators selected in this paper have a significant effect on grain output. The EDF value is an important measure of the contribution of a variable to the model. In addition, if the EDF value of a smoothing term is greater than 1 and significant, it usually indicates that the relationship between the variable and the response variable is nonlinear. As shown in Table 4, all smoothing terms have EDF values greater than 1. The order of magnitude of the variables' contribution to the model is: EIA (8.92), AMOSS (8.53), TSAOC (8.2), NURU (7.96), TPOAM (7.87), CODE (7.65), GDP (7.15) and CEPC (2.67).

![](images/21d8dee32e1dd4e64a2e393d33a237320a3e2f7da3b4f348dd03a4996ece4605.jpg)  
Figure 3. Heat map of variable correlation, source: authors own work

Table 4 GAM results, source: authors own work
<table><tr><td rowspan=1 colspan=1>Variables</td><td rowspan=1 colspan=1>EDF</td><td rowspan=1 colspan=1>F</td><td rowspan=1 colspan=1>p-value</td></tr><tr><td rowspan=1 colspan=1>S(CODE)</td><td rowspan=1 colspan=1>7.65</td><td rowspan=1 colspan=1>1.92</td><td rowspan=1 colspan=1>0.083528</td></tr><tr><td rowspan=1 colspan=1>S(TPOAM)</td><td rowspan=1 colspan=1>7.87</td><td rowspan=1 colspan=1>3.93</td><td rowspan=1 colspan=1>0.000141</td></tr><tr><td rowspan=1 colspan=1>S(AMOSS)</td><td rowspan=1 colspan=1>8.53</td><td rowspan=1 colspan=1>10.64</td><td rowspan=1 colspan=1>&lt;0.0001</td></tr><tr><td rowspan=1 colspan=1>S(EIA)</td><td rowspan=1 colspan=1>8.92</td><td rowspan=1 colspan=1>17.98</td><td rowspan=1 colspan=1>&lt;0.0001</td></tr><tr><td rowspan=1 colspan=1>S(TSAOC)</td><td rowspan=1 colspan=1>8.20</td><td rowspan=1 colspan=1>25.62</td><td rowspan=1 colspan=1>&lt;0.0001</td></tr><tr><td rowspan=1 colspan=1>S(GDP)</td><td rowspan=1 colspan=1>7.15</td><td rowspan=1 colspan=1>12.44</td><td rowspan=1 colspan=1>&lt;0.0001</td></tr><tr><td rowspan=1 colspan=1>S(CEPC)</td><td rowspan=1 colspan=1>2.67</td><td rowspan=1 colspan=1>15.08</td><td rowspan=1 colspan=1>&lt;0.0001</td></tr><tr><td rowspan=1 colspan=1>S(NURU)</td><td rowspan=1 colspan=1>7.96</td><td rowspan=1 colspan=1>7.73</td><td rowspan=1 colspan=1>&lt;0.0001</td></tr></table>

The GAM-adjusted R-sq value fitted in this paper is 0.97, indicating a model explanation rate of 97%. Figure 4 shows the fitting effect of the GAM. As shown in Figure 4, the fitted values and the actual observed values overlap well and most of them fit closely. Therefore, the nonlinear regression model fitted in this paper is effective.

## 4.3. The impact of agricultural technology on grain production

## 4.3.1. The impact of AMOSS on grain output

As shown in Figure 5(a), the impact of AMOSS on grain output shows significant fluctuations. Specifically, when the value of AMOSS is below 20, the impact effect is relatively weak. When the value of AMOSS falls within the range of 20 to 25, its positive impact on grain output begins to manifest. It is particularly noteworthy that when the value of AMOSS reaches 25, its positive effect on grain output reaches its peak.

As an important carrier of agrometeorological observation technology, AMOSS plays a crucial role in optimizing agricultural production. As shown in Figure 5(a), the positive impact effect of AMOSS on grain production is maximized when the number of operational agrometeorological observation stations is set at 20 to 25. This finding reveals the optimal proportionality between AMOSS inputs and grain production. Therefore, in future agricultural production practices, full attention should be paid to the inputs of AMOSS and other agro-meteorological observation technologies in order to achieve the sustainable development of grain production and to promote the deepening of the process of agricultural modernization.

![](images/f491bf45edfcaca5a65311174055977f4d399650282eed45d0e594b4fff7a0c0.jpg)  
Figure 4. The fitting effect of GAM, source: authors own work

![](images/1231ebc692e1aa97c445b1f53cc917b2d53bf5269bcecfe1bb891caa5ad3a200.jpg)  
Figure 5(a). The influence of AMOSS on grain output, source: authors own work

## 4.3.2. The impact of CODE on grain output

As shown in Figure 5(b), the impact of CODE on grain production is mainly divided into two intervals: 0-130,130- 200. Specifically, in the first interval, the effect is relatively weak. However, when the CODE value exceeds 130, its inhibitory effect on grain production begins to increase significantly, showing a clear negative effect.

CODE is an important indicator of water quality, and the change of its value reflects the degree of water pollution. Considering the important role of water resources in agricultural production, combating water pollution is of great significance in ensuring the stability and sustainability of grain production. Therefore, when the CODE value

reaches or exceeds 130, a high degree of alertness should be aroused and more efforts should be made to combat water pollution in order to prevent its possible serious adverse effects on grain production.

![](images/912291957e8a8961d3224fc007808beae1e2ce36e42da40893c6eedd5476199f.jpg)  
Figure 5(b). The influence of CODE on grain output, source: authors own work

## 4.3.3. The impact of EIA on grain output

As shown in Figure 5(c), the impact of EIA on grain production is generally categorized into three intervals: 0- 1500, 1500-1800, and 1800-6000.The impact effect is not obvious when EIA takes values in the first interval. It is worth noting that in the third interval, the positive impact effect of EIA on grain production gradually comes to the fore.

![](images/ce30cd668ee137fe68d19d907b5ddef2d36801a63a8d946a3ab973e4646046e1.jpg)  
Figure 5(c). The influence of EIA on grain output, source: authors own work

As an important embodiment of irrigation technology in agricultural production, the size of EIA is directly related to the improvement of agricultural production conditions and grain yield. As shown in Figure 5(c), when the effective irrigated area is greater than 1800, it can effectively increase grain yield. Therefore, in order to further improve the efficiency and quality of grain production, it is necessary to continue to increase the research and promotion of irrigation technology, increase the effective irrigation area, and provide strong technical support for the sustainable development of grain production.

## 4.3.4. The impact of TPOAM on grain output

As shown in Figure 5(d), the impact effect of TPOAM on grain production exhibits significant volatility characteristics, which is manifested in multiple wave changes. Observing the data distribution of TPOAM, it is mainly concentrated in the interval of 1000 to 6000. It is particularly noteworthy that the effect on grain production peaks when the value of TPOAM is close to 3000.

The total power of agricultural machinery not only affects the efficiency of grain production, but is also one of the key indicators of the modernization of agricultural production. When considering the balance of resource allocation and impact effect, controlling TPOAM in the range of 3000 to 4000 can maximize its impact effect on grain production, while avoiding excessive consumption and waste of resources.

![](images/1fb4492447476381f09a9f0580765cc2aa380e5bbfef8e1612d562c4f37618b3.jpg)  
Figure 5 (d) The influence of TPOAM on grain output, source: authors own work

## 4.3.5. The impact of TSAOC on grain output

As shown in Figure 5(e), the effect of TSAOC on grain production is categorized into three main intervals: 0-4000. 4000-7500, and 7500-15000.It is noteworthy that in the second interval the effect of TSAOC on grain production appears to be weak.

In the process of expanding the sown area of crops to enhance grain production, not all intervals of the area increase have significant impact effects. Despite the increase in sown area, it may be constrained by other factors such as soil quality, water distribution, climatic conditions, etc., resulting in insignificant boosting effect on grain production. However, from Figure 5(c), it can be seen that sown area greater than 7500 will effectively promote grain production.

## 4.3.6. The impact of GDP on grain output

As shown in Figure 5(f), the values of GDP are mainly concentrated in the range of 0-60000.The effect of GDP on grain out is mainly divided into two stages: 0-20000 and 20000-120000. In the first stage, GDP has a positive effect on grain out, and the effect of GDP on grain out reaches its maximum value at around 10000 reaches the maximum value.

GDP is a core indicator of social economy, and generally speaking, social economic development can effectively promote food production. However, not every stage of economic development can promote grain production. One possible reason is that GDP measures the level of economic development of all sectors combined, and the better the economic development of non-agricultural sectors, perhaps leading to a reduction in the number of people employed in agricultural production. Therefore, it is important to balance economic development with sustainable agricultural production.

![](images/f42ef0fdcf79338b33f1a07cfbda5fc69c9844f9213834beca34433723743a7b.jpg)  
Figure 5(e). The influence of TSAOC on grain output, source: authors own work

![](images/1c7531c413716c02b64595b59dcfcadba11d38a3633f6d42dbceb91fc93fdc0c.jpg)  
Figure 5(f). The influence of GDP on grain output, source: authors own work

## 4.3.7. The impact of CEPC on grain output

As shown in Figure 5(g), the distribution of CEPC is mainly concentrated in 7500-25000. the effect of CEPC on grain out is mainly divided into two stages: 0-17000 and 17000-50000, in the second stage, CEPC shows obvious positive effect on grain out.

CEPC is the main indicator of people's life, and when the threshold is reached, it presents a positive effect on grain out. With the improvement of living standards, people begin to pursue a higher quality of life and more diversified food consumption while satisfying the basic needs of life. The production of grain, as a basic necessity of life, increases accordingly. In addition, people's emphasis on healthy diets and higher requirements for food quality and safety may lead to an increase in the consumption of grain at higher consumption levels, thus driving the growth of grain out.

![](images/e0fb744373479da286308fdc4b1e8e96c1b4b80ab50b408454caff7a6ebdadf4.jpg)  
Figure 5(g). The influence of CEPC on grain output, source: authors own work

![](images/715f2029493c19fac8120fc0793ca007d630cc8ccbd86ea735a4243cad6a67dc.jpg)  
Figure 5(h). The influence of NURU on grain output, source: authors own work

## 4.3.8. The impact of NURU on grain output

As revealed in Figure 5(h), there is a clear threshold for the effect of NURU on grain out, with a significant positive effect on grain out when NURU is greater than 30. When NURU is between 20 and 30, its effect on grain out is relatively weak. This implies that when urban unemployment exceeds a certain level, this unemployment situation may have prompted some people to turn to agricultural production, thus increasing grain out.

As an important indicator of urban unemployment, changes in NURU not only reflect the stability of employment in society, but may also indirectly affect the source of labor for agricultural production. Typically, agricultural production workers are mainly sourced from rural workers, and the urban unemployed are often in opposition to this group in terms of their employment choices. Thus, one explanation is that the urban unemployed may turn to agricultural production due to employment pressures, which may have a positive impact on grain production. However, this effect is not unconditional. There needs to be a balance between agricultural production and urban development to achieve synergistic development. Therefore, when formulating relevant policies, the balance between urban unemployment, agricultural production demand and urban-rural development needs to be taken into account in order to achieve economic sustainability and social harmony and stability.

## 5. Conclusions

This study applies data from 31 provinces in China (excluding Hong Kong, Macau and Taiwan) from 2011 to 2022 to analyze the impact of agricultural technology and social factors on grain production. The main conclusions are as follows. First, China's grain output has shown an overall trend of growth, but the growth rate has fluctuated significantly and declined. Moreover, there was a significant difference in grain production before and after the COVID-19 epidemic. From a spatial perspective, the northern region is leading in terms of output, while the southern region has a relatively low output. Second, through correlation analysis, except for CEPC, all other variables showed a positive correlation with grain out, and the correlation order is: EIA, AMOSS, TSAOC, NURU, TPOAM, CODE, GDP and CEPC. Third, the effects of agricultural technology and social factors on grain production are all significantly nonlinear, with varying effects on grain production in different intervals. Specifically, AMOSS has a significant positive effect on grain production in the range of 20 to 25 number of sites. CODE significantly suppresses grain production when the value exceeds 130. EIA has a positive effect on grain production when the effective irrigated area is greater than 1800. TPOAM peaks at a value close to 3000. TSAOC will effectively contribute to grain production when the sown area is greater than 7500. GDP peaks at around 10000 for the impact effect on grain out. CEPC greater than 17000 had a significant positive effect on grain out. There is a significant positive effect on grain out when NURU is greater than 30.

Based on this, the following practical recommendations are made. First, in view of the fluctuating growth rate and declining trend, it is recommended that an early warning mechanism for grain production be established to monitor and analyze changes in production in a timely manner, so as to provide a scientific basis for policy adjustments. Secondly, in response to the leading grain production in the northern region and the relatively low production in the southern region, local conditions should be adapted to give full play to the advantages of each region's agricultural resources. Northern regions can continue to strengthen the protection of arable land and the construction of water conservancy facilities to enhance grain production capacity. The southern region, on the other hand, can improve land utilization and economic efficiency by adjusting its planting structure and developing specialty agriculture. Finally, to address the non-linear impact of agricultural technical and social factor on grain production, it is recommended that refined agricultural management policies be formulated. Differentiated measures should be taken to address the impact zones of different technical indicators. For example, optimizing technical inputs for agro-meteorological observation, strengthening water quality management and monitoring, and increasing the effective irrigated area and the total power of agricultural machinery in order to achieve sustainable development of grain production. In addition, it is important to balance the relationship between sustainable social and agricultural development, particularly in terms of socio-economic, people's living standards and social stability.

## References

1. BI X., WEN B., ZOU W., 2022, The Role of Internet Development in China's Grain Production: Specific Path and Dialectical Perspective, Agriculture, 12(3): 377.

2. CHAI J., WANG Z., YANG J., ZHANG L., 2019, Analysis for spatial-temporal changes of grain production and farmland resource: Evidence from Hubei Province, central China, Journal of Cleaner Production, 207: 474–482.

3. CHEN X., SHUAI C., WU Y., 2023, Global food stability and its socio-economic determinants towards sustainable development goal 2 (Zero Hunger), Sustainable Development, 31(3): 1768–1780.

4. CHENG J., YIN S., 2022, Quantitative Assessment of Climate Change Impact and Anthropogenic Influence on Crop Production and Food Security in Shandong, Eastern China, Atmosphere, 13(8): 1160.

5. DÍAZ MARTÍNEZ Z., FERNÁNDEZ MENÉNDEZ J., GARCÍA VILLALBA L. J., 2023, Tariff Analysis in Automobile Insurance: Is It Time to Switch from Generalized Linear Models to Generalized Additive Models?, Mathematics, 11(18): 3906.

6. FANG W., HUANG H., YANG B., HU Q., 2021, Factors on Spatial Heterogeneity of the Grain Production Capacity in the Major Grain Sales Area in Southeast China: Evidence from 530 Counties in Guangdong Province, Land, 10(2): 206.

7. FU Y., ZHU Y., 2023, Internet use and technical efficiency of grain production in China: A bias-corrected stochastic frontier model, Humanities and Social Sciences Communications, 10(1): 643.

8. GE D., KANG X., LIANG X., XIE F., 2023, The Impact of Rural Households' Part-Time Farming on Grain Output: Promotion or Inhibition? Agriculture, 13(3): 671.

9. HUANG H., HOU M., YAO S., 2022, Urbanization and Grain Production Pattern of China: Dynamic Effect and Mediating Mechanism, Agriculture, 12(4): 539.

10. LI X., ZHANG Y., MA N., ZHANG X., TIAN J., ZHANG L., MCVICAR T. R., WANG E., XU J, 2023, Increased Grain Crop Production Intensifies the Water Crisis in Northern China, Earth 's Future, 11(9): e2023EF003608

11. LI Z., LI J, 2022, The influence mechanism and spatial effect of carbon emission intensity in the agricultural sustainable supply: Evidence from china's grain production, Environmental Science and Pollution Research, 29(29): 44442–44460.

12. LI Ż., WANG W., JI X., WU P., ZHUO L., 2023, Machine learning modeling of water footprint in crop production distinguishing water supply and irrigation method scenarios, Journal of Hydrology, 625: 130171.

13. LIU X., XU Y., ENGEL B. A., SUN S., ZHAO X., WU P., WANG Y., 2021, The impact of urbanization and aging on food security in developing countries: The view from Northwest China, Journal of Cleaner Production, 292: 126067.

14. LU S., BAI X., LI W., WANG N., 2019, Impacts of climate change on water resources and grain production, Technological Forecasting and Social Change, 143: 76–84.

15. ONWUCHEKWA-HENRY C. B., OGTROP F. V., ROCHE R., TAN D. K. Y., 2022, Model for Predicting Rice Yield from Reflectance Index and Weather Variables in Lowland Rice Fields, Agriculture, 12(2): 130.

16. QIU T., BORIS CHOY S. T., LI S., HE Q., LUO B., 2020, Does land renting-in reduce grain production? Evidence from rural China, Land Use Policy, 90: 104311.

17. RAVINDRA K., RATTAN P., MOR S., AGGARWAL A. N., 2019, Generalized additive models: Building evidence of air pollution, climate change and human health, Environment International, 132: 104987.

18. SHEN X., ZHANG D., NAN Y., QUAN Y., YANG F., YAO, Y., 2023, Impact of urban expansion on grain production in the Japan Sea Rim region, Frontiers in Earth Science, 10: 1025069.

19. WANG J., ZHANG Z., LIU Y., 2018, Spatial shifts in grain production increases in China and implications for food security, Land Use Policy, 74 204–213.

20. WU Z., DANG J., PANG Y., XU W., 2021, Threshold effect or spatial spillover? The impact of agricultural mechanization on grain production, Journal of Applied Economics, 24(1): 478–503.

21. XU H., YANG R., SONG J., 2023, Water rights reform and water-saving irrigation: Evidence from China, Water Science & Technology, 88(11): 2779-2792.

22. YANG Q., ZHENG J., ZHU H., 2020, Influence of spatiotemporal change of temperature and rainfall on major grain yields in southern Jiangsu Province, China, Global Ecology and Conservation, 21: e00818.

23. YANG W., LI B., 2020, Prediction of grain supply and demand structural balance in China based on grey models, Grey Systems: Theory and Application, 11(2): 253–264.

24. YIN D., LI F., LU Y., ZENG X., LIN Z., ZHOU Y., 2024, Assessment of Crop Yield in China Simulated by Thirteen Global Gridded Crop Models, Advances in Atmospheric Sciences, 41(3): 420–434.

25. YUE Q., WU H., WANG Y., GUO P, 2021, Achieving sustainable development goals in agricultural energy-water-food nexus system: An integrated inexact multi-objective optimization approach, Resources, Conservation and Recycling, 174: 105833.

26. ZHANG S., LI B., YANG Y., ZHANG Y., 2022, Analysis on Scientific and Technological Innovation of Grain Production in Henan Province Based on SD-GM Approach, Discrete Dynamics in Nature and Society: 4165586.

27. ZHENG Y., FAN Q., JIA W., 2022, How Much Did Internet Use Promote Grain Production? – Evidence from a Survey of 1242 Farmers in 13 Provinces in China, Foods, 11(10): 1389.