# Slide-change cues

[Deck](../slides/presentation.pdf) · [Spoken script](presentation_script.md)

All pages are static: one advance moves to the next numbered slide. Switch
**immediately before** the quoted words, then keep that slide visible until the
next cue. The elapsed-time ranges are rehearsal targets totaling **25:00** of
uninterrupted speech; audience discussion and Q&A are additional.

**Speaker handoff:** Speaker 1 covers slides 1–14 (target **11:10**). Keep slide 14
visible through “With that, I will hand over to Xiaoyang, who will discuss how
the paper uses these environments to study protocol behavior.” Advance to slide
15 when Xiaoyang begins. Xiaoyang covers slides 15–30 (target **13:50**).

| Slide | Target elapsed time | Script location and cue | Visual focus |
| --- | --- | --- | --- |
| 01 | 00:00–00:25 | §1: “Today, we will introduce AdvNet…” | Opening question and roadmap. |
| 02 | 00:25–01:20 | §1: “First, a little background.” | Sender, bottleneck, receiver; ACK return; congestion window and pacing. |
| 03 | 01:20–02:05 | §1: “Network conditions also change over time…” | Same average bandwidth, different order; the 17-protocol finding. |
| 04 | 02:05–03:20 | §2: “The usual testing methods are still useful.” | Hand-designed tests, collected traces, simulation, emulation, and CC-Fuzz. |
| 05 | 03:20–04:05 | §3: “AdvNet treats the environment as the input to optimize.” | Follow the search loop, then PLS and independent evaluation. |
| 06 | 04:05–04:40 | §4: “The first challenge is sample efficiency.” | The cost of evaluation and the role of a useful reference. |
| 07 | 04:40–05:25 | §5.1: “Now, what exactly does the search change?” | Follow the three intervals; define B, L, D, and I. |
| 08 | 05:25–06:20 | §5.1: “CC-Fuzz represents link service…” | Read the BBR row, then compare 25 and 100 PDOs. |
| 09 | 06:20–07:30 | §5.2: “With the representation fixed…” | Complete traces, measured fitness, and one GA generation. |
| 10 | 07:30–08:30 | §5.2: “Let us look at the two operators.” | Follow the exchanged middle segment, then the 15-to-73 mutation. |
| 11 | 08:30–09:10 | §5.2: “Does this search actually help?” | Left: one-hour comparison. Right: two-hour comparison. |
| 12 | 09:10–09:35 | §5.3: “There is one more problem: noisy measurements.” | Point to B’s single high outlier and the two mean lines. |
| 13 | 09:35–10:25 | §5.3: “The paper uses repeated protocol runs…” | Top 25, elimination rounds, then repeated evaluation of the finalists. |
| 14 | 10:25–11:10 | §5.3: “How much time should selection receive?” | Point to the peak at 0.1; summarize search design and hand over. |
| 15 | 11:10–12:20 | §6.1: “Now that we've seen how AdvNet searches efficiently…” | Explain the formula using 10 Mbps versus 2 Mbps. |
| 16 | 12:20–12:55 | §6.1: “Multiple metrics can also be combined…” | Explain the normalization terms and the three weights. |
| 17 | 12:55–14:00 | §6.2: “The first use case is finding environments…” | Introduce capacity and protocol references; explain 544 tests and 448 outcomes. |
| 18 | 14:00–14:40 | §6.2: “Let's look at BBR and CUBIC…” | Read the four BBR/CUBIC entries and compare the two directions. |
| 19 | 14:40–15:25 | §6.3: “The first case study involves…” | Follow later packets and the three duplicate ACKs. |
| 20 | 15:25–16:30 | §6.3: “However, before that retransmitted copy arrives…” | Original arrives first; retransmitted copy triggers the ACK bug; explain diagnosis. |
| 21 | 16:30–16:55 | §6.3: “When the authors re-tested on a newer Linux kernel version…” | Compare CUBIC and BBR v3 in the throughput panel. |
| 22 | 16:55–18:25 | §6.4: “Another application of UC1 is testing fairness…” | Alone versus competing; then the shift to one-packet-at-a-time sending. |
| 23 | 18:25–19:20 | §6.5: “The second use case is regression testing…” | Name the measured CUBIC throughput in each setup; show the final 10 seconds. |
| 24 | 19:20–20:00 | §6.5: “In one adversarial environment discovered by AdvNet…” | Compare the 12× and 11.6× ratios; then mention the single-flow regression. |
| 25 | 20:00–21:05 | §6.6: “The third use case is validating specific design objectives.” | Single-path reference, dual-path target, and the 120 ms / 3 ms paths. |
| 26 | 21:05–21:50 | §6.6: “The culprit is DChannel's packet-steering heuristic…” | Explain early RTT measurement and premature RTO expiry. |
| 27 | 21:50–22:25 | §6.6: “Fig. 7 plots the throughput over time…” | Point to curve endpoints and the only-eMBB baseline; then explain the reduced-RTT check. |
| 28 | 22:25–23:35 | §6.7: “Beyond DChannel, the authors also tested…” | Explain the original two panels; point out the 0.5 s and 1.2 s events. |
| 29 | 23:35–24:00 | §6.8 / Conclusion: “To sum up Section 6…” | Connect the three choices of reference to the practical findings. |
| 30 | 24:00–25:00 | Conclusion: “Of course, AdvNet still has some limitations.” | Cover current scope, future directions, and the closing takeaway. |

The move from slide 19 to 20 happens within a paragraph, at “However, before
that retransmitted copy arrives…”. This separates fast retransmission from the
receiver-side arrival order that triggers the bug.

## Backup access

End the main talk on slide 30. The following pages support Q&A and are outside
the 25-minute schedule.

| Backup slide | PDF page | Topic |
| --- | --- | --- |
| B1 | 31 | Formal verification and GANs |
| B2 | 32 | RoundRobin, OCBA, and MRE |
| B3 | 33 | Two-point crossover and uniform integer mutation equations |
| B4 | 34 | Statistical selection experiment, Fig. 11 |
