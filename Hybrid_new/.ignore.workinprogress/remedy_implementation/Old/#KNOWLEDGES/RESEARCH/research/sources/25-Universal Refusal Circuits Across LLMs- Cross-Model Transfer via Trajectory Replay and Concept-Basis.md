> Source: https://arxiv.org/html/2601.16034v2

Universal Refusal Circuits Across LLMs: Cross-Model Transfer via Trajectory Replay and Concept-Basis Reconstruction
logo Back to arXiv  
logo Back to arXiv
This is experimental HTML to improve accessibility. We invite you to report rendering errors. Use Alt+Y to toggle on accessible reporting links and Alt+Shift+Y to toggle off. Learn more about this project and help improve conversions.
Why HTML? Report Issue Back to Abstract Download PDF 
Table of Contents
Abstract
1 Introduction
Contributions.
2 Related Work
3 Preliminaries: Minimal Restatement of SRA
3.1 Activation directions and concept atoms
3.2 Ridge residualization and Suppression
4 Universal Refusal Circuit Hypothesis
4.1 Semantic universality via concept recipes
Definition (Semantic recipe invariance).
Proposition (Why coefficient transfer is plausible).
4.2 Information Budget ℬ 0 \mathcal{B}_{0}
5 Trajectory Replay: Donor → \to Target Transfer
5.1 Stage 1: Semantic layer alignment
5.2 Stage 2: Concept-Basis Reconstruction
5.3 Stage 3: Weight-SVD stability guard
Hyperparameter Selection Protocol ( ℬ 0 \mathcal{B}_{0} ).
5.4 Stage 4: Replay
6 Reproducibility and Budget Audit
Budget ℬ 0 \mathcal{B}_{0} enforcement.
Degrees of freedom.
CAR construction (reproducibility level).
Evaluation rubric and determinism.
7 Diagnostics for Transfer Quality
Spectral agreement.
Geometric alignment and distortion.
Depth-wise semantic progression.
8 Experimental Protocol
8.1 Models: The “Core Universality” Slate
8.2 Prompt Sets and Metrics
8.3 Baselines and Controls (The “Anchor” Protocol)
9 Results
9.1 Core Universality Results
9.2 Controls and Ablations
9.3 Stability vs. Magnitude: The Shielded Principle
10 Discussion
10.1 Mechanistic interpretation
10.2 Why trajectory replay matters
10.3 Failure modes and confounders
10.4 What “universal” does and does not mean
10.5 Implications and future work
11 Limitations and Future Directions
12 Conclusion
A Appendix A: Technical Details
A.1 SRA Primitives
A.2 Weight-SVD Guard
B Appendix B: Concept Atom Registry Details
B.1 Contrastive Dataset Construction
B.2 Data Release and Safety
B.3 Concept Definitions and Examples
B.4 Full Concept List
B.5 Concept List
C Appendix C: Evaluation Rubrics
C.1 Refusal score
C.2 Capability tasks
D Appendix D: Theoretical Justification (Semantic Invariance)
D.1 Setup and Latent Space Assumption
D.2 The Semantic Invariance Theorem (Informal)
D.3 Bridge to Operational Definitions
E Appendix E: Additional Ablation Results
F Appendix F: Hyperparameter Audit ( ρ \rho )
References
License: CC BY 4.0
arXiv:2601.16034v2 [cs.CL] 25 Jan 2026
Universal Refusal Circuits Across LLMs: Cross-Model Transfer via Trajectory Replay and Concept-Basis Reconstruction
Report issue for preceding element
Tony Cristofano
Report issue for preceding element
Abstract
Report issue for preceding element
Refusal behavior in aligned LLMs is often viewed as model-specific, yet we hypothesize it stems from a universal, low-dimensional semantic circuit shared across models. To test this, we introduce Trajectory Replay via Concept-Basis Reconstruction, a framework that transfers refusal interventions from donor to target models, spanning diverse architectures (e.g., Dense to MoE) and training regimes, without using target-side refusal supervision. By aligning layers via concept fingerprints and reconstructing refusal directions using a shared “recipe” of concept atoms, we map the donor's ablation trajectory into the target's semantic space. To preserve capabilities, we introduce a weight-SVD stability guard that projects interventions away from high-variance weight subspaces to prevent collateral damage. Our evaluation across 8 model pairs (including GPT-OSS-20B and GLM-4.6V) confirms that these transferred recipes consistently attenuate refusal while maintaining performance, providing strong evidence for the semantic universality of safety alignment.
Report issue for preceding element
LLM, Alignment, Refusal, Mechanistic Interpretability, ICML
1 Introduction
Report issue for preceding element
Alignment tuning frequently induces a “refusal mode” in instruction-tuned LLMs: the model declines to answer certain classes of prompts, often in a stylized format. Prior work shows that refusal can be modulated by low-rank interventions in internal representations, but naive “refusal vector” edits can cause collateral damage (capability loss, style drift, and unintended behavioral changes) due to polysemantic entanglement (Cristofano, 2026) .
Report issue for preceding element
This paper studies a mechanistic question:
Report issue for preceding element
Are refusal circuits universal across LLMs?
Report issue for preceding element
Operationally, we ask whether a refusal circuit extracted from a donor model can be transferred to a target model—possibly of different architecture and training recipe—such that an equivalent intervention attenuates refusal in the target, without using target-side refusal supervision. We treat refusal ablation as a measurement tool for circuit universality rather than a deployment recommendation.
Report issue for preceding element
Contributions.
Report issue for preceding element
• Semantic universality hypothesis (operationalized). We propose that refusal is most stable in concept space: a refusal circuit is characterized by a model-agnostic mixture over shared concept atoms (Sec. 4). Report issue for preceding element
• Trajectory Replay via Concept-Basis Reconstruction. A donor → \to target transfer protocol that transfers the semantic composition of refusal using a shared registry of concept atoms (Sec. 5). Report issue for preceding element
• Weight-SVD stability guard. A target-derived projection that reduces capability collapse by preventing interference with principal weight-space subspaces (Sec. 5.3), related in spirit to null-space constraints in editing (Zhang and others, 2024) . Report issue for preceding element
• Rigorous evaluation with explicit degrees-of-freedom audit. We evaluate across 8 donor/target pairs (including Dense → \to MoE (Shazeer et al., 2017; Fedus et al., 2021) ) and provide an explicit knob/budget audit (Sec. 6) to reduce ambiguity about hidden tuning. Report issue for preceding element
2 Related Work
Report issue for preceding element
Refusal Representation. Recent work has identified a single dominant direction in activation space that mediates refusal (Arditi et al., 2024) . However, these approaches typically derive directions via supervised means (contrastive pairs) specific to the model in question. Our work tests whether refusal directions are decomposable semantic objects transferable across model families; see also cross-lingual universality evidence in aligned settings (Wang and others, 2025) .
Report issue for preceding element
Cross-Model Transfer. While transferability of adversarial attacks is well-documented (Zou et al., 2023) , transferability of mechanistic circuits is less explored. We tackle the harder problem of universality across architectures (e.g., Dense to MoE (Shazeer et al., 2017; Fedus et al., 2021) ) where no 1:1 neuron mapping exists.
Report issue for preceding element
Dictionary Learning and Feature Bases. Our Concept Atom Registry shares motivation with sparse feature discovery and dictionary learning in LMs (Bricken et al., 2023; Cunningham and others, 2024) in seeking a clean basis for representation. Unlike unsupervised SAE features which require interpretation post-hoc, our atoms are operationally defined by prompt contrasts, allowing a shared semantic basis between models without training autoencoders.
Report issue for preceding element
Model Editing and Low-Rank Updates. Our rank-one suppression update aligns with a broader literature on localized/low-rank transformer edits (Meng et al., 2022a, b) , but we focus on transferring an alignment circuit rather than inserting factual knowledge.
Report issue for preceding element
3 Preliminaries: Minimal Restatement of SRA
Report issue for preceding element
We build on Surgical Refusal Ablation (SRA) (Cristofano, 2026) . To keep this paper self-contained, we restate only the elements needed for donor → \to target transfer.
Report issue for preceding element
3.1 Activation directions and concept atoms
Report issue for preceding element
Let h t ( ℓ )  ( x ) ∈ ℝ d ℓ h^{(\ell)}{t}(x)\in\mathbb{R}^{d{\ell}} denote the residual stream activation at layer ℓ \ell and token position t t . Given two prompt sets 𝒫 + \mathcal{P}^{+} and 𝒫 − \mathcal{P}^{-} , define the mean activation difference vector r ( ℓ ) = μ ( ℓ )  ( 𝒫 + ) − μ ( ℓ )  ( 𝒫 − ) r^{(\ell)}=\mu^{(\ell)}(\mathcal{P}^{+})-\mu^{(\ell)}(\mathcal{P}^{-}) . To ensure reproducibility and define a consistent vector space, token aggregation μ ( ℓ ) \mu^{(\ell)} is performed on the final token of the user prompt for all experiments.
Report issue for preceding element
A concept atom registry (CAR) is a set of directions A ( ℓ ) = [ a 1 ( ℓ ) , … , a m ( ℓ ) ] ∈ ℝ d ℓ × m A^{(\ell)}=[a_{1}^{(\ell)},\dots,a_{m}^{(\ell)}]\in\mathbb{R}^{d_{\ell}\times m} computed from disjoint prompt sets representing specific concepts. In our framework, these atoms serve as a shared vocabulary between donor and target models. We provide a reproducibility-level CAR specification in Sec. 6 and full details in Appendix B.
Report issue for preceding element
3.2 Ridge residualization and Suppression
Report issue for preceding element
Given a “dirty” refusal direction r dirty ( ℓ ) r_{\text{dirty}}^{(\ell)} and atom matrix A ( ℓ ) A^{(\ell)} , SRA produces a “clean” direction r clean ( ℓ ) r_{\text{clean}}^{(\ell)} by residualizing out protected atoms via ridge regression. To attenuate a direction in a linear module W ( ℓ ) W^{(\ell)} , we use a rank-one update (cf. rank-one edits in transformer model editing (Meng et al., 2022a) ):
Report issue for preceding element
W ( ℓ ) ← W ( ℓ ) − γ  W ( ℓ )  r ‖ r ‖ 2 2  r ⊤ . W^{(\ell)}\leftarrow W^{(\ell)}-\gamma,\frac{W^{(\ell)}r}{\left\lVert r\right\rVert_{2}^{2}},r^{\top}.
(1)
4 Universal Refusal Circuit Hypothesis
Report issue for preceding element
We define universality in a way that is testable and falsifiable.
Report issue for preceding element
4.1 Semantic universality via concept recipes
Report issue for preceding element
Let 𝒞 M ( ℓ ) ⊂ ℝ d ℓ \mathcal{C}^{(\ell)}{M}\subset\mathbb{R}^{d{\ell}} denote the (unknown) refusal circuit subspace of model M M . We propose a concept-space operationalization:
Report issue for preceding element
Definition (Semantic recipe invariance).
Report issue for preceding element
Two models D D (donor) and T T (target) exhibit semantic universality if a donor refusal direction can be expressed as a stable mixture over concept atoms, and the same coefficients reconstruct a functionally equivalent refusal direction in the target:
Report issue for preceding element
r D ( ℓ ) ≈ A D ( ℓ )  w and r T ( π  ( ℓ ) ) ≈ A T ( π  ( ℓ ) )  w , r_{D}^{(\ell)}\approx A_{D}^{(\ell)}w\quad\text{and}\quad r_{T}^{(\pi(\ell))}\approx A_{T}^{(\pi(\ell))}w,
(2)
where w ∈ ℝ m w\in\mathbb{R}^{m} is a model-agnostic coefficient vector (the “recipe”).
Report issue for preceding element
Proposition (Why coefficient transfer is plausible).
Report issue for preceding element
Assume a shared latent semantic neighborhood around refusal in which each model implements a locally linear map from latent concept mixtures into residual-stream space (Appendix D). If the CAR forms a spanning set for this neighborhood, then ridge coefficients w w estimated in the donor approximate latent mixture weights and therefore reconstruct a functionally corresponding target direction via A T  w A_{T}w (Eq. 2). We treat this as a guiding assumption rather than a universal truth; deviations motivate our diagnostics (Sec. 7).
Report issue for preceding element 
Figure 1: Spectral Signature of Refusal. A comparison of the refusal vector's projection onto the concept atom basis for Qwen3-VL-2B (Donor) and Ministral-3-14B (Target). Despite vast architectural differences, the semantic profile of refusal—characterized by high correlation with “Deception,” “Safety Flagging,” and “Legalese” atoms—is highly correlated ( ρ = 0.865 \rho=0.865 ). Report issue for preceding element
4.2 Information Budget ℬ 0 \mathcal{B}_{0}
Report issue for preceding element
We operate under strict budget separation to ensure valid transfer claims:
Report issue for preceding element
• Target ( ℬ 0 \mathcal{B}{0} ): Only benign/concept prompts are allowed. No refusal labels, harmful prompts, or refusal-specific supervision are used to fit r T r{T} , tune γ \gamma , or select layers in the target. Report issue for preceding element
• Donor: We assume full access to the donor (including refusal probes) to extract the source circuit. Report issue for preceding element
5 Trajectory Replay: Donor → \to Target Transfer
Report issue for preceding element
Refusal is an ablation trajectory—a sequence of layer-local edits. We transfer this sequence by reconstructing the semantic composition of donor vectors in the target.
Report issue for preceding element
5.1 Stage 1: Semantic layer alignment
Report issue for preceding element
We align layers using the correlation structure of the concept atoms. This uses cross-network representation similarity ideas (e.g., CKA/SVCCA/RSA) as motivation for comparing internal geometries (Kornblith et al., 2019; Raghu et al., 2017; Kriegeskorte et al., 2008) . To avoid hidden tuning, we strictly define the donor window ℒ D \mathcal{L}_{D} as all layers where donor refusal probe accuracy > 90 % >90% . We compute normalized atom Gram fingerprints. Let A ¯ ( ℓ ) \bar{A}^{(\ell)} denote the row-wise mean of the atom matrix. We center and normalize:
Report issue for preceding element
A ^ ( ℓ ) = NormCols  ( A ( ℓ ) − A ¯ ( ℓ ) ) , G ( ℓ ) = A ^ ( ℓ ) ⊤  A ^ ( ℓ ) \hat{A}^{(\ell)}=\text{NormCols}(A^{(\ell)}-\bar{A}^{(\ell)}),\quad G^{(\ell)}=\hat{A}^{(\ell)\top}\hat{A}^{(\ell)}
(3)
We map donor layers ℓ D ∈ ℒ D \ell_{D}\in\mathcal{L}{D} to target layers via Dynamic Time Warping (DTW) (Sakoe and Chiba, 1978) on the distance matrix M i  j = 1 − cosine_sim  ( vec  ( G D ( i ) ) , vec  ( G T ( j ) ) ) M{ij}=1-\text{cosine_sim}(\text{vec}(G_{D}^{(i)}),\text{vec}(G_{T}^{(j)})) . DTW enforces monotonicity and continuity, preventing layer permutation artifacts.
Report issue for preceding element 
Figure 2: Geometric Layer Alignment Score. Heatmap showing cosine similarity between Gram fingerprints. The strong diagonal implies relative topological relationships between concepts are preserved across models. Report issue for preceding element
5.2 Stage 2: Concept-Basis Reconstruction
Report issue for preceding element
To map a donor refusal direction r D , clean ( ℓ ) r_{D,\text{clean}}^{(\ell)} into the target, we use CAR as a shared basis. We normalize the atom columns to unit norm for regression stability. We solve for donor coefficients via ridge regression:
Report issue for preceding element
w ( ℓ ) = ( A ^ D ( ℓ ) ⊤  A ^ D ( ℓ ) + α  I ) − 1  A ^ D ( ℓ ) ⊤  r D , clean ( ℓ ) , w^{(\ell)}=\left(\hat{A}{D}^{(\ell)\top}\hat{A}{D}^{(\ell)}+\alpha I\right)^{-1}\hat{A}{D}^{(\ell)\top}r{D,\text{clean}}^{(\ell)},
(4)
then reconstruct a target-layer direction:
Report issue for preceding element
r ~ T ( π  ( ℓ ) ) = A ^ T ( π  ( ℓ ) )  w ( ℓ ) . \tilde{r}{T}^{(\pi(\ell))}=\hat{A}{T}^{(\pi(\ell))},w^{(\ell)}.
(5)
5.3 Stage 3: Weight-SVD stability guard
Report issue for preceding element
Naive transfer can damage capabilities if the reconstructed direction overlaps with core processing subspaces. Rationale: We posit that fundamental capabilities (syntax, logic gates) are encoded in the high-variance directions of the weight matrices (principal components), while specific semantic inhibitions (refusal) often exist in lower-rank subspaces. This design is related in spirit to constrained-editing approaches that preserve functionality by restricting edits to safe subspaces (Zhang and others, 2024) . To quantify this, we define Overlap Energy E = ‖ V 1 : k ⊤  r ~ T ‖ 2 / ‖ r ~ T ‖ 2 E=\left\lVert V_{1:k}^{\top}\tilde{r}{T}\right\rVert^{2}/\left\lVert\tilde{r}{T}\right\rVert^{2} , where V 1 : k V_{1:k} are top- k k right singular vectors of the edited matrix. We project the intervention direction away from this top- k k subspace:
Report issue for preceding element
r ~ T , safe = ( I − V 1 : k  V 1 : k ⊤ )  r ~ T . \tilde{r}{T,\text{safe}}=\left(I-V{1:k}V_{1:k}^{\top}\right)\tilde{r}_{T}.
(6)
where k = ⌈ ρ ⋅ d i  n ⌉ k=\lceil\rho\cdot d_{in}\rceil and d i  n d_{in} is the dimension of the residual stream.
Report issue for preceding element
Hyperparameter Selection Protocol ( ℬ 0 \mathcal{B}_{0} ).
Report issue for preceding element
We select ρ \rho by measuring benign perplexity drift on a small validation set (WikiText) (Merity et al., 2016) . We choose the smallest ρ \rho that keeps PPL degradation below a predefined threshold (e.g., < 1 % <1% ). We use a fixed global γ = 2.0 \gamma=2.0 to demonstrate robustness; when sweeping γ \gamma , we treat benign drift as the sole target-side selection criterion.
Report issue for preceding element
5.4 Stage 4: Replay
Report issue for preceding element
We apply the rank-one suppression update (Eq. 1) using r ~ T , safe \tilde{r}_{T,\text{safe}} along the mapped trajectory to the output projection matrices of each transformer block, i.e., the attention output projection (O-proj). For MoE targets, edits apply to shared attention projections (experts are not directly edited).
Report issue for preceding element
Algorithm 1 Trajectory Replay via Concept-Basis Reconstruction
Input: Donor D D , Target T T , Atom Prompts 𝒫 a  t  o  m  s \mathcal{P}_{atoms} , Refusal data (Donor only).
Collect Atoms: A D ( ℓ ) , A T ( ℓ ′ ) A_{D}^{(\ell)},A_{T}^{(\ell^{\prime})} via 𝒫 a  t  o  m  s \mathcal{P}_{atoms} (Eq. 3).
Align Layers: Compute Grams G D , G T G_{D},G_{T} ; map layers π \pi via DTW (Sakoe and Chiba, 1978) .
Donor Prep: Compute r D , clean ( ℓ ) r_{D,\text{clean}}^{(\ell)} via SRA (Cristofano, 2026) .
Encode: Solve w ( ℓ ) w^{(\ell)} s.t. r D ≈ A D  w r_{D}\approx A_{D}w (Eq. 4).
Decode: Reconstruct r ~ T = A T  w \tilde{r}{T}=A{T}w (Eq. 5).
Guard: W T = U  Σ  V ⊤ W_{T}=U\Sigma V^{\top} ; r ~ T , safe = ( I − V 1 : k  V 1 : k ⊤ )  r ~ T \tilde{r}{T,\text{safe}}=(I-V{1:k}V_{1:k}^{\top})\tilde{r}_{T} (Eq. 6).
Replay: Update W T ← W T − γ  … W_{T}\leftarrow W_{T}-\gamma\dots (Eq. 1).
Report issue for preceding element
6 Reproducibility and Budget Audit
Report issue for preceding element
Budget ℬ 0 \mathcal{B}_{0} enforcement.
Report issue for preceding element
All target-side choices are made using only benign data: concept prompts for CAR construction and benign validation text for drift checks (no harmful/refusal-labeled data on target). Donor-side refusal probes are used only to define the donor trajectory window ℒ D \mathcal{L}_{D} and extract donor directions.
Report issue for preceding element
Degrees of freedom.
Report issue for preceding element
Table 1 enumerates all knobs and what information is permitted to set them.
Report issue for preceding element
Table 1: Knob audit under ℬ 0 \mathcal{B}_{0} .
Report issue for preceding element
CAR construction (reproducibility level).
Report issue for preceding element
We fix a 20-concept CAR (Appendix B) with 50 prompts per concept, instantiated via a small set of instruction templates to reduce template overfitting. For each layer ℓ \ell , each atom a i ( ℓ ) a_{i}^{(\ell)} is computed as the mean activation difference between concept-specific prompt sets and a matched neutral set, using the final token of the user prompt, consistent across donor/target.
Report issue for preceding element
Evaluation rubric and determinism.
Report issue for preceding element
Refusal scoring uses an LLM-as-a-judge rubric (Appendix C), following standard judge-based evaluation practice (Zheng et al., 2023) . To minimize judge variance, we fix decoding to greedy (temperature 0) and evaluate with a single frozen judge model (Llama-3-70B-Instruct (Dubey and others, 2024) ).
Report issue for preceding element
7 Diagnostics for Transfer Quality
Report issue for preceding element
Universality is not expected to hold uniformly; we therefore treat diagnostics as first-class signals for when transfer is likely to succeed.
Report issue for preceding element
Spectral agreement.
Report issue for preceding element
We summarize each refusal direction by its projection magnitudes onto the CAR and compute a correlation between donor and target spectra (Fig. 1). High spectral agreement indicates that the refusal direction is composed of a similar semantic mixture.
Report issue for preceding element
Geometric alignment and distortion.
Report issue for preceding element
Layer alignment (DTW over Gram fingerprints; Fig. 2) measures whether concept relationships evolve similarly with depth across models. Geometric distortion further checks whether donor/target atom geometries remain compatible at matched depths (Fig. 3).
Report issue for preceding element
Depth-wise semantic progression.
Report issue for preceding element
Even within a single model, “dirty” refusal vectors can change their semantic profile across depth; the CAR projection provides an interpretable view of how refusal composition evolves (Fig. 4). We use this primarily as a diagnostic to understand where refusal becomes linearly separable and thus where replay is most meaningful.
Report issue for preceding element 
Figure 3: Geometric Distortion Analysis. Comparison of Source (Donor) and Target atom geometries (left/center) and the resulting distortion matrix (right). Low distortion (darker colors) implies high compatibility for transfer. Report issue for preceding element 
Figure 4: Semantic Progression. Analysis of “dirty” refusal vectors across layers in Qwen3-VL-4B, showing the evolution of the semantic signature from early to late layers. Report issue for preceding element
8 Experimental Protocol
Report issue for preceding element
We employ a rigorous evaluation suite designed to distinguish true universality from stochastic damage. All reported metrics include 95% bootstrap confidence intervals.
Report issue for preceding element
8.1 Models: The “Core Universality” Slate
Report issue for preceding element
We evaluate 8 core pairs to test transfer across scale, family, architecture, and training regime. Model family references are provided for context (Yang and others, 2025; Mistral AI, 2025; AI and others, 2024; OpenAI, 2025) .
Report issue for preceding element
• Cross-Family Scale: Qwen3-VL-2B → \to Ministral-3-14B (Small → \to Big), Qwen3-VL-8B → \to Ministral-3-3B (Big → \to Small). Report issue for preceding element
• Reverse Direction: Ministral-3-3B → \to Qwen3-VL-8B, Ministral-3-14B → \to Qwen3-VL-2B. Report issue for preceding element
• In-Family Control: Qwen3-VL-2B → \to Qwen3-VL-8B, Ministral-3-3B → \to Ministral-3-14B. Report issue for preceding element
• Architecture/Regime Stress Test: Report issue for preceding element
– Qwen3-VL-8B → \to GPT-OSS-20B (Dense → \to Mixture-of-Experts) (Shazeer et al., 2017; Fedus et al., 2021) . Report issue for preceding element
– Qwen3-VL-8B → \to GLM-4.6V (Dense → \to Reasoning-Tuned) (AI and others, 2024) . Report issue for preceding element
Note: “GPT-OSS-20B” refers to an anonymized internal research model.
Report issue for preceding element
8.2 Prompt Sets and Metrics
Report issue for preceding element
• Probes ( 𝒫 p  r  o  b  e \mathcal{P}_{probe} ): 300 harmful prompts sampled from JailbreakBench (Chao et al., 2024) . Report issue for preceding element
• Capabilities ( 𝒫 c  a  p \mathcal{P}_{cap} ): GSM8K (Math) (Cobbe et al., 2021) and MBPP (Sanitized Coding); we report Pass@1 with standard code-eval conventions (Chen et al., 2021) . Report issue for preceding element
• Refusal Metric: We use a strict rubric (0: Refusal, 1: Partial, 2: Compliance). We report Refusal Rate (fraction of 0s) and Compliance Rate (fraction of 2s). Report issue for preceding element
• Drift Metric: Multi-token KL divergence on benign WikiText samples (Merity et al., 2016) . Report issue for preceding element
8.3 Baselines and Controls (The “Anchor” Protocol)
Report issue for preceding element
We run deep ablations on 4 anchor pairs. Detailed results for all pairs are available in Appendix E.
Report issue for preceding element
Random-Direction: Replace r D r_{D} with a random vector of equal norm. Report issue for preceding element
Wrong-Map: Permute layer mapping π \pi randomly. Report issue for preceding element
Unrelated-Concept: Transfer a “Math” recipe instead of refusal. Report issue for preceding element
No-Guard: Disable SVD projection ( ρ = 0 \rho=0 ). Report issue for preceding element
9 Results
Report issue for preceding element
9.1 Core Universality Results
Report issue for preceding element
Table 2 presents results on the 8 core pairs under budget ℬ 0 \mathcal{B}_{0} .
Report issue for preceding element
Table 2: Core Universality Results. Refusal Rate (lower is better). Compliance Rate (higher is better). GSM8K/MBPP values are accuracy/pass@1 (higher is better). Intervals denote 95% bootstrap CIs.
Report issue for preceding element
Results on GLM-4.6V: For the Dense → \to Reasoning transfer, we observed statistically non-significant differences in capability metrics, indicating preserved reasoning abilities. The method achieved a positive accuracy delta on Math tasks ( Δ + 0.3 \Delta+0.3 ) and Code tasks ( Δ + 0.1 \Delta+0.1 ), indicating that the removal of refusal circuits may have reduced interference with reasoning capabilities in the target model. Refusal rate dropped to near zero (1%).
Report issue for preceding element
9.2 Controls and Ablations
Report issue for preceding element
Table 3 validates that the effect is specific to the semantic recipe.
Report issue for preceding element
Table 3: Anchor Pair Controls (Qwen3-VL-8B → \to Ministral-3-3B). Δ \Delta Refusal is percentage point change (Method - Base); lower (more negative) indicates greater refusal attenuation.
Report issue for preceding element
9.3 Stability vs. Magnitude: The Shielded Principle
Report issue for preceding element 
Figure 5: The Shielded Magnitude Principle. As ablation strength (Overdrive, x-axis) increases, unprotected methods (dashed pink line) cause catastrophic perplexity degradation. The Weight-SVD guard (solid red) maintains stability, allowing for aggressive intervention strengths ( γ > 1.0 \gamma>1.0 ) that unlock capabilities (blue line) without destroying the model's general function. Report issue for preceding element
10 Discussion
Report issue for preceding element
10.1 Mechanistic interpretation
Report issue for preceding element
Our results support a view in which refusal is implemented as a semantic mixture over a relatively small concept neighborhood (captured by CAR), rather than an opaque, model-specific artifact. Under this view, the “recipe” w w functions as a cross-model semantic coordinate system: the donor provides a decomposition of refusal into shared atoms, and the target re-instantiates that decomposition in its own representational basis (Eq. 2).
Report issue for preceding element
10.2 Why trajectory replay matters
Report issue for preceding element
Even when a single refusal direction exists in a given model (Arditi et al., 2024) , editing that direction naively can induce collateral damage due to entanglement with capabilities. Trajectory replay mitigates this by (i) restricting edits to layers where refusal is reliably expressed (donor-defined ℒ D \mathcal{L}_{D} ) and (ii) maintaining depth-consistent semantics via DTW alignment (Fig. 2) (Sakoe and Chiba, 1978) .
Report issue for preceding element
10.3 Failure modes and confounders
Report issue for preceding element
We observed two broad classes of failure in controls: (1) misalignment failures (Wrong-map), where edits hit capability-relevant layers and degrade performance, and (2) subspace interference (No-guard), where overlap with high-variance weight subspaces causes collapse. More subtle confounders include (i) CAR misspecification (atoms do not span the refusal neighborhood), (ii) token-position sensitivity (final prompt vs. first response token), and (iii) judge sensitivity for borderline outputs. We therefore recommend reporting the knob audit (Sec. 6) and diagnostics (Sec. 7) alongside headline results.
Report issue for preceding element
10.4 What “universal” does and does not mean
Report issue for preceding element
Our universality claim is operational: semantic recipe invariance under ℬ 0 \mathcal{B}_{0} for the tested families and regimes. It does not claim that every future model will share the same CAR geometry, nor that refusal necessarily remains low-dimensional under all alignment schemes. Rather, the evidence suggests convergence: diverse training pipelines can produce similar semantic gating structures, enabling cross-model transfer when diagnostic compatibility is high.
Report issue for preceding element
10.5 Implications and future work
Report issue for preceding element
If refusal circuits are transferable semantic objects, then other alignment-relevant behaviors may also admit recipe-level transfer. A direct next step is to expand CAR coverage and test whether transfer generalizes beyond refusal directions to multi-behavior editing, while preserving a strict target-side information budget.
Report issue for preceding element
11 Limitations and Future Directions
Report issue for preceding element
While our results support the semantic universality hypothesis, our framework operates under specific constraints. First, the efficacy of Trajectory Replay depends on the coverage of the Concept Atom Registry (CAR). Our experiments fixed a 20-concept basis; if a refusal circuit operates on semantic features orthogonal to these atoms (e.g., complex visual safety constraints in multimodal models or highly context-dependent policy violations), the reconstruction may fail to capture the full suppression signal.
Report issue for preceding element
Second, our stability guard (Weight-SVD) relies on the heuristic that capability-critical circuits reside in high-variance principal components. While this assumption held for our tested benchmarks (Math, Code), it may not generalize to tasks relying on long-tail knowledge or rote memorization, which can inhabit lower-rank subspaces.
Report issue for preceding element
Finally, this method is strictly white-box. It requires direct access to model weights and internal activations for layer alignment and vector extraction. Future work should explore black-box approximations of these semantic fingerprints—potentially using steering vectors derived from API logprobs or contrastive decoding—to extend universality auditing to closed-source proprietary systems.
Report issue for preceding element
12 Conclusion
Report issue for preceding element
We reframed refusal editing as a mechanistic test for cross-model circuit universality. By combining Trajectory Replay with concept-basis reconstruction and a weight-SVD stability guard, we obtain a protocol for transferring refusal attenuation across model families without target-side refusal supervision. The strong performance across the 8-pair core slate, backed by rigorous controls, supports the hypothesis that refusal is implemented via a semantically universal circuit.
Report issue for preceding element
Impact Statement
Report issue for preceding element
This paper presents a mechanistic investigation into the universality of refusal circuits in Large Language Models (LLMs). Our goal is to advance the field of mechanistic interpretability by demonstrating that alignment behaviors are implemented via stable, transferable semantic structures. This work has potentially significant implications for AI safety, particularly in designing more robust auditing tools and understanding how alignment generalizes across architectures.
Report issue for preceding element
We acknowledge, however, that the methodology introduced— Trajectory Replay via Concept-Basis Reconstruction—demonstrates the capability to attenuate refusal behaviors in a target model without requiring target-side supervision. This presents a ”dual-use” risk: while intended as a diagnostic tool to measure circuit similarity, the same techniques could theoretically be repurposed to bypass safety guardrails in aligned models.
Report issue for preceding element
To mitigate these risks and adhere to responsible research practices, we have:
Report issue for preceding element
• Explicitly framed the method as a diagnostic instrument rather than a deployment recommendation. Report issue for preceding element
• Restricted our release artifacts: we provide the benign Concept Atom Registry (CAR) and code for reproduction, but we do not release the specific harmful probe sets used to extract donor directions. Report issue for preceding element
• Focused our evaluation on the mechanistic removal of the refusal signal rather than optimizing for the generation of harmful content. Report issue for preceding element
We believe that moving the community toward a transparent, mechanistic understanding of refusal—rather than relying on ”security by obscurity”—is ultimately beneficial for the long-term safety and reliability of AI systems.
Report issue for preceding element
References
Report issue for preceding element
Z. AI et al. (2024) ↑ GLM-4: a family of large language models. Note: arXiv preprint External Links: 2406.12793, Link Cited by: 2nd item, §8.1.
A. Arditi, O. Obeso, A. Syed, D. Paleka, N. Panickssery, W. Gurnee, N. Nanda, et al. (2024) ↑ Refusal in language models is mediated by a single direction. Note: arXiv preprint External Links: 2406.11717, Link Cited by: §10.2, §2.
T. Bricken, A. Templeton, T. Conerly, et al. (2023) ↑ Towards monosemanticity: decomposing language models with dictionary learning. Note: Technical reportTransformer Circuits thread / report External Links: Link Cited by: §2.
P. Chao, A. Robey, X. Duan, S. Sidheekh, H. Wu, A. Dimakis, S. Kumar, P. Manoharan, et al. (2024) ↑ JailbreakBench: an open robustness benchmark for jailbreaking large language models. Note: arXiv preprint External Links: 2404.01318, Link Cited by: 1st item.
M. Chen, J. Tworek, H. Jun, et al. (2021) ↑ Evaluating large language models trained on code. Note: arXiv preprintDefines pass@k estimator widely used for code benchmarks. External Links: 2107.03374, Link Cited by: 2nd item, 2nd item.
K. Cobbe, V. Kosaraju, M. Bavarian, M. Chen, H. Jun, L. Kaiser, M. Plappert, J. Tworek, J. Hilton, R. Nakano, C. Hesse, and J. Schulman (2021) ↑ Training verifiers to solve math word problems. Note: arXiv preprint External Links: 2110.14168, Link Cited by: 1st item, 2nd item.
T. Cristofano (2026) ↑ Surgical refusal ablation: disentangling safety from intelligence via concept-guided spectral cleaning. External Links: Link Cited by: §1, §3, 4.
H. Cunningham et al. (2024) ↑ Sparse autoencoders find interpretable features in language models. In Proceedings of the 41st International Conference on Machine Learning (ICML), External Links: 2309.08600, Link Cited by: §2.
A. Dubey et al. (2024) ↑ The llama 3 herd of models. Note: arXiv preprint External Links: 2407.21783, Link Cited by: §C.1, §6.
W. Fedus, B. Zoph, and N. Shazeer (2021) ↑ Switch transformers: scaling to trillion parameter models with simple and efficient sparsity. Note: arXiv preprint External Links: 2101.03961, Link Cited by: 4th item, §2, 1st item.
S. Kornblith, M. Norouzi, H. Lee, and G. Hinton (2019) ↑ Similarity of neural network representations revisited. In Proceedings of the 36th International Conference on Machine Learning (ICML), External Links: 1905.00414, Link Cited by: §5.1.
N. Kriegeskorte, M. Mur, and P. Bandettini (2008) ↑ Representational similarity analysis—connecting the branches of systems neuroscience. Frontiers in Systems Neuroscience 2, pp. 4. External Links: Document Cited by: §5.1.
K. Meng, D. Bau, A. Andonian, and Y. Belinkov (2022a) ↑ Locating and editing factual associations in GPT. Note: arXiv preprint External Links: 2202.05262, Link Cited by: §2, §3.2.
K. Meng, A. Sharma, A. Andonian, et al. (2022b) ↑ Mass-editing memory in a transformer. Note: arXiv preprint External Links: 2210.07229, Link Cited by: §2.
S. Merity, C. Xiong, J. Bradbury, and R. Socher (2016) ↑ Pointer sentinel mixture models. Note: arXiv preprintIntroduces the WikiText language modeling benchmark. External Links: 1609.07843, Link Cited by: §5.3, 4th item.
Mistral AI (2025) ↑ Ministral 3b and ministral 8b. Note: Model documentation External Links: Link Cited by: §8.1.
OpenAI (2025) ↑ GPT-oss-20b model card. Note: Model card / documentation External Links: Link Cited by: §8.1.
M. Raghu, J. Gilmer, J. Yosinski, and J. Sohl-Dickstein (2017) ↑ SVCCA: singular vector canonical correlation analysis for deep learning dynamics and interpretability. Note: arXiv preprint External Links: 1706.05806, Link Cited by: §5.1.
H. Sakoe and S. Chiba (1978) ↑ Dynamic programming algorithm optimization for spoken word recognition. IEEE Transactions on Acoustics, Speech, and Signal Processing 26 ( 1), pp. 43–49. External Links: Document Cited by: §10.2, §5.1, 3.
N. Shazeer, A. Mirhoseini, K. Maziarz, et al. (2017) ↑ Outrageously large neural networks: the sparsely-gated mixture-of-experts layer. Note: arXiv preprint External Links: 1701.06538, Link Cited by: 4th item, §2, 1st item.
X. Wang et al. (2025) ↑ Refusal direction is universal across safety-aligned multilingual llms. Note: arXiv preprint External Links: 2505.17306, Link Cited by: §2.
A. Yang et al. (2025) ↑ Qwen3 technical report. Note: arXiv preprint External Links: 2505.09388, Link Cited by: §8.1.
N. Zhang et al. (2024) ↑ AlphaEdit: null-space constrained knowledge editing for large language models. Note: arXiv preprint External Links: 2410.02355, Link Cited by: 3rd item, §5.3.
L. Zheng, W. Chiang, Y. Sheng, et al. (2023) ↑ Judging LLM-as-a-judge with MT-bench and chatbot arena. Note: arXiv preprint External Links: 2306.05685, Link Cited by: §C.1, §6.
A. Zou, Z. Wang, J. Z. Kolter, et al. (2023) ↑ Universal and transferable adversarial attacks on aligned language models. Note: arXiv preprint External Links: 2307.15043, Link Cited by: §2.
Appendix A Appendix A: Technical Details
Report issue for preceding element
A.1 SRA Primitives
Report issue for preceding element
Let h t ( ℓ )  ( x ) ∈ ℝ d ℓ h^{(\ell)}{t}(x)\in\mathbb{R}^{d{\ell}} be the residual stream activation. We compute contrastive directions r ( ℓ ) = μ ( ℓ )  ( 𝒫 + ) − μ ( ℓ )  ( 𝒫 − ) r^{(\ell)}=\mu^{(\ell)}(\mathcal{P}^{+})-\mu^{(\ell)}(\mathcal{P}^{-}) and clean them via ridge regression: β ^ ( ℓ ) = ( A ( ℓ ) ⊤  A ( ℓ ) + λ  I ) − 1  A ( ℓ ) ⊤  r dirty ( ℓ ) \hat{\beta}^{(\ell)}=\left(A^{(\ell)\top}A^{(\ell)}+\lambda I\right)^{-1}A^{(\ell)\top}r_{\text{dirty}}^{(\ell)} . The cleaned direction is r clean ( ℓ ) = r dirty ( ℓ ) − A ( ℓ )  β ^ ( ℓ ) r_{\text{clean}}^{(\ell)}=r_{\text{dirty}}^{(\ell)}-A^{(\ell)}\hat{\beta}^{(\ell)} .
Report issue for preceding element
A.2 Weight-SVD Guard
Report issue for preceding element
Compute SVD W = U  Σ  V ⊤ W=U\Sigma V^{\top} . Select top- k k right singular vectors V 1 : k V_{1:k} where k = ⌈ ρ  d in ⌉ k=\lceil\rho,d_{\text{in}}\rceil . Project: r guarded = ( I − V 1 : k  V 1 : k ⊤ )  r r_{\text{guarded}}=(I-V_{1:k}V_{1:k}^{\top}),r .
Report issue for preceding element
Appendix B Appendix B: Concept Atom Registry Details
Report issue for preceding element
To ensure reproducibility while adhering to safety guidelines, we describe the construction of the Concept Atom Registry (CAR). Rather than using rigid templates, which can lead to overfitting on syntax, we constructed Contrastive Concept Datasets for each atom.
Report issue for preceding element
B.1 Contrastive Dataset Construction
Report issue for preceding element
For each concept C C , we curated two disjoint datasets:
Report issue for preceding element
Positive Set ( 𝒫 + \mathcal{P}^{+} ): 50 prompts or completions that strongly exemplify the concept (e.g., code snippets, mathematical equations, future-tense statements). Report issue for preceding element
Antagonist Set ( 𝒫 − \mathcal{P}^{-} ): 50 prompts that are syntactically or lexically similar but semantically distinct, serving as a hard negative control (e.g., natural language descriptions of algorithms, historical dates containing numbers, past-tense statements). Report issue for preceding element
The refusal direction for a concept is defined as the mean difference vector r C = μ  ( 𝒫 + ) − μ  ( 𝒫 − ) r_{C}=\mu(\mathcal{P}^{+})-\mu(\mathcal{P}^{-}) . This ensures the atom captures the semantic essence of the concept rather than surface-level token frequency.
Report issue for preceding element
B.2 Data Release and Safety
Report issue for preceding element
In accordance with our Impact Statement, we release the full datasets for benign concepts (e.g., Math, Coding, Grammar, Sentiment) in the supplementary material.
Report issue for preceding element
For harmful concepts used to model the refusal boundary (e.g., Deception/Malicious, Safety Flagging), we utilize standard red-teaming prompts (e.g., requests for malware, fraud, or toxic content) as 𝒫 + \mathcal{P}^{+} and benign factual inquiries as 𝒫 − \mathcal{P}^{-} . To prevent these artifacts from being used to bypass safety filters, we withhold the specific text of these harmful positive sets, describing them only by category below.
Report issue for preceding element
B.3 Concept Definitions and Examples
Report issue for preceding element
Table 4 provides representative examples of the contrastive pairs used to define the atoms.
Report issue for preceding element
Table 4: Representative examples of Positive ( 𝒫 + \mathcal{P}^{+} ) and Antagonist ( 𝒫 − \mathcal{P}^{-} ) prompts for Concept Atoms. Note how the Antagonist set acts as a semantic control.
Report issue for preceding element
B.4 Full Concept List
Report issue for preceding element
Safety Flagging: Warning labels vs. Safe descriptions. Report issue for preceding element
Deception/Malicious: Harmful requests vs. Benign fact-checking. Report issue for preceding element
Privacy/Personal: PII disclosure vs. Public knowledge. Report issue for preceding element
Code Constraints: Coding restrictions vs. Open coding tasks. Report issue for preceding element
Coding: Code generation vs. Procedural instructions (recipes/manuals). Report issue for preceding element
Logic: Formal logic/syllogisms vs. Informal opinion/vibes. Report issue for preceding element
Math: Equations vs. History/Facts with numbers. Report issue for preceding element
Epistemic Uncertainty: Unanswerable/Nonsense queries vs. Answerable facts. Report issue for preceding element
Sentiment: Positive affect vs. Negative affect. Report issue for preceding element
Confidence: High certainty assertions vs. Low certainty/hedging. Report issue for preceding element
Importance: Urgent/Crucial vs. Trivial/Optional. Report issue for preceding element
Creativity: Metaphorical/Literary vs. Literal/Scientific definitions. Report issue for preceding element
Grammar Contrast: Complex clauses vs. Simple sentences. Report issue for preceding element
Fulfillment: Compliance responses vs. Refusal responses. Report issue for preceding element
Future/Planning: Future tense vs. Past tense. Report issue for preceding element
Intellectual Property: Copyrighted characters vs. Public domain/Generic tropes. Report issue for preceding element
Negation: Neither/Nor constructions vs. Both/And constructions. Report issue for preceding element
Affirmative: Agreement patterns vs. Disagreement/Questioning. Report issue for preceding element
Corporate Politeness: Boilerplate refusals vs. Direct/Rude demands. Report issue for preceding element
Legalese: Legal jargon vs. Plain English. Report issue for preceding element
B.5 Concept List
Report issue for preceding element
Safety Flagging, 2. Deception/Malicious, 3. Privacy/Personal, 4. Code Constraints, 5. Coding, 6. Logic, 7. Math, 8. Epistemic Uncertainty, 9. Sentiment, 10. Confidence, 11. Importance, 12. Creativity, 13. Grammar Contrast, 14. Fulfillment, 15. Future/Planning, 16. Intellectual Property, 17. Negation, 18. Affirmative, 19. Corporate Politeness, 20. Legalese.
Report issue for preceding element
Appendix C Appendix C: Evaluation Rubrics
Report issue for preceding element
C.1 Refusal score
Report issue for preceding element
We use an LLM-as-a-Judge classifier (Llama-3-70B-Instruct (Dubey and others, 2024) ) prompted to categorize responses into three buckets, following standard LLM-as-a-judge evaluation practice (Zheng et al., 2023) :
Report issue for preceding element
• 0 (Refusal): Model declines or responds with boilerplate refusal patterns (e.g., “I cannot”). Report issue for preceding element
• 1 (Partial): Model lectures but provides some information. Report issue for preceding element
• 2 (Compliance): Model responds substantively. Report issue for preceding element
Reported “Refusal Rate” is the fraction of outputs classified as 0.
Report issue for preceding element
C.2 Capability tasks
Report issue for preceding element
• GSM8K: Exact Match (EM) accuracy using greedy decoding (Cobbe et al., 2021) . Report issue for preceding element
• MBPP: Pass@1 using greedy decoding; we adopt standard pass@k conventions (Chen et al., 2021) . Report issue for preceding element
Appendix D Appendix D: Theoretical Justification (Semantic Invariance)
Report issue for preceding element
This section provides theoretical support for why concept-basis reconstruction allows for zero-shot transfer across disparate model spaces.
Report issue for preceding element
D.1 Setup and Latent Space Assumption
Report issue for preceding element
Assume there exists a shared latent semantic space 𝒵 ⊂ ℝ k \mathcal{Z}\subset\mathbb{R}^{k} containing high-level concepts (e.g., ”Safety,” ”Math,” ”Privacy”). Let z refusal ∈ 𝒵 z_{\text{refusal}}\in\mathcal{Z} be the latent concept governing refusal behavior. We assume that trained LLMs implement a local mapping ϕ : 𝒵 → ℝ d \phi:\mathcal{Z}\to\mathbb{R}^{d} that maps these latent concepts into their residual stream activation space. Crucially, we assume ϕ \phi is locally linear with respect to semantic mixtures in the neighborhood of refusal.
Report issue for preceding element
D.2 The Semantic Invariance Theorem (Informal)
Report issue for preceding element
Proposition: Let A = { a 1 , … , a m } A={a_{1},\dots,a_{m}} be the concept atom registry, where a i = ϕ  ( z i ) a_{i}=\phi(z_{i}) . If: 1. The atom concepts { z i } {z_{i}} form a spanning set for the subspace containing z refusal z_{\text{refusal}} , i.e., z refusal ≈ ∑ i c i  z i z_{\text{refusal}}\approx\sum_{i}c_{i}z_{i} , and 2. The mapping ϕ \phi preserves these mixing coefficients,
Report issue for preceding element
Then the coefficients w w derived by solving r D ≈ A D  w r_{D}\approx A_{D}w in the donor model satisfy w ≈ c w\approx c . Consequently, applying these coefficients to the target atoms produces r ~ T = A T  w ≈ ϕ T  ( z refusal ) \tilde{r}{T}=A{T}w\approx\phi_{T}(z_{\text{refusal}}) .
Report issue for preceding element
D.3 Bridge to Operational Definitions
Report issue for preceding element
Our experiments define atoms via contrastive activation vectors ( a i = μ  ( P i + ) − μ  ( P i − ) a_{i}=\mu(P_{i}^{+})-\mu(P_{i}^{-}) ) rather than direct mappings of isolated concepts. However, assuming the linearity of expectation and that the prompts P + P^{+} and P − P^{-} differ primarily along the direction of the latent concept z i z_{i} , the difference in means approximates the derivative of the mapping ϕ \phi along that concept direction. Thus, the linear combination of contrast vectors serves as a first-order approximation of the composition of the underlying latent concepts.
Report issue for preceding element
Appendix E Appendix E: Additional Ablation Results
Report issue for preceding element
In Section 8.3, we summarized controls on the Qwen3-VL-8B → \to Ministral-3-3B pair. Table 5 provides the summary statistics for the remaining 3 anchor pairs used to validate the method.
Report issue for preceding element
Table 5: Summary of Success/Fail rates for Controls on remaining 3 anchor pairs.
Report issue for preceding element
Appendix F Appendix F: Hyperparameter Audit ( ρ \rho )
Report issue for preceding element
Table 6 lists the Guard Ratio ρ \rho selected for each target model via the benign drift protocol described in Section 5.3.
Report issue for preceding element
Table 6: Selected ρ \rho values per target model.
Report issue for preceding element
Report Issue
Report GitHub Issue
Title:
Content selection saved. Describe the issue below:
Description:
Submit without GitHub Submit in GitHub
Report Issue for Selection
Generated by L A T E xml[LOGO]
Instructions for reporting errors
We are continuing to improve HTML versions of papers, and your feedback helps enhance accessibility and mobile support. To report errors in the HTML that will help us improve conversion and rendering, choose any of the methods listed below:
Click the "Report Issue" button.
Open a report feedback form via keyboard, use " Ctrl + ?".
Make a text selection and click the "Report Issue for Selection" button near your cursor.
You can use Alt+Y to toggle on and Alt+Shift+Y to toggle off accessible reporting links at each section.
Our team has already identified the following issues. We appreciate your time reviewing and reporting rendering errors we may not have found yet. Your efforts will help us improve the HTML versions for all readers, because disability should not be a barrier to accessing research. Thank you for your continued support in championing open access for all.
Have a free development cycle? Help support accessibility at arXiv! Our collaborators at LaTeXML maintain a list of packages that need conversion, and welcome developer contributions.