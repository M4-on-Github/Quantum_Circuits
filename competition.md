# Google Quantum AI - Verifiable Quantum Circuit Compilation (Kaggle)

- **URL:** https://www.kaggle.com/competitions/google-verifiable-quantum-circuit-compilation
- **Scrape date:** 2026-10-28
- **Method:** Overview, Rules, Data, Code, Discussion (including pinned topics and host posts), and Leaderboard pages read in a browser session (logged-in state; the Rules page showed the rules as already accepted). Models page was read and is empty. Team and Submissions pages were not scraped (see Scrape Notes).

---

## Overview

### Status and header

- Featured Prediction Competition, shown as "3 months to go" at scrape time.
- Start: 6 days before the scrape (page text "Start 6 days ago"); Close: "3 months to go".
- Tagline: "Reducing the resources required for quantum applications"

### Description

Quantum computers promise exponential speedups for some of science's toughest challenges, but current hardware is limited by qubit counts and gate errors. Quantum error correction can overcome those errors, but it adds substantial overhead to every qubit and gate an algorithm uses. Making fault-tolerant quantum algorithms practical therefore depends on compressing the circuits that implement them.

In this competition, you'll use AI agents and algorithmic insights to optimize quantum circuits for real-world bottlenecks in fusion energy, combinatorial optimization, and quantum chemistry—bringing practical quantum applications closer to reality.

The gap between theoretical quantum algorithms and practical quantum advantage often comes down to circuit size. Many high-impact algorithms rely on complex subroutines that require far more gates and qubits than near-term hardware can support. Shrinking these bottleneck subroutines directly reduces the hardware needed to run the full algorithm.

Historically, domain experts have optimized these circuits by hand, publishing incremental improvements one paper at a time. While verifying general quantum circuits is intractable on classical computers, many of the costliest fault-tolerant subroutines can be written as kickmix circuits—built from reversible classical logic, diagonal phase gates, and measurement-based uncomputation. As detailed in our companion paper, *Leveraging verifiable structure in quantum circuits to find more efficient compilations with agentic AI*, our new open-source kickmix library in Qualtran can build and fuzz-test circuits with tens of millions of gates on classical inputs in seconds.

Rather than training on a traditional dataset, you will use AI coding agents, classical optimization, and algorithmic insights in a closed verification loop to find smaller, faster circuit compilations—including smart approximations within each benchmark's accuracy bounds. No quantum physics background or quantum hardware is required. Your submissions will target three real-world bottlenecks:

- **Fusion Energy (1/√x Phasing):** Compressing fixed-point inverse-square-root circuits for pairwise Coulomb interactions used to model alpha-particle stopping power in warm dense plasmas during inertial confinement fusion (PNAS 2024).
- **Combinatorial Optimization (Decoded Quantum Interferometry):** Optimizing reversible Reed–Solomon syndrome decoders for Decoded Quantum Interferometry (DQI) on the Optimal Polynomial Intersection problem over finite fields (Nature 2025, arXiv:2510.10967).
- **Quantum Chemistry & Clean Energy (Hamiltonian Block Encoding):** Co-optimizing classical tensor factorizations, Givens rotation trees, and quantum lookup tables (QROMs) to simulate FeMoCo—the biological catalyst behind nitrogen fixation, where industrial fertilizer production consumes ~2% of global energy (PNAS 2017, PRX 2025).

Could we get more out of a quantum computer simply by asking it to do less? We invite you to help us answer that question.

### Evaluation

Submissions are evaluated using the geometric mean of each task's improvement relative to a baseline.

Score = ( ∏_{b=1}^{3} cost^ref_b / cost_b )^{1/3}

(Product over b = 1..3 of cost^ref_b / cost_b, raised to the power 1/3.)

Each task has a different loss function:

| Task | Paper | Cost |
|---|---|---|
| invsqrt (Fusion Energy) | Benchmark I | Q × C, where C = Toffolis + T gates/4 |
| dqi (Combinatorial Optimization) | Benchmark II | R(ε+) × Q² × T, where R(ε) = ln 2 / (−ln(1/2 + 2√ε)) |
| dfthcsos (Quantum Chemistry & Clean Energy) | Benchmark III | λ_eff × T × Q, where λ_eff = √(E_gap (2Λ − E_gap)) |

Where Q is the qubit count and T the Toffoli count, both per shot. For dqi, ε+ is an upper confidence bound on the decoder's failure rate. For dfthcsos, T and Q cover the whole block encoding, not just the submitted ANGLE circuits, and any ANGLE circuit wider than 128 qubits is rejected.

