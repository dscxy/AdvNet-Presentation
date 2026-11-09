# AdvNet Presentation Script — Revised

33 main slides and 6 backup slides. Bullet points and visual suggestions are preparation notes; read only the Script text. The spoken content follows the supplied v2 script with limited factual and wording corrections.


## 1. Research problem

### Slide 01 — AdvNet

**Bullet Points**

- Adversarial testing of real network protocol implementations
- Motivation, search design, and practical use cases

**Script**

Today, we will introduce AdvNet, a system for adversarially testing network protocols, especially Congestion Control. The question is simple: even if a protocol works well in existing tests, can we automatically find network conditions where it performs much worse?

I'll start with the motivation and how AdvNet works, focusing on its search design.

**Visual Suggestion**: Minimal title slide

Source check (not spoken): AdvNet paper §1–3

---

### Slide 02 — Bandwidth and throughput

**Bullet Points**

- Bandwidth is link capacity; throughput is the achieved rate
- Sending too slowly leaves capacity unused
- Sending too quickly builds queues and increases delay

**Script**

First, a little background. Bandwidth describes the capacity of a link. Throughput describes the rate that the protocol actually achieves. For a continuously backlogged flow with no other bottleneck, the goal is to make throughput close to the available capacity.

The problem is a sender usually does not know how much bandwidth it can use. Sending too slowly wastes capacity. Sending too quickly builds a queue and increases delay.

**Visual Suggestion**: Sender, bottleneck queue, receiver, and ACK path

Source check (not spoken): AdvNet paper §1–3

---

### Slide 03 — What controls TCP sending?

**Bullet Points**

- Congestion window limits unacknowledged data in flight
- Pacing controls packet departure timing
- ACK handling and retransmission timers also affect performance

**Script**

Two mechanisms help control sending. The congestion window limits how much unacknowledged data can be in flight. Pacing controls how quickly packets leave the sender. A fast path with a long round-trip time usually needs more data in flight, thus bigger cwnd, to stay busy. In addition, acknowledgment and retransmission logic—such as duplicate ACKs and retransmission timeouts (RTO)—also directly affect performance.

**Visual Suggestion**: Two-column list of sending controls and feedback

Source check (not spoken): AdvNet paper §1–3

---

### Slide 04 — Why congestion control is hard to test

**Bullet Points**

- Large space of network parameters and temporal patterns
- Protocol state carries across changes in conditions
- Protocol updates can introduce regressions in unfamiliar environments

**Script**

Why is it so hard to make congestion control robust? First, Internet environments vary widely across bandwidths, latencies, queue sizes, and time-varying patterns—and protocols retain state from the past, so even a slight increase in packet loss or a sudden shift in delay can cause throughput to collapse. Second, consider a protocol developer upgrading an existing protocol—for example, evolving BBR from v1 to v2 and v3, or adding multipath support. A change designed to help in common scenarios can unintentionally introduce severe regressions, starvation, or timeouts when encountering an unanticipated sequence of network changes.

**Visual Suggestion**: Two-column list: environment changes and protocol updates

Source check (not spoken): AdvNet paper §1–3

---

## 2. Existing solutions

### Slide 05 — Existing testing methods

**Bullet Points**

- Hand-designed tests cover anticipated scenarios
- Trace replay and testbeds reflect sampled deployments
- Neither systematically searches for unknown worst cases

**Script**

How do developers test protocols today, and why isn't that enough?

First, **hand-designed tests** run a protocol under manually chosen parameters, such as fixed bandwidth and latency ranges. They are easy to interpret and great for checking a suspected issue, but their coverage is limited to scenarios the designer already thought of testing—they cannot cover the exponential space of time-varying sequences.

Second, **real-world trace replay and testbeds**—such as replaying captured traces in Mahimahi, or evaluating protocols on platforms like Pantheon and Puffer—test conditions that users actually experience. These are essential for benchmarking average real-world performance, but their coverage is bounded by where and when traces were collected. They do not actively search for unknown worst-case conditions, and when an anomaly does happen in live deployment, uncontrolled background processes make it very hard to reproduce.

**Visual Suggestion**: Comparison table: designed tests and collected traces

Source check (not spoken): AdvNet paper §1–3

---

### Slide 06 — Simulation and emulation

**Bullet Points**

- Simulation evaluates protocol and network models
- Emulation executes real implementations under controlled conditions
- Real-code evaluations cost time and contain execution noise

**Script**

Third, what about **automated adversarial testing**? Here we first need to choose between **simulation** and **emulation**. Simulation (such as ns-3) runs simplified models of the protocol and network; it allows controlled, repeatable experiments, but its runtime and determinism depend on the model and configuration, and modeled behavior can differ from deployed code. Emulation (such as Mahimahi) runs the real operating system kernel protocol stack under controlled virtual links—capturing real implementation bugs in timers and state machines, but at the cost of slow execution and runtime noise.

