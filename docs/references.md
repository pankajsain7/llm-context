# References

Compiled 2026-10-19 and **updated in the Phase 2 review** (JIT-LSM, JIT-Defect-Extended, Yeo2026, Shahini2025, Ding2024) and **after the external audit** (Deng2026, Song2026; Yeo2026 read in full). Every entry was checked against at least one primary bibliographic source. The **Level** column shows how deeply each source was checked. Before you cite a specific claim from a source marked MD or SEC, read the full text.

| Level | Meaning |
|---|---|
| FT | Full text (arXiv HTML) read for this review |
| AB | Abstract read (arXiv API or publisher page) |
| MD | Title, year, and DOI/arXiv ID verified through the OpenAlex or arXiv API. The content summary comes from background knowledge |
| SEC | Bibliographic data taken from the reference list of a paper read in full text (ApacheJIT, ReDef) or from a Crossref reference list (Huang2026). The DOI was not resolved independently |
| RP | Replication package or dataset record inspected (GitHub, Git LFS data, Zenodo, figshare API) |

Author lists are shortened to "et al." unless the authors appeared in a verified source.

## Just-in-time defect prediction: foundations and evaluation

| Key | Reference | Level |
|---|---|---|
| Mockus2000 | Mockus, A., Weiss, D. M. *Predicting risk of software changes.* Bell Labs Technical Journal. DOI: [10.1002/bltj.2229](https://doi.org/10.1002/bltj.2229). OpenAlex lists the year as 2002, but the paper is usually cited as 2000 | MD |
| Kim2008 | Kim, S., Whitehead, E. J., Zhang, Y. *Classifying Software Changes: Clean or Buggy?* IEEE TSE 34(2), 2008. DOI: [10.1109/TSE.2007.70773](https://doi.org/10.1109/TSE.2007.70773) | MD + SEC |
| Kamei2013 | Kamei, Y., Shihab, E., Adams, B., Hassan, A. E., Mockus, A., Sinha, A., Ubayashi, N. *A large-scale empirical study of just-in-time quality assurance.* IEEE TSE 39(6):757–773, 2013. DOI: [10.1109/TSE.2012.70](https://doi.org/10.1109/TSE.2012.70) | MD + SEC |
| McIntosh2018 | McIntosh, S., Kamei, Y. *Are Fix-Inducing Changes a Moving Target? A Longitudinal Case Study of Just-In-Time Defect Prediction.* IEEE TSE 44(5):412–428, 2018. DOI: [10.1109/TSE.2017.2693980](https://doi.org/10.1109/TSE.2017.2693980) | MD + SEC |
| Tan2015 | Tan, M., Tan, L., Dara, S., Mayeux, C. *Online Defect Prediction for Imbalanced Data.* ICSE 2015 (SEIP). DOI: [10.1109/ICSE.2015.139](https://doi.org/10.1109/ICSE.2015.139) | SEC |
| Yang2016 | Yang, Y., Zhou, Y., Liu, J., et al. *Effort-Aware Just-in-Time Defect Prediction: Simple Unsupervised Models Could Be Better than Supervised Models.* FSE 2016. DOI: [10.1145/2950290.2950353](https://doi.org/10.1145/2950290.2950353) | SEC |
| Cabral2019 | Cabral, G. G., et al. *Class Imbalance Evolution and Verification Latency in Just-in-Time Software Defect Prediction.* ICSE 2019. DOI: [10.1109/ICSE.2019.00076](https://doi.org/10.1109/ICSE.2019.00076) | MD |
| Cabral2023 | Cabral, G. G., Minku, L. L., Oliveira, A. L. I., Pessoa, D. A., Tabassum, S. *An investigation of online and offline learning models for online Just-in-Time Software Defect Prediction.* EMSE, 2023. DOI: [10.1007/s10664-023-10335-6](https://doi.org/10.1007/s10664-023-10335-6) | MD |
| Gesi2021 | Gesi, J., Li, J., Ahmed, I. *An Empirical Examination of the Impact of Bias on Just-in-Time Defect Prediction.* ESEM 2021. DOI: [10.1145/3475716.3475791](https://doi.org/10.1145/3475716.3475791) | MD + SEC |
| Shahini2024 | Shahini, X., Metzger, A., Pohl, K. *An Empirical Study on Just-in-time Conformal Defect Prediction.* MSR 2024. DOI: [10.1145/3643991.3644928](https://doi.org/10.1145/3643991.3644928) | MD |
| Shahini2025 | Shahini, X., Bartel, J., Pohl, K. *On the calibration of Just-in-time Defect Prediction.* MSR 2025. DOI: [10.1109/MSR66628.2025.00018](https://doi.org/10.1109/MSR66628.2025.00018); arXiv:[2504.12051](https://arxiv.org/abs/2504.12051) | AB |

## Defect labels, SZZ, and label noise

| Key | Reference | Level |
|---|---|---|
| Sliwerski2005 | Śliwerski, J., Zimmermann, T., Zeller, A. *When do changes induce fixes?* MSR 2005. DOI: [10.1145/1083142.1083147](https://doi.org/10.1145/1083142.1083147) | MD + SEC |
| daCosta2017 | da Costa, D. A., McIntosh, S., Shang, W., Kulesza, U., Coelho, R., Hassan, A. E. *A Framework for Evaluating the Results of the SZZ Approach for Identifying Bug-Introducing Changes.* IEEE TSE 43(7):641–657, 2017. DOI: [10.1109/TSE.2016.2616306](https://doi.org/10.1109/TSE.2016.2616306) | SEC |
| Neto2018 | Neto, E. C., da Costa, D. A., Kulesza, U. *The impact of refactoring changes on the SZZ algorithm: An empirical study.* SANER 2018. DOI: [10.1109/SANER.2018.8330225](https://doi.org/10.1109/SANER.2018.8330225) | SEC |
| RodriguezPerez2020 | Rodríguez-Pérez, G., Nagappan, M., Robles, G. *Watch out for Extrinsic Bugs! A Case Study of their Impact in Just-In-Time Bug Prediction Models on the OpenStack project.* IEEE TSE, 2020. DOI: [10.1109/TSE.2020.3021380](https://doi.org/10.1109/TSE.2020.3021380) | SEC |
| Rosa2021 | Rosa, G., et al. *Evaluating SZZ Implementations Through a Developer-Informed Oracle.* ICSE 2021. DOI: [10.1109/ICSE43902.2021.00049](https://doi.org/10.1109/ICSE43902.2021.00049) | MD |
| Fan2021 | Fan, Y., Xia, X., da Costa, D. A., Lo, D., Hassan, A. E., Li, S. *The Impact of Mislabeled Changes by SZZ on Just-in-Time Defect Prediction.* IEEE TSE 47(8):1559–1586, 2021. DOI: [10.1109/TSE.2019.2929761](https://doi.org/10.1109/TSE.2019.2929761) | MD + SEC |
| Herbold2022a | Herbold, S., Trautsch, A., Trautsch, F., Ledel, B. *Problems with SZZ and features: An empirical study of the state of practice of defect prediction data collection.* EMSE 27(2):42, 2022. DOI: [10.1007/s10664-021-10092-4](https://doi.org/10.1007/s10664-021-10092-4) | MD + SEC |
| Herbold2022b | Herbold, S., et al. *A fine-grained data set and analysis of tangling in bug fixing commits* (the source of LLTC4J). EMSE, 2022. DOI: [10.1007/s10664-021-10083-5](https://doi.org/10.1007/s10664-021-10083-5) | MD |
| Guo2024 | Guo, S., et al. *Estimating Uncertainty in Labeled Changes by SZZ Tools on Just-In-Time Defect Prediction.* ACM TOSEM. DOI: [10.1145/3637226](https://doi.org/10.1145/3637226) | MD |
| Lyu2024 | Lyu, Y., Kang, H. J., Widyasari, R., Lawall, J., Lo, D. *Evaluating SZZ Implementations: An Empirical Study on the Linux Kernel.* IEEE TSE 50(9):2219–2239, 2024. DOI: [10.1109/TSE.2024.3406718](https://doi.org/10.1109/TSE.2024.3406718) | MD + SEC |
| Tang2025 | Tang, L., Liu, J., Liu, Z., Yang, X., Bao, L. *LLM4SZZ: Enhancing SZZ Algorithm with Context-Enhanced Assessment on Large Language Models.* arXiv:[2504.01404](https://arxiv.org/abs/2504.01404), 2025 | AB |
| Shi2026 | Shi, Y., Li, H., Adams, B., Hassan, A. E. *AgenticSZZ: Temporal Knowledge Graph-Guided Agentic Bug-Inducing Commit Identification.* arXiv:[2602.02934](https://arxiv.org/abs/2602.02934), 2026 | AB |
| Lyu2026 | Lyu, Y., et al. *AgentSZZ: Teaching the LLM Agent to Play Detective with Bug-Inducing Commits.* arXiv:[2604.02665](https://arxiv.org/abs/2604.02665), 2026 | AB |
| Bludau2026 | Bludau, P., Pretschner, A. *Quantifying SZZ-Induced Evaluation Bias in Just-in-Time Defect Prediction.* Research Square preprint (not peer reviewed), 2026. DOI: [10.21203/rs.3.rs-9846265/v1](https://doi.org/10.21203/rs.3.rs-9846265/v1) | MD |

## Learned and semantic JIT-DP models

| Key | Reference | Level |
|---|---|---|
| Hoang2019 | Hoang, T., Dam, H. K., Kamei, Y., Lo, D., Ubayashi, N. *DeepJIT: An End-to-End Deep Learning Framework for Just-in-Time Defect Prediction.* MSR 2019. DOI: [10.1109/MSR.2019.00016](https://doi.org/10.1109/MSR.2019.00016) | MD + SEC |
| Hoang2020 | Hoang, T., Kang, H. J., Lo, D., Lawall, J. *CC2Vec: Distributed Representations of Code Changes.* ICSE 2020. arXiv DOI: [10.48550/arXiv.2003.05620](https://doi.org/10.48550/arXiv.2003.05620) | MD + SEC |
| Zeng2021 | Zeng, Z., et al. *Deep just-in-time defect prediction: how far are we?* ISSTA 2021. DOI: [10.1145/3460319.3464819](https://doi.org/10.1145/3460319.3464819) | MD |
| Pornprasit2021 | Pornprasit, C., Tantithamthavorn, C. *JITLine: A Simpler, Better, Faster, Finer-grained Just-In-Time Defect Prediction.* MSR 2021. DOI: [10.1109/MSR52588.2021.00049](https://doi.org/10.1109/MSR52588.2021.00049) | MD |
| Ni2022 | Ni, C., Wang, W., Yang, K., Xia, X., Liu, K., Lo, D. *The best of both worlds: integrating semantic features with expert features for defect prediction and localization* (JIT-Fine; introduces JIT-Defect4J). ESEC/FSE 2022. DOI: [10.1145/3540250.3549165](https://doi.org/10.1145/3540250.3549165). Replication package: <https://github.com/jacknichao/JIT-Fine> (`data.zip` with labels committed 2022-08-30) | MD + RP |
| Guo2023 | Guo, Y., Gao, X., Zhang, Z., Chan, W. K., Jiang, B. *A study on the impact of pre-trained model on Just-In-Time defect prediction.* QRS 2023. DOI: [10.1109/QRS60937.2023.00020](https://doi.org/10.1109/QRS60937.2023.00020) | MD + SEC |
| Lin2023 | Lin, B., Wang, S., Liu, Z., Liu, Y., Xia, X., Mao, X. *CCT5: A Code-Change-Oriented Pre-trained Model.* ESEC/FSE 2023. DOI: [10.1145/3611643.3616339](https://doi.org/10.1145/3611643.3616339) | MD + SEC |
| Chen2024 | Chen et al. *JIT-Smart: A Multi-task Learning Framework for Just-in-Time Defect Prediction and Localization.* PACMSE 1(FSE), 2024. DOI: [10.1145/3643727](https://doi.org/10.1145/3643727). First author's surname from the Huang2026 reference list | MD + SEC |
| Zhou2024 | Zhou, X., Han, D., Lo, D. *Bridging expert knowledge with deep learning techniques for just-in-time defect prediction.* EMSE, 2024. DOI: [10.1007/s10664-024-10591-0](https://doi.org/10.1007/s10664-024-10591-0) | MD |
| Jiang2025 | Jiang, Y., Shen, B., Gu, X. *Just-in-time software defect prediction via bi-modal change representation learning.* JSS 219:112253, 2025. DOI: [10.1016/j.jss.2024.112253](https://doi.org/10.1016/j.jss.2024.112253) | MD + SEC |
| Monteiro2026 | Monteiro, M. L., Cabral, G. G., Oliveira, A. L. I. *Pre-trained Code Language Models for Just-in-Time Software Defect Prediction: An Empirical Study.* LNCS, 2026. DOI: [10.1007/978-3-032-15984-7_24](https://doi.org/10.1007/978-3-032-15984-7_24) | MD |
| Monteiro2025 | Monteiro, M. L., Cabral, G. G., Oliveira, A. L. I. *CodeFlowLM: Incremental Just-In-Time Defect Prediction with Pretrained Language Models and Exploratory Insights into Defect Localization.* arXiv:[2512.00231](https://arxiv.org/abs/2512.00231), 2025 | AB |

## Datasets

| Key | Reference | Level |
|---|---|---|
| Keshavarz2022 | Keshavarz, H., Nagappan, M. *ApacheJIT: A Large Dataset for Just-In-Time Defect Prediction.* MSR 2022 Data Showcase. arXiv:[2203.00101](https://arxiv.org/abs/2203.00101). Data: Zenodo [10.5281/zenodo.5907001](https://doi.org/10.5281/zenodo.5907001) (CC BY 4.0); <https://github.com/hosseinkshvrz/apachejit> | FT + RP |
| Nam2026 | Nam, D., Kim, T., Ryu, D., Baik, J. *ReDef: Do Code Language Models Truly Understand Code Changes for Just-in-Time Software Defect Prediction?* PACMSE (FSE 2026). DOI: [10.1145/3808179](https://doi.org/10.1145/3808179); arXiv:[2509.09192](https://arxiv.org/abs/2509.09192). Data: <https://figshare.com/s/4f202bc0921e26b41dc2> | FT |
| Mahbub2023 | Mahbub, P., Shuvo, O., Rahman, M. M. *Defectors: A Large, Diverse Python Dataset for Defect Prediction.* MSR 2023. DOI: [10.1109/MSR59073.2023.00085](https://doi.org/10.1109/MSR59073.2023.00085). Data: Zenodo [10.5281/zenodo.7708984](https://doi.org/10.5281/zenodo.7708984) (CC BY 4.0) | AB + RP |
| JITDefectExtended | JIT-Defect-Extended dataset, released with Huang2026. <https://github.com/JIT-LSM/JIT-Defect-Extended> (created July 2025; no LICENSE file). Layout, schema, and overlap with JIT-Defect4J inspected; two records downloaded | RP |

## LLMs for change risk and JIT-DP

| Key | Reference | Level |
|---|---|---|
| Abreu2024 | Abreu, R., Murali, V., Rigby, P. C., et al. *Moving Faster and Reducing Risk: Using LLMs in Release Deployment.* arXiv:[2410.06351](https://arxiv.org/abs/2410.06351), 2024 | AB |
| Kim2025 | Kim, S., Shivaji, S., Whitehead, J. *A Reflection on Change Classification in the Era of Large Language Models.* IEEE TSE, 2025. DOI: [10.1109/TSE.2025.3539566](https://doi.org/10.1109/TSE.2025.3539566) | MD (title only) |
| Huang2026 | Huang, Y., Chen, M., Chen, X., Liu, Y. *Towards integrating large model with small model for Just-in-Time Defect Prediction and Localization* (JIT-LSM). Information and Software Technology 198:108244, October 2026. DOI: [10.1016/j.infsof.2026.108244](https://doi.org/10.1016/j.infsof.2026.108244). Closed access; ScienceDirect returned HTTP 403 and no abstract is indexed, so **the paper was not read**. Replication package: <https://github.com/JIT-LSM/JIT_LSM> (no LICENSE file; code, README, and the Git LFS evaluation subsets inspected) | MD + RP |
| Yeo2026 | Yeo, I., Lee, S., Ryu, D., Baik, J. *Project Evolution-aware Prompting of LLMs for Just-in-time Defect Prediction in Edge-cloud Systems* (PROPER-SDP). Journal of Web Engineering 25(3):395–416, 2026. DOI: [10.13052/jwe1540-9589.2535](https://doi.org/10.13052/jwe1540-9589.2535). HTML full text: <https://journals.riverpublishers.com/index.php/JWE/article/download/33016/23782?inline=1> | FT |
| Deng2026 | Deng, Y., Li, W., Xu, L., Cen, Y. *Context Matters: Learning Structural Code Representations for Just-in-Time Defect Prediction* (JIT-Context). ICSME 2026, Research Papers Track. Programme page: <https://conf.researchr.org/details/icsme-2026/icsme-2026-papers/1/Context-Matters-Learning-Structural-Code-Representations-for-Just-in-Time-Defect-Pre>. DOI not yet indexed | AB |
| Song2026 | Song, X., Wu, Y., Chen, B., Lu, Z., Liu, S., Peng, X. *Characterizing Regression Bug-Inducing Changes and Improving LLM-Based Regression Bug Detection* (LLM4Reg). ICSE 2026. DOI: [10.1145/3744916.3773182](https://doi.org/10.1145/3744916.3773182). Preprint and README: <https://github.com/FudanSELab/LLM4Reg> | FT (preprint) + RP |
| Liu2026 | Liu, Y., Jabre, K., Abreu, R., et al. *A Preliminary Study on Explaining Risk of Code Changes using LLM-Based Prediction Models.* arXiv:[2607.02782](https://arxiv.org/abs/2607.02782), 2026 | AB |
| Adams2026 | Adams, C., et al. *Automating Low-Risk Code Review at Meta: RADAR, Risk Calibration, and Review Efficiency.* arXiv:[2605.30208](https://arxiv.org/abs/2605.30208), 2026 | AB |
| Kurup2026 | Kurup, M., et al. *Deployment Risk Assessment Using Diff-Aware Features: A Case Study at Prime Video.* ASE 2026 Industry Showcase (accepted). arXiv:[2607.06766](https://arxiv.org/abs/2607.06766) | AB |
| Hesamolhokama2025 | Hesamolhokama, M., et al. *From Illusion to Insight: Change-Aware File-Level Software Defect Prediction Using Agentic AI.* arXiv:[2512.23875](https://arxiv.org/abs/2512.23875), 2025 | AB |
| Boughriou2026 | Boughriou, S. Replication package for *"Are Large Language Models a Silver Bullet? Benchmarking LLMs vs. Machine Learning for Just-in-Time Defect Prediction".* figshare, 2026. DOI: [10.6084/m9.figshare.31076551](https://doi.org/10.6084/m9.figshare.31076551). **The paper itself was not found** | RP |

## Context in LLM-based code tasks

| Key | Reference | Level |
|---|---|---|
| Shrivastava2023 | Shrivastava, D., et al. *Repository-Level Prompt Generation for Large Language Models of Code.* ICML 2023. arXiv:[2206.12839](https://arxiv.org/abs/2206.12839) | MD |
| Zhang2023 | Zhang, F., et al. *RepoCoder: Repository-Level Code Completion Through Iterative Retrieval and Generation.* EMNLP 2023. DOI: [10.18653/v1/2023.emnlp-main.151](https://doi.org/10.18653/v1/2023.emnlp-main.151) | MD |
| Ding2023 | Ding, Y., et al. *CrossCodeEval: A Diverse and Multilingual Benchmark for Cross-File Code Completion.* NeurIPS 2023 Datasets & Benchmarks Track | MD |
| Hu2025 | Hu, R., et al. *Benchmarking LLMs for Fine-Grained Code Review with Enriched Context in Practice* (ContextCRBench). arXiv:[2511.07017](https://arxiv.org/abs/2511.07017), 2025 | AB |
| Zhang2026 | Zhang, L., et al. *AACR-Bench: Evaluating Automatic Code Review with Holistic Repository-Level Context.* arXiv:[2601.19494](https://arxiv.org/abs/2601.19494), 2026 | AB |
| Sun2026 | Sun, K., et al. *Improving LLM-Based Go Code Review through Issue-List Generation and Context Augmentation.* arXiv:[2606.01859](https://arxiv.org/abs/2606.01859), 2026 | AB |
| Lu2025 | Lu, J., et al. *Towards Practical Defect-Focused Automated Code Review.* ICML 2025. arXiv:[2505.17928](https://arxiv.org/abs/2505.17928) | AB |
| Risse2025 | Risse, N., Liu, J., Böhme, M. *Top Score on the Wrong Exam: On Benchmarking in Machine Learning for Vulnerability Detection.* 2025. DOI: [10.1145/3728887](https://doi.org/10.1145/3728887) | MD |
| Ding2025 | Ding, Y., et al. *Vulnerability Detection with Code Language Models: How Far are We?* (PrimeVul). ICSE 2025. DOI: [10.1109/ICSE55347.2025.00038](https://doi.org/10.1109/ICSE55347.2025.00038) | MD + SEC |
| Wen2024 | Wen, X.-C., et al. *VulEval: Towards Repository-Level Evaluation of Software Vulnerability Detection.* arXiv:[2404.15596](https://arxiv.org/abs/2404.15596), 2024 | MD |
| Yildiz2025 | Yildiz, A., et al. *Benchmarking LLMs and LLM-based Agents in Practical Vulnerability Detection for Code Repositories* (JitVul). ACL 2025. DOI: [10.18653/v1/2025.acl-long.1490](https://doi.org/10.18653/v1/2025.acl-long.1490) | MD |
| Li2025 | Li, Y., Li, X., Wu, H., et al. *Everything You Wanted to Know About LLM-based Vulnerability Detection But Were Afraid to Ask* (CORRECT). arXiv:[2504.13474](https://arxiv.org/abs/2504.13474), 2025 | AB |

## Long-context behaviour of LLMs

| Key | Reference | Level |
|---|---|---|
| Shi2023 | Shi, F., et al. *Large Language Models Can Be Easily Distracted by Irrelevant Context.* ICML 2023. arXiv:[2302.00093](https://arxiv.org/abs/2302.00093) | MD |
| Liu2024 | Liu, N. F., et al. *Lost in the Middle: How Language Models Use Long Contexts.* TACL, 2024. DOI: [10.1162/tacl_a_00638](https://doi.org/10.1162/tacl_a_00638) | MD |
| Levy2024 | Levy, M., Jacoby, A., Goldberg, Y. *Same Task, More Tokens: the Impact of Input Length on the Reasoning Performance of Large Language Models.* ACL 2024. DOI: [10.18653/v1/2024.acl-long.818](https://doi.org/10.18653/v1/2024.acl-long.818) | MD |
| Ding2024 | Ding et al. *Do code summarization models process too much information? Function signature may be all that is needed.* ACM TOSEM 33(6), 2024. DOI: [10.1145/3652156](https://doi.org/10.1145/3652156) | SEC (from the Huang2026 reference list) |

## Methodology for LLM-based SE studies, metrics, and statistics

| Key | Reference | Level |
|---|---|---|
| Sallou2024 | Sallou, J., Durieux, T., Panichella, A. *Breaking the Silence: the Threats of Using LLMs in Software Engineering.* ICSE-NIER 2024. DOI: [10.1145/3639476.3639764](https://doi.org/10.1145/3639476.3639764) | MD |
| Wagner2025 | Wagner, S., et al. *Towards Evaluation Guidelines for Empirical Studies Involving LLMs.* WSESE 2025. DOI: [10.1109/WSESE66602.2025.00011](https://doi.org/10.1109/WSESE66602.2025.00011) | MD |
| Ouyang2025 | Ouyang, S., Zhang, J. M., Harman, M., Wang, M. *An Empirical Study of the Non-determinism of ChatGPT in Code Generation.* ACM TOSEM. DOI: [10.1145/3697010](https://doi.org/10.1145/3697010) | AB |
| Ramos2025 | Ramos, D., Mamede, C., Jain, K., Canelas, P., Gamboa, C., Le Goues, C. *Are Large Language Models Memorizing Bug Benchmarks?* LLM4Code 2025. DOI: [10.1109/LLM4Code66737.2025.00005](https://doi.org/10.1109/LLM4Code66737.2025.00005) | AB |
| Xiong2024 | Xiong, M., et al. *Can LLMs Express Their Uncertainty? An Empirical Evaluation of Confidence Elicitation in LLMs.* ICLR 2024. arXiv:[2306.13063](https://arxiv.org/abs/2306.13063) | AB |
| Yao2020 | Yao, J., Shepperd, M. *Assessing software defection prediction performance: why using the Matthews correlation coefficient matters.* EASE 2020. Preprint: Zenodo [10.5281/zenodo.3581262](https://doi.org/10.5281/zenodo.3581262) | MD |
| Chicco2020 | Chicco, D., Jurman, G. *The advantages of the Matthews correlation coefficient (MCC) over F1 score and accuracy in binary classification evaluation.* BMC Genomics 21:6, 2020. DOI: [10.1186/s12864-019-6413-7](https://doi.org/10.1186/s12864-019-6413-7) | MD |
| Dietterich1998 | Dietterich, T. G. *Approximate Statistical Tests for Comparing Supervised Classification Learning Algorithms.* Neural Computation 10(7), 1998. DOI: [10.1162/089976698300017197](https://doi.org/10.1162/089976698300017197) | MD |
| DeLong1988 | DeLong, E. R., DeLong, D. M., Clarke-Pearson, D. L. *Comparing the Areas under Two or More Correlated Receiver Operating Characteristic Curves: A Nonparametric Approach.* Biometrics 44(3), 1988. DOI: [10.2307/2531595](https://doi.org/10.2307/2531595) | MD |
| Lakens2017 | Lakens, D. *Equivalence Tests: A Practical Primer for t-Tests, Correlations, and Meta-Analyses.* Preprint DOI: [10.31234/osf.io/97gpc](https://doi.org/10.31234/osf.io/97gpc). The journal version (Social Psychological and Personality Science, 2017) was not verified | MD |
| Holm1979 | Holm, S. *A simple sequentially rejective multiple test procedure.* Scandinavian Journal of Statistics 6:65–70, 1979 | SEC |

## Tools

| Key | Reference | Level |
|---|---|---|
| Spadini2018 | Spadini, D., Aniche, M., Bacchelli, A. *PyDriller: Python Framework for Mining Software Repositories.* ESEC/FSE 2018. DOI: [10.1145/3236024.3264598](https://doi.org/10.1145/3236024.3264598) | SEC |
| Falleri2014 | Falleri, J.-R., Morandat, F., Blanc, X., Martinez, M., Monperrus, M. *Fine-grained and accurate source code differencing* (GumTree). ASE 2014. DOI: [10.1145/2642937.2642982](https://doi.org/10.1145/2642937.2642982) | SEC |
