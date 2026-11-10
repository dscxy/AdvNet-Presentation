# AdvNet Presentation Script

## 1. What Research Problem Are We Trying to Solve?

Today, we will introduce AdvNet, a system for adversarially testing network protocols, especially congestion control.

I'll start with the motivation and how AdvNet works.

First, let's start with some background. Bandwidth describes the capacity of a link, while throughput describes the rate that the protocol actually achieves.

In a network, a sender typically does not know how much bandwidth it can use. If it sends too slowly, throughput can be much lower than available bandwidth. If it sends too fast, packets will build up in router queues. This leads to higher round-trip time and eventually packet loss.

Creating a robust congestion control algorithm is hard. First, available resources and network conditions can change over time. So CC algorithms need to be optimized for throughput, loss, and latency in lots of environments. Second, they need to guarantee quick convergence to stable and fair rates when multiple senders compete. (**Adapted from PCC Vivace: Online-Learning Congestion Control §1**)

These requirements also make it difficult for the protocols to be thoroughly tested. Therefore, new protocols or an upgrade to an existing protocol may perform better in test suites, but they could introduce hidden performance regressions. How to find these scenarios is the main focus of this paper.

## 2. What Are the Existing Solutions, and Why Do They Fall Short?

How do developers test protocols today, and why isn't that enough?

First, hand-designed tests run a protocol under manually chosen parameters, such as fixed bandwidth and latency ranges. They are easy to interpret and they can check suspected problems directly, but their coverage depends on what the designer thinks of testing. Another problem is that many protocols retain certain states from the past, so the actual behavior may depend on previous environments. Thus, the number of possible test cases grows exponentially with sequence length.

Second, developers may replay captured traces in emulators like Mahimahi, or evaluate protocols on platforms like Pantheon and Puffer to test conditions that users actually experience. These are essential for benchmarking average real-world performance, but their coverage is bounded by where and when traces were collected. In addition, they do not actively search for unknown worst-case conditions. Reproducing real-world anomalies is also difficult due to uncontrolled background processes. (**Visual Suggestion**: Add visual-only notes that explain differences between Pantheon, Puffer, and Mahimahi.)

Third, what about automated adversarial testing? Here we first need to distinguish between simulation and emulation. Simulation (such as ns-3) runs simplified models of the protocol and network; it is fast and deterministic, but the modeled behavior can differ from real deployed code. Emulation (such as Mahimahi) runs the real operating system kernel protocol stack under controlled virtual links. It can capture real implementation bugs, but at the cost of slow execution and runtime noise.

An important piece of prior work, CC-Fuzz, used a genetic algorithm to generate adversarial environments, but only inside the ns-3 simulator, representing links via low-level Packet Delivery Opportunities. The problem is that its high-dimensional PDO representation struggles to find strong adversarial examples within a limited emulation budget.

## 3. How Does AdvNet Solve the Problem?

AdvNet addresses these gaps by formulating environment generation as a black-box search over real protocol executions. The user provides parameter bounds, a target protocol under test, and a reference baseline. The different baselines shown in the paper include another protocol, an older version of the same protocol, a single-path configuration, or a calculated capacity benchmark. (**Visual Suggestion**: Show Fig. 1.)

In each iteration, the generator outputs a candidate network trace, and the execution module runs both the target and reference inside an extended Mahimahi emulator (**Visual Suggestion**: Could add a note about the modifications that support time-varying one-way delay and dual paths). The scoring module then quantifies their relative performance gap as a score:

$$
\text{score} = \frac{R - P}{\max(R, P)} \quad (\text{when a higher metric value is better}).
$$