(Formulas verified against the page's MathML on 2026-10-28: R(ε) = ln 2 / ( −ln( 1/2 + 2·√ε ) ), so R(0) = 1; and λ_eff = √( E_gap · (2Λ − E_gap) ).)

You can review the full metric implementation on the competition page (linked "here" from the Evaluation section). Scoring takes roughly 45 minutes.

### Submission File

You must submit a zip archive containing the following files:

- `invsqrt.kmb` or `invsqrt.kmx`
- `dqi.kmb` or `dqi.kmx`
- a folder named `dfthcsos` containing the circuits `angle_k_0`, `angle_k_1`, … `angle_k_<n-1>`, numbered from 0 with no gaps, each as `.kmb` or `.kmx`, plus `submission.npz` holding the factorization (`U`, `W`, `H2_I`, `H1_I`, `Hsym_lower`) and the Givens tree (`tree_edges`).

### Timeline

- **October 22, 2026** – Start Date.
- **November 20, 2026** – Mid-Competition Milestone Prize. The team with the highest public leaderboard score at this deadline wins, provided its notebook is public.
- **January 4, 2027** – Longest Leader Prize. The leaderboard period this prize counts ends, and the qualifying notebooks and any datasets they use must be public by this deadline.
- **January 13, 2027** – Entry Deadline. You must accept the competition rules before this date in order to compete.
- **January 13, 2027** – Team Merger Deadline. This is the last day participants may join or merge teams.
- **January 20, 2027** – Final Submission Deadline.

All deadlines are at 11:59 PM UTC on the corresponding day unless otherwise noted. The competition organizers reserve the right to update the contest timeline if they deem it necessary.

### Prizes

**Leaderboard Prizes**

| Place | Prize |
|---|---|
| 1st Place | $50,000 |
| 2nd Place | $25,000 |
| 3rd Place | $10,000 |
| 4th Place | $5,000 |
| 5th Place | $5,000 |
| 6th Place | $5,000 |

**Additional Prizes**

- Mid-Competition Milestone Prize: $10,000
- Longest Leader Prize: $10,000
- Single Task Performance Prizes: $30,000

**Total prize pool:** $150,000 (leaderboard $100,000 + additional $50,000). Points and medals are also awarded.

For each additional prize, the winning notebooks or submissions need to adhere to the same requirements and restrictions regarding licensing, reproducibility, and documentation to which the winning Submission is subject (see Competition Rules).

**Mid-Competition Milestone Prize.** Participants are encouraged to make publicly available their notebooks through the competition. At the end of the competition, $10,000 will be awarded to the team with the highest public leaderboard score at 11:59 PM UTC, November 20th. To be eligible, you will need to: publish a notebook and keep the notebooks and any datasets they use publicly available until the Final Submission Deadline.

**Longest Leader Prize.** Awarded to the team whose notebook(s) generates the best scoring submission on the leaderboard for the longest period of time between the competition start date and January 4th, 2027. The notebook(s) and any datasets used must be made publicly available at latest at January 4th, 2027 11:59 PM UTC and kept public until the end of the competition. In the event that a team has multiple public notebooks, each achieving the top leaderboard position at different times, those durations will be combined.

**Single Task Performance Prizes.** For each of the three tasks (combinatorial optimization, chemistry, and fusion), the selected submission with the best score for that specific task will receive a $10,000 prize.

### Domain Context

You don't need a background in quantum physics to participate! This section gives you the essentials: what quantum circuits are, what makes them expensive, why the circuits in this competition can be checked automatically, and some more details behind each of the three tasks.

#### Quantum circuits in 60 seconds

A classical bit is either 0 or 1. A qubit, like a classical bit, can be 0 or 1—or in a superposition of both. n qubits can be in a superposition of all 2ⁿ bit strings at once, each with its own complex amplitude. Quantum algorithms work by steering these amplitudes so that wrong answers cancel out and right answers reinforce each other. This effect is called interference.

Quantum programs are specified with circuits: a sequence of gates, usually acting on one to three qubits. Many important quantum gates are reversible versions of ordinary logic, such as NOT, controlled-NOT, and the Toffoli gate, which flips a target bit when two control bits are both 1. In many quantum algorithms, the subroutines that dominate the cost are essentially classical arithmetic (adders, multipliers, table lookups) applied to a superposition of many inputs at once.

There's a catch: quantum computation must be reversible. You can't erase or overwrite a value, so temporary results go into extra "scratch" qubits (ancillas), and every scratch qubit must be returned to 0 at the end. This clean-up is sometimes called uncomputation. Leftover garbage would destroy the interference that the algorithm relies on.

#### What makes a circuit expensive

Physical qubits are noisy, so large quantum algorithms will run on error-corrected (logical) qubits, each built from some number of physical qubits (depending on the error correcting code used). On such machines most gates are cheap, but Toffoli gates (and similar "non-Clifford" gates such as T gates) are expensive: each one consumes a special resource state that dedicated "magic state factories" take a long time to produce. That's why the cost of a fault-tolerant circuit is usually summarized by two numbers:

- the Toffoli count, which drives the runtime, and
- the logical qubit count, which drives the size of the machine.

Compiling an algorithm into a concrete circuit means navigating a huge design space: which arithmetic decompositions to use, when to allocate and clean up scratch qubits, and how much precision each step really needs. One classic trick is measurement-based uncomputation. Instead of spending a second Toffoli to clean up a scratch qubit that holds a AND b, you measure it and cancel the leftover sign with a cheap gate, halving the cost. Experts have historically discovered tricks like this by hand, one paper at a time.

#### Why these circuits can be verified automatically

For general quantum circuits, checking that a candidate does what it should is believed to be intractable: beyond roughly 40 qubits, it's out of reach for classical computers. The subroutines in this competition are different. They're built only from reversible classical gates, phase gates, and measurement-based uncomputation, a family called kickmix circuits. Each of these instructions maps a definite bit string to another definite bit string, at most changing its phase. So a classical computer can run the circuit one input at a time, tracking just one bit per qubit plus a phase. The open-source kickmix simulator in Google's Qualtran library processes 64 to 512 test inputs with each CPU instruction and handles circuits with more than 100 million gates on a single core.

This is enough to check the quantum behavior, too. Quantum mechanics is linear, so a circuit that maps every bit-string input to the right output with the right phase, and leaves its scratch qubits clean, also behaves correctly on every superposition of those inputs. Nearly correct circuits are nearly right: if a circuit fails on a fraction ε of inputs (weighted the way the real algorithm weights them), its quantum output is within a distance of 2√ε of the ideal output.

So the verifier fuzz tests your circuit. Depending on the input domain size, it simulates the circuit across every valid input or across many random inputs drawn the way the full algorithm weights them, checking that the inputs are restored, the scratch qubits are clean, and the phase is right. Random inputs and internal measurement outcomes are seeded with a salted cryptographic hash of your submission (the Fiat–Shamir heuristic), so there's no hidden test set and any change to your submission gets fresh random draws. Passing many random tests is strong evidence: for example, a circuit that passes 100,000 of them without a single failure fails on fewer than 0.1% of inputs, with overwhelming confidence.

Because verification is fast and trustworthy, it gives AI coding agents, classical optimization, and automated search an instant reward signal. When the ecdsa.fail challenge ran a similar verifiable competition for cryptography circuits in 2026, more than 100 participants, most with no quantum computing background, used AI coding agents to cut the Toffoli count roughly in half.

Not every part of a quantum algorithm fits this mold. Steps that create genuine superpositions, such as preparing arbitrary quantum states, can't be checked by simulating one input at a time. Each task therefore isolates the kickmix subroutine that dominates its algorithm's cost, and prices any other parts with analytical formulas, so your score still reflects the full algorithm.

#### The three tasks at a glance

| Task | Scientific goal | Quantum algorithm | Bottleneck you'll compress |
|---|---|---|---|
| Fusion Energy | Predict how energy is deposited in fusion fuel | Step-by-step (Trotter) simulation of electrons on a grid | Phasing by 1/√x for every pair of electrons |
| Combinatorial Optimization | A verifiable quantum advantage for optimal polynomial intersection problem | Decoded Quantum Interferometry (DQI) | A reversible Reed–Solomon syndrome decoder |
| Quantum Chemistry & Clean Energy | Understand how nature fixes nitrogen (the FeMoCo cluster) | Phase estimation on an encoded molecular Hamiltonian | Tensor factorizations, Givens trees, and lookup tables that load the Hamiltonian |

#### Fusion Energy: stopping power in fusion fuel

In inertial confinement fusion, lasers crush a tiny capsule of fuel to extreme temperatures and densities. Whether the fuel ignites depends on how quickly fast charged particles, such as the alpha particles released by fusion reactions, deposit their energy in the surrounding fuel. This rate is called the stopping power. On the way to ignition, the fuel passes through warm dense matter, a state too hot and dense for standard theories and hard to probe experimentally, which makes stopping power a key uncertainty in target design (Rubin et al., PNAS 2024).

A quantum computer can simulate the electrons directly. It stores every electron's position on a 3D grid and steps time forward, alternating between kinetic-energy updates and potential-energy updates. The potential energy is the Coulomb repulsion between every pair of electrons, which is proportional to 1/distance. For each pair, the circuit computes the squared distance x, phases by 1/√x to about 7 significant digits (a relative error of 2⁻²⁴), and cleans up any scratch work. With 218 electrons, there are 23,653 pairs per time step, so this one subroutine dominates the cost of the whole simulation. The task isolates it: given x, apply the right phase for every possible x.

You may recognize the classical version of this problem. The famous "fast inverse square root" from the video game Quake III combines a clever first guess with one step of Newton's method. The quantum version must be reversible, use fixed-point arithmetic, and be far more accurate. The reference circuit follows the same recipe; you're free to find a better one.

#### Combinatorial Optimization: Decoded Quantum Interferometry

Suppose that at every input in a finite field, you are given a set of allowed output values, and your goal is to find a low-degree polynomial whose curve lands inside as many of those allowed sets as possible. This problem is called Optimal Polynomial Intersection (OPI) (closely related to list recovery in coding theory). Checking how many sets a proposed polynomial hits takes milliseconds on an ordinary computer, yet when the allowed sets are large—about half the field at every point in our benchmark—finding an optimal or near-optimal polynomial appears beyond the reach of known classical algorithms. That combination makes OPI a leading candidate for a verifiable quantum advantage (Jordan et al., Nature 2025).

Decoded Quantum Interferometry (DQI) tackles OPI using the quantum Fourier transform to mathematically transform this hard optimization problem into a classic error-correction problem: decoding a Reed–Solomon code—the same family of codes used to read scratched QR codes, damaged CDs, and noisy deep-space transmissions. Classical computers decode a single Reed–Solomon codeword quickly using tools like the extended Euclidean algorithm, and Khattar et al. (arXiv:2510.10967) estimate that DQI could solve classically intractable OPI instances with just a few million Toffoli gates—with the Reed–Solomon decoder accounting for over 90% of the total circuit cost.

The catch is that in DQI, this decoder must run inside the quantum computer: reversibly, on a massive superposition of error patterns at once, and leaving zero scratch garbage behind so quantum interference can constructively amplify high-scoring polynomials. In optimized DQI, the error pattern is erased early via measurement-based uncomputation, leaving behind a ±1 phase sign. Your circuit's job is to recover that sign from the error syndromes (a compact fingerprint of the errors), cancel it, and clean up all workspace qubits. Unusually, your decoder doesn't even have to be perfect: because every candidate polynomial sampled by DQI is checked classically at the end anyway, an occasional decoding failure only adds a small repetition overhead—a trade-off captured directly in the score.

#### Quantum Chemistry & Clean Energy: simulating nitrogen fixation

Industrial fertilizer production relies on the Haber–Bosch process, which turns nitrogen from the air into ammonia at high temperature and pressure. Bacteria do the same thing at room temperature using the enzyme nitrogenase, whose active site is a cluster of iron, molybdenum and sulfur atoms known as FeMoCo. Its electrons are so strongly correlated that classical computers can't reliably predict its chemistry. A quantum computer could compute the energy of each step of the reaction and reveal how nature does it (Reiher et al., PNAS 2017).

The algorithm is quantum phase estimation, which repeatedly applies a circuit that encodes the molecule's Hamiltonian (the operator that gives its energy). The Hamiltonian is specified by an enormous table of numbers: for N orbitals, roughly N⁴ of them. The most efficient known algorithms (Low et al., PRX 2025) compress this table with a tensor factorization, stream the compressed data into the quantum computer with QROM circuits (quantum read-only memory: lookup tables that work on a superposition of addresses), and apply it as sequences of Givens rotations (rotations that mix pairs of orbitals). These lookups and controlled rotations dominate the Toffoli count.

This task couples classical and quantum design. Your choice of factorization affects both how much data the circuits have to load and how many times phase estimation has to repeat them, and it must still reproduce the molecule's energies accurately. The lookup circuits that load the angle data are yours to design, as are the classical Givens tree and bit precision. The state-preparation and Givens-rotation gates themselves, which aren't kickmix circuits, are priced with analytical formulas.

#### Key terms

- **Ancilla (scratch qubit):** a temporary qubit that must be returned to 0 by the end of the circuit.
- **Block encoding:** a circuit that embeds a scaled copy of a matrix, such as a Hamiltonian, inside a larger quantum operation, so that algorithms like phase estimation can use it.
- **Hamiltonian:** the operator that gives a physical system's energy.
- **kickmix circuit:** a circuit made only of reversible classical gates, phase gates, and measurement-based uncomputation, which makes it efficient to verify on a classical computer.
- **Logical qubit:** an error-corrected qubit built from many physical qubits.
- **Measurement-based uncomputation:** cleaning up a scratch qubit by measuring it and cancelling the resulting sign with cheap gates, instead of reversing the computation.
- **QROM:** a quantum lookup table that returns the entry for every address in a superposition at once.
- **Syndrome:** a compact fingerprint of the errors in a codeword, which can be computed without knowing the original message.
- **Toffoli gate:** a controlled-controlled-NOT gate; the main expensive operation on error-corrected hardware, and a key cost metric in this competition.
- **Trotterization:** simulating how a system evolves over time by alternating many small steps of simpler evolutions.

#### Learn more

- Khattar et al. (arXiv:2610.23832), the companion paper for this competition covering the kickmix package, verification guarantees, and all three benchmarks.
- *Quantum computing for the very curious*, a free introductory essay by Andy Matuschak and Michael Nielsen, and Wikipedia's overview of quantum computing.
- Quirk, a drag-and-drop quantum circuit simulator that runs in your browser.
- The kickmix documentation in Google's open-source Qualtran library: the circuit file format, the instruction set, and the Python API.
- The Qualtran documentation, for the library kickmix is part of.
- Babbush et al. (arXiv:2603.28846), which introduced kickmix circuits and this style of verification to estimate the cost of breaking elliptic-curve cryptography.
- The papers cited in the Description for each task.

### Citation

> Tanuj Khattar, Nicholas Rubin, Craig Gidney, Michael Broughton, Guang Hao Low, Ryan Babbush, Sohier Dane, Brandon Horton, and María Cruz. Google Quantum AI - Verifiable Quantum Circuit Compilation. https://www.kaggle.com/competitions/google-verifiable-quantum-circuit-compilation, 2026. Kaggle.

### Host, tags and stats

- **Competition Host:** Google Quantum AI
- **Tags:** Computer Science, Physics, Custom Metric
- **Prizes & Awards:** $150,000 (awards points & medals)
- **Participation:** 4,686 Entrants; 1,477 Participants; 1,388 Teams; 9,392 Submissions

### Table of contents (as shown on page)

Overview, Description, Evaluation, Timeline, Prizes, Domain Context, Citation

---

## Rules

Source: https://www.kaggle.com/competitions/google-verifiable-quantum-circuit-compilation/rules (captured while logged in; the page showed "You have accepted the rules for this competition. Good luck!"). Text reproduced from the page.

### Competition-specific summary

- **Competition title (per rules):** Quantum AI - Verifiable quantum circuit compilation
- **Sponsor:** Google LLC, 1600 Amphitheatre Parkway, Mountain View, CA 94043
- **Competition website:** https://www.kaggle.com/competitions/google-verifiable-quantum-circuit-compilation
- **Total prizes available:** $150,000
- **Winner license type:** Apache 2.0
- **Data access and use:** Apache 2.0
- **Competition will award points and medals.**

### Full rules text

**ENTRY IN THIS COMPETITION CONSTITUTES YOUR ACCEPTANCE OF THESE OFFICIAL COMPETITION RULES.**

**A. LEGALLY BINDING AGREEMENT**

The Competition named below is a skills-based competition to promote and further the field of data science. You must register via the Competition website ("Competition Website") to enter. To enter the Competition, you must agree to these Official Competition Rules, which incorporate by reference the provisions and content of the Competition Website and any Specific Competition Rules herein (collectively, the "Rules"). Please read these Rules carefully before entry to ensure you understand and agree. You further agree that Submission (as defined below) in the Competition constitutes agreement to these Rules. You may not submit to the Competition and are not eligible to receive the prizes associated with this Competition unless you agree to these Rules. These Rules form a binding legal agreement between you and the Competition Sponsor with respect to the Competition. Your competition Submissions must conform to the requirements stated on the Competition Website. Your Submissions will be scored based on the evaluation metric described on the Competition Website. Subject to compliance with the Competition Rules, Prizes, if any, will be awarded to Participants (as defined below) with the best scores, based on the merits of the data science models submitted.

You cannot sign up to Kaggle.com from multiple accounts and therefore you cannot enter or submit from multiple accounts.

Unless otherwise stated in the Competition-Specific Rules below or prohibited by internal policies of the Competition Entities, employees, interns, contractors, officers and directors of Competition Entities may enter and participate in the Competition, but are not eligible to win any Prizes. "Competition Entities" means the Competition Sponsor, Kaggle Inc. ("Kaggle"), and their respective parent companies, subsidiaries and affiliates. If you are such a Participant from a Competition Entity, you are subject to all applicable internal policies of your employer with respect to your participation.

**B. COMPETITION-SPECIFIC TERMS AND RULES**

**COMPETITION TITLE:** Quantum AI - Verifiable quantum circuit compilation

**COMPETITION SPONSOR:** Google LLC

**COMPETITION SPONSOR ADDRESS:** 1600 Amphitheatre Parkway, Mountain View, CA 94043

**COMPETITION WEBSITE:** https://www.kaggle.com/competitions/google-verifiable-quantum-circuit-compilation

**TOTAL PRIZES AVAILABLE:** $150,000

- 1st Place – $50,000
- 2nd Place – $25,000
- 3rd Place – $10,000
- 4th Place – $5,000
- 5th Place – $5,000
- 6th Place – $5,000

**Additional Prizes:** $50,000

- Mid-Competition Milestone Prize: $10,000
- Longest Leader Prize: $10,000
- Single Task Performance Prizes: $30,000

Please review the Overview tab for specifications to qualify for additional prizes.

Competition will award points and medals.

**WINNER LICENSE TYPE:** Apache 2.0

**DATA ACCESS AND USE:** Apache 2.0

In addition to the provisions of the General Competition Rules below, you understand and agree to the Competition-Specific Rules required by the Competition Sponsor as set forth below:

**1. TEAM LIMITS**

a. The maximum Team (as defined below) size is five (5).

b. Team mergers are allowed and can be performed by the Team leader. In order to merge, the combined Team must have a total Submission count less than or equal to the maximum allowed as of the Team Merger Deadline (as described below). The maximum allowed is the number of Submissions per day multiplied by the number of days the competition has been running.

**2. SUBMISSION LIMITS**

a. You may submit a maximum of five (5) Submissions per day.

b. You may select up to two (2) Final Submissions (as defined below) for judging.

**3. COMPETITION TIMELINE**

Competition Timeline dates (including Entry Deadline, Final Submission Deadline, Start Date, and Team Merger Deadline, as applicable) are set forth on the Competition's Overview > Timeline page.

**4. COMPETITION DATA**

a. **Data Access and Use.** Competition Use and Commercial Purposes: You may access and use the Competition Data for any purpose, whether commercial or non-commercial, including for participating in the Competition and on Kaggle.com forums, and for academic research and education. The Competition Sponsor reserves the right to disqualify any Participant who uses the Competition Data other than as permitted by the Competition Website and these Rules.

b. **Data Security.** You agree to use reasonable and suitable measures to prevent persons who have not formally agreed to these Rules from gaining access to the Competition Data. You agree not to transmit, duplicate, publish, redistribute or otherwise provide or make available the Competition Data to any party not participating in the Competition. You agree to notify Kaggle immediately upon learning of any possible unauthorized transmission of or unauthorized access to the Competition Data and agree to work with Kaggle to rectify any unauthorized transmission or access.

**5. WINNERS' LICENSE**

a. In furtherance of Section C(6) below, you hereby grant and will grant the Competition Sponsor the following license(s) with respect to your Submission if you are a Competition winner:

Open Source: You hereby license and will license your winning Submission and the source code used to generate the Submission under Open Source License Apache 2.0. In the event that input data or pretrained models with an incompatible license are used to generate your winning solution, you do not need to grant an open source license in the preceding sentence for that data and/or model(s).

b. For generally commercially available software that you used to generate your Submission that is not owned by you, but that can be procured by the Competition Sponsor at a cost that does not exceed the amount of a prize in the competition, you do not need to grant the license in the preceding Section for that software.

c. You may be required by the Sponsor to provide a detailed description of how the winning Submission was generated, to the Competition Sponsor's specifications, as outlined in Section B(7) (Winners' Obligations). This may include a detailed description of methodology, where one must be able to reproduce the approach by reading the description, and includes a detailed explanation of the architecture, preprocessing, loss function, training details, hyper-parameters, etc. The description should also include a link to a code repository with complete and detailed instructions so that the results obtained can be reproduced.

