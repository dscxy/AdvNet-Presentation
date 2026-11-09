# Slide-change cues — v3

[Deck](../slides/presentation.pdf) · [Spoken script](presentation_script.md)

This cue sheet matches **33 main slides and 6 backup slides** in
`slides/presentation.tex`. All pages are static: one advance moves to the next
PDF page. Advance immediately before the quoted words and keep the slide visible
until the next cue. Slide numbers match the script headings and `notes/01.tex`
through `notes/39.tex`.

**Speaker handoff:** Speaker 1 covers slides **1–21**. Keep slide 21 visible
through “With that, I will hand over to Xiaoyang, who will show how AdvNet uses
these environments across concrete protocol testing use cases.” Advance to slide
**22** when Xiaoyang begins “Now that we have seen how AdvNet searches efficiently…”.
Xiaoyang covers slides **22–33**. End the main talk on slide **33**.

## Timing status

The repository's course requirement remains **25 minutes of uninterrupted
content**, excluding audience discussion and Q&A. The current full v3 script
**does not fit that requirement at the planning pace below**. The former 25:00
schedule described a different, shorter 30-slide deck and must not be used for v3.

The table below is a **text-based estimate**, not a measured rehearsal or a
promised delivery schedule. It assumes **85 spoken words per minute plus five
seconds per main slide** for transitions and pointing. Display equations are
excluded from word counts; each inline math expression counts as one token.
Explaining formulas, discussion, and Q&A can add more time.

- Speaker 1: approximately **1,889 prose words**, **22:13** of
  speech, or **23:58** with the per-slide allowance.
- Speaker 2: approximately **1,779 prose words**, **20:56** of
  speech, or **21:56** with the per-slide allowance.
- Main talk: approximately **45:54** with this allowance. Reaching
  25 minutes requires a separate content/timing revision; this synchronization
  preserves the current accepted v3 text.

## Main-slide cues

