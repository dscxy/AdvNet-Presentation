# AdvNet Presentation Script

## 1. What Research Problem Are We Trying to Solve?

Today, we will introduce AdvNet, a system for adversarially testing network protocols, especially congestion control.

I'll start with the motivation and how AdvNet works.

(**Click**)

First, let's start with some background. Bandwidth describes the capacity of a link, while throughput describes the rate that the protocol actually achieves.

In a network, a sender typically does not know how much bandwidth it can use. If it sends too slowly, throughput can be much lower than available bandwidth. If it sends too fast, packets will build up in router queues. This leads to higher round-trip time and eventually packet loss.

(**Click**)

To adapt, congestion control algorithms use feedback like ACKs, delay, and loss to adjust their congestion window and packet pacing, while TCP relies on duplicate ACKs and retransmission timeouts (RTO) to recover from lost packets.

(**Click**)

Creating a robust congestion control algorithm is hard. First, available resources and network conditions can change over time. So CC algorithms need to be optimized for throughput, loss, and latency in lots of environments. Second, they need to guarantee quick convergence to stable and fair rates when multiple senders compete. (**Adapted from PCC Vivace: Online-Learning Congestion Control §1**)

(**Click**)

These requirements also make it difficult for the protocols to be thoroughly tested. Therefore, new protocols or an upgrade to an existing protocol may perform better in test suites, but they could introduce hidden performance regressions. How to find these scenarios is the main focus of this paper.

(**Click**)

## 2. What Are the Existing Solutions, and Why Do They Fall Short?

How do developers test protocols today, and why isn't that enough?

First, hand-designed tests run a protocol under manually chosen parameters, such as fixed bandwidth and latency ranges. They are easy to interpret and they can check suspected problems directly, but their coverage depends on what the designer thinks of testing. Another problem is that many protocols retain certain states from the past, so the actual behavior may depend on previous environments. Thus, the number of possible test cases grows exponentially with sequence length.

(**Click**)

Second, developers may replay captured traces in emulators like Mahimahi, or evaluate protocols on platforms like Pantheon and Puffer to test conditions that users actually experience. These are essential for benchmarking average real-world performance, but their coverage is bounded by where and when traces were collected. In addition, they do not actively search for unknown worst-case conditions. Reproducing real-world anomalies is also difficult due to uncontrolled background processes. (**Visual Suggestion**: Add visual-only notes that explain differences between Pantheon, Puffer, and Mahimahi.)

(**Click**)

Third, what about automated adversarial testing? Here we first need to distinguish between simulation and emulation. Simulation (such as ns-3) runs simplified models of the protocol and network; it is fast and deterministic, but the modeled behavior can differ from real deployed code. Emulation (such as Mahimahi) runs the real operating system kernel protocol stack under controlled virtual links. It can capture real implementation bugs, but at the cost of slow execution and runtime noise.

(**Click**)

An important piece of prior work, CC-Fuzz, used a genetic algorithm to generate adversarial environments, but only inside the ns-3 simulator, representing links via low-level Packet Delivery Opportunities. The problem is that its high-dimensional PDO representation struggles to find strong adversarial examples within a limited emulation budget.

(**Click**)

## 3. How Does AdvNet Solve the Problem?

AdvNet addresses these gaps by formulating environment generation as a black-box search over real protocol executions. The user provides parameter bounds, a target protocol under test, and a reference baseline. The different baselines shown in the paper include another protocol, an older version of the same protocol, a single-path configuration, or a calculated capacity benchmark. (**Visual Suggestion**: Show Fig. 1.)

In each iteration, the generator outputs a candidate network trace, and the execution module runs both the target and reference inside an extended Mahimahi emulator (**Visual Suggestion**: Could add a note about the modifications that support time-varying one-way delay and dual paths). The scoring module then quantifies their relative performance gap as a score:

$$
\text{score} = \frac{R - T}{\max(R, T)} \quad (\text{when a higher metric value is better}).
$$