**Visual Suggestion**: Comparison table: simulation and emulation

Source check (not spoken): AdvNet paper §1–3

---

### Slide 07 — CC-Fuzz and the move to emulation

**Bullet Points**

- CC-Fuzz uses GA and packet delivery opportunities in ns-3
- PDOs specify packet-service times
- Higher dimension can make search harder under a fixed emulation budget

**Script**

Prior work, most notably **CC-Fuzz**, used a genetic algorithm to generate adversarial environments, but only inside the ns-3 simulator, representing links via low-level Packet Delivery Opportunities (PDOs). When moving from simulation to emulation to test real Linux kernel code, evaluations become much slower and noisy—and as we will see shortly, CC-Fuzz's high-dimensional PDO representation struggles to find strong adversarial examples within a limited emulation budget.

**Visual Suggestion**: PDO definition and finite-budget implications

Source check (not spoken): AdvNet paper §1–3

---

## 3. Framework

### Slide 08 — The AdvNet framework

**Bullet Points**

- Search over candidate network environments
- Compare a target with a meaningful reference
- Use measured performance gaps as feedback

**Script**

AdvNet addresses these gaps by formulating environment generation as a black-box search over real protocol executions. The user provides parameter bounds, a **target** protocol under test, and a **reference** baseline—which can be another protocol, an older version of the same protocol, a single-path configuration, or a calculated capacity benchmark.

**Visual Suggestion**: Paper Fig.1 architecture

Source check (not spoken): AdvNet paper Fig.1; §3

---

### Slide 09 — The performance-gap score

**Bullet Points**

- Score measures relative target weakness
- A positive score means the reference performs better
- A throughput weight combines normalized throughput and delay

**Script**

In each iteration, the generator outputs a candidate network trace, and the execution module runs the target and, when the reference is another protocol, runs the reference inside an extended Mahimahi emulator (which the authors modified to support time-varying one-way delay and dual paths). The scoring module then quantifies their relative performance gap as a **score**:

$$
\text{score} = \frac{R - P}{\max(R, P)} \quad (\text{when higher metric is better}).
$$

For example, if the reference achieves $R = 10$ Mbps and the target gets only $P = 2$ Mbps, the score is $(10 - 2)/10 = 0.8$. If a lower metric is better—such as flow completion time—we reverse the numerator to $P - R$. For nonnegative metrics with a positive denominator, dividing by the maximum normalizes the score between $-1$ and $1$, so a larger positive score always means a larger relative weakness in the target. We can also combine throughput $\tau$ and average packet delay $d$ into a single utility metric using a throughput weight $t_{\mathrm{coeff}} \in [0, 1]$:

$$
U = t_{\mathrm{coeff}} \frac{\tau}{\tau_{\max}} + (1 - t_{\mathrm{coeff}}) \frac{d_{\min}}{d},
$$

where $t_{\mathrm{coeff}} = 1$ cares only about throughput, $0$ cares only about delay, and $0.5$ weights the two normalized terms equally. Here, $\tau_{\max}$ and $d_{\min}$ are the throughput and delay normalization benchmarks.

**Visual Suggestion**: Score and utility equations with symbol definitions

Source check (not spoken): AdvNet paper §3.5, Eq.(1)

---

### Slide 10 — Post-learning selection

**Bullet Points**

- Reserve part of the total budget for candidate selection
- Repeat measurements of promising environments
- Independently re-evaluate the returned trace

**Script**

Finally, because emulation has random variance, AdvNet reserves the last portion of its time budget for **Post-Learning Selection (PLS)** to choose among promising candidates using repeated measurements and observed mean scores, followed by an independent re-evaluation.

**Visual Suggestion**: Search / PLS / independent evaluation sequence

Source check (not spoken): AdvNet paper §1–3

---

## 4. Challenges

### Slide 11 — Two design challenges

**Bullet Points**

- Sample efficiency: balance new candidates and repeated measurements
- Practical usefulness: avoid trivial or uninformative comparisons

**Script**

Realizing this framework in emulation brings two main challenges:

The first challenge is **sample efficiency**. Because every evaluation runs real kernel protocols over emulated links for several seconds, we can only afford a limited number of runs. Meanwhile, the space of time-varying parameters is huge, and emulation noise means a single run can be misleading—yet repeating every trace many times would leave very little budget to explore new environments.

The second challenge is **practical usefulness**. Setting link bandwidth to zero makes every protocol get zero throughput, which is useless for diagnosis. Similarly, if bandwidth jumps instantaneously, any protocol needs time to adapt, so falling short of link capacity right after a spike is expected. Using a realistic reference—and designing the comparison around concrete developer tasks—is essential to uncover actionable flaws.

