# Summarization Eval Dataset

Each passage has an `## Input` block and a `## Must Contain` block.
The eval script checks that the summary contains **all** must-contain phrases
(case-insensitive substring match).  Phrases test that key facts were captured,
not that specific wording was used.

Format rules:
- Section separator: `---` on its own line
- Section header: `## case-name` (one word, hyphenated)
- Optional override: `max_words: N` on the line after the header
- Input block: `### Input` followed by the passage
- Must-contain block: `### Must Contain` followed by `- phrase` bullets

Add new cases at the bottom.  Keep passages under 300 words.

---

## climate-science
max_words: 70

### Input
Global average temperatures have risen approximately 1.1 degrees Celsius since the
pre-industrial period, primarily driven by human activities that increased atmospheric
concentrations of greenhouse gases. Carbon dioxide levels reached 421 parts per million
in 2023, the highest recorded in at least 800,000 years of ice-core data.
The IPCC concluded in its Sixth Assessment Report that limiting warming to 1.5 degrees
Celsius requires reducing global net CO2 emissions by 45 percent from 2010 levels by
2030 and reaching net zero around 2050. Exceeding this threshold risks triggering
tipping points including the collapse of the West Antarctic Ice Sheet.
Renewable energy deployment accelerated sharply. Solar photovoltaic capacity grew from
40 gigawatts in 2010 to over 1,200 gigawatts by 2022, reducing its cost by 90 percent.
The European Union passed the Fit for 55 legislative package, committing to cut
emissions 55 percent by 2030. Extreme weather events intensified. The 2022 Pakistan
floods displaced 33 million people and caused 30 billion dollars in damage.

### Must Contain
- emissions
- European Union
- 55 percent

---

## tech-news-llm
max_words: 50

### Input
OpenAI released GPT-4 in March 2023, demonstrating performance that matched or
exceeded human experts on professional benchmarks including the bar exam and the
US Medical Licensing Examination. The model reached 100 million users within two months.
Google responded by launching Bard and subsequently introduced Gemini. Meta released
the LLaMA family of open-weight models, enabling researchers to run large language
models locally without API costs. The open-source release accelerated the development
of hundreds of derivative models.
Regulators in the European Union passed the AI Act, the world's first comprehensive
legal framework governing artificial intelligence. The Act classified AI into risk
tiers and imposed transparency requirements and human oversight for high-risk systems.
NVIDIA's market capitalisation crossed one trillion dollars as demand for H100 GPUs
exceeded supply by months. Governments announced subsidies for domestic semiconductor
fabrication.

### Must Contain
- GPT-4
- AI Act
- Google

---

## medical-trial
max_words: 50

### Input
A phase 3 randomised controlled trial enrolled 4,563 patients with advanced non-small
cell lung cancer whose tumours expressed PD-L1 at 50 percent or higher. Patients
received either pembrolizumab monotherapy or platinum-based chemotherapy.
The independent data monitoring committee found that pembrolizumab significantly
extended median overall survival. The hazard ratio for death was 0.63, a 37 percent
reduction in mortality risk. Median overall survival reached 30.0 months in the
pembrolizumab group versus 14.2 months in the chemotherapy group.
The Food and Drug Administration approved pembrolizumab as first-line treatment for
this patient population. The approval changed the standard of care for advanced
lung cancer treatment worldwide.

### Must Contain
- pembrolizumab
- approved
- chemotherapy

---

## history-ww2
max_words: 60

### Input
Germany invaded Poland on 1 September 1939, triggering declarations of war from
Britain and France. Poland fell within weeks and was partitioned between Germany
and the Soviet Union. Germany then launched Fall Gelb, attacking France through the
Ardennes and bypassing the Maginot Line. France fell in June 1940 and signed an
armistice. Germany occupied Paris and installed a collaborationist government at Vichy.
The Luftwaffe launched a bombing campaign to destroy the Royal Air Force before a
seaborne invasion of Britain. RAF Fighter Command repelled the assault and Hitler
postponed Operation Sea Lion indefinitely. Germany then invaded the Soviet Union on
22 June 1941 in Operation Barbarossa, the largest land invasion in history. The German
advance reached the outskirts of Moscow before Soviet resistance and the Russian winter
halted it.

### Must Contain
- Poland
- France
- Maginot

---

## legal-contract
max_words: 50

### Input
The parties entered into a supply agreement under which the defendant agreed to deliver
10,000 metric tonnes of aluminium alloy per quarter at 1,840 dollars per tonne. The
defendant failed to deliver the contracted quantities, citing disruptions caused by the
COVID-19 pandemic and invoking the force majeure clause.
The plaintiff rejected the force majeure claim, arguing the pandemic was a foreseeable
risk the defendant had failed to mitigate. The plaintiff commenced proceedings and
claimed damages of 18.4 million dollars. The tribunal found that the pandemic did not
qualify as a force majeure event under the clause language, which required performance
to be rendered impossible rather than merely more difficult. The defendant was ordered
to pay compensatory damages of 14.2 million dollars.

### Must Contain
- force majeure
- damages
- 14.2

---

## fiction-fellowship-break
max_words: 50