**6. EXTERNAL DATA AND TOOLS**

a. Subject to Subsection (b) below, you may use data other than the Competition Data ("External Data") to develop and test your Submissions. However, you will ensure the External Data is either publicly available and equally accessible to use by all Participants of the Competition for purposes of the competition at no cost to the other Participants, or satisfies the Reasonableness Standard as described in Subsection (b) below. The ability to use External Data under this Section does not limit your other obligations under these Competition Rules, including but not limited to Section B(7) (Winners' Obligations).

b. The use of External Data and models is acceptable unless specifically prohibited by the Competition Host. Because of the potential costs or restrictions (e.g., territorial restrictions or "geo restrictions") associated with obtaining rights to use External Data or certain software and associated tools, their use must meet the Reasonableness Standard as described below. Also, regardless of the cost challenges as they might affect all Participants during the course of the competition, the costs of potentially procuring a license for software used to generate a Submission, must also be considered. The Competition Host will employ an assessment of whether or not the following criteria can exclude the use of the particular LLM, dataset(s), or tool(s):

i. Are Participants being excluded from a competition because of the "excessive" costs for access to certain LLMs, external data, or tools that might be used by other Participants. The Competition Host will assess the excessive cost concern by applying a "reasonableness" standard (the "Reasonableness Standard"). The Reasonableness Standard will be determined by the Competition Host in consultation with Kaggle and applied by the Competition Host in light of certain criteria, including but not limited to, cost thresholds and accessibility. By way of example only, purchasing a license to use a proprietary dataset that exceeds the cost of a prize in the competition may not be considered reasonable.

c. **Automated Machine Learning Tools**

i. Individual Participants and Teams may use automated machine learning tool(s) ("AMLT") (e.g., Google AutoML, H2O Driverless AI, etc.) to create a Submission, provided that the Participant or Team ensures that they have an appropriate license to the AMLT such that they are able to comply with the Competition Rules.

**7. WINNERS' OBLIGATIONS**

a. As a condition to being awarded a Prize, a Prize winner must fulfill the following obligations:

i. Deliver to the Competition Sponsor the final model's software code as used to generate the winning Submission and associated documentation. The delivered software code should follow these documentation guidelines, must be capable of generating the winning Submission, and contain a description of resources required to build and/or run the executable code successfully. For avoidance of doubt, delivered software code should include training code, inference code, and a description of the required computational environment.

ii. To the extent that the final model's software code includes generally commercially available software that is not owned by you, but that can be procured by the Competition Sponsor at a cost that does not exceed the amount of a prize in the competition, then instead of delivering the code for that software to the Competition Sponsor, you must identify that software, method for procuring it, and any parameters or other information necessary to replicate the winning Submission; Individual Participants and Teams who create a Submission using an AMLT may win a Prize. However, for clarity, the potential winner's Submission must still meet the requirements of these Rules, including but not limited to Section B(5) (Winners' License), Section B(7) (Winners' Obligations), and Section C(14) (Warranty, Indemnity, and Release).

iii. Individual Participants and Teams who create a Submission using an AMLT may win a Prize. However, for clarity, the potential winner's Submission must still meet the requirements of these Rules.

b. Grant to the Competition Sponsor the license to the winning Submission stated in the Competition Specific Rules above, and represent that you have the unrestricted right to grant that license;

c. Sign and return all Prize acceptance documents as may be required by Competition Sponsor or Kaggle, including without limitation: (a) eligibility certifications; (b) licenses, releases and other agreements required under the Rules; and (c) U.S. tax forms (such as IRS Form W-9 if U.S. resident, IRS Form W-8BEN if foreign resident, or future equivalents).

**8. GOVERNING LAW**

Unless otherwise provided in the Competition Specific Rules above, all claims arising out of or relating to these Rules will be governed by California law, excluding its conflict of laws rules, and will be litigated exclusively in the Federal or State courts of Santa Clara County, California, USA. The parties consent to personal jurisdiction in those courts. If any provision of these Rules is held to be invalid or unenforceable, all remaining provisions of the Rules will remain in full force and effect.

**C. GENERAL COMPETITION RULES**

**1. ELIGIBILITY**

a. To be eligible to enter the Competition, you must be (i) a registered account holder at Kaggle.com; (ii) the older of 18 years old or the age of majority in your jurisdiction of residence (unless otherwise agreed to by Competition Sponsor and appropriate parental/guardian consents have been obtained by Competition Sponsor); (iii) not a resident of Crimea, so-called Donetsk People's Republic (DNR) or Luhansk People's Republic (LNR), Cuba, Iran, or North Korea; and (iv) not a person or representative of an entity under U.S. export controls or sanctions (see https://ofac.treasury.gov/).

b. Competitions are open to residents of the United States and worldwide, except that if you are a resident of Crimea, so-called Donetsk People's Republic (DNR) or Luhansk People's Republic (LNR), Cuba, Iran, North Korea, or are subject to U.S. export controls or sanctions, you may not enter the Competition. Other local rules and regulations may apply to you, so please check your local laws to ensure that you are eligible to participate in skills-based competitions. The Competition Host reserves the right to forego or award alternative Prizes where needed to comply with local laws. If a winner is located in a country where prizes cannot be awarded, then they are not eligible to receive a prize.

c. If you are entering as a representative of a company, educational institution or other legal entity, or on behalf of your employer, these rules are binding on you, individually, and the entity you represent or where you are an employee. If you are acting within the scope of your employment, or as an agent of another party, you warrant that such party or your employer has full knowledge of your actions and has consented thereto, including your potential receipt of a Prize. You further warrant that your actions do not violate your employer's or entity's policies and procedures.

d. The Competition Sponsor reserves the right to verify eligibility and to adjudicate on any dispute at any time. If you provide any false information relating to the Competition concerning your identity, residency, mailing address, telephone number, email address, ownership of right, or information required for entering the Competition, you may be immediately disqualified from the Competition.

**2. SPONSOR AND HOSTING PLATFORM**

The Competition is sponsored by Competition Sponsor named above. The Competition is hosted on behalf of Competition Sponsor by Kaggle. Kaggle is an independent contractor of Competition Sponsor, and is not a party to this or any agreement between you and Competition Sponsor. You understand that Kaggle has no responsibility with respect to selecting the potential Competition winner(s) or awarding any Prizes. Kaggle will perform certain administrative functions relating to hosting the Competition, and you agree to abide by the provisions relating to Kaggle under these Rules. As a Kaggle.com account holder and user of the Kaggle competition platform, remember you have accepted and are subject to the Kaggle Terms of Use in addition to these Rules.

**3. COMPETITION PERIOD**

For the purposes of Prizes, the Competition will run from the Start Date and time to the Final Submission Deadline (such duration, the "Competition Period"). The Competition Timeline is subject to change, and Competition Sponsor may introduce additional hurdle deadlines during the Competition Period. Any updated or additional deadlines will be publicized on the Competition Website. It is your responsibility to check the Competition Website regularly to stay informed of any deadline changes. YOU ARE RESPONSIBLE FOR DETERMINING THE CORRESPONDING TIME ZONE IN YOUR LOCATION.

**4. COMPETITION ENTRY**

a. NO PURCHASE REQUIRED TO ENTER OR WIN. To enter the Competition, you must register on the Competition Website prior to the Entry Deadline, and follow the instructions for developing and entering your Submission through the Competition Website. Your Submissions must be made in the manner and format, and in compliance with all other requirements, stated on the Competition Website (the "Requirements"). Submissions must be received before any Submission deadlines stated on the Competition Website. Submissions not received by the stated deadlines will not be eligible to receive a Prize.

b. Submissions may not use or incorporate information from hand labeling or human prediction of the validation dataset or test data records.

c. If the Competition is a multi-stage competition with temporally separate training and/or test data, one or more valid Submissions may be required during each Competition stage in the manner described on the Competition Website in order for the Submissions to be Prize eligible.

d. Submissions are void if they are in whole or part illegible, incomplete, damaged, altered, counterfeit, obtained through fraud, or late. Competition Sponsor reserves the right to disqualify any entrant who does not follow these Rules, including making a Submission that does not meet the Requirements.

**5. INDIVIDUALS AND TEAMS**

a. **Individual Account.** You may make Submissions only under one unique Kaggle.com account. You will be disqualified if you make Submissions through more than one Kaggle.com account, or attempt to falsify an account to act as your proxy. You may submit up to the maximum number of Submissions per day as specified on the Competition Website.

b. **Teams.** If permitted under the Competition Website guidelines, multiple individuals may collaborate as a Team; however, you may join or form only one Team. Each Team member must be a single individual with a separate Kaggle.com account. You must register individually for the Competition before joining a Team. You must confirm your Team membership to make it official by responding to the Team notification message sent to your Kaggle.com account. Team membership may not exceed the Maximum Team Size stated on the Competition Website.

c. **Team Merger.** Teams (or individual Participants) may request to merge via the Competition Website. Team mergers may be allowed provided that: (i) the combined Team does not exceed the Maximum Team Size; (ii) the number of Submissions made by the merging Teams does not exceed the number of Submissions permissible for one Team at the date of the merger request; (iii) the merger is completed before the earlier of: any merger deadline or the Competition deadline; and (iv) the proposed combined Team otherwise meets all the requirements of these Rules.

d. **Private Sharing.** No private sharing outside of Teams. Privately sharing code or data outside of Teams is not permitted. It's okay to share code if made available to all Participants on the forums.

**6. SUBMISSION CODE REQUIREMENTS**

a. **Private Code Sharing.** Unless otherwise specifically permitted under the Competition Website or Competition Specific Rules above, during the Competition Period, you are not allowed to privately share source or executable code developed in connection with or based upon the Competition Data or other source or executable code relevant to the Competition ("Competition Code"). This prohibition includes sharing Competition Code between separate Teams, unless a Team merger occurs. Any such sharing of Competition Code is a breach of these Competition Rules and may result in disqualification.

b. **Open Source.** You hereby license your Submission and the source code used to generate the Submission under the Open Source Initiative license presented on the Competition Website (see http://www.opensource.org) that in no event limits commercial use of such code or model containing or depending on such code. In the event that input data or pretrained models with an incompatible license are used to generate your winning solution, you do not need to grant an open source license in the preceding sentence for that data and/or model(s).

c. For generally commercially available software that you used to generate your Submission that is not owned by you, but that can be procured by the Competition Sponsor at a cost that does not exceed the amount of a prize in the competition, you do not need to grant the license in the preceding Section for that software.

**7. DETERMINING WINNERS**

a. Each Submission will be scored and/or ranked by the evaluation metric, stated on the Competition Website. During the Competition Period, the current ranking will be visible on the Competition Website's Public Leaderboard. The potential winner(s) are determined solely by the leaderboard ranking on the Private Leaderboard, subject to compliance with these Rules. The Public Leaderboard will be based on the public test set and the Private Leaderboard will be based on the private test set.

b. In the event of a tie, the Submission that was entered first to the Competition will be the winner. In the event a potential winner is disqualified for any reason, the Submission that received the next highest score rank will be chosen as the potential winner.

**8. NOTIFICATION OF WINNERS & DISQUALIFICATION**

a. The potential winner(s) will be notified by email.

b. If a potential winner (i) does not respond to the notification attempt within one (1) week from the first notification attempt or (ii) notifies Kaggle within one week after the Final Submission Deadline that the potential winner does not want to be nominated as a winner or does not want to receive a Prize, then, in each case (i) and (ii) such potential winner will not receive any Prize, and an alternate potential winner will be selected from among all eligible entries received based on the Competition's judging criteria.

c. In case (i) and (ii) above Kaggle may disqualify the Participant. However, in case (ii) above, if requested by Kaggle, such potential winner may provide code and documentation to verify the Participant's compliance with these Rules. If the potential winner provides code and documentation to the satisfaction of Kaggle, the Participant will not be disqualified pursuant to this paragraph.

d. Competition Sponsor reserves the right to disqualify any Participant from the Competition if the Competition Sponsor reasonably believes that the Participant has attempted to undermine the legitimate operation of the Competition by cheating, deception, or other unfair playing practices or abuses, threatens or harasses any other Participants, Competition Sponsor or Kaggle.

e. A disqualified Participant may be removed from the Competition leaderboard, at Kaggle's sole discretion. If a Participant is removed from the Competition Leaderboard, additional winning features associated with the Kaggle competition platform, for example Kaggle points or medals, may also not be awarded.

f. The final leaderboard list will be publicly displayed at Kaggle.com. Determinations of Competition Sponsor are final and binding.

**9. PRIZES**

a. Prize(s) are as described on the Competition Website and are only available for winning during the time period described on the Competition Website. The odds of winning any Prize depends on the number of eligible Submissions received during the Competition Period and the skill of the Participants.

b. All Prizes are subject to Competition Sponsor's review and verification of the Participant's eligibility and compliance with these Rules, and the compliance of the winning Submissions with the Submissions Requirements. In the event that the Submission demonstrates non-compliance with these Competition Rules, Competition Sponsor may at its discretion take either of the following actions: (i) disqualify the Submission(s); or (ii) require the potential winner to remediate within one week after notice all issues identified in the Submission(s) (including, without limitation, the resolution of license conflicts, the fulfillment of all obligations required by software licenses, and the removal of any software that violates the software restrictions).

c. A potential winner may decline to be nominated as a Competition Winner in accordance with Section C(8)(b).

d. Potential winners must return all required Prize acceptance documents within two (2) weeks following notification of such required documents, or such potential winner will be deemed to have forfeited the prize and another potential winner will be selected. Prize(s) will be awarded within approximately thirty (30) days after receipt by Competition Sponsor or Kaggle of the required Prize acceptance documents. Transfer or assignment of a Prize is not allowed.

e. You are not eligible to receive any Prize if you do not meet the Eligibility requirements in Section C(1).

f. If a Team wins a monetary Prize, the Prize money will be allocated in even shares between the eligible Team members, unless the Team unanimously opts for a different Prize split and notifies Kaggle before Prizes are issued.

**10. TAXES**

ALL TAXES IMPOSED ON PRIZES ARE THE SOLE RESPONSIBILITY OF THE WINNERS. Payments to potential winners are subject to the express requirement that they submit all documentation requested by Competition Sponsor or Kaggle for compliance with applicable state, federal, local and foreign (including provincial) tax reporting and withholding requirements. Prizes will be net of any taxes that Competition Sponsor is required by law to withhold. If a potential winner fails to provide any required documentation or comply with applicable laws, the Prize may be forfeited and Competition Sponsor may select an alternative potential winner. Any winners who are U.S. residents will receive an IRS Form-1099 in the amount of their Prize.

**11. GENERAL CONDITIONS**

You will comply with all applicable federal, state, provincial and local laws and regulations.

**12. PUBLICITY**

You grant to Competition Sponsor and Kaggle and its affiliates an unrestricted, sublicensable, assignable, irrevocable, perpetual, worldwide, royalty-free license to your name, voice, image, persona, likeness, and performance in any audio, visual, and audiovisual recordings (including, but not limited to, photographs, digital images, digital video, digital audio, video tape, and audio tape) taken or to be taken of you by or on behalf of Kaggle (the "Content") in the Competition listed above. This license includes without limitation the right to (i) reproduce, create derivative works of, and otherwise use the Content, in whole or in part, in any manner or in combination with any other material (the "Works"); and (ii) publicly display, publicly perform, sell, rent, distribute (directly or indirectly), transmit, or broadcast the Works. You further acknowledge that this license grants Kaggle the right to include Content in end-of-the-year recaps, Kaggle events, award show submissions, and fixed media for award shows. You waive all rights and release Kaggle from, and hold Kaggle harmless from, any claim, whether now known or unknown, relating to the use and exploitation of the Content.

**13. PRIVACY**

a. You acknowledge and agree that Competition Sponsor and Kaggle may collect, store, share and otherwise use personally identifiable information provided by you during the Kaggle.com account registration process and the Competition, including but not limited to, name, mailing address, phone number, and email address ("Personal Information"). Kaggle acts as an independent controller with regard to its collection, storage, sharing, and other use of this Personal Information, and will use this Personal Information in accordance with its Privacy Policy, including for administering the Competition. As a Kaggle.com account holder, you have the right to request access to, review, rectification, portability or deletion of any personal data held by Kaggle about you by logging into your account and/or contacting Kaggle Support.

b. As part of Competition Sponsor performing this contract between you and the Competition Sponsor, Kaggle will transfer your Personal Information to Competition Sponsor, which acts as an independent controller with regard to this Personal Information. As a controller of such Personal Information, Competition Sponsor agrees to comply with all U.S. and foreign data protection obligations with regard to your Personal Information. Kaggle will transfer your Personal Information to Competition Sponsor in the country specified in the Competition Sponsor Address listed above, which may be a country outside the country of your residence. Such country may not have privacy laws and regulations similar to those of the country of your residence.

**14. WARRANTY, INDEMNITY AND RELEASE**

a. You warrant that your Submission is your own original work and, as such, you are the sole and exclusive owner and rights holder of the Submission, and you have the right to make the Submission and grant all required licenses. You agree not to make any Submission that: (i) infringes any third party proprietary rights, intellectual property rights, industrial property rights, personal or moral rights or any other rights, including without limitation, copyright, trademark, patent, trade secret, privacy, publicity or confidentiality obligations, or defames any person; or (ii) otherwise violates any applicable U.S. or foreign state or federal law.

b. To the maximum extent permitted by law, you indemnify and agree to keep indemnified Competition Entities at all times from and against any liability, claims, demands, losses, damages, costs and expenses resulting from any of your acts, defaults or omissions and/or a breach of any warranty set forth herein. To the maximum extent permitted by law, you agree to defend, indemnify and hold harmless the Competition Entities from and against any and all claims, actions, suits or proceedings, as well as any and all losses, liabilities, damages, costs and expenses (including reasonable attorneys fees) arising out of or accruing from: (i) your Submission or other material uploaded or otherwise provided by you that infringes any third party proprietary rights, intellectual property rights, industrial property rights, personal or moral rights or any other rights, including without limitation, copyright, trademark, patent, trade secret, privacy, publicity or confidentiality obligations, or defames any person; (ii) any misrepresentation made by you in connection with the Competition; (iii) any non-compliance by you with these Rules or any applicable U.S. or foreign state or federal law; (iv) claims brought by persons or entities other than the parties to these Rules arising from or related to your involvement with the Competition; and (v) your acceptance, possession, misuse or use of any Prize, or your participation in the Competition and any Competition-related activity.

c. You hereby release Competition Entities from any liability associated with: (a) any malfunction or other problem with the Competition Website; (b) any error in the collection, processing, or retention of any Submission; or (c) any typographical or other error in the printing, offering or announcement of any Prize or winners.

**15. INTERNET**

Competition Entities are not responsible for any malfunction of the Competition Website or any late, lost, damaged, misdirected, incomplete, illegible, undeliverable, or destroyed Submissions or entry materials due to system errors, failed, incomplete or garbled computer or other telecommunication transmission malfunctions, hardware or software failures of any kind, lost or unavailable network connections, typographical or system/human errors and failures, technical malfunction(s) of any telephone network or lines, cable connections, satellite transmissions, servers or providers, or computer equipment, traffic congestion on the Internet or at the Competition Website, or any combination thereof, which may limit a Participant's ability to participate.

**16. RIGHT TO CANCEL, MODIFY OR DISQUALIFY**

If for any reason the Competition is not capable of running as planned, including infection by computer virus, bugs, tampering, unauthorized intervention, fraud, technical failures, or any other causes which corrupt or affect the administration, security, fairness, integrity, or proper conduct of the Competition, Competition Sponsor and Kaggle each reserves the right to cancel, terminate, modify or suspend the Competition. Competition Sponsor and Kaggle each further reserves the right to disqualify any Participant who tampers with, undermines, or otherwise damages the submission process or any other part of the Competition or Competition Website. Any attempt by a Participant to deliberately damage any website, including the Competition Website, or undermine the legitimate operation of the Competition is a violation of criminal and civil laws. Should such an attempt be made, Competition Sponsor and Kaggle each reserves the right to disqualify and seek damages, equitable relief, and any available remedy from any such Participant to the fullest extent of the applicable law.

**17. NOT AN OFFER OR CONTRACT OF EMPLOYMENT**

Under no circumstances will the entry of a Submission, the awarding of a Prize, or anything in these Rules be construed as an offer or contract of employment with Competition Sponsor or any of the Competition Entities. You acknowledge that you have submitted your Submission voluntarily and not in confidence or in trust. You acknowledge that no confidential, fiduciary, agency, employment or other similar relationship is created between you and Competition Sponsor or any of the Competition Entities by your acceptance of these Rules or your entry of your Submission.

**18. DEFINITIONS**

"Competition Data" are the data or datasets available from the Competition Website for the purpose of use in the Competition, including any prototype or executable code provided on the Competition Website. The Competition Data will contain private and public test sets. Which data belongs to which set will not be made available to Participants.

An "Entry" is when a Participant has joined, signed up, or accepted the rules of a competition. Entry is required to make a Submission to a competition.

"Final Submission" is the Submission selected by the user, or automatically selected by Kaggle in the event not selected by the user, that is/are used for final placement on the competition leaderboard.

"Participant" or "Participant User" is an individual who participates in a competition by entering the competition and making a Submission.

"Private Leaderboard" is a ranked display of Participants' Submission scores against the private test set. The Private Leaderboard determines the final standing in the competition.

"Public Leaderboard" is a ranked display of Participants' Submission scores against a representative sample of the test data. This leaderboard is visible throughout the competition.

"Sponsor" is responsible for hosting the competition, which includes but is not limited to providing the data for the competition, determining winners, and enforcing competition rules.

"Submission" is anything provided by the Participant to the Sponsor to be evaluated for competition purposes and determine leaderboard position. A Submission may be made as a model, notebook, prediction file, or other format as determined by the Sponsor.

"Team" is one or more Participants participating together in a Kaggle competition, by officially merging together as a Team within the competition platform.

---

## Data

Source: https://www.kaggle.com/competitions/google-verifiable-quantum-circuit-compilation/data

### Dataset Description

Your task is to optimize three quantum circuits relevant for combinatorial optimization, fusion research, and chemistry. The more optimal the circuit, the sooner it will be possible to build working implementations on real quantum hardware.

#### Problem specification

The verifiers in `verifiers/` are the authoritative specification, and the paper explains each contract. A verifier simulates your circuit with kickmix on many inputs and checks every shot: inputs restored, scratch qubits back to |0⟩, and the right phase. Measurement-based uncomputation is allowed. Tests are seeded from your submission's hash plus a secret salt, so any change to a circuit gets fresh tests (paper §II.C).

**invsqrt (the paper's Benchmark I, §III.A)**

Map |x⟩|0⟩ ↦ e^{2πi/√x} |x⟩|0⟩ for every x from 1 to 3,133,452, held in a 22-qubit register named `x`. Each input is tested 64 times, and every phase must be within 2^{-24}/√x turns. Cost: qubits × Toffoli-equivalents (Toffolis plus T gates / 4, with rotations priced in T gates).

**dqi (the paper's Benchmark II, §III.B)**

A reversible decoder for the Reed–Solomon code RS(4095, 4025) over GF(2¹²). Given error syndromes in registers S0 to S69 and a classical record M in E0 to E4094, it restores the syndromes and applies the phase (−1)^{Σ_j popcount(e_j ∧ M_j)} for the error e. It is tested on 102,400 shots; failures are allowed but raise the cost. Cost: R(ε+) × Q² × T, with R a repetition factor that grows with the failure rate (paper Eq. (43)).

**dfthcsos (the paper's Benchmark III, §III.C and App. A)**

Circuits that load the Givens-rotation angles of a factorized FeMoCo Hamiltonian, one batch of J angles per circuit, plus the factorization and rotation tree in `submission.npz`. A submission is rejected if any circuit uses more than 128 qubits, if the encoded Hamiltonian is more than 20 mHa from the reference, or if the LCU normalization Λ ≤ 49.0 or E_gap ≤ 3.914898 Ha. Cost: λ_eff × T_total × Q_total over the whole block encoding (paper Eq. (44)). The full contract is in `verifiers/dfthcsos/SCORING_README.md`, and the starter kit builds a complete submission from the provided baseline.

#### Files

**Total:** 34 files, 1.04 GB. Type: py, kmb, npz + 5 others. License: Apache 2.0.

Exact paths and sizes below come from `kaggle competitions files google-verifiable-quantum-circuit-compilation` (sizes in bytes, upload date 2026-10-22). Note that `sample_submission/dqi.kmb` alone is ~886 MB, i.e. most of the dataset.

| Path | Size (bytes) | Size |
|---|---:|---:|
| verifiable_circuit_compilation.pdf (the paper) | 1,092,999 | 1.09 MB |
| kickmix/LICENSE.txt | 11,358 | 11.36 kB |
| kickmix/kickmix.so | 3,220,392 | 3.22 MB |
| sample_submission/invsqrt.kmb | 579,721 | 579.7 kB |
| sample_submission/dqi.kmb | 886,118,180 | 886.1 MB |
| sample_submission/dfthcsos/angle_k_0.kmb | 1,671,932 | 1.67 MB |
| sample_submission/dfthcsos/angle_k_1.kmb | 1,662,896 | 1.66 MB |
| sample_submission/dfthcsos/angle_k_2.kmb | 1,665,821 | 1.67 MB |
| sample_submission/dfthcsos/angle_k_3.kmb | 1,666,802 | 1.67 MB |
| sample_submission/dfthcsos/angle_k_4.kmb | 1,954,082 | 1.95 MB |
| sample_submission/dfthcsos/angle_k_5.kmb | 1,948,583 | 1.95 MB |
| sample_submission/dfthcsos/angle_k_6.kmb | 1,947,980 | 1.95 MB |
| sample_submission/dfthcsos/angle_k_7.kmb | 1,968,527 | 1.97 MB |
| sample_submission/dfthcsos/angle_k_8.kmb | 1,957,124 | 1.96 MB |
| sample_submission/dfthcsos/angle_k_9.kmb | 1,953,830 | 1.95 MB |
| sample_submission/dfthcsos/submission.npz | 4,537,436 | 4.54 MB |
| verifiers/LICENSE.txt | 11,358 | 11.36 kB |
| verifiers/dfthcsos/FeMoCo76o113e.fcidump | 128,128,348 | 128.1 MB |
| verifiers/dfthcsos/FeMoCo76o113e.fixed_shifts.npz | 61,028 | 61.0 kB |
| verifiers/dfthcsos/SCORING_README.md | 22,477 | 22.5 kB |
| verifiers/dfthcsos/__init__.py | 326 | 326 B |
| verifiers/dfthcsos/verify.py | 31,752 | 31.8 kB |
| verifiers/dfthcsos/example_submission/angle_k_reference_circuit.py | 10,258 | 10.3 kB |
| verifiers/dfthcsos/scoreinfra/__init__.py | 280 | 280 B |
| verifiers/dfthcsos/scoreinfra/circuits.py | 24,418 | 24.4 kB |
| verifiers/dfthcsos/scoreinfra/costs_prepare.py | 8,335 | 8.3 kB |
| verifiers/dfthcsos/scoreinfra/dfthc_math.py | 17,608 | 17.6 kB |
| verifiers/dfthcsos/scoreinfra/reference.py | 13,180 | 13.2 kB |
| verifiers/dqi/__init__.py | 87 | 87 B |
| verifiers/dqi/dqi_reference_circuit.py | 30,450 | 30.5 kB |
| verifiers/dqi/verify_submission_dqi.py | 20,959 | 21.0 kB |
| verifiers/invsqrt/__init__.py | 84 | 84 B |
| verifiers/invsqrt/nr_reference_circuit.py | 18,862 | 18.9 kB |
| verifiers/invsqrt/verify_submission_invsqrt.py | 17,210 | 17.2 kB |

Summary breakdown shown on page: .kmb x12, .fcidump x1, .npz x2, Other x19 (34 files total).

(The earlier version of this section listed `code/` subfolders under `verifiers/`; the file listing above shows no such folders, so those were an artifact of the Data Explorer view and have been removed.)

#### Pending Kickmix Update

The kickmix library should be available on PyPI in the near future. When it's available there, the competition will drop it from the competition dataset and migrate the metric to use the PyPI copy. (Note from the host post: kickmix is now on PyPI; see Discussion section.)

#### Metadata

- **License:** Apache 2.0

#### Companion dataset

The dfthcsos starter kit is a separate dataset, the "Verifiable Circuit Compilation Starter Kit". It builds a complete dfthcsos submission from the provided baseline in three steps, and its page describes its files.

---

## Code

Source: https://www.kaggle.com/competitions/google-verifiable-quantum-circuit-compilation/code

Notebook listing (sorted as shown on the page, default "All" filter). Format: title | score (as displayed) | comments | badge (if shown). Authors are not shown in the captured page text; "Google Quantum AI - Verifiable Quantum Circuit Compilation" appears as the dataset attached to each notebook.

| # | Title | Score | Comments | Badge | Updated |
|---|---|---|---|---|---|
| 1 | The dataset is now public now. Enjoy!⭐⭐⭐ | 22.58102 | 0 | – | 1h ago |
| 2 | 22.57 LB: Verified Three-Task Portfolio | 22.57358 | 0 | Silver | 38m ago |
| 3 | 🪶 The Unbearable Lightness of Quantum Circuits | 22.57336 | 0 | Bronze | 3h ago |
| 4 | LB 22.33981 \| 22x Cheaper Than Google's Circuits | 22.33981 | 2 | Bronze | 7h ago |
| 5 | 🜁 But Some Q Squared \| Width Lab | 22.37455 | 0 | Bronze | 3h ago |
| 6 | The Real $150K Was the Friends We Made | 22.00949 | 1 | Bronze | 13m ago |
| 7 | Google Quantum AI - Verifiable Quantum Circuit 7 | 1.01496 | 0 | – | 2h ago |
| 8 | 🧠 Google Quantum AI \| Deep EDA with Analogies | 21.87976 | 0 | Bronze | 16h ago |
| 9 | Narrowed 877Q DQI and Progressive R10 Chemistry | 21.8796 | 0 | Bronze | 18h ago |
| 10 | "Google Quantum AI - Verifiable Quantum Circuit 5 | 1.01496 | 0 | – | 4h ago |
| 11 | Quantum Circuits \| 22.44 Local GM: Our Chemistry | 22.37455 | 3 | Silver | 6h ago |
| 12 | kickmix_tools | – | 0 | – | 1h ago |
| 13 | DQI Width Anatomy 897 Qubits | – | 0 | – | 4h ago |
| 14 | DQI Salt Check: Public Frontier | – | 0 | – | 5h ago |
| 15 | 🚀 21.87+ Fused DQI & C46 Chemistry [Gold] | 22.5093 | 0 | Gold | 5h ago |
| 16 | Qcomp harvest 210 | 20.50608 | 0 | – | 7h ago |
| 17 | 21.0 circuits, let's all reach the plateau! | 21.02523 | 8 | Bronze | 1d ago |
| 18 | 22.34 LB Reproducible Best-of-Public Portfolio | 22.33981 | 0 | – | 7h ago |
| 19 | DF-THC: Merge Groups Before Dropping Them | – | 0 | – | 1d ago |
| 20 | Quantum Circuit Compilation from Source | 22.00949 | 2 | Silver | 10h ago |

Note: the page text lists these notebooks in one listing, but some badges and score values are shown without an explicit author name in the captured text. The "Score" values are as displayed on the notebook cards (the listing does not show which metric column they correspond to). Notebook authors are not visible in the captured text. The list may be incomplete (the page loads more on scroll; only the first page was captured).

---

## Discussion

Source: https://www.kaggle.com/competitions/google-verifiable-quantum-circuit-compilation/discussion (listing sorted by recent comments)

### Pinned topics

**[Update] kickmix is now on PyPI (Windows, Linux, and macOS wheels)** (topic 753307)
- Author: Tanuj Khattar, marked "Competition Host", posted 14 hours before scrape; the page showed a vote count of 9, a reaction count of 3, and "0 Comments" at read time.
- Full text (host announcement):

> Hi Everyone,
>
> To make local development easier, we've released kickmix on PyPI with prebuilt wheels for Windows (x86_64), Linux (x86_64), and macOS (Apple Silicon and Intel) for Python 3.10–3.14: https://pypi.org/project/kickmix/#files
>
> You can now install it directly with:
>
> `pip install kickmix`
>
> and build and verify circuits locally without needing to build from source.
>
> Please reply in this thread if you run into any issues.
>
> Thanks!

**How to get started + Competition's Official Discord** (topic 750817)
- Author: María Cruz, marked "Kaggle Staff", posted 9 days before scrape; 13 upvotes; 1 comment.
- Full text (Kaggle Staff post):

> Information for newbies
>
> New to machine learning and data science? No question is too basic or too simple. Feel free to start your own thread, or use this thread as a place to post any first-timer clarifying questions for the Kaggle community to help you with!
>
> New to Kaggle? Take a look at a few videos to learn a bit more about site etiquette, Kaggle lingo, and how to enter a competition using Kaggle Notebooks. Publish and share your models on Kaggle Models!
>
> Participants under 18 years old: If you are under 18 years old and want to participate in this competition, you need to submit a couple of forms:
>
> Form #1: Parent/Guardian consent for minor's use of kaggle.com. You only have to fill this out once, and it is valid for any competitions on Kaggle. If you already filled this out in the past, you can move on to the next form.
>
> Form #2: Parent/Guardian consent for minor's participation in Kaggle competition. You have to fill out form #2 for this and any future competitions you want to join. Kids under 13 years of age are not allowed to participate on Kaggle. If you have any questions, please leave a comment and we'll follow up with you!
>
> Looking for a team? Express your interest in joining a team through our Team Up feature.
>
> Remember: Kaggle is for everyone. Whether you're teaming up or sharing tips in the competition forum, we expect everyone to follow our Kaggle community guidelines.
>
> **Competition's Official Discord**
>
> In addition to this competition forum, you can continue the discussion in our official Kaggle Discord Server here: discord.gg/kaggle
>
> The Discord is a great place to ask getting started questions, chat about the nuances of this competition, and connect with potential team mates. Learn more about Discord at our announcement here. Here are a few things to keep in mind though:
>
> 1. **Discord Competition Channels are 'Public' - Don't Share Private Information.** Discord channels for specific competitions are considered 'public' spaces where you are allowed to talk about competition details. Please remember that private sharing of competition code or data outside of your team is, as always, not permitted. Code sharing must always be done publicly through the Kaggle forums/notebooks.
> 2. **Discord Competition Channels are Not Monitored by Staff - Keep Important Questions on the Kaggle Forums.** Kaggle Staff and Hosts running competitions will not monitor Discord or be available to answer questions in Discord. This is intended to be a more casual space to discuss competitions and help each other. Please keep important questions, insights, writeups, and other valuable conversation on the Kaggle forums.
>
> Happy modeling!

### Other topics (as listed, sorted by recent comments; titles and authors as shown)

| Title | Author | Activity |
|---|---|---|
| What didn't work: 30-odd measured nulls across invsqrt, dqi and the chemistry | alex chilton | last comment 1h ago by manwithacat; 2 comments; 3 upvotes |
| This competition has gone absolutely wild！ | ynhuhu | last comment 3h ago by Valerio Dolci; 4 comments; 2 upvotes |
| invsqrt verifier: skipping x that can't arise in the algorithm? | manwithacat | posted 4h ago; 0 upvotes |
| Reading DQI leaderboard scores: a small salt effect | manwithacat | last comment 5h ago by manwithacat; 1 comment; -1 |
| An interactive look inside the invsqrt circuit | manwithacat | posted 8h ago; 1 upvote |
| dqi task: ~8e-5 phase errors with value_errors = 0 — expected, or a fixable implementation detail? | xhsmsuper | last comment 8h ago by xhsmsuper; 6 comments; 0 |
| Uhh I ain't giving you everything. Should I exit? | Jason Chewning | last comment 9h ago by D Chakraborty; 9 comments; -8 |
| Clarification on ANGLE_k target-register inputs | Chat8903 | last comment 9h ago by manwithacat; 6 comments; 2 |
| 20.39 circuits, let's all reach the plateau! | mrmeows | last comment 10h ago by mrmeows; 11 comments; 18 |
| Winner source-delivery requirements for public compiled inputs | Adem Vessell | last comment 12h ago by Tanuj Khattar; 2 comments; 6 |
| Verifying big circuits locally: a kickmix build that uses far less memory (same results) | manwithacat | last comment 14h ago by manwithacat; 6 comments; 1 |
| Clarification on Apache-2.0 circuit reuse and winner reproducibility | Michael O'Flaherty | posted 14h ago; 0 |
| What are you guys scoring in each task? | mikelou1 | last comment 15h ago by Yair Be'ery; 16 comments; 6 |
| Briefing: the plateau moved to 21, the top is still private — 2026-10-27 | manwithacat | last comment 16h ago by D Chakraborty; 2 comments; 0 |
| What happened in scoring？ | Zejun_ | last comment 16h ago by Sohier Dane; 5 comments; 0 |
| Briefing: what we know after two days (ish) 2026-OCT-26 | manwithacat | last comment 1d ago by alex chilton; 5 comments; 0 |
| 이 대회용 알고리즘 등을 잘 만들어지도록 하려면 AI 들 중 어떤 모델 사용하는게 나은가요? | Ari_Sullae official (아리술래) | last comment 1d ago by De DQ; 8 comments; -5 |
| How to start the competition ? | Affes Ahmed | last comment 1d ago by Roko Torbarina; 1 comment; 1 |

Note: the listing shows page 1 only (the page shows "1 2" pagination; page 2 was not captured). Non-host topics are listed by title only; their bodies were not read.

---

## Leaderboard

Source: https://www.kaggle.com/competitions/google-verifiable-quantum-circuit-compilation/leaderboard

- **Leaderboard views:** Public / Private (the Public view was captured).
- **Caveat stated on page:** "This leaderboard is calculated with approximately 50% of the test data. The final results will be based on the other 50%, so the final standings may be different."
- **Number of teams:** 1,388 (from overview stats). The leaderboard shows "1389" as the last position marker and "See 1340 More" beyond the top 49 shown.

### Top entries (Public, as displayed)

| Rank | Team | Members | Score | Entries | Last submission |
|---|---|---|---|---|---|
| 1 | Breaking1800 | – | 26.14113 | 17 | 6h |
| 2 | Jack | – | 25.05174 | 22 | 10h |
| 3 | Thinking... | – | 24.58925 | 24 | 2h |
| 4 | Schrödinger's cat lived | – | 24.15873 | 24 | 12h |
| 5 | Distortion!! | – | 23.94623 | 14 | 3h |
| 6 | Kevin Bogner | – | 23.90345 | 10 | 2h |
| 7 | Z³uperposition | – | 23.84846 | 25 | 7h |
| 8 | Bingran You | – | 23.83253 | 20 | 5h |
| 9 | Zyy7390 | – | 23.66860 | 16 | 1d |
| 10 | James & Tony | – | 23.64469 | 30 | 11h |
| 11 | shyjin | – | 23.60350 | 9 | 4h |
| 12 | 田村さんを囲む会 | – | 23.14567 | 30 | 1h |
| 13 | bunnywasnothere | – | 23.11598 | 23 | 10h |
| 14 | Riemann | – | 23.08451 | 9 | 6h |
| 15 | Xiangyi Li | – | 23.05746 | 20 | 7h |
| 16 | Shohrux Azizov | – | 23.03789 | 5 | 2h |
| 17 | Bhargav6031 | – | 23.01218 | 7 | 1h |
| 18 | Adisak Sukul | – | 23.00250 | 29 | 5h |
| 19 | Season | – | 22.98990 | 31 | 10h |
| 20 | Danial Motlagh | – | 22.97868 | 16 | 12h |
| 21 | catv eg | – | 22.97394 | 17 | 1h |
| 22 | Slingshot Effect | – | 22.97273 | 18 | 20h |
| 23 | Doraking | – | 22.94011 | 25 | 3h |
| 24 | Álvaro | – | 22.86698 | 11 | 2h |
| 25 | ㅤ | – | 22.79334 | 4 | 4h |
| 26 | Gagandeep singh | – | 22.78164 | 9 | 10h |
| 27 | Лукин Алексей | – | 22.77786 | 10 | 2h |
| 28 | Snehal Raj | – | 22.73577 | 6 | 2h |
| 29 | VAGO Superposition | – | 22.72031 | 6 | 17h |
| 30 | Azamat Sarsembay | – | 22.69810 | 8 | 3h |
| 31 | Houssem Alayet | – | 22.69810 | 27 | 1h |
| 32 | Adarsh Balanolla | – | 22.67401 | 18 | 4h |
| 33 | yesterdays_rebel | – | 22.67235 | 11 | 1h |
| 34 | Shuyu | – | 22.66832 | 11 | 6h |
| 35 | Moegi | – | 22.64141 | 10 | 2h |
| 36 | Alessandro Summer | – | 22.63976 | 12 | 2h |
| 37 | xi luo | – | 22.62793 | 22 | 4h |
| 38 | Stas | – | 22.62580 | 13 | 5h |
| 39 | Maurice | – | 22.62559 | 7 | 6h |
| 40 | Quan Vu | – | 22.62147 | 19 | 2h |
| 41 | Sma1lboy | – | 22.61965 | 8 | 5h |
| 42 | ktm | – | 22.61777 | 7 | 38m |
| 43 | Max Freedom Pollard | – | 22.60855 | 23 | 1h |
| 44 | Amanie El-Hajj | – | 22.60831 | 23 | 43m |
| 45 | JINSEI | – | 22.60331 | 5 | 2h |
| 46 | Phạm Ngọc Thiên Ân | – | 22.60246 | 2 | 2h |
| 47 | Satvik Verma | – | 22.60113 | 15 | 4h |
| 48 | MOHAMMADJAFAR ZAMANI | – | 22.60090 | 19 | 32m |
| 49 | Nevska | – | 22.59191 | 4 | 1h |

Pagination: "50 - 1389 · See 1340 More" (not expanded). Team member names were not shown in the captured text.

---

## Models

Source: https://www.kaggle.com/competitions/google-verifiable-quantum-circuit-compilation/models

Page showed the filter tabs (All / Your Work / Shared With You / Most Usage) with no model entries listed. No models are attached to this competition at scrape time.

---

## Team

Not scraped. The Team tab is a per-user page (requires being logged in and entered); it was not opened in this session.

---

## Submissions

Not scraped. The Submissions tab is per-user and was not opened in this session.

---

## Scrape Notes

- **Browser session:** Logged-in Chrome session used via the browser tools. A new tab was created for the scrape and closed afterward.
- **Pages fully captured:** Overview, Rules, Data (file listing partially expanded), Code (first page of notebooks), Discussion (first page of topic listing plus the two pinned topics read in full), Leaderboard (Public view, top 49 entries), Models (empty).
- **Pages not captured:** Team, Submissions (per-user). Private leaderboard was not viewed.
- **Incomplete items:**
  - Data file sizes: resolved in a follow-up pass using the Kaggle CLI file listing (see Data > Files).
  - Code notebook authors were not visible in the captured text.
  - Discussion listing page 2 was not captured; non-host threads were recorded by title and metadata only.
  - Leaderboard: only top 49 of approximately 1,388 teams shown.
- **Formula rendering:** Evaluation formulas were re-checked in a follow-up pass directly against the page's MathML and match the plain-text forms in the Evaluation section.
- **No login-gated content was guessed or invented.** Items not visible are marked as such above.