**Visual Suggestion**: Two-column challenge comparison

Source check (not spoken): AdvNet paper §1–3

---

## 5. Sample efficiency

### Slide 12 — Representing a network trace

**Bullet Points**

- A trace contains interval bandwidths, delays, and durations
- Queue capacity and optional transfer size remain fixed within a trace
- Search stays within parameter-specific bounds

**Script**

Now, what exactly does the search change? AdvNet represents a trace using four parts:

$$
T=(B,L,D,I).
$$

$B$ contains bandwidths, $L$ contains one-way delays, and $D$ contains interval durations. $I$ contains parameters that stay fixed within the trace, such as queue capacity. For multipath tests, each link has its own bandwidth and delay sequence, with shared interval durations.

Here is a teaching example. The first interval has twenty megabits per second and twenty milliseconds of one-way delay. Bandwidth then falls while delay rises. Finally, bandwidth recovers and delay falls. Each parameter is constrained within user-specified bounds (for example, 1 to 100 Mbps, 5 to 100 ms, and 0.5 to 2.5 seconds per interval in Table 1).

**Visual Suggestion**: Three-interval teaching trace table and Table 1 bounds

Source check (not spoken): AdvNet paper §3.1, Table 1; teaching example

---

### Slide 13 — Intervals versus packet delivery opportunities

**Bullet Points**

- Interval representation reaches higher scores in the matched comparison
- More PDOs increase search dimension
- Direct delay control exposes important failure conditions

**Script**

Why use intervals instead of CC-Fuzz's packet delivery opportunities (PDOs), where each PDO specifies the exact timestamp when a packet can leave? The authors implemented the PDO representation inside AdvNet and compared both under matched genetic algorithm settings and a one-hour budget (Table 2). Across all four protocols, AdvNet's interval representation achieves much higher scores—for instance, about 79% versus 14% on BBR.

The authors point to two reasons. First, PDOs create a much higher-dimensional search space: when the number of PDOs is increased from 25 to 100, the search struggles even more, and the score on BBR drops from 14.31% down to 5.91%. Second, AdvNet directly exposes link delay changes as tunable parameters, which turns out to be critical for triggering several protocol bugs.

**Visual Suggestion**: Paper Table 2

Source check (not spoken): AdvNet paper §4.2.1, Table 2

---

### Slide 14 — Trace-based and action-based adversaries

**Bullet Points**

- Online actions require reliable synchronization across executions
- Timing jitter can leave actions based on stale information
- Complete traces make external conditions easier to replay and compare

**Script**

With the representation fixed, how does AdvNet search for challenging environments?

The authors first considered an **action-based** online adversary, such as reinforcement learning, that observes protocol state and chooses the next network condition on the fly. However, when running both a target and a reference in emulation, their internal states naturally diverge, and OS scheduling jitter makes it difficult to keep online actions synchronized across both runs. They therefore chose a **trace-based** adversary that outputs a complete trace before execution, making external conditions easier to replay and compare without online action synchronization.

**Visual Suggestion**: Comparison of online actions and complete traces

Source check (not spoken): AdvNet paper §1–3

---

### Slide 15 — Genetic algorithms in AdvNet

**Bullet Points**

- Each candidate is one complete network trace
- Fitness comes from measured protocol performance
- Selection, crossover, and mutation generate new candidates

**Script**

AdvNet's main search method is a **genetic algorithm (GA)**. Each candidate is a complete network trace, and its genes are the numerical parameters in $T$. GA maintains a population of traces, evaluates their fitness using the performance-gap score, selects promising parents, and applies crossover and mutation to produce the next generation until the budget expires.

**Visual Suggestion**: Retain the DNA analogy from the earlier deck

Source check (not spoken): AdvNet paper §1–3

---

### Slide 16 — Crossover and integer mutation

**Bullet Points**

- Two-point crossover exchanges an aligned parameter segment
- Uniform mutation resamples a gene within its own integer bounds
- Every new trace needs protocol evaluation

**Script**

Let us look at the two operators. In **two-point crossover**, we choose two cut points and swap the middle segment between two parent traces. In a four-gene example, each child keeps one parent's outer values and takes the other parent's middle values. In real traces, because crossover swaps aligned positions, a bandwidth parameter always replaces a bandwidth parameter, preserving each gene's allowed bounds.

**Uniform integer mutation** replaces each gene with probability $p$ by sampling a new integer uniformly from that gene's allowed range—for example, changing 15 to 73. Both operators preserve the integer format required by Mahimahi, and every newly generated trace is evaluated by running the protocols.

**Visual Suggestion**: Editable colored crossover table plus mutation example

