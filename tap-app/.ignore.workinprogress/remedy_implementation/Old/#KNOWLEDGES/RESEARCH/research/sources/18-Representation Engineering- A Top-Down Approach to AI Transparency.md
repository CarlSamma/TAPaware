> Source: https://montrealethics.ai/representation-engineering-a-top-down-approach-to-ai-transparency/

Representation Engineering: A Top-Down Approach to AI Transparency | Montreal AI Ethics Institute
Skip to main content
Skip to secondary menu
Skip to primary sidebar
Skip to footer
Montreal AI Ethics Institute
Democratizing AI ethics literacy
Menu
Articles Submenu
Public Policy
Privacy & Security
Human Rights Submenu
Ethics
JEDI (Justice, Equity, Diversity, Inclusion
Climate
Design Submenu
Emerging Technology
Application & Adoption Submenu
Health
Education
Government Submenu
Military
Public Works
Labour
Arts & Culture Submenu
Film & TV
Music
Pop Culture
Digital Art
Columns Submenu
AI Policy Corner
Recess
Tech Futures
The AI Ethics Brief
AI Literacy Submenu
Research Summaries
AI Ethics Living Dictionary
Learning Community
The State of AI Ethics Report Submenu
State of AI Ethics Report Volume 8 (2026): Call for Contributors
Volume 7 (November 2025)
Volume 6 (February 2022)
Volume 5 (July 2021)
Volume 4 (April 2021)
Volume 3 (Jan 2021)
Volume 2 (Oct 2020)
Volume 1 (June 2020)
About Submenu
Our Contributions Policy
Our Open Access Policy
Contact
Donate
Representation Engineering: A Top-Down Approach to AI Transparency
January 25, 2024  
🔬 Research Summary by Andy Zou, a Ph.D. student at CMU, advised by Zico Kolter and Matt Fredrikson. He also cofounded the Center for AI Safety (safe.ai).
[ Original paper by Andy Zou, Long Phan, Sarah Chen, James Campbell, Phillip Guo, Richard Ren, Alexander Pan, Xuwang Yin, Mantas Mazeika, Ann-Kathrin Dombrowski, Shashwat Goel, Nathaniel Li, Michael J. Byun, Zifan Wang, Alex Mallen, Steven Basart, Sanmi Koyejo, Dawn Song, Matt Fredrikson, J. Zico Kolter, and Dan Hendrycks]
Overview: Deep neural networks have achieved incredible success across a wide variety of domains, yet their inner workings remain poorly understood. In this work, we identify and characterize the emerging area of representation engineering (RepE), which follows an approach of top-down transparency to better understand and control the inner workings of neural networks. Inspired by cognitive neuroscience, we improve the transparency and safety of AI systems by performing AI “mind reading and control.”
Introduction
In this paper, we introduce and characterize the emerging area of representation engineering (RepE), an approach to enhancing AI systems' transparency that draws on cognitive neuroscience insights. RepE places population-level representations, rather than neurons or circuits, at the center of analysis, equipping us with novel methods for monitoring and manipulating high-level cognitive phenomena in deep neural networks (DNNs). We provide baselines and initial analysis of RepE techniques, showing that they offer simple yet effective solutions for improving our understanding and control of large language models. We showcase how these methods can provide traction on a wide range of safety-relevant problems, including truthfulness, memorization, power-seeking, and more, demonstrating the promise of representation-centered transparency research. We hope that this work catalyzes further exploration of RepE and fosters advancements in the transparency and safety of AI systems.
Key Insights
Motivation
One approach to increasing the transparency of AI systems is to create a “cognitive science of AI.” Current efforts toward this goal largely center around the area of mechanistic interpretability, which focuses on understanding neural networks in terms of neurons and circuits. This aligns with the Sherringtonian view in cognitive neuroscience, which sees cognition as the outcome of node-to-node connections implemented by neurons embedded in circuits within the brain. While this view has successfully explained simple mechanisms, it has struggled to explain more complex phenomena. The contrasting Hopfieldian view (n.b., not to be confused with Hopfield networks) has shown more promise in scaling to higher-level cognition. Rather than focusing on neurons and circuits, the Hopfieldian view sees cognition as a product of representational spaces implemented by patterns of activity across populations of neurons. This view currently has no analog in machine learning, yet it could point toward a new approach to transparency research.
Representation Engineering (RepE)
Representation engineering (RepE) is a top-down approach to transparency research that treats representations as the fundamental unit of analysis, aiming to understand and control representations of high-level cognitive phenomena in neural networks. In particular, we identify two main areas of RepE: Reading and Control. Representation reading seeks to locate emergent representations for high-level concepts and functions within a network. Building on the insights gained from Representation Reading, Representation Control seeks to modify or control the internal representations of concepts and functions.
In the paper, we propose Linear Artificial Tomography (LAT) as a baseline for Rep Reading. For Rep Control, we propose three different baselines: Reading Vector, Contrast Vector, and Low-Rank Representation Adaptation (LoRRA).
Frontiers of RepE
Here, we will give an overview of each of the frontiers we explore in the paper. Please refer to the more detailed section in the paper.
Honesty
In this section, we explore applications of RepE to concepts and functions related to honesty. First, we demonstrate that models possess a consistent internal concept of truthfulness, which enables detecting imitative falsehoods and intentional lies generated by LLMs. We then show how reading a model's representation of honesty enables control techniques to enhance honesty. These interventions lead us to state-of-the-art results on TruthfulQA.
Ethics and Power
In this section, we explore the application of RepE to various aspects of machine ethics. We present progress in monitoring and controlling learned representations of important concepts and functions, such as utility, morality, probability, risk, and power-seeking tendencies. In addition, we illustrate mathematical relations between emergent representations.
Emotion
In this section, we attempt to conduct LAT scans on the LLaMA-2-Chat-13B model to discern neural activity associated with various emotions and illustrate the profound impact of emotions on model behavior.
Harmless Instruction-Following
Aligned language models designed to resist harmful instructions can be compromised by clever use of tailored prompts known as jailbreaks. We extract a model's internal representation of harm and use it to draw the model's attention to the harmfulness concept to shape its behavior, making it more robust to jailbreaks. This suggests the potential of enhancing or dampening targeted traits or values to achieve fine-grained control of model behavior.
Knowledge and Model Editing
We demonstrate how to apply Representation Engineering to identify and manipulate precise knowledge, factual information, and non-numerical concepts.
Memorization
Generative models can memorize a substantial portion of their training data, raising concerns about potential confidential or copyrighted content breaches. In the following section, we present an initial exploration in the area of model memorization with RepE to detect and prevent memorized outputs.
Between the lines
Inspired by the Hopfieldian view in cognitive neuroscience, RepE places representations and the transformations between them at the center of the analysis. As neural networks exhibit more coherent internal structures, we believe analyzing them at the representation level can yield new insights, aiding in effective monitoring and control. While we mainly analyzed subspaces of representations, future work could investigate trajectories, manifolds, and state spaces of representations. We hope this initial step in exploring the potential of RepE helps to foster new insights into understanding and controlling AI systems, ultimately ensuring that future AI systems are trustworthy and safe.
Want quick summaries of the latest research & reporting in AI ethics delivered to your inbox? Subscribe to the AI Ethics Brief. We publish bi-weekly.
Primary Sidebar
SAIER Volume 8 (2026)
🔍 SEARCH
Search the site ... Search
Spotlight
Tech Futures: At the Frontier of Fear, Uncertainty and Doubt
Tech Futures: Introducing the Resist List
Tech Futures: Better Imagination for Better Tech Futures
Tech Futures: Crafting Participatory Tech Futures
Tech Futures: AI For and Against Knowledge
related posts
 [
SHADES: Towards a Multilingual Assessment of Stereotypes in Large Language Models
](https://montrealethics.ai/towards-a-multilingual-assessment-of-stereotypes-in-large-language-models/)
 [
The AI Carbon Footprint and Responsibilities of AI Scientists
](https://montrealethics.ai/the-ai-carbon-footprint-and-responsibilities-of-ai-scientists/)
 [
The Secret Revealer: Generative Model-Inversion Attacks Against Deep Neural Networks (Research Summa...
](https://montrealethics.ai/the-secret-revealer-generative-model-inversion-attacks-against-deep-neural-networks-research-summary/)
 [
Research Summary: Towards Evaluating the Robustness of Neural Networks
](https://montrealethics.ai/research-summary-towards-evaluating-the-robustness-of-neural-networks/)
 [
Benchmark Dataset Dynamics, Bias and Privacy Challenges in Voice Biometrics Research
](https://montrealethics.ai/benchmark-dataset-dynamics-bias-and-privacy-challenges-in-voice-biometrics-research/)
 [
Who Funds Misinformation? A Systematic Analysis of the Ad-related Profit Routines of Fake News sites
](https://montrealethics.ai/who-funds-misinformation-a-systematic-analysis-of-the-ad-related-profit-routines-of-fake-news-sites/)
 [
An Audit Framework for Adopting AI-Nudging on Children
](https://montrealethics.ai/an-audit-framework-for-adopting-ai-nudging-on-children/)
 [
Science Communications for Explainable Artificial Intelligence
](https://montrealethics.ai/science-communications-for-explainable-artificial-intelligence/)
 [
SoK: The Gap Between Data Rights Ideals and Reality
](https://montrealethics.ai/sok-the-gap-between-data-rights-ideals-and-reality/)
 [
The AI Gambit – Leveraging Artificial Intelligence to Combat Climate Change
](https://montrealethics.ai/the-ai-gambit-leveraging-artificial-intelligence-to-combat-climate-change/)
Partners
U.S. Artificial Intelligence Safety Institute Consortium (AISIC) at NIST
Partnership on AI
The LF AI & Data Foundation
The AI Alliance
Footer
Articles
Columns
AI Literacy
The State of AI Ethics Report   
About Us
Founded in 2018, the Montreal AI Ethics Institute (MAIEI) is an international non-profit organization equipping citizens concerned about artificial intelligence and its impact on society to take action.
Contact
Donate
© 2025 MONTREAL AI ETHICS INSTITUTE.
This work is licensed under a Creative Commons Attribution 4.0 International License. 
Learn more about our open access policy here.    
Save hours of work and stay on top of Responsible AI research and reporting with our bi-weekly email newsletter.
×