(**Visual Suggestion**: The formula is for display only. Also show a version that plugs in the numbers. Don't read the formula out. Add a note explaining R is for reference and T is for target.)

For example, if the reference achieves 10 Mbps and the target gets only 2 Mbps, the score is 0.8. If a lower metric value is better—such as flow completion time—we reverse the numerator to T minus R. Dividing by the maximum normalizes the score between $-1$ and $1$, so a larger positive score always means a larger relative weakness in the target. The generator uses these scores as feedback to search for environments that expose larger performance gaps.

We can also combine throughput $\tau$ and average packet delay $d$ into a single utility metric using a throughput weight $t_{\mathrm{coeff}} \in [0, 1]$:

$$
U = t_{\mathrm{coeff}} \frac{\tau}{\tau_{\max}} + (1 - t_{\mathrm{coeff}}) \frac{d_{\min}}{d},
$$

(**Visual Suggestion**: The formula is for display only. Label $\tau_{\max}$ as the maximum-throughput benchmark and $d_{\min}$ as the minimum-delay benchmark used for normalization.)

A throughput weight of $1$ considers only throughput, $0$ considers only delay, and $0.5$ weights both normalized components equally. We compute this utility separately for the reference and target, using the same normalization benchmarks and weight. We then use their utilities as $R$ and $T$ in the earlier score formula. Since higher utility is better, a positive score means the target performs worse under the chosen throughput–delay tradeoff.

Finally, because emulation has random variance, AdvNet reserves part of its time budget for Post-Learning Selection to pick the candidate with the most reliably high average score, followed by an independent re-evaluation.

## 4. What Are the Key Challenges?

Realizing this framework in emulation brings two main challenges:

The first challenge is sample efficiency. Because every evaluation runs real protocol implementations over emulated links for several seconds, we can only afford a limited number of runs. Meanwhile, the space of parameters is huge, and emulation noise means a single run can be misleading. Simply repeating every trace many times would leave very little budget to explore new environments.

The second challenge is practical usefulness. Setting link bandwidth to zero makes every protocol get zero throughput, which is useless for diagnosis. Similarly, if bandwidth jumps instantaneously, any protocol needs time to adapt, so falling short of link capacity right after a spike is expected. Using a suitable reference is essential to uncover actionable flaws.

## 5. How Does AdvNet Address Sample Efficiency?

### 5.1 Representing a Network Trace

Now, what exactly does the search change? AdvNet represents a trace using four parts:

$$
T=(B,L,D,I).
$$

$B$ contains bandwidths, $L$ contains one-way delays, and $D$ contains interval durations. $I$ contains parameters that stay fixed within the trace, such as queue capacity. For multipath tests, each link has its own bandwidth and delay sequence, with shared interval durations.

Here is an example trace. The first interval has 20 Mbps and 20 ms of one-way delay. Bandwidth then falls while delay rises. Finally, bandwidth recovers and delay falls. Each parameter is constrained within user-specified bounds like the ones in Table 1.

(**Visual Suggestion**: Show Table 1 and possibly a plot illustrating the example trace.)

The paper chooses not to use CC-Fuzz's packet delivery opportunities (PDOs). A PDO specifies the exact timestamp when a packet can leave. The authors implemented the PDO representation inside AdvNet and compared both under matched genetic algorithm settings and a one-hour budget (**Visual Suggestion**: Show Table 2). Across all four protocols, AdvNet's interval representation achieves much higher scores. This means AdvNet can find larger throughput shortfalls relative to available capacity.

The authors point to two reasons. First, PDOs create a much higher-dimensional search space: when the number of PDOs is increased from 25 to 100, the search struggles even more, and the score on BBR drops from about 14% down to about 6%. Second, AdvNet directly exposes link delay changes as tunable parameters. In later use cases it turns out to be important for finding adversarial environments.

### 5.2 Generating the Next Batch of Environments

With the representation fixed, how does AdvNet search for challenging environments?

The authors first considered an action-based online adversary, such as reinforcement learning. It observes protocol state and chooses the next network condition during emulation.

However, it requires fine-grained observation of protocol behavior and control over network conditions, which adds engineering work when supporting different protocols. Timing differences and execution randomness also make it difficult to synchronize the target, reference, and adversary. As a result, the adversary may act on stale or mismatched observations, making learning unstable.

AdvNet's main search method is a genetic algorithm, or GA. Each candidate is a complete network trace, and its genes are the numerical parameters in $T$. (**Visual Suggestion**: Show $T$ again?) GA maintains a population of traces, evaluates their fitness using the performance-gap score, selects promising parents, and applies crossover and mutation to produce the next generation until the budget expires. (**Visual Suggestion**: Consider GA cycle diagram.)

Let us look at the two operators. In two-point crossover, we choose two cut points and swap the middle segment between two parent traces. In a four-gene example, each child keeps one parent's outer values and takes the other parent's middle values. In real traces, because crossover swaps aligned positions, a bandwidth parameter always replaces a bandwidth parameter, preserving each gene's allowed bounds.

Uniform integer mutation replaces each gene with probability $p$ by sampling a new integer uniformly from that gene's allowed range. For example, it might change 15 to 73. Both operators preserve the integer format required by Mahimahi, and every newly generated trace is evaluated by running the protocols.

(**Visual Suggestion**: Show parents [20, 5, 40, 10] and [60, 30, 15, 80], with cuts around the middle two genes. Show children [20, 30, 15, 10] and [60, 5, 40, 80], then mutate 15 → 73 within an illustrative range of 1–100. Consider explaining "aligned positions" using visual elements.)

The authors also compared GA against three other trace-based methods: Random Generation (RG), which samples traces uniformly at random as a baseline; Bayesian Optimization (BO) with a random forest surrogate model; and Epsilon-Greedy Search (EPS), which mutates top-performing traces with probability $1-\epsilon$ and explores randomly with probability $\epsilon$.

In Figure 3a, GA consistently outperforms random generation across all three throughput weights. This confirms that learning from execution feedback helps. In Figure 3b, under a two-hour budget, GA, Bayesian optimization, and epsilon-greedy search achieve fairly similar performance, with GA having a slightly higher average, so the authors adopt GA as the default.

(**Visual Suggestion**: Show Fig. 3a and Fig. 3b from the paper.)

### 5.3 Avoiding Lucky Outliers

Finding high scores during search is only part of the problem; measurement noise can still mislead our final choice. The simplest rule, SimpleMax, outputs the trace that had the single highest observed score during search.

However, when evaluating hundreds of traces, the single highest observation is often an outlier inflated by positive random noise. Its score can drop sharply when re-tested independently.

To mitigate noise, AdvNet runs each trace multiple times in parallel during search. It then takes the median performance for the reference and target separately, and then computes the score. After search finishes, Post-Learning Selection takes the top 25 candidate environments and allocates a dedicated evaluation budget using Multi-Round Elimination (MRE). In each round, MRE evaluates every remaining candidate once and discards the bottom half based on their observed mean scores so far. Once 5 or fewer candidates remain, elimination stops and they are repeatedly evaluated until the budget is spent, returning the one with the highest mean score.

How should we split the total runtime between search and PLS? In Figure 2, when $0\%$ of the time is used for PLS, which is just SimpleMax, noisy outliers leave the average re-tested score around $0.59$. Dedicating **$10\%$** of the runtime to PLS raises the average score to $0.80$, which yields the best performance.

(**Visual Suggestion**: Show Figure 2.)

Together, the compact interval representation, genetic search, and post-learning selection allow AdvNet to find reliably adversarial environments within a limited emulation budget. With that, I will hand over to Xiaoyang, who will show how AdvNet uses these environments across concrete protocol testing use cases.

## 6. How Does AdvNet Ensure Practical Utility?

### 6.1 Mapping Developer Tasks to Reference and Target

Now that we have seen how AdvNet searches efficiently, let's look at how developers can use it to answer practical questions. By changing the definition of the reference and the target, the authors apply AdvNet to three distinct use cases:

* UC1 — Finding suboptimal performance and fairness issues
* UC2 — Regression testing across versions
* UC3 — Validating design objectives

(**Visual Suggestion**: Show a table of 3 UCs.)

Let's examine what AdvNet discovered in each of these three use cases.

### 6.2 UC1: Finding Suboptimal Performance and Comparing Protocol Weaknesses

In the first use case, the target is the protocol under test, and it is compared against either theoretical link capacity or another protocol implementation to uncover severe underutilization or kernel bugs.

Under UC1, comparing against theoretical link capacity can flag extreme underutilization. Comparing against another real protocol is more informative: if another protocol achieves much higher performance under the exact same trace, we know better performance is achievable.

The authors ran an all-pairs comparison across 17 TCP congestion control algorithms in the Linux kernel (**Visual Suggestion**: Show Figure 4 heatmaps). That gives 272 directed pairs (**Visual Suggestion**: $17\times16=272$). These pairs are tested under two utility definitions: an equal split between throughput and delay, and throughput only. So the total number of scenarios is doubled. AdvNet found positive scores, which indicate adversarial environments, in 448 of 544 scenarios. Every single protocol had at least one environment where a reference protocol substantially outperformed it.

Look at BBR and CUBIC in the top-left corner of both heatmaps. Under both objectives, AdvNet finds environments with large performance gaps in both directions. This is not a contradiction: it shows that even under the same metric, both protocols have distinct blind spots under different network environments. (**Visual Suggestion**: Zoom in on the top-left corner of both heatmaps.)

However, a high score alone only tells us where a protocol struggles, not why. Next, let's look at how the authors diagnosed the root causes inside several discovered environments.

### 6.3 UC1 Case Study: TCP Acknowledgment Bug Triggered by a Sudden RTT Drop

The authors further investigate why BBR scored so poorly under the throughput-only objective. By examining the logs, the authors found that AdvNet generated an environment that maintains a high RTT for about one second and then suddenly drops the RTT. As a result, packets sent earlier during the high-RTT phase are still in flight when packets sent later during the low-RTT phase arrive at the receiver first.

Using eBPF and Wireshark, the authors traced the exact sequence of events:

1. The receiver sends duplicate ACKs (dup ACKs) after seeing out-of-order packets. Duplicate ACKs quickly reach the sender during the low-RTT phase.
2. Upon receiving three dup ACKs, the sender initiates a fast retransmit for the delayed packet.
3. Crucially, the original delayed packet finally arrives at the receiver just before its fast-retransmitted copy. The receiver processes the original packet and advances its ACK number.
4. Then, the fast-retransmitted copy arrives. This specific arrival order triggers a bug in the Linux kernel's ACK-update logic: even as subsequent packets arrive normally, the receiver fails to advance the acknowledgment number and keeps sending dup ACKs, eventually forcing the sender into a retransmission timeout (RTO).

(**Visual Suggestion**: Draw a sequence diagram showing the timeline.)

Why did this kernel TCP receive bug surface specifically when testing BBR? Unlike traditional window-based protocols that send bursts of packets, BBR paces packets smoothly to maintain a steady volume in flight. This allows AdvNet's RTT drop to space the packets into this exact arrival order. This also underscores the value of emulating real kernel code rather than testing simplified simulator models.

When the authors re-tested on a newer Linux kernel from Google's BBR team, this ACK bug no longer appeared. Even so, AdvNet found another scenario (**Visual Suggestion**: Show Figure 6) where CUBIC quickly ramps up throughput while BBR v3 stays low during a short 5-second run. Extending the run showed that BBR v3 eventually ramps up. This indicates slow convergence of BBR v3 in this environment.

### 6.4 UC1 Case Study: Fairness Between Competing Flows

Another case study under UC1 is testing fairness between competing flows. Here, the authors define the reference score as the throughput of a reference protocol running alone on the link, and the target score as the throughput of that same reference flow when competing simultaneously against a target protocol. A score close to 1 means the competing flow severely starves the reference flow.

While BBR is commonly believed to dominate loss-based protocols like CUBIC, AdvNet discovered environments where CUBIC consumes nearly 100% of the link bandwidth and starves BBR. When their roles were reversed, AdvNet also found environments where BBR starves CUBIC.

Digging into the logs, the authors found that the affected flow initially operates normally for 40 to 80 seconds, but then suddenly drops its sending rate to just a single packet at a time. It's waiting for an ACK before sending the next packet for the remaining 25 to 60 seconds of the test. The authors reported this environment to the BBR development team, who confirmed the issue.

### 6.5 UC2: Comparing Different Versions of BBR

The second use case is regression testing: setting the older version of a protocol as the reference and the newer version as the target, searching for environments where an update degrades throughput or fairness.

As an example, the authors used AdvNet for regression testing between BBR v1 and BBR v3, focusing on their fairness toward a competing CUBIC flow. In each candidate environment, they run two tests:

1. CUBIC competing alongside BBR v1. CUBIC throughput from this test serves as the reference score.
2. CUBIC competing alongside BBR v3. CUBIC throughput from this test serves as the target score.

To measure steady-state impact rather than transient jitter, AdvNet first varies bandwidth and latency, then holds the network conditions fixed for one minute, and measures throughput over the final ten seconds.

In one adversarial environment discovered by AdvNet, when CUBIC competes with BBR v1, CUBIC achieves 12 times the throughput of BBR v1; yet when BBR v1 is replaced by BBR v3 under the exact same trace, BBR v3 achieves 11.6 times the throughput of CUBIC. In single-flow tests, AdvNet also found scenarios where BBR v1 achieves more than five times the throughput of BBR v3.

Even though BBR v3 was designed to improve fairness in typical settings, adversarial testing reveals specific conditions where version changes trigger severe regressions.

### 6.6 UC3: Does Adding a Path Hurt Performance? — DChannel

The third use case is validating specific design objectives. For example, a basic "do no harm" expectation for any multipath transport system is that using two paths should at least never perform worse than using just one of those paths alone. This can be tested by setting a single-path configuration as the reference and a dual-path configuration as the target.

They first evaluated **DChannel**, which combines a high-bandwidth path (HBP) and a low-latency path (LLP) in parallel while steering packets transparently below the transport layer. Here, the reference uses only the high-bandwidth path, the target uses DChannel over both paths, and the metric is flow completion time (FCT) for downloading a 20 MB file. Although prior work saw no issues when running loss-based CUBIC over DChannel, AdvNet found an environment where the HBP has a 120 ms one-way delay and the LLP has only a 3 ms one-way delay. In this environment, DChannel's throughput drops to one-third of that achieved using the HBP alone.

The root cause lies in DChannel's packet-steering heuristic. DChannel sends small control packets, such as TCP handshakes, over the fast LLP and large data packets over the slower HBP. Because the initial handshake completes over the 3 ms path, TCP estimates a tiny RTT and sets its retransmission timeout (RTO) to a small value. When large data packets subsequently take the 120 ms one-way HBP, their round-trip and queuing delay exceeds the small RTO before ACKs can return. This triggers spurious timeouts and rate reductions.

Figure 7 shows the download bitrate over time. Curves ending earlier mean the download finished faster. DChannel steers a packet to the LLP only when its estimated reward exceeds $\alpha$ times its cost (**Visual Suggestion**: Show $R > \alpha \times C$, with default $\alpha = 0.75$). As Fig. 7 shows, across all tested values of $\alpha$, DChannel takes longer to finish than using the single high-bandwidth path marked as `only eMBB`.

The authors confirm the root cause by manually reducing the HBP's RTT below 200 ms. In this case, DChannel once again outperformed the single path.

(**Visual Suggestion**: Show Fig. 7.)

### 6.7 UC3: Single-Path vs. Dual-Path in Kernel MPTCP

Finally, the authors tested the same "do no harm" objective on the Linux kernel implementation of MPTCP across all four of its congestion control algorithms: LIA, OLIA, BALIA, and wVegas. For every single one of them, AdvNet found environments where two paths yield lower throughput than one path.

For BALIA, dual-path throughput was 85.5% lower than single-path throughput. Plotting cumulative bytes sent over time, `balia2` initially sends faster by using the high bandwidth of Link 1, but `balia1` overtakes it after about 0.5 seconds. Around 1.2 seconds, after the receiver delays an ACK by roughly 40 ms, `balia2` sharply reduces its sending rate on both links—even though Link 1 still has plenty of available bandwidth.

(**Visual Suggestion**: Show Fig. 8. Mark balia2 as dual-path and balia1 as single-path.)

## Conclusion and Takeaways

To wrap up, AdvNet turns worst-case protocol testing into an automated black-box search over real code in emulation. Its search pipeline can uncover kernel bugs, catch version regressions, and validate design goals by pairing a compact interval representation and Post-Learning Selection with customizable reference comparisons.

The choice of optimizer could be a secondary factor, since GA achieves only a slightly better average score compared with the other optimization algorithms the authors tested. Formulating a compact domain representation and handling system execution noise may matter more. (**Visual Suggestion**: Consider showing Fig. 3b again.)

At the same time, AdvNet has clear boundaries. Its current environment model only covers link bandwidth, delay, and buffer size under simple workloads. In addition, it doesn't estimate how often a counterexample occurs in real deployments or automate root-cause diagnosis. Looking ahead, the framework could be extended to automatically simplify adversarial traces to speed up debugging, and applied to other dynamic systems such as adaptive bitrate video streaming.

## Backup Notes (For Q&A Only)

### Related Approaches — Formal Verification and GANs

**Formal verification** checks whether a system satisfies specified properties, using techniques such as model checking and symbolic analysis. These techniques typically require precise models or specifications and can struggle to scale to complex kernel implementations and large spaces of time-varying network conditions. AdvNet instead uses execution feedback to search for performance weaknesses in real implementations.

**Generative Adversarial Networks (GANs)** typically learn to generate data resembling an existing dataset. For AdvNet, the challenge is that we do not already have a dataset of challenging network environments to imitate. The search instead creates these environments using the observed performance gap as feedback.

### Alternative PLS Methods — RoundRobin and OCBA

**RoundRobin** divides the evaluation budget equally among the candidate environments, then selects the one with the highest observed mean score.

**Optimal Computing Budget Allocation (OCBA)** distributes evaluations adaptively to increase the probability of selecting the candidate with the highest true mean. It prioritizes candidates with greater uncertainty or scores close to the current best. Compared with RoundRobin, it focuses measurements where they can most help distinguish the leading candidates. Figure 11 compares these methods with MRE.

### Backup 1 — GA Operators in Equations

Here, $a$ and $b$ are the parent parameter vectors, and $i$ is a gene index. The cut points determine which coordinates the child takes from each parent. Mutation replaces each selected coordinate with a uniform integer sample from that coordinate's bounds.

### Backup 2 — Statistical Simulation of Selection (Fig. 11)

This experiment (Appendix B, Fig. 11) uses fifty Gaussian alternatives, with their true means sampled uniformly between zero and one hundred. The vertical axis is the true mean of the alternative selected by each method, averaged over two thousand trials. The oracle knows those true means. MRE performs best among the tested selection methods under this model, whereas OCBA struggles at small budgets (< 100 samples) because there are not enough samples per candidate to estimate variance reliably. Note that these values use a different scale from the normalized protocol-gap score.

### Backup 3 — Parallel Execution and Measurement Interference (Fig. 9 & Fig. 10)

To evaluate each candidate environment multiple times without increasing wall-clock time, AdvNet runs multiple Mahimahi instances in parallel, pinning 3 dedicated CPU cores per instance (one each for the emulator, `iperf` client, and `iperf` server).

In Appendix A (Fig. 9), testing fixed network parameters (1 Gbps bandwidth, 5 ms one-way delay) on a 30-core server showed that mean throughput gradually drops as parallelism increases due to hardware contention, and variance spikes sharply at 9 and 10 concurrent runs (where $9 \times 3 = 27$ cores approaches the 30-core limit). The authors therefore capped parallelism at 8.

In Fig. 10 (250 GA iterations), moving from 1 to 2 parallel runs initially lowers the final score because emulator contention distorts throughput during search (while the final output is always evaluated using a single isolated instance). Increasing parallelism further provides more samples to combat noise, peaking at 5-way parallelism—though the gain over a single evaluation per environment is marginal, so 1-way evaluation remains a practical low-CPU alternative.