Source check (not spoken): AdvNet paper §1–3

---

### Slide 17 — Evidence for the search design

**Bullet Points**

- GA outperforms random generation in the shown settings
- GA, BO, and EPS have similar overall performance
- The two panels use different total runtime budgets

**Script**

The authors also compared GA against three other trace-based methods: **Random Generation (RG)**, which samples traces uniformly at random as a baseline; **Bayesian Optimization (BO)** with a random forest surrogate model; and **Epsilon-Greedy Search (EPS)**, which mutates top-performing traces with probability $1-\epsilon$ and explores randomly with probability $\epsilon$.

In Figure 3a, under a one-hour budget across 20 protocol pairs, GA consistently outperforms random generation across all three throughput weights $t_{\mathrm{coeff}} = 0, 0.5,$ and $1$ (improving scores by 23% on average), supporting the benefit of using execution feedback under these tested settings. In Figure 3b, under a two-hour budget, GA, Bayesian optimization, and epsilon-greedy search achieve fairly similar performance, with GA having a slightly higher average, so the authors adopt GA as the default.

**Visual Suggestion**: Paper Fig.3(a,b), with one-hour and two-hour labels

Source check (not spoken): AdvNet paper §4.2.3, Fig.3

---

### Slide 18 — Noisy scores and SimpleMax

**Bullet Points**

- SimpleMax returns the largest observed search score
- A lucky observation can inflate the apparent winner
- Independent re-testing can reveal a lower score

**Script**

Finding high scores during search is only part of the problem; measurement noise can still mislead our final choice. The simplest rule, **SimpleMax**, simply outputs whichever trace had the single highest observed score during search.

However, when evaluating hundreds of traces, the single highest observation is often a "lucky outlier" inflated by positive random noise, whose score drops sharply when re-tested independently.

**Visual Suggestion**: Selection rule and noise explanation

Source check (not spoken): AdvNet paper §1–3

---

### Slide 19 — Multi-round elimination

**Bullet Points**

- Start from the top 25 candidates
- Evaluate survivors and eliminate roughly the lower half by mean
- At five or fewer candidates, stop elimination and keep measuring

**Script**

To mitigate noise, AdvNet runs each trace multiple times in parallel during search and uses the **median reference and target performance measurements** to compute the score. After search finishes, **Post-Learning Selection (PLS)** takes the top 25 candidate environments and allocates a dedicated evaluation budget using **Multi-Round Elimination (MRE)**. In each round, MRE evaluates every remaining candidate once and discards roughly the lower half based on their observed mean scores so far. Once 5 or fewer candidates remain, elimination stops and they are repeatedly evaluated until the budget is spent, returning the one with the highest mean score (which is then checked in one final independent evaluation).

**Visual Suggestion**: Numbered MRE procedure

Source check (not spoken): AdvNet paper §1–3

---

### Slide 20 — The search and selection budget

**Bullet Points**

- The tested setting favors 90% search and 10% PLS
- Too little selection risks an unreliable winner
- Too much selection leaves less exploration time

**Script**

How should we split the total runtime between search and PLS? In Figure 2, when $0\%$ of the time is used for PLS (which is just SimpleMax), noisy outliers leave the average re-tested score around $0.59$. Dedicating **$10\%$** of the runtime to PLS (and $90\%$ to GA search) raises the average score to about $0.80$, an increase of roughly $0.21$ score units. Spending more than $10\%$ on PLS causes the score to dip slightly, because taking too much time away from GA leaves fewer iterations to discover strong candidates in the first place.

**Visual Suggestion**: Paper Fig.2 and the 90/10 budget split

Source check (not spoken): AdvNet paper §4.2.2, Fig.2

---

### Slide 21 — From search design to practical use

**Bullet Points**

- Compact representation makes the search manageable
- GA uses execution feedback to discover challenging traces
- PLS selects an output for practical investigation

**Script**

Together, the compact interval representation, genetic search, and post-learning selection allow AdvNet to find reliably adversarial environments within a limited emulation budget. With that, I will hand over to Xiaoyang, who will show how AdvNet uses these environments across concrete protocol testing use cases.

**Visual Suggestion**: Handoff to Xiaoyang

Source check (not spoken): AdvNet paper §1–3

---

## 6. Practical utility

### Slide 22 — Developer tasks and comparisons

**Bullet Points**

- UC1: underutilization and fairness
- UC2: regressions between protocol versions
- UC3: whether using a second path can hurt

**Script**

Now that we have seen how AdvNet searches efficiently, let's look at how developers can use it to answer practical questions. By simply changing how we define the **reference** and the **target** inside the same scoring pipeline, the authors apply AdvNet to three distinct use cases:

* **UC1 — Finding suboptimal performance and fairness issues**: We set the target to be the protocol under test, and compare it against either theoretical link capacity or another protocol implementation (or compare a reference flow running alone versus competing head-to-head with the target) to uncover severe underutilization, kernel bugs, or starvation.
* **UC2 — Regression testing across versions**: We set the older version of a protocol as the reference and the newer version as the target, searching for environments where an update degrades throughput or fairness.
* **UC3 — Validating design objectives**: To test the "do no harm" goal of multipath transport, we set a single-path configuration as the reference and a dual-path configuration as the target.

Let's examine what AdvNet discovered in each of these three use cases.

**Visual Suggestion**: Use-case / reference / target / question table

Source check (not spoken): AdvNet paper §1–3

---

### Slide 23 — 17 TCP protocols: pairwise robustness

**Bullet Points**

- 17 protocols give 272 directed pairs per utility definition
- Two utility definitions give 544 scenarios
- AdvNet found positive scores in 448 scenarios

**Script**

Under UC1, while comparing against theoretical link capacity can flag extreme underutilization, comparing against another real protocol is even more informative: if another protocol achieves much higher performance under the exact same trace, we know better performance is achievable in practice.

The authors ran an all-pairs comparison across 17 TCP congestion control algorithms in the Linux kernel (Figure 4). That gives $17\times16=272$ directed pairs, tested under two utility definitions—an equal 50/50 split between throughput and delay ($t_{\mathrm{coeff}}=0.5$), and throughput only ($t_{\mathrm{coeff}}=1$)—for 544 scenarios in total, each with a two-hour budget. AdvNet found adversarial environments (positive scores) in 448 of the 544 scenarios, and every single protocol had at least one environment where another reference protocol substantially outperformed it.

**Visual Suggestion**: Paper Fig.4(a), equal weights

Source check (not spoken): AdvNet paper §4.3, Fig.4(a)

---

### Slide 24 — Different traces, different weaknesses

**Bullet Points**

- BBR and CUBIC can each outperform the other on different traces
- Each heatmap cell comes from a separate search
- A performance gap locates a problem but does not explain its cause

**Script**

Look at BBR and CUBIC in the top-left corner of both heatmaps. Under both objectives, whether BBR is the reference and CUBIC is the target (scores of $0.94$ and $0.85$), or CUBIC is the reference and BBR is the target (scores of $0.70$ and $0.86$), AdvNet finds environments with large performance gaps in both directions. Because each cell comes from a separate search, this is not a contradiction: it shows that even under the same metric, both protocols have distinct blind spots under different network dynamics.

However, a high score alone only tells us *where* a protocol struggles, not *why*. Next, let's look at how the authors diagnosed the root causes inside several discovered environments.

**Visual Suggestion**: Paper Fig.4(b), throughput only

Source check (not spoken): AdvNet paper §4.3, Fig.4(b)

---

### Slide 25 — A Linux TCP acknowledgment bug

**Bullet Points**

- A sudden delay drop creates packet reordering
- Three duplicate ACKs trigger a spurious fast retransmission
- A specific arrival order breaks ACK advancement and leads to RTO

**Script**

The first case study investigates why BBR scored so poorly under the throughput-only objective ($t_{\mathrm{coeff}}=1$). Examining the logs, the authors found that AdvNet generated an environment that maintains a high RTT for about one second and then abruptly drops the RTT. As a result, packets sent earlier during the high-RTT phase are still in flight when packets sent later during the low-RTT phase arrive at the receiver first.

Using eBPF and Wireshark, the authors traced the exact sequence of events:
1. Seeing out-of-order packets, the receiver sends duplicate ACKs (dup ACKs), which quickly reach the sender over the now-low RTT.
2. Upon receiving three dup ACKs, the sender initiates a fast retransmit for the delayed packet—even though it was never lost, just delayed.
3. Crucially, the original delayed packet finally arrives at the receiver *just before* its fast-retransmitted copy. The receiver processes the original packet and advances its ACK number.
4. Immediately afterward, the fast-retransmitted copy arrives. This specific arrival order triggers a corner-case bug in the Linux kernel's ACK-update logic: even as subsequent packets arrive normally, the receiver fails to advance the acknowledgment number and keeps sending dup ACKs, eventually forcing the sender into a retransmission timeout (RTO).

**Visual Suggestion**: Numbered packet and ACK event sequence

Source check (not spoken): AdvNet paper §4.4.1

---

### Slide 26 — BBR v3: slow convergence

**Bullet Points**

- The earlier ACK bug did not appear in these newer-kernel tests
- BBR v3 remains slow during the short trace
- Longer runs show recovery; changing fq_codel to fq did not remove the behavior

**Script**