(**Visual Suggestion**: The formula is for display only. Also show a version that plugs in the numbers. Don't read the formula out. Add a note explaining P and R.)

For example, if the reference achieves 10 Mbps and the target gets only 2 Mbps, the score is 0.8. If a lower metric value is better—such as flow completion time—we reverse the numerator to P minus R. Dividing by the maximum normalizes the score between $-1$ and $1$, so a larger positive score always means a larger relative weakness in the target. The generator uses these scores as feedback to search for environments that expose larger performance gaps.

We can also combine throughput $\tau$ and average packet delay $d$ into a single utility metric using a throughput weight $t_{\mathrm{coeff}} \in [0, 1]$:

$$
U = t_{\mathrm{coeff}} \frac{\tau}{\tau_{\max}} + (1 - t_{\mathrm{coeff}}) \frac{d_{\min}}{d},
$$

(**Visual Suggestion**: The formula is for display only. Label $\tau_{\max}$ as the maximum-throughput benchmark and $d_{\min}$ as the minimum-delay benchmark used for normalization.)

A throughput weight of $1$ considers only throughput, $0$ considers only delay, and $0.5$ weights both normalized components equally. We compute this utility separately for the reference and target, using the same normalization benchmarks and weight. We then use their utilities as $R$ and $P$ in the earlier score formula. Since higher utility is better, a positive score means the target performs worse under the chosen throughput–delay tradeoff.

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

Uniform integer mutation replaces each gene with probability $p$ by sampling a new integer uniformly from that gene's allowed range. For example, change 15 to 73. Both operators preserve the integer format required by Mahimahi, and every newly generated trace is evaluated by running the protocols.

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

(**Visual Suggestion**: Show a table of 3 UCs. Don't read.)

Let's examine what AdvNet discovered in each of these three use cases.

### 6.2 UC1: Finding Suboptimal Performance and Comparing Protocol Weaknesses

The first use case is finding environments where an individual protocol performs suboptimally. Here, there are two ways to choose the reference. One is to use the theoretical link capacity, which helps catch severe underutilization—even though no protocol can achieve the theoretical limit at all times in a dynamic network, extremely poor performance still points to potential issues worth investigating.

The second, more realistic option is to compare against other existing protocols. In the paper, the authors ran an all-pairs comparison across 17 TCP congestion control algorithms in the Linux kernel. That gives $17\times16=272$ directed pairs, and with two different score definitions—an equal 50/50 split between throughput and delay, versus throughput only—there are 544 test scenarios in total. AdvNet found adversarial environments in 448 of them.

Let's look at BBR and CUBIC in the top-left corner. Under both score definitions, whether BBR is the reference and CUBIC is the target, or vice versa, AdvNet finds adversarial environments with scores close to 1 in all four cases (**TODO**: Consider reproducing this experiment and reporting the actual traces). It shows that even under the exact same performance metric, both protocols have their own distinct blind spots in different environments.

(**Visual Suggestion**: Show the full Fig. 4 heatmap, highlighting/zooming in on the top-left corner.)

In the paper, the authors dug into several of the discovered scenarios to find the root causes. Let's look at what they found.

### 6.3 UC1 Case Study: TCP Acknowledgment Bug Triggered by a Sudden RTT Drop

The first case study involves the Linux TCP implementation with BBR. AdvNet generated an adversarial environment that maintains a high RTT for about one second and then abruptly drops the RTT. As a result, packets sent later can arrive at the receiver before packets sent earlier.

Using tools like eBPF and Wireshark, the authors verified that this out-of-order arrival indeed happens. Seeing a gap in the sequence numbers, the receiver starts sending duplicate ACKs (dup ACKs). Once the sender receives three dup ACKs, it fast-retransmits the first delayed packet. However, before that retransmitted copy arrives, the original delayed packet finally reaches the receiver, which then sends an ACK advancing to the next expected packet in sequence. Right after that, the fast-retransmitted copy arrives—and this specific arrival order triggers a logic bug in how the receiver updates its acknowledgment number. Even after subsequent packets arrive normally, the receiver fails to advance the ACK number and keeps sending dup ACKs, eventually forcing the sender into a retransmission timeout (RTO).

(**TODO**: Draw a sequence diagram of this packet arrival order.)

This case highlights why manual root-cause analysis and real-code emulation are both essential. On the surface, we just see a sharp drop in throughput, but the underlying root cause is an implementation bug in the Linux kernel's TCP receive logic—something we would never catch if we only tested simplified protocol models in a simulator.

When the authors re-tested on a newer Linux kernel version, this bug no longer appeared. However, AdvNet uncovered another scenario where CUBIC ramps up its throughput quickly while BBR's throughput grows much more slowly. Fig. 6 shows the behavior over a short run, where BBR fails to utilize the available bandwidth.

(**Visual Suggestion**: Show Fig. 6.) (**TODO**: Consider analyzing this further.)

### 6.4 UC1 Case Study: Fairness Between Competing Flows

Another application of UC1 is testing fairness between competing flows. Here, we set the reference score to be the throughput of a protocol flow running alone, and the target score to be the throughput of that same flow when competing head-to-head against another protocol. This measures how badly the competing flow hurts our reference flow.

(**Visual Suggestion**: Show the topology comparison between "Running Alone" and "Competing Flows".)

While it is widely believed in the networking community that BBR tends to dominate CUBIC, AdvNet found environments where CUBIC grabs nearly 100% of the bandwidth and starves BBR. Conversely, when the authors swapped their roles, AdvNet also found environments where BBR starves CUBIC. Once again, which protocol is more aggressive depends heavily on the specific network conditions.

Inspecting the logs, the authors noticed that the starved flow initially runs normally for 40 to 80 seconds, but then abruptly degrades into sending just a single packet at a time—waiting for an ACK before sending the next packet—for the rest of the experiment. The authors reported this issue to the BBR development team, who confirmed the environment was problematic.

### 6.5 UC2: Comparing Different Versions of BBR

The second use case is regression testing: using the older version as the reference and the newer version as the target to find performance regressions.

The authors compared the fairness of BBR v1 and BBR v3 when competing against CUBIC. They run CUBIC alongside each version in turn. The throughput CUBIC gets when competing with BBR v1 is the reference score. Its throughput when competing with BBR v3 is the target score. In this experiment, AdvNet first varies the bandwidth and latency, then holds the network parameters fixed for one minute to let the protocols stabilize, and finally measures performance over the last ten seconds.

(**Visual Suggestion**: Show the two competing flow setups alongside a timeline of "Dynamic changes — 1 min fixed parameters — Final 10s measurement".)

In one adversarial environment discovered by AdvNet, CUBIC achieves 12 times the throughput of BBR v1; yet when BBR v1 is replaced by BBR v3, the outcome completely reverses, with BBR v3 achieving 11.6 times the throughput of CUBIC. In addition, the paper notes in the introduction that in single-flow tests, AdvNet found environments where BBR v1 achieves more than five times the throughput of BBR v3. These tests expose regressions in both fairness and throughput.

### 6.6 UC3: Does Adding a Path Hurt Performance? — DChannel

The third use case is validating specific design objectives. For example, a basic "do no harm" expectation for any multipath transport system is that using two paths should at least never perform worse than using just one of those paths alone. We can test this by setting a single-path configuration as the reference and a dual-path configuration as the target.

The authors first tested DChannel, a system that combines a high-bandwidth path (HBP) and a low-latency path (LLP) in parallel while steering packets transparently beneath the transport layer. Prior work found no issues when running loss-based CUBIC over DChannel. But AdvNet discovered a problematic environment: the HBP has a one-way delay of 120 ms, while the LLP has only 3 ms. In this environment, DChannel's throughput drops to one-third of what it achieves using the high-bandwidth path alone.

The culprit is DChannel's packet-steering heuristic, which prefers sending small control packets (like TCP handshakes) over the low-latency path and large data packets over the high-bandwidth path. Because the initial handshake travels over the fast path, the sender estimates a very small RTT and sets a short retransmission timeout, or RTO. The minimum RTO in Linux is roughly 200 ms. When subsequent large data packets are routed over the high-latency path, their ACKs cannot return before the RTO expires, triggering spurious timeouts and slashing the sending rate.

(**Visual Suggestion**: Show a diagram of small/large packet steering and how early low-RTT measurements lead to premature RTO expiration.)

Fig. 7 plots the throughput over time when downloading a 20 MB file—note that a curve ending earlier means the file finished transferring sooner, corresponding to a shorter flow completion time (FCT). Regardless of how we tune DChannel's internal steering parameter $\alpha$, it consistently trails the single high-bandwidth path (`only eMBB`). However, when the authors manually reduced the HBP's RTT below 200 ms, DChannel once again outperformed the single path, confirming the timeout explanation.

(**Visual Suggestion**: Show Fig. 7.)

### 6.7 UC3: Single-Path vs. Dual-Path in Kernel MPTCP

Beyond DChannel, the authors also tested the Linux kernel implementation of MPTCP across all four of its congestion control algorithms: LIA, OLIA, BALIA, and wVegas. For every single one of them, AdvNet found environments where using two paths yields lower throughput than using a single path.

Taking BALIA as an example, in the discovered adversarial environment, dual-path throughput was 85.5% lower than single-path throughput. Looking at cumulative bytes sent in Fig. 8, the dual-path configuration (`balia2`) initially sends faster by leveraging the high bandwidth of Link 1, but the single-path configuration (`balia1`) catches up and overtakes it after about 0.5 seconds. Around 1.2 seconds, after the receiver delays an ACK by roughly 40 ms, `balia2` sharply reduces its sending rate across both links—even though Link 1 still has plenty of bandwidth available.

(**Visual Suggestion**: Show Fig. 8, highlighting where the slope flattens at 1.2 seconds.)

### 6.8 Practical Takeaways from These Results

To sum up Section 6, these three use cases show how choosing different references allows the exact same search pipeline to uncover implementation bugs, catch version regressions, and validate design goals.

## Conclusion

To wrap up, AdvNet turns extreme-case testing into an automated search over network environments, revealing performance problems in real protocol implementations.

Of course, AdvNet still has some limitations. Its current environment model only covers a limited set of network parameters and relatively simple traffic workloads, and root-cause analysis still requires manual investigation. It also does not estimate how often the discovered environments occur in real deployments. Looking forward, the framework could be extended to support more complex network environments and to automatically simplify adversarial traces for easier diagnosis. The same approach could also be applied beyond network protocols, such as to adaptive bitrate video streaming, for which the authors have already built a prototype.

Overall AdvNet provides a practical complementary tool that helps developers proactively uncover hidden performance weaknesses and turn them into reproducible test cases.

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