| Slide | Estimated elapsed time | Advance immediately before | Visual focus |
| --- | --- | --- | --- |
| 01 | 00:00–00:42 | “Today, we will introduce AdvNet, a system for adversarially testing network protocols, especially Congestion Control.” | Minimal title slide |
| 02 | 00:42–01:36 | “First, a little background.” | Sender, bottleneck queue, receiver, and ACK path |
| 03 | 01:36–02:26 | “Two mechanisms help control sending.” | Two-column list of sending controls and feedback |
| 04 | 02:26–03:38 | “Why is it so hard to make congestion control robust?” | Two-column list: environment changes and protocol updates |
| 05 | 03:38–05:20 | “How do developers test protocols today, and why isn't that enough?” | Comparison table: designed tests and collected traces |
| 06 | 05:20–06:26 | “Third, what about **automated adversarial testing**?” | Comparison table: simulation and emulation |
| 07 | 06:26–07:18 | “Prior work, most notably **CC-Fuzz**, used a genetic algorithm to generate adversarial environments, but only inside the…” | PDO definition and finite-budget implications |
| 08 | 07:18–07:58 | “AdvNet addresses these gaps by formulating environment generation as a black-box search over real protocol executions.” | Paper Fig.1 architecture |
| 09 | 07:58–10:07 | “In each iteration, the generator outputs a candidate network trace, and the execution module runs the target and, when the…” | Score and utility equations with symbol definitions |
| 10 | 10:07–10:37 | “Finally, because emulation has random variance, AdvNet reserves the last portion of its time budget for **Post-Learning…” | Search / PLS / independent evaluation sequence |
| 11 | 10:37–12:16 | “Realizing this framework in emulation brings two main challenges:” | Two-column challenge comparison |
| 12 | 12:16–13:42 | “Now, what exactly does the search change?” | Three-interval teaching trace table and Table 1 bounds |
| 13 | 13:42–15:17 | “Why use intervals instead of CC-Fuzz's packet delivery opportunities (PDOs), where each PDO specifies the exact timestamp…” | Paper Table 2 |
| 14 | 15:17–16:27 | “With the representation fixed, how does AdvNet search for challenging environments?” | Comparison of online actions and complete traces |
| 15 | 16:27–17:11 | “AdvNet's main search method is a **genetic algorithm (GA)**.” | Retain the DNA analogy from the earlier deck |
| 16 | 17:11–18:33 | “Let us look at the two operators.” | Editable colored crossover table plus mutation example |
| 17 | 18:33–20:03 | “The authors also compared GA against three other trace-based methods: **Random Generation (RG)**, which samples traces…” | Paper Fig.3(a,b), with one-hour and two-hour labels |
| 18 | 20:03–20:52 | “Finding high scores during search is only part of the problem; measurement noise can still mislead our final choice.” | Selection rule and noise explanation |
| 19 | 20:52–22:12 | “To mitigate noise, AdvNet runs each trace multiple times in parallel during search and uses the **median reference and…” | Numbered MRE procedure |
| 20 | 22:12–23:22 | “How should we split the total runtime between search and PLS?” | Paper Fig.2 and the 90/10 budget split |
| 21 | 23:22–23:58 | “Together, the compact interval representation, genetic search, and post-learning selection allow AdvNet to find reliably…” | Handoff to Xiaoyang |
| 22 | 23:58–26:03 | “Now that we have seen how AdvNet searches efficiently, let's look at how developers can use it to answer practical questions.” | Use-case / reference / target / question table |
| 23 | 26:03–27:34 | “Under UC1, while comparing against theoretical link capacity can flag extreme underutilization, comparing against another…” | Paper Fig.4(a), equal weights |
| 24 | 27:34–29:00 | “Look at BBR and CUBIC in the top-left corner of both heatmaps.” | Paper Fig.4(b), throughput only |
| 25 | 29:00–31:26 | “The first case study investigates why BBR scored so poorly under the throughput-only objective ($t_{\mathrm{coeff}}=1$).” | Numbered packet and ACK event sequence |
| 26 | 31:26–33:06 | “Why did this kernel TCP receive bug surface specifically when testing BBR?” | Paper Fig.6 |
| 27 | 33:06–35:11 | “A second way to use UC1 is testing fairness between competing flows.” | Fairness comparison and reported one-packet-per-ACK behavior |
| 28 | 35:11–37:55 | “Moving to UC2, the authors used AdvNet for regression testing between BBR v1 and BBR v3, focusing on their fairness toward a…” | Fixed-condition measurement sequence and version comparison table |
| 29 | 37:55–40:33 | “In UC3, the authors test a clear design objective for multipath transport: using two paths should never perform worse than…” | Path delays and a numbered timeout mechanism |
| 30 | 40:33–41:43 | “Figure 7 shows the download bitrate over time (where a curve ending earlier means the 20 MB file finished faster).” | Paper Fig.7 |
| 31 | 41:43–43:14 | “Finally, the authors tested the same "do no harm" objective on the Linux kernel implementation of **MPTCP** across all four…” | Paper Fig.8 |
| 32 | 43:14–44:33 | “To wrap up, AdvNet turns worst-case protocol testing into an automated black-box search over real code in emulation.” | Key takeaways |
| 33 | 44:33–45:54 | “At the same time, AdvNet has clear boundaries.” | Boundaries and future work |

## Backup access

The following PDF pages support Q&A and are excluded from the main-talk estimate.
They follow slide 33 in the PDF. Access them manually as needed.

| Backup | PDF page / script slide | Topic |
| --- | --- | --- |
| B1 | 34 | formal methods and GANs |
| B2 | 35 | alternatives to MRE |
| B3 | 36 | GA operator equations |
| B4 | 37 | the selection simulation |
| B5 | 38 | parallel execution costs |
| B6 | 39 | choosing the parallelism level |