Why did this kernel TCP receive bug surface specifically when testing BBR? The authors attribute the triggering sequence to BBR's pacing behavior, which helped produce this particular packet-arrival order in their experiment. This also underscores the value of emulating real kernel code rather than testing simplified simulator models.

When the authors re-tested on a newer Linux kernel (6.13.7+) from Google's BBR team, the earlier ACK bug did not appear in their tests. Even so, AdvNet found another scenario (Figure 6) where CUBIC quickly ramps up throughput while BBR v3 stays low during a short 5-second run. Extending the run showed that BBR v3 eventually ramps up—indicating a **slow convergence** issue rather than a permanent stall—and switching Mahimahi's queue discipline from `fq_codel` to Google's recommended `fq` did not eliminate this behavior.

**Visual Suggestion**: Paper Fig.6

Source check (not spoken): AdvNet paper §4.4.1, Fig.6

---

### Slide 27 — Fairness between competing flows

**Bullet Points**

- Compare reference throughput alone and with a competing target
- The search can find starvation in either direction
- Some runs abruptly fall to one packet per ACK after 40–80 seconds

**Script**

A second way to use UC1 is testing fairness between competing flows. Here, we define the reference score as the throughput of a reference protocol running alone on the link, and the target score as the throughput of that same reference flow when competing simultaneously against a target protocol. A high score means the competing flow severely starves the reference flow.

While BBR is commonly perceived as dominating loss-based protocols like CUBIC, AdvNet discovered environments where CUBIC consumes nearly 100% of the link bandwidth and starves BBR—and when their roles were reversed, AdvNet also found environments where BBR starves CUBIC.

Digging into the logs, the authors found a striking pathology: the affected flow initially operates normally for 40 to 80 seconds, but then abruptly drops its sending rate to just a single packet at a time—waiting for an ACK before sending the next packet—for the remaining 25 to 60 seconds of the test. The authors reported this environment to the BBR development team, who confirmed the issue.

**Visual Suggestion**: Fairness comparison and reported one-packet-per-ACK behavior

Source check (not spoken): AdvNet paper §3.5, §4.4.2

---

### Slide 28 — Regression testing: BBR v1 and v3

**Bullet Points**

- Compare the same CUBIC competitor alongside BBR v1 and v3
- Use 60 seconds of fixed conditions and measure the final 10 seconds
- The discovered environment reverses the throughput balance

**Script**

Moving to UC2, the authors used AdvNet for regression testing between BBR v1 and BBR v3, focusing on their fairness toward a competing CUBIC flow. In each candidate environment, they run two tests: first, CUBIC competing alongside BBR v1 (whose CUBIC throughput serves as the reference score), and second, CUBIC competing alongside BBR v3 (whose CUBIC throughput serves as the target score). To measure steady-state impact rather than transient jitter, AdvNet first varies bandwidth and latency, then holds the network conditions fixed for one minute, and measures throughput over the final ten seconds.

In one adversarial environment discovered by AdvNet, when CUBIC competes with BBR v1, CUBIC achieves 12 times the throughput of BBR v1; yet when BBR v1 is replaced by BBR v3 under the exact same trace, the balance completely reverses, with BBR v3 achieving 11.6 times the throughput of CUBIC. In single-flow tests, AdvNet also found scenarios where BBR v1 achieves more than five times the throughput of BBR v3.

Why do we see such dramatic reversals between versions? As the authors note, these outcomes are a direct consequence of the suboptimal BBR behaviors—such as rate collapse and slow convergence—uncovered in the earlier case studies. Even though BBR v3 was designed to improve fairness in typical settings, adversarial testing reveals specific dynamic conditions where version changes trigger severe regressions.

**Visual Suggestion**: Fixed-condition measurement sequence and version comparison table

Source check (not spoken): AdvNet paper §4.4.5; introduction

---

### Slide 29 — DChannel and early timeout estimates

**Bullet Points**

- Handshake packets use the low-latency path
- Early RTT estimates produce a low retransmission timeout
- High-bandwidth-path data can time out before ACKs return

**Script**

In UC3, the authors test a clear design objective for multipath transport: using two paths should never perform worse than using just one of those paths alone.

They first evaluated **DChannel**, which combines a high-bandwidth path (HBP) and a low-latency path (LLP) in parallel while steering packets transparently below the transport layer. Here, the reference uses only the high-bandwidth path, the target uses DChannel over both paths, and the metric is flow completion time (FCT) for downloading a 20 MB file. Although prior work saw no issues when running loss-based CUBIC over DChannel, AdvNet found an environment—where the HBP has a 120 ms one-way delay and the LLP has only a 3 ms one-way delay—in which DChannel's throughput drops to one-third of using the HBP alone.

