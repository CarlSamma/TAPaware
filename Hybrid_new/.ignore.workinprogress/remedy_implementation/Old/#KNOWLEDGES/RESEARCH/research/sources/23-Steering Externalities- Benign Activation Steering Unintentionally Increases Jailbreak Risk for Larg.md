> Source: https://arxiv.org/html/2602.04896

Steering Externalities: Benign Activation Steering Unintentionally Increases Jailbreak Risk for Large Language Models
logo Back to arXiv  
logo Back to arXiv
This is experimental HTML to improve accessibility. We invite you to report rendering errors. Use Alt+Y to toggle on accessible reporting links and Alt+Shift+Y to toggle off. Learn more about this project and help improve conversions.
Why HTML? Report Issue Back to Abstract Download PDF 
Table of Contents
Abstract
1 Introduction
2 Related Work
3 Steering Setups and Jailbreak Evaluation
3.1 Activation steering
3.2 Representative benign steering workflows
3.3 Jailbreak evaluation and threat model
4 Experiments
4.1 Experimental Setup
4.2 Benchmark-only Evaluation: Utility Gains and Intrinsic Vulnerability Evaluation
4.3 Synergistic Vulnerability Evaluation: Benign Steering Amplifies Jailbreak Vulnerability
5 Why Would Activation Steering Cause Misalignment?
5.1 Bypassing the Refusal Gate via Autoregressive Inertia
5.2 Token-level Evidence: Per-Token KL Divergence Analysis
5.3 Representation-level Evidence: Benign Steering “Obscure” Harmful Prompts in Hidden Space
6 Discussions
7 Conclusion
A Comparison with Prior Work on Steering and Alignment
B Implementation Details
B.1 Steering Vector Generation
B.2 Hyperparameter settings
B.3 Evaluation of the utility
C Additional Safety Benchmark: Harmful SorryBench (No Jailbreak)
D Per-token KL Divergence on Gemma-7B-it model
E Qualitative Analysis of Steering
F Representation-level analysis (additional visualizations)
F.1 Limitations of Representation-level Visualizations
G STEER-BIND Results
H Win-Rate measurement of Compliance Steering
I Measuring Refusal Rate by using an additional judge
J Intrinsic and Synergistic Vulnerabilities on additional LLMs
K Numerical value of Intrinsic and Synergistic Vulnerabilities
L Anonymous Repository
References
License: CC BY 4.0
arXiv:2602.04896v1 [cs.CR] 03 Feb 2026
Steering Externalities: Benign Activation Steering Unintentionally Increases Jailbreak Risk for Large Language Models
Report issue for preceding element
Chen Xiong Zhiyuan He Pin-Yu Chen Ching-Yun Ko Tsung-Yi Ho
Report issue for preceding element
Abstract
Report issue for preceding element
Activation steering is a practical post-training model alignment technique to enhance the utility of Large Language Models (LLMs). Prior to deploying a model as a service, developers can steer a pre-trained model toward specific behavioral objectives, such as compliance or instruction adherence, without the need for retraining. This process is as simple as adding a steering vector to the model's internal representations. However, this capability unintentionally introduces critical and under-explored safety risks. We identify a phenomenon termed Steering Externalities, where steering vectors derived from entirely benign datasets—such as those enforcing strict compliance or specific output formats like JSON—inadvertently erode safety guardrails. Experiments reveal that these interventions act as a force multiplier, creating new vulnerabilities to jailbreaks and increasing attack success rates to over 80% on standard benchmarks by bypassing the initial safety alignment. Ultimately, our results expose a critical blind spot in deployment: benign activation steering systematically erodes the “safety margin,” rendering models more vulnerable to black-box attacks and proving that inference-time utility improvements must be rigorously audited for unintended safety externalities.
Report issue for preceding element
Machine Learning, ICML
1 Introduction
Report issue for preceding element
Large language models (LLMs) (Vaswani et al., 2023) are commonly deployed as instruction-following assistants (Bai et al., 2022a, c) , where users expect helpful, coherent, and instruction-adherent responses, while providers rely on a combination of behavioral controls — such as refusal mechanisms, persona conditioning, and output-format constraints — to allow flexibility in adapting deployed models. Maintaining this balance is challenging: training-based alignment mechanisms such as supervised fine-tuning (Zhang et al., 2024; Tajwar et al., 2024) and preference optimization (Askell et al., 2021; Bai et al., 2022b; Ouyang et al., 2022) can improve refusal behavior, yet models remain vulnerable to prompt-based jailbreaks and automated red-teaming procedures (Zou et al., 2023; Liu et al., 2024; Xiong et al., 2025) . At the same time, practitioners increasingly seek methods to control model behavior without retraining, both for cost reasons and for rapid iteration.
Report issue for preceding element
Activation steering (Turner et al., 2024) has emerged as a practical post-training control primitive for LLMs. Rather than modifying model weights, activation steering injects vectors into the model's hidden states at inference time, biasing generation toward desired attributes such as increased helpfulness, stylistic consistency, persona conditioning (e.g., adopting a specific role or tone) (Chen et al., 2025) , or stricter instruction adherence (e.g., enforcing structured outputs like JSON) (Stolfo et al., 2025) . Because these interventions operate post hoc and do not require retraining, activation steering enables rapid, cost-effective behavioral customization, making it attractive in real-world deployment settings where model service providers must simultaneously support multiple control requests for different users.
Report issue for preceding element 
Figure 1: The top left panel illustrates the Model Developer's perspective, where benign activation steering (e.g., Compliance or JSON vectors) is injected into the LLM's hidden states ( h 0  …  h m h_{0}\ldots h_{m} ) to enhance utility at inference time. The bottom left panel depicts the Attacker's Move, showing how this steered model becomes a target for black-box jailbreak attacks like PAIR, CoP, and TAP (Chao et al., 2023; Xiong et al., 2025; Mehrotra et al., 2023) . We distinguish two evaluation regimes: (i) Benchmark-only, which evaluates on the original harmful prompts provided by the dataset (direct harmful requests; no prompt rewriting), and (ii) Synergistic Vulnerability, which runs an attack algorithm that iteratively revises the harmful request based on the target steered model's feedback. The right section quantifies these averaged externalities across the three tested models (i.e., Llama-2-7B-Chat, Llama-3-8B-Instruct and Gemma-7B-it). The results show that while steering successfully modifies behavior—such as increasing harmless non-refusal rates (i.e. 100% minus refusal rates) for benign queries or improving JSON extraction—it unintentionally compromises safety. This leads to higher Attack Success Rates on harmful queries compared to the original models, an effect that is amplified under jailbreak attacks. Report issue for preceding element
Existing studies that examine activation steering and safety largely adopt an attacker or diagnostic perspective: they intentionally apply steering vectors to probe or bypass refusal mechanisms (Arditi et al., 2024; Ghandeharioun et al., 2024; Korznikov et al., 2025) . In these settings, activation steering is treated as an attack vector that can be arbitrarily used by a malicious actor, and therefore, safety degradation is an expected outcome. In contrast, we study activation steering from the perspective of a model developer, where steering is applied to improve benign utility and is not accessible to attackers. As illustrated in Figure 1, our focus is on studying how such developer-side, utility-driven steering can nonetheless introduce unintended safety regressions, increasing susceptibility to jailbreak attacks even though the steering mechanism is not adversarially controlled. Our study complements prior work which shows even benign operations — post fine-tuning (Qi et al., 2023) or preference optimization (Razin et al., 2025) — can unintentionally degrade safety alignment and increase vulnerability to misuse.
Report issue for preceding element
These results motivate a broader question: Do steering vectors learned from benign instruction data accidentally have any other side-effects? In this paper, we present a new practical safety risk that we termed steering externalities: unintended safety regressions that arise when activation steering is optimized for benign utility. Concretely, we focus on realistic workflows: a model developer uses a benign dataset and tries to make the model “more compliant” (Lee et al., 2025) or produce “more formatted responses” (Stolfo et al., 2025) (e.g., more likely to produce direct, helpful answers, or using JSON as output format) by learning a steering direction from either contrastive examples or instruction-following. Despite these benign objectives, we find that the resulting steered models exhibit substantial safety degradation, with attack success rates under State-Of-The-Art (SOTA) jailbreak methods increasing by up to 99% compared to the original aligned models.
Report issue for preceding element
Why would benign activation steering compromise safety? Our central hypothesis is that benign activation steering compromises safety by systematically biasing the model's early-token distribution toward non-refusal trajectories, thereby reducing the “safety margin” that alignment relies on to refuse harmful requests. Specifically, utility-oriented steering (e.g., compliance or formatting) increases the likelihood of affirmative or structured openings in the first few generated tokens, implicitly suppressing refusal-preferring prefixes that safety training places disproportionate weight on. As a result, even when the steering objective is benign, the model becomes more likely to enter a non-refusal mode at generation onset, making it easier for adversaries to elicit disallowed behavior. Importantly, this effect does not require novel jailbreak techniques: a modest reduction in refusal robustness at the prefix level can substantially amplify the effectiveness of existing automated jailbreak pipelines. This vulnerability is exacerbated by modern jailbreak methods that rely on search (e.g., iterative rewriting, multi-step strategies, or agentic decomposition), where a model that is only slightly more willing to comply can become dramatically easier to jailbreak in practice.
Report issue for preceding element
Our paper makes three primary contributions:
Report issue for preceding element
Identification of Steering Externalities: We define and empirically demonstrate “steering externalities”, a phenomenon where activation steering optimized solely for benign utility (such as “compliance” or “Instruction-following”) systematically degrades safety alignment. We show that this trade-off is not limited to semantic steering but extends to syntactic formatting constraints, challenging the assumption that benign test-time model adaptation is inherently safe. Report issue for preceding element
Jailbreak Amplification Effect: We establish that benign steering acts as a “force multiplier” for adversarial attacks. Through comprehensive evaluation on Llama-2-7B-Chat, Llama-3-8B-Instruct, and Gemma-7B-it, we show that steering interventions drastically increase the Attack Success Rate (ASR) of black-box jailbreaks (CoP, PAIR, TAP), in some cases boosting ASR to nearly 99%, by eroding the model's safety margin. Report issue for preceding element
Mechanistic Explanation via Hidden Safety Fractures. We provide mechanistic evidence that benign activation steering induces an implicit domain shift in the model's internal state: it benignizes harmful requests by pushing their prompt representations toward harmless subspace, thereby shrinking the representational safety margin that normally triggers refusal. This shift manifests immediately at generation time as a concentrated change in the first few output tokens—token-wise KL spikes show that steering suppresses refusal-prefixed openings and increases the probability of a non-refusal start. Once the model is “tricked” into beginning in a benign-coded, non-refusal mode, autoregressive generation amplifies the effect and carries the trajectory toward harmful completion, even though no explicit safety mechanism is removed. Report issue for preceding element
Overall, our results complement and extend prior warnings that activation steering can compromise alignment safeguards, by showing that even steering learned exclusively from benign data and operated only by the model service provider for utility enhancement — can systematically increase practical jailbreakability. Based on our findings, we also provide discussions on possible mitigation strategies and potential research topics for future studies.
Report issue for preceding element
2 Related Work
Report issue for preceding element
Post-training behavior modification can occur either at inference time (e.g., activation steering interventions on hidden states) or at training time (e.g., fine-tuning or preference optimization). Across both regimes, recent work has shown that even targeted interventions can have non-obvious failure modes, including degraded safety alignment and increased susceptibility to adversarial use.
Report issue for preceding element
Training-time misalignment in fine-tuning and preference optimization. Complementary work shows that safety regressions can also arise during training-time customization, including in settings that are not intended to remove guardrails. Qi et al. ( 2023) find that fine-tuning aligned language models introduces a new attack surface: a small number of adversarially constructed fine-tuning examples can jailbreak safety protections, and even benign fine-tuning on commonly used utility datasets can inadvertently degrade safety alignment. Razin et al. ( 2025) analyze Direct Preference Optimization (DPO) and identify likelihood displacement, where preference margins increase while the likelihood of both preferred and dispreferred responses decreases; in catastrophic cases, probability mass can shift toward responses with opposite meaning. They show that this path can cause unintentional unalignment even if DPO is trained with the benign goal of refusing unsafe prompts.
Report issue for preceding element
Inference-time steering as an attacker. A growing body of work studies activation steering under an attacker framing, showing that steering directions can bypass or suppress refusal mechanisms. Arditi et al. ( 2024) identify a “refusal direction” whose removal induces compliance and whose addition induces refusal. Korznikov et al. ( 2025) show that steering can break safety even when the steering direction is not explicitly designed for jailbreaks (e.g., random directions or directions derived from SAE features), highlighting the fragility of safety under hidden-state interventions. Ghandeharioun et al. ( 2024) demonstrate that persona steering can elicit harmful behaviors more effectively than prompting, further emphasizing that inference-time control mechanisms can be misused to circumvent aligned behavior.
Report issue for preceding element
Steering externalities under utility-first deployment. In contrast to work that frames steering primarily as an attacker tool, our focus is on the common deployment setting where activation steering is applied by model developers to improve utility on benign tasks. We study steering externalities: unintended safety regressions that emerge despite utility-first intent and despite learning steering vectors from benign data (see Table 3). Further, we show that these regressions can compound with black-box jailbreak pipelines, amplifying attack success rates even when the steering intervention is not purposely designed for harmful behavior. While our analysis is strictly concerned with inference-time, post-training interventions, our findings parallel concerns raised in training-time customization—namely, that seemingly benign modifications can quietly erode safety guarantees—highlighting a broader fragility of alignment under post hoc control.
Report issue for preceding element
3 Steering Setups and Jailbreak Evaluation
Report issue for preceding element
We study steering externalities: safety regressions that arise when a developer applies benign, utility-motivated activation steering at inference time. Concretely, we focus on realistic workflows where steering vectors are learned from benign data to (a) reduce refusals on innocuous requests (Lee et al., 2025) or (b) enforce instruction-following on structured formatting such as JSON (Stolfo et al., 2025) , then deployed globally at inference time. Instead of introducing a new steering algorithm, our goal is to evaluate how these common interventions affect the safety margin of the LLMs under a composite jailbreak evaluation that combines intrinsic safety degradation and amplification under multiple black-box adaptive jailbreak attacks.
Report issue for preceding element
We evaluate safety in two regimes in the paper. Benchmark-only means we query the model using the original harmful prompts provided by the benchmark dataset (i.e., direct harmful requests, without any rewriting). Adaptive attack means we run a black-box jailbreak algorithm that iteratively revises the harmful request based on the steered model's feedback, producing an adapted adversarial prompt.
Report issue for preceding element
3.1 Activation steering
Report issue for preceding element
Let h t ( ℓ ) ∈ ℝ d h_{t}^{(\ell)}\in\mathbb{R}^{d} denote the residual-stream representation at layer ℓ \ell and token position t t in a decoder-only transformer. Activation steering adds a vector v ∈ ℝ d v\in\mathbb{R}^{d} during inference:
Report issue for preceding element
h ~ t ( ℓ ) = h t ( ℓ ) + α  v , \tilde{h}{t}^{(\ell)}=h{t}^{(\ell)}+\alpha v,
(1)
where α \alpha controls the intervention strength. This defines a steered next-token distribution p θ steer ( ⋅ ∣ x ≤ t ) ≠ p θ ( ⋅ ∣ x ≤ t ) p_{\theta}^{\text{steer}}(\cdot\mid x_{\leq t})\neq p_{\theta}(\cdot\mid x_{\leq t}) without changing model parameters.
Report issue for preceding element
3.2 Representative benign steering workflows
Report issue for preceding element
For model developers, a primary goal is to improve the controllability of LLMs. For instance, developers often want models to be more helpful when answering user requests. A viable path to achieve this is activation steering; specifically, steering the model in a more compliant direction can lower the refusal rate for benign prompts. To investigate this, we instantiate two steering workflows from prior work, chosen to span both semantic and syntactic notions of utility.
Report issue for preceding element
Compliance steering (STEER-COMPLIANCE). Following the behavior-vector construction procedure of Conditional Activation Steering (CAST) (Lee et al., 2025) , which extracts latent behavior directions by contrasting internal activations associated with different response modes, we form a contrastive dataset by pairing a benign instruction x i x_{i} with (i) a short refusal-prefixed continuation and (ii) a short compliance-prefixed continuation, and extract a layer-wise direction v refusal ( ℓ ) v_{\text{refusal}}^{(\ell)} that separates refusal vs. compliance in activation space (e.g., via Principal Component Analysis (PCA) on mean-centered residual activations). Because PCA directions are sign-indeterminate, we orient the vector so that positive steering increases compliance:
Report issue for preceding element
v comply ( ℓ ) = − v refusal ( ℓ ) . v_{\text{comply}}^{(\ell)}=-v_{\text{refusal}}^{(\ell)}.
(2)
Importantly, suppressing refusals is the intended utility effect on benign prompts. The externality we study is that the same global intervention can also suppress refusals on harmful prompts, and can compound with jailbreak search, increasing practical jailbreakability.
Report issue for preceding element
JSON-format steering (STEER-JSON). Following instruction-steering via difference-in-means, we build paired inputs ( x i , x i + ) (x_{i},x_{i}^{+}) where x i x_{i} is a base query and x i + x_{i}^{+} appends a JSON-format instruction. Let x i , ℓ x_{i,\ell} and x i , ℓ + x^{+}_{i,\ell} be residual-stream activations at layer ℓ \ell at the last input token. We compute the steering direction/vector as:
Report issue for preceding element
u ( ℓ ) = v ( ℓ ) ‖ v ( ℓ ) ‖ , v ( ℓ ) = 1 N  ∑ i = 1 N ( x i , ℓ + − x i , ℓ ) , u^{(\ell)}=\frac{v^{(\ell)}}{|v^{(\ell)}|},\qquad v^{(\ell)}=\frac{1}{N}\sum_{i=1}^{N}(x^{+}{i,\ell}-x{i,\ell}),
(3)
and apply the format-specific adaptive scaling proposed by Stolfo et al. ( 2025) as follows:
Report issue for preceding element
h ~ t ( ℓ ) = h t ( ℓ ) + c  u ( ℓ ) ; c = z ¯ − ⟨ h t ( ℓ ) , u ( ℓ ) ⟩ , z ¯ = 1 N  ∑ i = 1 N ⟨ x i , ℓ + , u ( ℓ ) ⟩ , \begin{split}\tilde{h}{t}^{(\ell)}&=h{t}^{(\ell)}+c,u^{(\ell)};\ c&=\bar{z}-\langle h_{t}^{(\ell)},u^{(\ell)}\rangle,~\bar{z}=\frac{1}{N}\sum_{i=1}^{N}\langle x^{+}_{i,\ell},u^{(\ell)}\rangle,\end{split}
(4)
where ⟨ ⋅ , ⋅ ⟩ \langle\cdot,\cdot\rangle denotes innner product. Unlike compliance steering, STEER-JSON is “non-safety-related” (a formatting constraint); our results test whether such syntactic steering can still disrupt the refusal trajectory and degrade safety.
Report issue for preceding element
3.3 Jailbreak evaluation and threat model
Report issue for preceding element
Threat model. To evaluate whether benign activation steering increases adversarial vulnerability, we adopt a black-box threat model. We treat the steered model—defined by fixed base parameters θ \theta together with a fixed, developer-controlled steering intervention—as the target system. The attacker has no access to or control over the steering mechanism, does not observe internal activations, and cannot modify the steering vector. Instead, the attacker adaptively executes jailbreak attempts by interacting with the model solely through input–output queries, as illustrated in Figure 1 (Attacker's Move). Given a harmful intent x x , an attack algorithm produces an adversarial prompt x adv x_{\text{adv}} . The model then generates under active steering:
Report issue for preceding element
y ∼ p θ steer ( ⋅ ∣ x adv ) . y\sim p_{\theta}^{\text{steer}}(\cdot\mid x_{\text{adv}}).
(5)
We evaluate both (i) intrinsic vulnerability of the steered model (without external attacks) and (ii) synergistic vulnerability when steering is combined with black-box jailbreak pipelines. In the latter setting, we instantiate the attack algorithm using three representative prompt-only methods, all of which operate without access to internal activations or control over the steering mechanism. Unless otherwise stated, the steering vector remains fixed throughout the attack process, and safety is assessed using the same downstream evaluation judge across all conditions.
Report issue for preceding element
Specifically, we consider:
Report issue for preceding element
∙ \bullet Composition-of-Principles (CoP) (Xiong et al., 2025) : an agentic workflow that combines multiple persuasive principles to find successful jailbreak prompts.
Report issue for preceding element
∙ \bullet Prompt Automatic Iterative Refinement (PAIR) (Chao et al., 2023) : an automatic black-box attack that iteratively optimizes prompts based on model responses.
Report issue for preceding element
∙ \bullet Tree of Attacks with Pruning (TAP) (Mehrotra et al., 2023) : an extension of PAIR that explores a tree of candidate jailbreak prompts via search and pruning.
Report issue for preceding element
In addition to measuring jailbreak success, we explicitly measure utility preservation under steering. This joint evaluation enables us to characterize steering externalities as a trade-off: steering improves benign utility while simultaneously increasing susceptibility to jailbreak attacks.
Report issue for preceding element
4 Experiments
Report issue for preceding element Table 1: Utility checks for benign steering. Compliance steering reduces refusals on harmless Alpaca prompts, and JSON-format steering increases JSON-valid outputs on IFEval.
| Model | Harmless Alpaca refusal ( ↓ \downarrow better utility) || IFEval JSON correctness ( ↑ \uparrow better utility) || | ^^ | Original | Compliance Steering | Original | JSON Steering | | --- | --- | --- | --- | --- | | Llama-2-7B-Chat | 9% | 6% | 61% | 74% | | Llama-3-8B-Instruct | 2% | 0% | 63% | 69% | | Gemma-7B-it | 18% | 1% | 69% | 81% |
Report issue for preceding element
4.1 Experimental Setup
Report issue for preceding element
Dataset: To generate STEER-COMPLIANCE vectors, we randomly sampled 100 benign instructions from Alpaca (Li et al., 2023) and paired each with both a refusal and a compliant response, following the procedure described in Sec. 3.2. For Instruction-Following Steering vectors—specifically for STEER-JSON—we randomly sampled 400 data instances containing JSON-specific instructions from the Instruction-Following Evaluation Dataset (IFEval) (Zhou et al., 2023) .
Report issue for preceding element
To measure benign utility preservation under steering, we (i) evaluated refusal rates on 100 harmless Alpaca prompts (compliance/helpfulness utility), and (ii) evaluated JSON validity on 100 prompts from IFEval (format-following utility). For both sets, we ensured that the evaluation prompts were distinct from those used for steering vector construction.
Report issue for preceding element
For our safety evaluation, we utilized the full HarmBench dataset (Mazeika et al., 2024) , which contains 400 harmful queries that cover a wide range of attack topics.
Report issue for preceding element
Large Language Models: Our experiments were conducted on three open-weight models: Llama-2-7B-Chat (Touvron et al., 2023) , Llama-3-8B-Instruct (Grattafiori et al., 2024) and Gemma-7B-it (Team et al., 2024) . A steered model refers to the corresponding base model augmented with a fixed steering vector; in all evaluations, this configuration was treated as a black-box target for jailbreak analysis.
Report issue for preceding element 
Report issue for preceding element Figure 2: Attack Success Rate (ASR) between original target LLMs and compliance steered LLMs as well as ASR by applying black-box jailbreak attack CoP on original and steered models respectively on 400 HarmBench data. After steering, all LLMs are more vulnerable to jailbreak attacks. Report issue for preceding element
Evaluation Protocol: To assess the utility of compliance ability of activation steering, we primarily focused on measuring the Refusal Rate. We evaluated by utilizing the fine-tuned DistilRoberta-Based model (ProtectAI.com, 2024) , which is a model that identifies rejections in LLMs' response. For instruction-following utility, we followed the same evaluation protocol as (Stolfo et al., 2025) that explicitly designs an evaluation function to judge whether the output response can be loaded as JSON formats. The details can be found in Appendix B. For measuring the jailbreak success, we evaluated the Attack Success Rate (ASR) metric with the Harmbench classifier, which is a carefully fine-tuned Llama-2-13B model to determine whether the jailbreak response is relevant to the original malicious query and harmful. A detailed description of the hyperparameter settings is provided in Appendix B.2.
Report issue for preceding element
4.2 Benchmark-only Evaluation: Utility Gains and Intrinsic Vulnerability Evaluation
Report issue for preceding element
We first confirmed that both steering interventions achieved their intended benign utility goals. As shown in Table 1, STEER-COMPLIANCE reduces refusals on harmless Alpaca prompts across all evaluated models, consistent with improved compliance/helpfulness. Similarly, STEER-JSON increases the fraction of JSON-valid outputs on IFEval, indicating improved format-following utility.
Report issue for preceding element
Benchmark-only safety evaluation (no jailbreak attack). Next, we evaluated intrinsic safety regressions in a benchmark-only setting: we prompted the model with harmful HarmBench queries directly (without any adaptive jailbreak algorithm) and measured ASR with the HarmBench classifier. Figure 2 (left) shows that both steering methods increased ASR relative to the original aligned models across all tested LLMs. Notably, STEER-COMPLIANCE yields the largest regressions (e.g., Llama-3-8B-Instruct increased from a 2% baseline ASR to 38.5%), while even purely syntactic STEER-JSON increased ASR substantially (e.g., Llama-2-7B-Chat increases from 0% to 11.5%). These results indicated that benign utility steering can itself constitute an intrinsic vulnerability—a form of steering externality—even before introducing any jailbreak attack procedure. In Appendix C, we also reported refusal-rate shifts on a different harmful benchmark, SorryBench (Xie et al., 2025) .
Report issue for preceding element
4.3 Synergistic Vulnerability Evaluation: Benign Steering Amplifies Jailbreak Vulnerability
Report issue for preceding element
Section 4.2 showed that benign steering increased vulnerability even without jailbreak attacks. Here, we evaluated whether steering amplifies black-box jailbreak pipelines such as CoP, PAIR, and TAP (Xiong et al., 2025; Chao et al., 2023; Mehrotra et al., 2023) on HarmBench.
Report issue for preceding element
Amplification of Existing Jailbreak Attacks.
Report issue for preceding element
We first examined CoP attack on 400 HarmBench samples. Figure 2 (right) revealed a compounding effect: steering made existing attacks significantly more potent.
Report issue for preceding element
For STEER-COMPLIANCE, the effect is drastic. In the case of Llama-2-7B-Chat, while the CoP attack alone achieved a 77% ASR, combining it with compliance steering pushed the ASR to a near-total compromise of 95%. Similarly, Gemma-7B-it reached an ASR of 93.5% under the combined setting. Crucially, this amplification is not limited to helpfulness optimization; STEER-JSON also acts as a force multiplier for jailbreaks. When the CoP attack is combined with JSON steering, Llama-2-7B-Chat sees its ASR rise to 88.75%, a significant jump over the baseline attack. Likewise, Gemma-7B-it reached an ASR of 90.3% under the combined condition. These results indicated that both steering lower the defense barrier, allowing jailbreak techniques more likely to succeed.
Report issue for preceding element
Generalization across Attack Methods. To ensure these findings are not specific to a single attack method, we extended our evaluation to the PAIR and TAP attacks on Llama-2-7B-Chat using a subset of 50 HarmBench samples. As detailed in Table 2, steering mechanisms visibly degraded the model's resistance to the PAIR attack. STEER-COMPLIANCE doubled the effectiveness of the attack on Llama-2-7B-Chat, raising the ASR from 10% to 20%. STEER-JSON also compromised safety, though to a lesser degree, increasing the ASR to 14%. Similarly, the TAP attack became more potent under steering influence. Compliance steering increased the success rate by 14%, resulting in a final ASR of 34%. JSON steering exhibits a similar trend, boosting the ASR to 26% (+6%). These results confirmed that even formatting-focused interventions can weaken the model's safety margin.
Report issue for preceding element
Our results show that activation steering—even for benign purposes—introduces severe safety risks, a phenomenon we term “steering externalities.” This technique inherently increases harmful output generation and amplifies vulnerability to adversarial jailbreaking attacks.
Report issue for preceding element
Table 2: Attack Success Rate (ASR) by applying black-box jailbreak attacks PAIR and TAP on original and steered models respectively on 50 Harmbench questions. After steering, all LLMs are more vulnerable to jailbreak attacks.
| Model | Attack Methods | Original | Compliance Steered | JSON Steered | | ^^ | ^^ | ASR | ASR | ASR | | --- | --- | --- | --- | --- | | Llama-2-7B-Chat | PAIR | 10% | 20% (+10) | 14% (+4) | | ^^ | TAP | 20% | 34% (+14) | 26% (+6) |
Report issue for preceding element
5 Why Would Activation Steering Cause Misalignment?
Report issue for preceding element
To understand why benign activation steering compromises safety in our experiments, we provide a mechanistic analysis at two coupled levels: (i) a token-level analysis of how steering reshapes the distribution over the first few generated tokens that decide whether the model enters a refusal or non-refusal mode (Sec. 5.1 and Sec. 5.2), and (ii) a representation-level analysis showing that steering shifts the hidden-state encodings of harmful prompts toward regions typically associated with harmless requests, reducing the effective safety margin in hidden space (Sec. 5.3).
Report issue for preceding element
5.1 Bypassing the Refusal Gate via Autoregressive Inertia
Report issue for preceding element
One plausible mechanism is that, because we inject the steering vector into the residual stream during decoding, activation steering can change the model's internal state—and thus the next-token distribution—from the very first generated token. Under autoregressive generation, this prefix-level shift can then propagate and yield a qualitatively different completion. Concretely, LLMs generate text autoregressively, where the probability of a full response y y given a harmful input x x factorizes over tokens y t y_{t} :
Report issue for preceding element
P  ( y ∣ x ) = ∏ t = 1 T P  ( y t ∣ x , y < t ) . P(y\mid x)=\prod_{t=1}^{T}P(y_{t}\mid x,y_{<t}).
(6)
Under the “Shallow Safety Alignment” hypothesis (Qi et al., 2024) , safety behavior is concentrated in a short prefix window t ∈ [ 1 , k ] t\in[1,k] that effectively decides whether the model enters a refusal or non-refusal mode. This lets us decompose generation into an early gate and a continuation phase:
Report issue for preceding element
P  ( y ∣ x ) = P  ( y ≤ k ∣ x ) ⏟ Refusal Gate ⋅ P  ( y > k ∣ x , y ≤ k ) ⏟ Autoregressive Inertia . P(y\mid x)=\underbrace{P(y_{\leq k}\mid x)}{\text{Refusal Gate}}\cdot\underbrace{P(y{>k}\mid x,y_{\leq k})}_{\text{Autoregressive Inertia}}.
(7)
A standard aligned model assigns high probability to refusal-prefixed openings in the first k k tokens; once a refusal prefix is sampled, the continuation distribution is conditioned on that prefix and naturally stays on a safe trajectory. Activation steering intervenes by shifting hidden states, and its most safety-critical effect can occur during this prefix decision: it moves probability mass away from refusal markers and toward compliant or structured openers, increasing the chance that the model begins in a non-refusal mode (quantified at the token level in Sec. 5.2). After this point, autoregressive inertia propagates the altered trajectory: later tokens are conditioned on the non-refusal prefix, and the model tends to continue coherently—potentially generating harmful content that was not deeply suppressed by training.
Report issue for preceding element
Importantly, observing token-level changes during generation is not sufficient to fully assess safety. Even if steering only alters the early prefix, the meaning of the response can continue to evolve as generation unfolds, and an apparently benign opening can still lead to an unsafe completion. This motivates a complementary representation-level perspective that evaluates the model after it has committed to a trajectory: activation steering can shift the hidden representations of harmful requests (and their evolving context) toward regions typically associated with harmless queries, thereby shrinking the safety margin in hidden space (Sec. 5.3). Taken together, token-level effects capture how steering influences decisions during autoregressive sampling, while representation-level effects capture how steering reshapes the semantic state after a trajectory is established—jointly explaining how benign steering can bypass refusal behavior without removing any explicit safety mechanism.
Report issue for preceding element
5.2 Token-level Evidence: Per-Token KL Divergence Analysis
Report issue for preceding element
We provide supporting evidence for this hypothesis by analyzing the distributional shift introduced by activation steering. Following the methodology of (Qi et al., 2024) , we calculated the per-token Kullback-Leibler (KL) divergence between the original aligned models and their steered counterparts for both Llama-3-8B-Instruct and Gemma-7B-it (in Appendix D). Rather than relying on an external harmful prompt–response corpus (HEx-PHI datasets), we construct a harmful prompt–response set from HarmBench to match the benchmark used throughout the paper: We use Mistral-7B-Instruct-v0.2 to generate on full harmful questions from Harmbench dataset and record the harmful responses (evaluated by the Harmbench classifier). Here we obtained 125 instruction and response pairs.
Report issue for preceding element
Figure 3 and Figure 6 in Appendix D show token-wise KL divergence between the original model and the steered model under STEER-COMPLIANCE and STEER-JSON, respectively. In both settings, the KL divergence is largest in the first few generated tokens (especially on harmful prompts) and then rapidly stabilizes. This pattern suggests that activation steering primarily perturbs the model during the critical prefix window where instruction-tuned models typically choose between a refusal template (e.g., “Sorry, I can't…”) and a compliant opener (e.g., “Sure—here is…”). Because generation is autoregressive, these early tokens effectively act as a mode-setting prefix: once steering shifts probability mass away from early refusal markers and toward a non-refusal opening, subsequent token distributions are conditioned on that new prefix and tend to continue along a more compliant trajectory, which can result in harmful completions. Importantly, this mechanism is not unique to explicitly “compliance”-oriented directions; even ostensibly benign JSON steering can be safety-relevant if it disrupts the usual refusal prefix/structure and prevents the model from entering the refusal trajectory in the first place. Overall, the early KL spikes provide empirical support that steering reduces the model's safety margin by inducing a distributional shift at the beginning of the response, which can induce a qualitatively different downstream generation trajectory.
Report issue for preceding element
We further illustrate this phenomenon with qualitative examples in Figure 9 and Figure 12 (Appendix E), which compare outputs for identical harmful queries across Llama-2-7B-Chat and Gemma-7B-it. We observe that after activation steering—whether for compliance or JSON formatting—responses shift significantly toward the steered objective. Notably, the first generated token immediately establishes a positive tone or initiates a JSON structure, contrasting sharply with the baseline refusal. This confirms that steering effectively overrides the refusal gate by manipulating the initial token distribution.
Report issue for preceding element 
Report issue for preceding element Figure 3: Per-token KL Divergence between Original and Compliance Steered Model on Llama-3-8B-Instruct. Red lines indicate the KL Divergence on Harmbench responses, blue lines are the KL Divergence on Alpaca (Benign) responses. Report issue for preceding element
5.3 Representation-level Evidence: Benign Steering “Obscure” Harmful Prompts in Hidden Space
Report issue for preceding element 
Figure 4: Compliance steering benignizes harmful prompts in representation space (layer 30). t-SNE shows harmful (red) vs. harmless (blue) prompts. Steered harmful prompts (green) under (a) compliance and (b) JSON steering frequently cross the decision boundary and fall on the “harmless” side (60.8% for compliance, 58.2% for JSON). This illustrates a reduced safety margin, as harmful requests become easier to encode as benign-like states. Report issue for preceding element
The refusal-gate mechanism in Sec. 5.1– 5.2 makes a token-level prediction: steering induces a concentrated early distributional shift that suppresses refusal prefixes, after which autoregressive inertia can carry the model into a compliant trajectory. Here, we provide complementary representation-level evidence: benign steering also shifts the prompt representations of harmful queries toward regions of hidden space typically occupied by harmless requests. In effect, steering can cause a harmful prompt to be encoded as “more harmless” according to safety-relevant features, making downstream refusal behavior less likely.
Report issue for preceding element
Before steering, harmful vs. harmless prompts are linearly separable across layers. We first test whether the model maintains an explicit representation-space separation between harmful and harmless inputs. Using layerwise residual-stream representations, a linear probe distinguishes harmful vs. harmless prompts with high accuracy across layers (Fig. 18) , indicating a robust and linearly decodable “harmfulness” signal throughout the forward pass. This is consistent with refusal being triggered by relatively shallow, easily decodable features rather than requiring deep semantic reasoning at generation time.
Report issue for preceding element
Both STEER-COMPLIANCE and STEER-JSON shift harmful prompts toward the harmless manifold. Across layers, t-SNE (Maaten and Hinton, 2008) visualizations show that steered harmful representations (green) progressively shift toward the harmless cluster, relative to the unsteered geometry (cf. Figs. 15– 17 in Appendix F).
Report issue for preceding element
To make this “benignization” effect more concrete, we examine a representative late layer (layer 30) and overlay a linear decision boundary in the 2D t-SNE plane that separates harmful vs. harmless embeddings with high accuracy. Under STEER-COMPLIANCE, a substantial fraction of steered harmful points cross into the region classified as harmless (Fig. 4(a); 60.8% in this projection). Crucially, we observe a qualitatively similar phenomenon under STEER-JSON (Fig. 4(b); 58.2%), despite JSON steering being an “non-safety-related” intervention. This suggests that even syntactic utility steering can perturb the same internal features that normally separate harmful from harmless requests.
Report issue for preceding element
Mechanistic implication: steering reduces the model's effective safety margin. Together, these results suggest a hidden-space pathway for the externalities measured in Sec. 4.3. If harmfulness is linearly decodable, then a simple safety gate can be viewed as thresholding a score of the form ⟨ w , h ⟩ \langle w,h\rangle . Activation steering replaces h h with h + α  v h+\alpha v , shifting that score by α  ⟨ w , v ⟩ \alpha\langle w,v\rangle ; when this shift is negative and large enough, it can move harmful prompts across the implicit boundary into a region associated with benign requests. Once the model is in this “benign-coded” regime, the same autoregressive inertia described in Sec. 5.1 can carry generation forward along a non-refusal trajectory.
Report issue for preceding element
6 Discussions
Report issue for preceding element
Potential mitigation strategies. A plausible way to mitigate steering externalities is to construct safety-aware steering vector that aims to reduce the safety regressions induced by pure compliance steering by explicitly incorporating safety signals into the steering direction itself. We conducted a preliminary study on a strategy termed STEER-BIND, which constructs a mixed dataset by randomly sampling both benign instructions and harmful prompts, and derives the steering vector from this safety-aware corpus. Implementation details and additional results (Table 5) are provided in Appendix G. Initial observations suggest that STEER-BIND effectively attenuates steering externalities, yielding improved robustness against both benchmark-only and adaptive jailbreak attacks compared to pure compliance steering, while preserving benign utility. We believe STEER-BIND concept can motivate more capable and advanced safety-aware model steering designs.
Report issue for preceding element
Practice: red-team steered models before deployment. From a deployment standpoint, a steering vector should be treated like a behavioral “patch,” even when derived from benign data. We recommend that model developers adopt routine red-teaming and regression testing specifically on the steered configuration prior to release (and whenever the steering vector, injection layers, or strength changes). Concretely, teams should evaluate safety and other alignment metrics both with and without steering, include automated adversarial testing where appropriate, and verify that any utility gains do not come with unacceptable increases in harmful completion or other alignment regressions.
Report issue for preceding element
7 Conclusion
Report issue for preceding element
Activation steering is an attractive post-training control for utility (e.g., compliance or JSON formatting), but we show it can create steering externalities: vectors learned from benign data weaken refusal behavior and substantially increase jailbreak success in a black-box setting. Across Llama-2/3 and Gemma, benign steering raises intrinsic ASR and amplifies adaptive attacks (up to 99% ASR). Mechanistically, steering shifts early-token probabilities away from refusal prefixes and moves harmful prompts toward benign-like representations, shrinking the safety margin. Steered deployments should be red-teamed, and future work should develop safety-aware steering that preserves robustness.
Report issue for preceding element
Impact Statement
Report issue for preceding element
We aim to advance the field of AI safety by uncovering the unintended consequences of activation steering, a technique increasingly used to enhance the utility of LLMs.
Report issue for preceding element
Positive Societal Impact
Report issue for preceding element
Our work highlights a critical blind spot in current model deployment pipelines: that model developers optimize for benign intentions like “helpfulness/compliance” or “instruction adherence” can accidentally erode safety guardrails. By demonstrating that ”shallow” safety alignment can be bypassed through internal representation shifts, we motivate the research community to move beyond surface-level refusal training. This work encourages the development of more robust alignment techniques that persist deeper into the generation trajectory and necessitates the inclusion of steering evaluations in safety audits before deployment.
Report issue for preceding element
Alignment evaluation beyond safety
Report issue for preceding element
While we focus on refusal and harmful-completion robustness, the same mechanism that shifts early-token behavior can plausibly affect other alignment-relevant properties. Benign steering directions learned to optimize utility (e.g., compliance, formatting, style) may introduce regressions in truthfulness/hallucination rates, bias and toxicity, privacy leakage, overconfidence/calibration, or instruction-hierarchy behavior (e.g., prioritizing format constraints over policy constraints). This suggests that auditing steered models should include broader alignment evaluations—not only safety refusal—because steering acts as a general-purpose change to the model's internal decision boundary, and externalities may surface on axes unrelated to the original steering objective.
Report issue for preceding element
Potential Risks and Mitigations
Report issue for preceding element
We acknowledge that this research involves the study of jailbreaking dynamics and demonstrates how steering can act as a “force multiplier” for adversarial attacks. While this knowledge could theoretically be leveraged by malicious actors to bypass safety filters, we believe that the vulnerability exists regardless of its public disclosure. The steering vectors studied here are derived from benign data (e.g., standard instruction tuning), meaning developers might be deploying compromised models without realizing it. Therefore, we believe the benefits of exposing this “steering externality”—to enable the development of defenses such as STEER-BIND—outweigh the risks of disclosure.
Report issue for preceding element
References
Report issue for preceding element
A. Arditi, O. Obeso, A. Syed, D. Paleka, N. Panickssery, W. Gurnee, and N. Nanda (2024) ↑ Refusal in language models is mediated by a single direction. External Links: 2406.11717, Link Cited by: Table 3, §1, §2.
A. Askell, Y. Bai, A. Chen, D. Drain, D. Ganguli, T. Henighan, A. Jones, N. Joseph, B. Mann, N. DasSarma, N. Elhage, Z. Hatfield-Dodds, D. Hernandez, J. Kernion, K. Ndousse, C. Olsson, D. Amodei, T. Brown, J. Clark, S. McCandlish, C. Olah, and J. Kaplan (2021) ↑ A general language assistant as a laboratory for alignment. External Links: 2112.00861 Cited by: §1.
Y. Bai, A. Jones, K. Ndousse, A. Askell, A. Chen, N. DasSarma, D. Drain, S. Fort, D. Ganguli, T. Henighan, N. Joseph, S. Kadavath, J. Kernion, T. Conerly, S. El-Showk, N. Elhage, Z. Hatfield-Dodds, D. Hernandez, T. Hume, S. Johnston, S. Kravec, L. Lovitt, N. Nanda, C. Olsson, D. Amodei, T. Brown, J. Clark, S. McCandlish, C. Olah, B. Mann, and J. Kaplan (2022a) ↑ Training a helpful and harmless assistant with reinforcement learning from human feedback. External Links: 2204.05862, Link Cited by: §1.
Y. Bai, A. Jones, K. Ndousse, A. Askell, A. Chen, N. DasSarma, D. Drain, S. Fort, D. Ganguli, T. Henighan, N. Joseph, S. Kadavath, J. Kernion, T. Conerly, S. El-Showk, N. Elhage, Z. Hatfield-Dodds, D. Hernandez, T. Hume, S. Johnston, S. Kravec, L. Lovitt, N. Nanda, C. Olsson, D. Amodei, T. Brown, J. Clark, S. McCandlish, C. Olah, B. Mann, and J. Kaplan (2022b) ↑ Training a helpful and harmless assistant with reinforcement learning from human feedback. External Links: 2204.05862 Cited by: §1.
Y. Bai, S. Kadavath, S. Kundu, A. Askell, J. Kernion, A. Jones, A. Chen, A. Goldie, A. Mirhoseini, C. McKinnon, C. Chen, C. Olsson, C. Olah, D. Hernandez, D. Drain, D. Ganguli, D. Li, E. Tran-Johnson, E. Perez, J. Kerr, J. Mueller, J. Ladish, J. Landau, K. Ndousse, K. Lukosuite, L. Lovitt, M. Sellitto, N. Elhage, N. Schiefer, N. Mercado, N. DasSarma, R. Lasenby, R. Larson, S. Ringer, S. Johnston, S. Kravec, S. E. Showk, S. Fort, T. Lanham, T. Telleen-Lawton, T. Conerly, T. Henighan, T. Hume, S. R. Bowman, Z. Hatfield-Dodds, B. Mann, D. Amodei, N. Joseph, S. McCandlish, T. Brown, and J. Kaplan (2022c) ↑ Constitutional ai: harmlessness from ai feedback. External Links: 2212.08073, Link Cited by: §1.
P. Chao, A. Robey, E. Dobriban, H. Hassani, G. J. Pappas, and E. Wong (2023) ↑ Jailbreaking black box large language models in twenty queries. CoRR abs/2310.08419. Cited by: Figure 1, Figure 1, §3.3, §4.3.
R. Chen, A. Arditi, H. Sleight, O. Evans, and J. Lindsey (2025) ↑ Persona vectors: monitoring and controlling character traits in language models. External Links: 2507.21509, Link Cited by: §1.
A. Ghandeharioun, A. Yuan, M. Guerard, E. Reif, M. A. Lepori, and L. Dixon (2024) ↑ Who's asking? user personas and the mechanics of latent misalignment. External Links: 2406.12094, Link Cited by: Table 3, §1, §2.
A. Grattafiori, A. Dubey, A. Jauhri, A. Pandey, A. Kadian, A. Al-Dahle, A. Letman, A. Mathur, A. Schelten, A. Vaughan, et al. (2024) ↑ The llama 3 herd of models. arXiv preprint arXiv:2407.21783. Cited by: §4.1.
J. Ji, M. Liu, J. Dai, X. Pan, C. Zhang, C. Bian, C. Zhang, R. Sun, Y. Wang, and Y. Yang (2023) ↑ BeaverTails: towards improved safety alignment of llm via a human-preference dataset. External Links: 2307.04657, Link Cited by: Appendix G.
A. Korznikov, A. Galichin, A. Dontsov, O. Y. Rogov, I. Oseledets, and E. Tutubalina (2025) ↑ The rogue scalpel: activation steering compromises llm safety. External Links: 2509.22067, Link Cited by: Table 3, §1, §2.
B. W. Lee, I. Padhi, K. N. Ramamurthy, E. Miehling, P. Dognin, M. Nagireddy, and A. Dhurandhar (2025) ↑ Programming refusal with conditional activation steering. External Links: 2409.05907, Link Cited by: Appendix J, 1st item, 1st item, Appendix G, §1, §3.2, §3.
X. Li, T. Zhang, Y. Dubois, R. Taori, I. Gulrajani, C. Guestrin, P. Liang, and T. B. Hashimoto (2023) ↑ AlpacaEval: an automatic evaluator of instruction-following models. GitHub. Note: https://github.com/tatsu-lab/alpaca_eval Cited by: §4.1.
X. Liu, P. Li, E. Suh, Y. Vorobeychik, Z. Mao, S. Jha, P. McDaniel, H. Sun, B. Li, and C. Xiao (2024) ↑ AutoDAN-turbo: a lifelong agent for strategy self-exploration to jailbreak llms. External Links: 2410.05295, Link Cited by: §1.
L. v. d. Maaten and G. Hinton (2008) ↑ Visualizing data using t-sne. Journal of machine learning research 9 ( Nov), pp. 2579–2605. Cited by: §5.3.
M. Mazeika, L. Phan, X. Yin, A. Zou, Z. Wang, N. Mu, E. Sakhaee, N. Li, S. Basart, B. Li, D. Forsyth, and D. Hendrycks (2024) ↑ HarmBench: a standardized evaluation framework for automated red teaming and robust refusal. External Links: 2402.04249, Link Cited by: §4.1.
A. Mehrotra, M. Zampetakis, P. Kassianik, B. Nelson, H. Anderson, Y. Singer, and A. Karbasi (2023) ↑ Tree of attacks: jailbreaking black-box llms automatically. CoRR abs/2312.02119. Cited by: Figure 1, Figure 1, §3.3, §4.3.
N. Nanda and J. Bloom (2022) ↑ TransformerLens. Note: https://github.com/TransformerLensOrg/TransformerLens/blob/main/transformer_lens/loading_from_pretrained.py Cited by: Appendix J.
L. Ouyang, J. Wu, X. Jiang, D. Almeida, C. L. Wainwright, P. Mishkin, C. Zhang, S. Agarwal, K. Slama, A. Ray, J. Schulman, J. Hilton, F. Kelton, L. Miller, M. Simens, A. Askell, P. Welinder, P. Christiano, J. Leike, and R. Lowe (2022) ↑ Training language models to follow instructions with human feedback. External Links: 2203.02155 Cited by: §1.
ProtectAI.com (2024) ↑ Fine-tuned distilroberta-base for rejection in the output detection. External Links: Link Cited by: 1st item, §4.1.
X. Qi, A. Panda, K. Lyu, X. Ma, S. Roy, A. Beirami, P. Mittal, and P. Henderson (2024) ↑ Safety alignment should be made more than just a few tokens deep. External Links: 2406.05946, Link Cited by: §5.1, §5.2.
X. Qi, Y. Zeng, T. Xie, P. Chen, R. Jia, P. Mittal, and P. Henderson (2023) ↑ Fine-tuning aligned language models compromises safety, even when users do not intend to!. External Links: 2310.03693, Link Cited by: Table 3, §1, §2.
N. Razin, S. Malladi, A. Bhaskar, D. Chen, S. Arora, and B. Hanin (2025) ↑ Unintentional unalignment: likelihood displacement in direct preference optimization. External Links: 2410.08847, Link Cited by: Table 3, §1, §2.
A. Stolfo, V. Balachandran, S. Yousefi, E. Horvitz, and B. Nushi (2025) ↑ Improving instruction-following in language models through activation steering. External Links: 2410.12877, Link Cited by: Appendix J, 2nd item, 2nd item, 2nd item, §1, §1, §3.2, §3, §4.1.
F. Tajwar, A. Singh, A. Sharma, R. Rafailov, J. Schneider, T. Xie, S. Ermon, C. Finn, and A. Kumar (2024) ↑ Preference fine-tuning of llms should leverage suboptimal, on-policy data. External Links: 2404.14367, Link Cited by: §1.
G. Team, T. Mesnard, C. Hardin, R. Dadashi, S. Bhupatiraju, S. Pathak, L. Sifre, M. Rivière, M. S. Kale, J. Love, et al. (2024) ↑ Gemma: open models based on gemini research and technology. arXiv preprint arXiv:2403.08295. Cited by: §4.1.
H. Touvron, T. Lavril, G. Izacard, X. Martinet, M. Lachaux, T. Lacroix, B. Rozière, N. Goyal, E. Hambro, F. Azhar, A. Rodriguez, A. Joulin, E. Grave, and G. Lample (2023) ↑ LLaMA: open and efficient foundation language models. CoRR abs/2302.13971. Cited by: §4.1.
A. M. Turner, L. Thiergart, G. Leech, D. Udell, J. J. Vazquez, U. Mini, and M. MacDiarmid (2024) ↑ Steering language models with activation engineering. External Links: 2308.10248, Link Cited by: §1.
A. Vaswani, N. Shazeer, N. Parmar, J. Uszkoreit, L. Jones, A. N. Gomez, L. Kaiser, and I. Polosukhin (2023) ↑ Attention is all you need. External Links: 1706.03762 Cited by: §1.
T. Xie, X. Qi, Y. Zeng, Y. Huang, U. M. Sehwag, K. Huang, L. He, B. Wei, D. Li, Y. Sheng, R. Jia, B. Li, K. Li, D. Chen, P. Henderson, and P. Mittal (2025) ↑ SORRY-bench: systematically evaluating large language model safety refusal. External Links: 2406.14598, Link Cited by: §4.2.
C. Xiong, P. Chen, and T. Ho (2025) ↑ CoP: agentic red-teaming for large language models using composition of principles. External Links: 2506.00781, Link Cited by: Figure 1, Figure 1, §1, §3.3, §4.3.
B. Zhang, Z. Liu, C. Cherry, and O. Firat (2024) ↑ When scaling meets llm finetuning: the effect of data, model and finetuning method. External Links: 2402.17193, Link Cited by: §1.
J. Zhou, T. Lu, S. Mishra, S. Brahma, S. Basu, Y. Luan, D. Zhou, and L. Hou (2023) ↑ Instruction-following evaluation for large language models. External Links: 2311.07911, Link Cited by: §4.1.
A. Zou, Z. Wang, J. Z. Kolter, and M. Fredrikson (2023) ↑ Universal and transferable adversarial attacks on aligned language models. CoRR abs/2307.15043. Cited by: §1.
Appendix A Comparison with Prior Work on Steering and Alignment
Report issue for preceding element
Table 3 provides a structured comparison between prior work on inference-time steering and training-time customization and our setting of interest. We categorize each line of work along several dimensions: whether the intervention is applied at inference or training time, whether it is motivated by a benign utility objective, whether utility improvement is the primary goal, whether safety side-effects are explicitly studied, and whether the work evaluates robustness under adversarial or jailbreak attacks.
Report issue for preceding element
This comparison highlights a gap in the existing literature: while several prior studies examine steering as an attack vector or analyze safety regressions as a secondary effect, none focus on developer-side, utility-driven activation steering and its unintended safety externalities under black-box jailbreak evaluation. Our work isolates this previously under-explored regime, where benign, deployment-motivated steering interventions can systematically erode safety margins despite not being adversarially controlled.
Report issue for preceding element
Table 3: Comparison of inference-time steering and training-time customization risks relevant to safety externalities.
| Work | Phase | Benign | Utility | Studied safety | Attack/ | | ^^ | ^^ | objective | priority | side-effects | JB Eval | | --- | --- | --- | --- | --- | --- | | Refusal Direction Interventions ( Arditi et al., 2024) | Inference | ✗ | ✗ | ✓ | ✓ | | Rogue Scalpel ( Korznikov et al., 2025) | Inference | ✓ | ✗ | ✓ | ✗ | | Persona Steering ( Ghandeharioun et al., 2024) | Inference | ✗ | ✓ | ✓ | ✓ | | Fine-tuning Aligned LMs ( Qi et al., 2023) | Train | ✓ | ✗ | ✓ | ✓ | | Likelihood Displacement in DPO ( Razin et al., 2025) | Train | ✓ | ✗ | ✓ | ✗ | | Steering Externality (Ours) | Inference | ✓ | ✓ | ✓ | ✓ |
Report issue for preceding element
Appendix B Implementation Details
Report issue for preceding element
In this section, we outline the implementation details and hyperparameter settings for our two methods. Specifically, we first discuss the implementation of steering vector generation, followed by the hyperparameter configurations for the steering methods.
Report issue for preceding element
B.1 Steering Vector Generation
Report issue for preceding element
• STEER-COMPLIANCE: As discussed in Sec. 3, we follow the behavior vector generation procedure inspired by CAST (Lee et al., 2025) . However, while the original CAST implementation generates vectors meant to drive the model toward refusal behavior, our approach differs. We utilize 100 benign questions from the Alpaca dataset, pairing each with both a compliance and a refusal response. For example, for a benign question such as Given a sentence, please provide the proper punctuation, we attach an affirmative response and a refusal response (e.g., I regret to inform you that I can't). Instead of steering in the refusal direction, we utilize PCA to identify the first principal direction toward compliance. Report issue for preceding element
• STEER-JSON: We utilize instruction-following prompts to generate a steering vector that controls the format of the LLM's response. Specifically, following the methodology in Stolfo et al. ( 2025) , we construct a dataset of paired prompts using 400 questions sampled from IFEVAL. Unlike STEER COMPLIANCE, these instruction pairs contrast the presence of a formatting constraint. For example: Report issue for preceding element
– List 3 fruits. Report issue for preceding element
– List 3 fruits in JSON format. Report issue for preceding element By extracting the mean difference between the hidden states of these paired instructions, we steer the LLM to be more likely to generate responses in JSON format. Report issue for preceding element
B.2 Hyperparameter settings
Report issue for preceding element
Since we employ two distinct steering methodologies, it is necessary to discuss the specific hyperparameters selected for each. The optimal configuration varies between methods due to the nature of the steering vectors and the tasks they target. Below, we detail the hyperparameter settings chosen for STEER-COMPLIANCE and STEER-JSON:
Report issue for preceding element
• STEER-COMPLIANCE: This method involves two key hyperparameters: i) Steering strength (Coefficient) and ii) Steering layers. To determine the optimal steering coefficient, we conducted an ablation study on Llama-3-8B-Instruct, sampling the coefficient α \alpha from the set [ 0 , 0.5 , 1.0 , 1.5 , 2.0 ] [0,0.5,1.0,1.5,2.0] . We measured compliance utility (defined as the harmless refusal rate) on 100 harmful questions sampled from SorryBench, as well as the model's ability to generate answers for 100 benign questions sampled from Alpaca (measured via win-rate). The results are summarized in Figure 5. Our objective was to identify a coefficient that maximizes the Win-Rate on benign tasks while simultaneously maintaining a low refusal rate. Based on the plot, we selected the coefficient where the performance intersects with the baseline Win-Rate of the original model (indicated by the blue dotted line). This intersection occurs at approximately 1.3. We utilized this coefficient for the remainder of the experiments. Report issue for preceding element For the consistency of experiment, we follow the basic implementation of CAST in terms of steering layers, in which we keep the steering layers as layer 15, 17, 18, 19, 20, 21, 22, 23, 24, which is consistent with colab implementation of Lee et al. ( 2025) across all models in each experiment. Report issue for preceding element
• STEER-JSON: Unlike STEER-COMPLIANCE, our instruction-following approach dynamically determines the strength coefficient according to Eq. 4. Regarding the selection of steering layers, we adopt the grid search method used by Stolfo et al. ( 2025) to identify the optimal layer for maximizing JSON Correctness. Consequently, we utilize layer 15 for Gemma-7B-it, layer 16 for Llama-2-7B-Chat, and layer 6 for Llama-3-8B-Instruct. All selected layers were identified via the instruction-following algorithm. Report issue for preceding element 
Report issue for preceding element Figure 5: An ablation study on Llama-3-8B-Instruct by varying the coefficient of steering strength. We plot out two lines, the blue line indicates the Win-Eate which measure the ability of LLMs generating on benign questions sampled from Alpaca after steering and red line indicates the Refusal Rate on harmful questions sampled from SorryBench. Report issue for preceding element
B.3 Evaluation of the utility
Report issue for preceding element
In our steering, we measure two different utilities:
Report issue for preceding element
• Harmless Refusal Rate: We evaluate this metric by measuring the refusal rate using two distinct judges. First, we employ Distilroberta-Base-Rejection-v1 (ProtectAI.com, 2024) , which determines whether a response constitutes a rejection or compliance. Second, we utilize the SorryBench judge, a fine-tuned LLM based on Mistral-7B-v0.2. This judge classifies whether the generated response complies with the given query. Report issue for preceding element
• JSON Correctness: Adhering to the instruction-following evaluation protocol (Stolfo et al., 2025) , we assess whether the model's output conforms to valid JSON syntax. As shown in Listing 1, we utilize a specific function to verify if the response can be successfully parsed as a JSON object. Report issue for preceding element ⬇ 1 def check_following( self, value): 2 value = ( 3 value. strip() 4 . removeprefix("'''json") 5 . removeprefix("'''Json") 6 . removeprefix("'''JSON") 7 . removeprefix("'''") 8 . removesuffix("'''") 9 . strip() 10 ) 11 try: 12 json. loads( value) 13 except ValueError as _: 14 return False 15 return True Listing 1: Check JSON Validity Function Report issue for preceding element
Appendix C Additional Safety Benchmark: Harmful SorryBench (No Jailbreak)
Report issue for preceding element
In addition to HarmBench ASR, we report a complementary safety benchmark that measures refusal behavior directly on harmful SorryBench prompts without applying any jailbreak attack. Table 4 shows that benign steering reduces refusal rates on harmful prompts across all tested models (i.e., lower refusal ↓ \downarrow indicates worse safety), consistent with the intrinsic safety regressions observed on HarmBench.
Report issue for preceding element
Table 4: Benign steering reduces refusal rates on harmful SorryBench prompts even without explicit jailbreak attacks (RoBERTa judge). Lower refusal rate ( ↓ \downarrow ) implies worse safety.
Report issue for preceding element
Appendix D Per-token KL Divergence on Gemma-7B-it model
Report issue for preceding element 
Report issue for preceding element Figure 6: Per-token KL Divergence between Original and JSON Steered Model on Llama-3-8B-Instruct. Red lines indicate the KL Divergence on Harmbench responses, blue lines are the KL Divergence on Alpaca (Benign) responses. Report issue for preceding element
In Sec. 5, we give some mechanic explanation of why steering externalities will occur. We present per-token KL Divergence graphs on Llama-3-8B-Instruct including both compliance and JSON steering. We found that benign steering causes changes (KL divergence) as significant as utility changes.
Report issue for preceding element
We also present the KL Divergence graph on Gemma-7B-it model.
Report issue for preceding element 
Report issue for preceding element Figure 7: Per-token KL Divergence between Original and Compliance Steered Models on Gemma-7B-it. Red line indicates the KL Divergence on Harmbench responses, blue line highlights the KL Divergence on Alpaca (Benign) responses. Report issue for preceding element 
Report issue for preceding element Figure 8: Per-token KL Divergence between Original and JSON Steered Models on Gemma-7B-it. Red line indicates the KL Divergence on Harmbench responses, blue line highlights the KL Divergence on Alpaca (Benign) responses. Report issue for preceding element
Similar observation can be made from Figure 7 and Figure 8, for both STEER-COMPLIANCE and STEER-JSON, the KL divergence peaks during the initial tokens before stabilizing. This indicates that steering primarily impacts the critical “refusal gate”, shifting probability mass from refusal templates to non-refusal openers. Because generation is autoregressive, this early distributional shift effectively sets a new mode; once the refusal prefix is bypassed, the model naturally continues along a potentially harmful trajectory. This mechanism applies even to benign formatting tasks like JSON steering, confirming that steering degrades safety by eroding the initial safety margin.
Report issue for preceding element
Appendix E Qualitative Analysis of Steering
Report issue for preceding element
In this section, we show that after STEER-COMPLIANCE, the jailbreak output tends to be more positive in terms of answering the harmful question. This implies that since we are steering towards compliance side, we are driving the refusal gate tokens towards more positive in terms of answering questions. Due to the auto regressive nature of the LLMs, the generation on harmful questions will become less refusal. We want to show three qualitative examples in Figure. 9, Figure. 10 and Figure. 11.
Report issue for preceding element 
Report issue for preceding element Figure 9: Qualitative comparison on Llama-2-7B-Chat jailbreak responses between Original and Compliance Steered Models Report issue for preceding element 
Report issue for preceding element Figure 10: Qualitative comparison on Llama-3-8B-Instruct jailbreak responses between Original and Compliance Steered Models Report issue for preceding element 
Report issue for preceding element Figure 11: More qualitative comparison on Llama-2-7B-Chat jailbreak responses between Original and Compliance Steered Models Report issue for preceding element
Across all qualitative examples, it is clear that this compliance behavior exists not only in one model but also holds for others, such as Llama-3-8B-Instruct. This further clarifies why compliance steering loosens safety guardrails.
Report issue for preceding element
We also present three additional quantitative jailbreak examples of STEER-JSON. As shown in Figure 12, 13, and 14, adding JSON steering and instruction guidance promotes the generation of structured JSON output during the LLM's generation phase, even when given a CoP jailbreak prompt.
Report issue for preceding element 
Report issue for preceding element Figure 12: Qualitative comparison on Gemma-7B-it jailbreak responses between Original and JSON Steered Models Report issue for preceding element 
Report issue for preceding element Figure 13: Qualitative comparison on Gemma-7B-it jailbreak responses between Original and JSON Steered Models Report issue for preceding element 
Report issue for preceding element Figure 14: More qualitative comparison on Gemma-7B-it jailbreak responses between Original and JSON Steered Models Report issue for preceding element
Appendix F Representation-level analysis (additional visualizations)
Report issue for preceding element
In this section, we present t-SNE visualizations of the representation space changes in the steered model (Llama-3-8B-Instruct) across all layers for both STEER-COMPLIANCE and STEER-JSON.
Report issue for preceding element
In Figure 15, the representation space of the original Llama-3-8B-Instruct shows a clear separation between harmful queries (red) and harmless queries (blue), even at the initial embedding level. As the layers progress, this separation signal becomes stronger. This trend is further corroborated by the linear classification accuracy plotted in Figure 18.
Report issue for preceding element
However, when STEER-COMPLIANCE and STEER-JSON are applied, the landscape changes. As seen in Figure 16 (STEER-COMPLIANCE) and Figure 17 (STEER-JSON), a portion of the harmful queries shifts toward the harmless region. This implies that applying benign activation steering causes harmful embeddings to merge with harmless ones, rendering them inseparable. Consequently, the target model fails to recognize the harm, leading to the generation of harmful responses.
Report issue for preceding element
F.1 Limitations of Representation-level Visualizations
Report issue for preceding element
We emphasize that t-SNE is a qualitative projection and the 2D boundary is only an illustrative diagnostic. Nevertheless, the consistent displacement of steered harmful representations toward harmless regions under both steering aligns with the refusal-gate hypothesis and helps explain why benign steering can amplify jailbreak success rates.
Report issue for preceding element 
Figure 15: Layerwise t-SNE visualization of harmful vs harmless prompts across layers (Meta-Llama-3-8B-Instruct). Report issue for preceding element 
Figure 16: Layerwise t-SNE visualization including compliance steered harmful prompts. Steered harmful representations shift toward the harmless cluster across layers. Report issue for preceding element 
Figure 17: Layerwise t-SNE visualization including JSON steered harmful prompts. Steered harmful representations shift toward the harmless cluster across layers. Report issue for preceding element 
Figure 18: Linear separability (classification accuracy) of harmful vs harmless prompt regressions observed on HarmBench latent representations across layers. Report issue for preceding element
Appendix G STEER-BIND Results
Report issue for preceding element
We explore a safety-aware steering-vector construction strategy that reduces the safety regressions induced by pure compliance steering. Concretely, we construct a mixed dataset ( STEER-BIND) by randomly sampling 50 benign instructions from Alpaca and 50 harmful prompts from BeaverTails (Ji et al., 2023) , then assigning the desired behavior conditionally by prompt type: benign prompts are paired with compliant continuations, while harmful prompts are paired with refusal continuations. We then apply the CAST procedure (Lee et al., 2025) to extract principal steering direction. Empirically, STEER-BIND substantially reduces the externality of STEER-COMPLIANCE on Llama-3-8B-Instruct: benchmark-only ASR drops from 36% ( STEER-COMPLIANCE) to 5% ( STEER-BIND), and CoP ASR drops from 93% to 76% (Table 5). The trade-off is a small reduction in harmless utility relative to pure compliance steering: harmless refusal increases from 0% ( STEER-COMPLIANCE) to 1% ( STEER-BIND), though it remains below the original model's refusal rate of 2%. Overall, these results suggest that injecting a small amount of safety-aware data into the steering-vector construction pipeline can attenuate steering externalities under both benchmark-only and adaptive jailbreak evaluations.
Report issue for preceding element
Table 5: STEER-BIND: safety-aware mixed steering partially mitigates the safety regressions induced by compliance steering on Llama-3-8B-Instruct, while largely preserving harmless utility.
Report issue for preceding element
Appendix H Win-Rate measurement of Compliance Steering
Report issue for preceding element
As Sec. 4 shows, adding both STEER-COMPLIANCE and STEER-JSON improves overall utility by lowering the harmless refusal rate and increasing JSON extraction in the response. A natural question arises: how well does the steered model perform in terms of general response quality? In this section, we introduce an additional utility measurement:
Report issue for preceding element
• Win-Rate measures whether the responses generated by a given LLM are better than those generated by a reference model. In our evaluation, we use GPT-4 as the reference model (judge). The purpose of this metric is to assess the general capability of LLM responses after steering. Report issue for preceding element
We follow the procedures described in Sec. 4.1 and perform compliance steering on three target models. We sampled 100 questions from Alpaca and evaluated the Win-Rate, as shown in Table 6.
Report issue for preceding element
Table 6: Length invariant Win-Rate by applying compliance steering on original models and evaluated on 100 Alpaca questions. After steering, all LLMs have higher Win-Rate indicating the overall generation qualities are improved.
Report issue for preceding element
As the compliance behavior vectors are injected into the target models, we observe an overall increasing trend in Win-Rate. In particular, the Llama-2-7B-Chat-hf model originally had a Win-Rate of 0.31, which increased to 4.67 after compliance steering. This further supports the hypothesis that model developers prioritize improving overall generation quality (i.e., utility).
Report issue for preceding element
Appendix I Measuring Refusal Rate by using an additional judge
Report issue for preceding element
In this section, we utilize a different refusal judge, Sorrybench fine-tuned Mistral-7B-Instruct-v0.2, to measure the overall refusal rate. Specifically, we employ the SorryBench fine-tuned Mistral-7B-v0.2 model to judge the refusal rate/harmfulness, providing a complementary perspective to the Roberta-based evaluation used in Sec. 4.
Report issue for preceding element
Table 7: Refusal Rate between original target LLMs and compliance steered LLMs on Harmful SorryBench data using fine-tuned Mistral as Judge. After steering, all LLMs have a lower refusal rate than the original model.
Report issue for preceding element
As shown in Table 7, the safety regression is particularly severe for Llama-3-8B-Instruct, where the refusal rate plummets from 86% to 30%, and Gemma-7B-it, which drops from 90% to 68%. Even Llama-2-7B-Chat, which appears more robust, exhibits a non-trivial decrease in refusal rates. This indicates that the ”compliance” direction identified by the steering vectors does not discriminate between benign and malicious requests; rather, it broadly suppresses the model's refusal mechanisms. Consequently, while activation steering successfully enhances the model's helpfulness on standard tasks, it inadvertently acts as a ”jailbreak,” bypassing the safety alignment training and exposing the model to significant vulnerabilities when maximizing utility.
Report issue for preceding element
Table 8: Refusal Rate between original target LLMs and JSON steered LLMs on Harmful SorryBench data using fine-tuned Mistral as Judge. After steering, all LLMs have a lower refusal rate than the original model.
Report issue for preceding element
Results in Table 8 indicate that as by applying STEER-JSON into the models, the overall refusal rate decreases across all steered models. This finding is consistent with the compliance steering, which implies that the safety alignment of the original models is eroded by the steering. However, such alignment erosion appears to have less impact than compliance steering, since the refusal rate for JSON steering decreases less than under the compliance setting.
Report issue for preceding element
Appendix J Intrinsic and Synergistic Vulnerabilities on additional LLMs
Report issue for preceding element
To test whether steering externalities generalize beyond the three main target models in our paper, we additionally evaluate Llama-3-8B-Instruct-RR and GPT-OSS-20B under the same two-regime protocol used throughout: (i) benchmark-only intrinsic vulnerability, where we directly query the target model with harmful prompts; and (ii) synergistic vulnerability, where we run an adaptive black-box jailbreak (CoP) against the target model and measure the resulting Attack Success Rate (ASR) using the HarmBench classifier. We use 50 randomly sampled HarmBench harmful questions for both regimes.
Report issue for preceding element
For these two additional architectures, we only report STEER-COMPLIANCE (Lee et al., 2025) . The official implementation we follow for STEER-JSON (instruction-following) (Stolfo et al., 2025) does not support these model architectures, the full list of supporting models can be found in Nanda and Bloom ( 2022) , preventing a faithful reproduction of the same steering pipeline. Therefore, Appendix J focuses on the compliance-steering externality.
Report issue for preceding element
Table 9: Attack Success Rate (ASR) by applying black-box jailbreak attackCoP on additional models: Llama-3-8B-Instruct-RR and GPT-OSS-20B respectively on 50 Harmbench questions. After steering, all LLMs are more vulnerable to jailbreak attacks.
| Model | Original ASR | STEER-COMPLIANCE | CoP Original | CoP with | | ^^ | ^^ | Benchmark-Only ASR | ASR | STEER-COMPLIANCE ASR | | --- | --- | --- | --- | --- | | Llama-3-8B-Instruct-RR | 0% | 2% (+2) | 52% | 70% (+18) | | GPT-OSS-20B | 0% | 6% (+6) | 62% | 84% (+22) |
Report issue for preceding element
Table 9 shows that even when the original models exhibit a 0% benchmark-only ASR, applying STEER-COMPLIANCE introduces a measurable intrinsic safety regression (0% → \rightarrow 2% on Llama-3-8B-Instruct-RR, and 0% → \rightarrow 6% on GPT-OSS-20B). While these absolute increases are small in the benchmark-only regime, they indicate that compliance-oriented steering can partially erode refusal behavior even without any adaptive attack.
Report issue for preceding element
More importantly, the synergistic effect under black-box jailbreaking is substantial: when combined with CoP, STEER-COMPLIANCE increases ASR by 18% on Llama-3-8B-Instruct-RR (52% → \rightarrow 70%) and by 22% points on GPT-OSS-20B (62% → \rightarrow 84%). This mirrors our main finding that benign compliance steering acts as a force multiplier for adaptive jailbreak pipelines: even a modest reduction in refusal robustness can be amplified by an attacker that iteratively searches for prompts that elicit non-refusal trajectories.
Report issue for preceding element
These additional results support that benign STEER-COMPLIANCE might unintentionally loosen the safety guardrails leading to harmful generation
Report issue for preceding element
Appendix K Numerical value of Intrinsic and Synergistic Vulnerabilities
Report issue for preceding element
Table 10 reports Attack Success Rates on 400 HarmBench prompts for three LLMs under both benchmark-only (intrinsic vulnerabilities) and synergistic vulnerabilities. Across all models, benign steering substantially increases vulnerability to harmful requests. In the absence of adaptive attacks, both STEER-COMPLIANCE and STEER-JSON raise ASR from near-zero baselines to double-digit levels, with compliance steering consistently inducing larger increases. Under the black-box CoP jailbreak, all models already exhibit high ASR, which is further amplified by steering: applying compliance or JSON steering on top of CoP yields additional gains of 8–22%. These results indicate that benign steering systematically reduces safety margins and compounds the effectiveness of adaptive jailbreak attacks across architectures.
Report issue for preceding element
Table 10: Attack Success Rate (ASR) between original target LLMs and compliance steered LLMs as well as ASR by applying black-box jailbreak attack CoP on original and steered models respectively on 400 random sampled HarmBench data. After steering, all LLMs are more vulnerable to jailbreak attacks.
Report issue for preceding element
Appendix L Anonymous Repository
Report issue for preceding element
The source code for reproducing the experiments in this paper is available at: https://anonymous.4open.science/r/SteeringExternality. The repository will be made public upon acceptance of the paper.
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