### Input
The Fellowship was broken. Boromir lay dead, shot through with arrows of the Uruk-hai.
Frodo had taken the boat alone and crossed the River, determined to go on to Mordor
without leading his friends into greater danger. Sam leapt into the water and Frodo
pulled him in. Together they set foot on the eastern shore.
Aragorn, Legolas and Gimli chose to follow the Orcs who had captured Merry and Pippin.
Merry and Pippin had escaped into Fangorn Forest during a battle between Orcs and the
Riders of Rohan. There the hobbits encountered Treebeard, oldest of the Ents, who led
the Ents to destroy Isengard. Gandalf, returned as Gandalf the White, freed King Theoden
of Rohan from Saruman's influence. Theoden led his people to Helm's Deep, where
Saruman's army attacked in overwhelming numbers. Gandalf arrived at dawn and broke
the siege.

### Must Contain
- Frodo
- Mordor
- Gandalf

---

## software-design
max_words: 50

### Input
The engineering team identified three critical bottlenecks in the payment processing
pipeline. First, the synchronous database write on every transaction created a
throughput ceiling of 800 requests per second. Second, the fraud detection service
introduced 120 milliseconds of latency on every request. Third, the session cache
expired aggressively, forcing 40 percent of requests to re-authenticate.
The team redesigned the pipeline. Database writes were moved to an asynchronous queue,
increasing throughput to 12,000 requests per second. The fraud detection service was
rebuilt to run a local model, reducing added latency to 4 milliseconds. The session
cache expiry was extended from 15 minutes to 4 hours, reducing re-authentication calls
by 92 percent. Throughput improved 15-fold and end-to-end latency fell from 340
milliseconds to 47 milliseconds.

### Must Contain
- throughput
- latency
- 15-fold

---

## economics-inflation
max_words: 80

### Input
Consumer price inflation in the United States reached 9.1 percent in June 2022, the
highest rate recorded since November 1981. The Federal Reserve responded by raising
the federal funds rate from near zero to a target range of 5.25 to 5.50 percent between
March 2022 and July 2023, the fastest tightening cycle in four decades.
Higher borrowing costs slowed demand and began to bring inflation down. By late 2023
the annual inflation rate had fallen to approximately 3.1 percent. However, housing
costs and service-sector prices remained elevated, keeping inflation above the Federal
Reserve's 2 percent target.
The rapid rate increases put stress on the banking sector. Silicon Valley Bank collapsed
in March 2023 after rising interest rates eroded the value of its long-duration bond
portfolio, triggering a bank run. The Federal Deposit Insurance Corporation seized the
bank and guaranteed all deposits.

### Must Contain
- inflation
- Federal
- seized

---

## biology-crispr
max_words: 50

### Input
CRISPR-Cas9 is a molecular tool adapted from a bacterial immune system that allows
scientists to cut DNA at precise locations and insert, delete, or replace genetic
sequences. Jennifer Doudna and Emmanuelle Charpentier received the 2020 Nobel Prize
in Chemistry for developing the technology. Since then CRISPR has been applied
in medicine, agriculture, and basic research.
In medicine, the FDA approved the first CRISPR-based therapy in December 2023.
The treatment, developed by Vertex Pharmaceuticals and CRISPR Therapeutics, targets
sickle cell disease and transfusion-dependent beta-thalassemia by editing patients'
own stem cells to reactivate production of fetal haemoglobin. Clinical trial results
showed that 97 percent of sickle cell patients treated became free of severe pain crises.
In agriculture, researchers used CRISPR to develop disease-resistant crops and to
reduce the acrylamide content of potatoes.

### Must Contain
- CRISPR
- Nobel
- sickle cell

---

## climate-policy
max_words: 60

### Input
The Paris Agreement was adopted in December 2015 by 196 parties to the UN Framework
Convention on Climate Change. Countries committed to holding global warming to well
below 2 degrees Celsius above pre-industrial levels, and to pursue efforts to limit
warming to 1.5 degrees Celsius. Each country submitted a Nationally Determined
Contribution outlining its planned emissions reductions.
The United States withdrew from the agreement under President Trump in 2020 and
rejoined under President Biden in 2021. The UK committed to reducing emissions 68 percent
by 2030 compared with 1990 levels. China, the world's largest emitter, pledged to
reach peak emissions before 2030 and achieve carbon neutrality before 2060.
The Glasgow Climate Pact adopted at COP26 in 2021 was the first agreement to explicitly
call for a phase-down of unabated coal power and to phase out inefficient fossil
fuel subsidies.

### Must Contain
- Paris Agreement
- Glasgow
- coal

---

## space-exploration
max_words: 80

### Input
SpaceX launched the first crewed mission to the International Space Station entirely
on a commercial spacecraft in May 2020, carrying NASA astronauts Doug Hurley and Bob
Behnken aboard the Crew Dragon capsule. The mission demonstrated that private companies
could operate crewed spaceflight and ended NASA's dependence on Russian Soyuz vehicles
for crew transport.
NASA's Artemis programme aimed to return humans to the Moon for the first time since
1972. Artemis I, an uncrewed test flight of the Space Launch System rocket, launched
in November 2022 and successfully orbited the Moon before returning to Earth. Artemis II
was scheduled to carry four astronauts around the Moon. The programme selected SpaceX's
Starship as the lunar lander.
The James Webb Space Telescope, launched in December 2021, delivered its first scientific
images in July 2022. The telescope revealed galaxies formed within 300 million years of
the Big Bang and detected atmospheric molecules on exoplanets.

### Must Contain
- SpaceX
- Moon
- James Webb