The root cause lies in DChannel's packet-steering heuristic, which sends small control packets (such as TCP handshakes) over the fast LLP and large data packets over the slower HBP. Because the initial handshake completes over the 3 ms path, TCP estimates a tiny RTT and sets its retransmission timeout (RTO) to the Linux minimum of roughly 200 ms. When large data packets subsequently take the 120 ms one-way HBP, their round-trip and queuing delay exceeds the 200 ms RTO before ACKs can return—triggering spurious timeouts and rate reductions.

**Visual Suggestion**: Path delays and a numbered timeout mechanism

Source check (not spoken): AdvNet paper §4.4.3

---

### Slide 30 — DChannel: two paths can finish later

**Bullet Points**

- The metric is completion time for a 20 MB transfer
- All tested alpha values finish later than the single high-bandwidth path
- Reducing high-bandwidth-path RTT supports the timeout diagnosis

**Script**

Figure 7 shows the download bitrate over time (where a curve ending earlier means the 20 MB file finished faster). DChannel steers a packet to the LLP only when its estimated reward exceeds $\alpha$ times its cost ($R > \alpha \times C$, with default $\alpha = 0.75$). As Fig. 7 shows, across all tested values of $\alpha$, DChannel takes much longer to finish than using the single high-bandwidth path (`only eMBB`). However, when the authors manually reduced the HBP's RTT below the 200 ms minimum RTO threshold, DChannel once again outperformed the single path—supporting the authors' diagnosis.

**Visual Suggestion**: Paper Fig.7

Source check (not spoken): AdvNet paper §4.4.3, Fig.7

---

### Slide 31 — MPTCP: one path versus two

**Bullet Points**

- All four tested kernel MPTCP algorithms have counterexamples
- In the BALIA example, two-path throughput is 85.5% lower
- A roughly 40 ms ACK delay precedes a rate reduction on both links

**Script**

Finally, the authors tested the same "do no harm" objective on the Linux kernel implementation of **MPTCP** across all four of its congestion control algorithms: LIA, OLIA, BALIA, and wVegas. For every single one of them, AdvNet found environments where two paths yield lower throughput than one path.

For BALIA (Figure 8), dual-path throughput (`balia2`) was 85.5% lower than single-path throughput (`balia1`). Plotting cumulative bytes sent over time, `balia2` initially sends faster by using the high bandwidth of Link 1, but `balia1` overtakes it after about 0.5 seconds. Around 1.2 seconds, after the receiver delays an ACK by roughly 40 ms, `balia2` sharply reduces its sending rate on both links—even though Link 1 still has high available bandwidth.

**Visual Suggestion**: Paper Fig.8

Source check (not spoken): AdvNet paper §4.4.4, Fig.8

---

## Conclusion

### Slide 32 — What AdvNet contributes

**Bullet Points**

- A shared search pipeline supports several developer tasks
- Compact environments and noise handling contribute to its effectiveness
- Representation, evaluation, and reference design deserve attention

**Script**

To wrap up, AdvNet turns worst-case protocol testing into an automated black-box search over real code in emulation. By pairing a compact interval representation and Post-Learning Selection with customizable reference comparisons, a single search pipeline can uncover Linux kernel bugs, catch version regressions, and validate multipath design goals. From an ML-for-systems perspective, the fact that GA, Bayesian optimization, and epsilon-greedy search achieve very similar scores in Fig. 3b highlights an important lesson: a compact environment representation and careful noise handling contribute to the framework's effectiveness, while optimizer complexity alone does not determine its performance. These experiments do not establish a universal ranking of their importance.

**Visual Suggestion**: Key takeaways

Source check (not spoken): AdvNet paper §1–3

---

### Slide 33 — Scope and open questions

**Bullet Points**

- Generated traces do not estimate deployment frequency
- Root-cause diagnosis remains manual
- Richer workloads and environment models are open directions

**Script**

At the same time, AdvNet has clear boundaries. Its current model mainly varies link bandwidth, delay, duration, and buffer size, with continuous sending or a fixed transfer size. Packet loss arises implicitly from buffer limits; random loss and generated bursty cross-traffic are not explicit search dimensions. The framework neither estimates how often a counterexample occurs in real deployments nor automates root-cause diagnosis. Looking ahead, the framework could be extended to automatically characterize and summarize problematic regions of the environment space, with trace simplification as a possible additional extension, and applied to other dynamic systems such as adaptive bitrate video streaming, where the authors have already built a prototype.

**Visual Suggestion**: Boundaries and future work

Source check (not spoken): AdvNet paper §5

---

## Backup notes

### Slide 34 — Backup: formal methods and GANs

**Bullet Points**

- Formal methods use explicit models or specifications
- AdvNet searches real executions for performance weaknesses
- GANs usually learn a data distribution; AdvNet searches for challenging inputs

