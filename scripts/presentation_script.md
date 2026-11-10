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

The first challenge is sample efficiency. One evaluation requires an actual protocol run. Longer traces cost more time, and repeating measurements leaves fewer chances to explore new environments.

The second challenge is practical usefulness. An environment with almost no capacity makes every protocol look bad. That alone tells a developer very little.

A reference makes the comparison more useful. If another implementation performs much better under the same external conditions, the gap is worth investigating.

(**Visual Suggestion**: Two-column summary comparing "Sample Efficiency: huge search space + slow execution + noise" and "Practical Usefulness: avoiding trivial extreme cases + meaningful reference comparisons".)

## 5. How Does AdvNet Address Sample Efficiency?

### 5.1 Representing a Network Trace

Now, what exactly does the search change? AdvNet represents a trace using four parts:

$$
T=(B,L,D,I).
$$

$B$ contains bandwidths, $L$ contains delays, and $D$ contains interval durations. $I$ contains parameters that stay fixed within the trace, such as queue capacity. For multipath tests, each link has its own bandwidth and delay sequence, with shared interval durations.

Here is a teaching example. The first interval has twenty megabits per second and twenty milliseconds of one-way delay. Bandwidth then falls while delay rises. Finally, bandwidth recovers and delay falls. Each parameter has allowed bounds.

(**Visual Suggestion**: Show a step-function plot illustrating the 3-interval bandwidth/one-way delay teaching trace, alongside the parameter bounds in Table 1.)

CC-Fuzz represents link service using packet delivery opportunities, or PDOs. Each PDO specifies a time when the link can transmit a packet.

The authors implemented that representation inside AdvNet and compared it with their interval representation under matched configurations (Table 2). For BBR, the scores were about seventy-nine percent and fourteen percent. Higher means a larger throughput shortfall relative to available capacity.

The authors give two explanations. First, PDOs create a larger search space. For example, increasing from twenty-five to one hundred PDOs causes the score on BBR to drop from about fourteen percent to about six percent. Second, AdvNet directly exposes delay changes as search parameters.

(**Visual Suggestion**: Show the comparison results in Table 2.)

### 5.2 Generating the Next Batch of Environments

With the representation fixed, how does AdvNet find increasingly challenging environments?

The authors first considered an online adversary, such as reinforcement learning, that observes protocol behavior and chooses the next network condition during execution. But synchronizing the adversary with both the target and reference proved difficult, so they chose to generate complete traces before execution, making them easy to replay and compare.

AdvNet's main search method is a **genetic algorithm**, or **GA**. Each candidate is a complete network trace, and its genes are the numerical parameters we just introduced: bandwidths, delays, durations, and fixed settings such as queue capacity.

GA maintains a population of these candidates. It runs the protocols to evaluate each candidate's fitness, using the performance-gap score. Selection favors promising candidates, while crossover and mutation produce the next generation. This cycle continues until the search budget runs out.

(**Visual Suggestion**: Show the GA loop: population of traces → protocol evaluation → selection → crossover and mutation → next generation.)

Let us look at the two operators. In **two-point crossover**, we choose two cut points and exchange the segment between them. In this simplified four-gene example, each child keeps one parent's outside values and takes the other parent's middle values. For actual traces, corresponding positions represent the same network parameter, so swapping them preserves their allowed bounds.

**Uniform integer mutation** introduces new values. Each gene has a probability of being replaced by an integer sampled uniformly from its allowed range. Here, one gene changes from fifteen to seventy-three. Crossover recombines existing values; mutation can introduce values absent from the parents. Both preserve the integer format required by the emulator, and every new trace is evaluated by running the protocols.

(**Visual Suggestion**: Show parents [20, 5, 40, 10] and [60, 30, 15, 80], with cuts around the middle two genes. Show children [20, 30, 15, 10] and [60, 5, 40, 80], then mutate 15 → 73 within an illustrative range of 1–100.)

Does this search actually help? In Figure 3a, GA outperforms random generation under each tested throughput–delay weighting, within a one-hour budget. The authors also compare GA with Bayesian optimization and epsilon-greedy search using two-hour budgets. No method wins every setting, but GA has the highest overall average, so they use it in subsequent experiments.

(**Visual Suggestion**: Show Fig. 3a and Fig. 3b; label the throughput weight and runtime budgets.)

Finding high scores is only part of the problem. Next, we need to choose a trace whose score remains high when we run it again.

### 5.3 Avoiding Lucky Outliers

There is one more problem: noisy measurements. The simplest rule, **SimpleMax**, returns whichever trace had the highest observed score during search.

But that winner may have benefited from an unusually favorable measurement. When we test it again, its score may drop. Searching more candidates creates more opportunities for such lucky observations.

(**Visual Suggestion**: Show a scatter plot of Environment A (high mean, low variance) vs. Environment B (low mean, but one lucky high outlier) to explain why SimpleMax can pick the wrong trace.)

The paper uses repeated protocol runs during search and takes median performance measurements. **Post-Learning Selection**, or **PLS**, adds a separate selection stage after search. Finally, independent evaluation checks the returned trace.

PLS starts with the twenty-five highest-scoring environments found during search.

AdvNet uses **multi-round elimination**, or **MRE**. In each round, it evaluates every remaining candidate once, then removes roughly the lower half according to their observed means so far.

Once five or fewer remain, it stops eliminating and keeps evaluating until the budget ends. It returns the highest observed mean. This concentrates measurements on promising candidates.

How much time should selection receive? In this experiment (Fig. 2), the best result came from spending ninety percent of the budget on search and ten percent on PLS.

Too little selection can leave an unreliable winner. Too much selection leaves less time to discover strong candidates. The best split here reflects that tradeoff.

(**Visual Suggestion**: Show the MRE funnel diagram alongside Fig. 2, and a bottom timeline summarizing "Median during search → Mean via MRE in PLS → Independent final evaluation".)

Together, the compact trace representation, genetic search, and post-learning selection help AdvNet find environments with reliably high scores within a limited evaluation budget.

With that, I will hand over to Xiaoyang, who will discuss how the paper uses these environments to study protocol behavior.

## 6. How Does AdvNet Ensure Practical Utility?

### 6.1 Formulating Test Objectives as Relative Performance Gaps

Now that we've seen how AdvNet searches efficiently, the next question is: why are the environments it finds actually useful? The authors' answer is to let the user choose the reference, the target, and the performance metrics that matter for their task, and then turn those into an optimizable score.

(**Visual Suggestion**: Show the score definition from the paper.)

For example, suppose the reference protocol achieves 10 Mbps and the target gets only 2 Mbps. We take the difference, 8 Mbps, and divide by the larger value, 10 Mbps. That gives a score of 0.8. For a metric where lower is better, such as flow completion time, we reverse the subtraction: target minus reference. A higher score therefore always means a larger disadvantage for the target. Dividing by the larger value keeps the score between -1 and 1 and removes the effect of absolute scale.

Multiple metrics can also be combined via a weighted average. We first normalize throughput and delay so that higher values mean better performance, then combine them using the chosen weights. (**Visual Suggestion**: Show the weighted utility formula with throughput and delay as an example. Normalize throughput as $\tau/\tau_{\max}$ and delay as $d_{\min}/d$, so both are higher-is-better quantities, then combine them as $t_{\mathrm{coeff}}\,\tau/\tau_{\max} + (1-t_{\mathrm{coeff}})\,d_{\min}/d$).

In the paper, the authors demonstrate three practical use cases for adversarial testing. Let's walk through each of them.

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