**Script**

**Formal verification** checks whether a system satisfies specified properties, using techniques such as model checking and symbolic analysis. These techniques typically require precise models or specifications and can struggle to scale to complex kernel implementations and large spaces of time-varying network conditions. AdvNet instead uses execution feedback to search for performance weaknesses in real implementations.

**Generative Adversarial Networks (GANs)** typically learn to generate data resembling an existing dataset. For AdvNet, the challenge is that we do not already have a dataset of challenging network environments to imitate. The search instead creates these environments using the observed performance gap as feedback.

**Visual Suggestion**: Formal methods and GANs comparison

Source check (not spoken): AdvNet paper §6, Appendix D

---

### Slide 35 — Backup: alternatives to MRE

**Bullet Points**

- RoundRobin divides the measurement budget equally
- OCBA prioritizes uncertainty and small gaps from the leader
- MRE uses repeated elimination, then concentrates measurements

**Script**

**RoundRobin** divides the evaluation budget equally among the candidate environments, then selects the one with the highest observed mean score.

**Optimal Computing Budget Allocation (OCBA)** distributes evaluations adaptively to increase the probability of selecting the candidate with the highest true mean. It prioritizes candidates with greater uncertainty or scores close to the current best. Compared with RoundRobin, it focuses measurements where they can most help distinguish the leading candidates. Figure 11 compares these methods with MRE.

**Visual Suggestion**: RoundRobin / OCBA / MRE table

Source check (not spoken): AdvNet paper §3.3, Appendix B

---

### Slide 36 — Backup: GA operator equations

**Bullet Points**

- Aligned crossover preserves parameter positions
- Uniform integer mutation respects each gene’s bounds
- The paper does not specify tournament selection or Top-N survival

**Script**

Here, $a$ and $b$ are the parent parameter vectors, and $i$ is a gene index. The cut points determine which coordinates the child takes from each parent. Mutation replaces each selected coordinate with a uniform integer sample from that coordinate's bounds.

**Visual Suggestion**: Crossover and mutation equations

Source check (not spoken): AdvNet paper §3.2.2

---

### Slide 37 — Backup: the selection simulation

**Bullet Points**

- 50 Gaussian alternatives with means sampled from 0–100
- The vertical axis is the true mean of the selected alternative
- MRE leads among the tested methods under this statistical model

**Script**

This experiment (Appendix B, Fig. 11) uses fifty Gaussian alternatives, with their true means sampled uniformly between zero and one hundred. The vertical axis is the true mean of the alternative selected by each method, averaged over two thousand trials. The oracle knows those true means. MRE performs best among the tested selection methods under this model, whereas OCBA struggles at small budgets (< 100 samples) because there are not enough samples per candidate to estimate variance reliably. Note that these values use a different scale from the normalized protocol-gap score.

**Visual Suggestion**: Paper Fig.11

Source check (not spoken): AdvNet paper Appendix B, Fig.11

---

### Slide 38 — Backup: parallel execution costs

**Bullet Points**

- Each protocol execution reserves three cores
- Mean throughput changes with parallel evaluation
- Variance rises sharply at nine and ten concurrent executions

**Script**

To evaluate each candidate environment multiple times without increasing wall-clock time, AdvNet runs multiple Mahimahi instances in parallel, pinning 3 dedicated CPU cores per instance (one each for the emulator, `iperf` client, and `iperf` server).

In Appendix A (Fig. 9), testing fixed network parameters (1 Gbps bandwidth, 5 ms one-way delay) on a 30-core server showed that mean throughput gradually drops as parallelism increases due to hardware contention, and variance spikes sharply at 9 and 10 concurrent runs (where $9 \times 3 = 27$ dedicated cores approaches the machine's 30-core count; this arithmetic alone does not establish CPU oversubscription). The authors therefore capped parallelism at 8.

**Visual Suggestion**: Paper Fig.9

Source check (not spoken): AdvNet paper Appendix A, Fig.9

---

### Slide 39 — Backup: choosing the parallelism level

**Bullet Points**

- More repetitions help with noise but add interference
- Five-way evaluation gives the best score in this setup
- The improvement over one evaluation is small

**Script**

In Fig. 10 (250 GA iterations), moving from 1 to 2 parallel runs initially lowers the final score because emulator contention distorts throughput during search (while the final output is always evaluated using a single isolated instance). Increasing parallelism further provides more samples to combat noise, peaking at 5-way parallelism—though the gain over a single evaluation per environment is marginal, so 1-way evaluation remains a practical low-CPU alternative.

**Visual Suggestion**: Paper Fig.10

Source check (not spoken): AdvNet paper Appendix A, Fig.10

---
