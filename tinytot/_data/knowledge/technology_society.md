# Technology, Computing, and Society

## Machine Learning and Artificial Intelligence

Machine learning (ML) is a branch of artificial intelligence (AI) in which systems learn patterns from data without being explicitly programmed for each task. AI is the broader field of computer science focused on creating systems that perform tasks requiring human intelligence. ML trains models on labelled examples that generalise to new inputs. Types of machine learning: supervised learning (labelled data — e.g. spam classification), unsupervised learning (no labels — finds structure), and reinforcement learning (learns via reward signals).

Deep learning uses neural networks with many layers (deep networks). Each layer learns increasingly abstract representations. Deep learning powers image recognition, speech recognition, and large language models.

A neural network is a computational model inspired by the brain — layers of interconnected nodes (neurons) with learned weights. Input flows through hidden layers to produce an output. Training uses backpropagation and gradient descent to adjust weights to minimise prediction error.

## How the Internet Works

The internet is a global network of networks — billions of devices connected by routers that forward data packets. Key concepts:

- IP (Internet Protocol): every device has an IP address. IPv4 uses 32-bit addresses (e.g. 192.168.1.1); IPv6 uses 128-bit addresses.
- DNS (Domain Name System): translates human-readable domain names (google.com) to IP addresses — the internet's phone book.
- TCP (Transmission Control Protocol): ensures reliable, ordered delivery of data. Breaks data into packets, numbers them, and reassembles them at the destination.
- HTTP/HTTPS: the protocol for transferring web pages. HTTPS adds TLS encryption (SSL certificate), so data is encrypted in transit — the padlock icon in browsers.
- Routers: forward packets toward their destination using routing tables. Data may traverse dozens of routers across continents.
- A web request: browser → DNS lookup → TCP connection → HTTP request → server response → rendered page.

## HTTP vs HTTPS

HTTP (Hypertext Transfer Protocol): data sent in plain text — anyone who intercepts the connection can read it. Used for non-sensitive web content.

HTTPS (HTTP Secure): wraps HTTP in TLS (Transport Layer Security) encryption. The server presents a digital certificate to prove its identity; browser and server exchange encryption keys; all subsequent data is encrypted. HTTPS prevents eavesdropping and man-in-the-middle attacks. Indicated by the padlock icon and "https://" in the browser URL bar.

## API (Application Programming Interface)

API stands for Application Programming Interface. An API defines how two pieces of software communicate — what requests can be made, what format data should be in, and what responses look like. A REST API uses HTTP methods (GET, POST, PUT, DELETE) on URLs representing resources, typically returning JSON. APIs allow different services to talk to each other: a weather app calls a weather API, a payment form calls Stripe's API.

## Encryption and Cybersecurity

Encryption scrambles data so only authorised parties can read it using a key. Two main types:
- Symmetric encryption: same key encrypts and decrypts (e.g. AES). Fast; used for bulk data.
- Asymmetric (public-key) encryption: a public key encrypts; only the matching private key decrypts (e.g. RSA). Used for key exchange and digital signatures.

TLS/SSL uses asymmetric encryption to establish a shared symmetric key, then symmetric encryption for the actual data transfer.

A digital certificate (X.509) ties a public key to an identity, signed by a trusted Certificate Authority (CA). Browsers ship with a list of trusted CAs.

## Democracy, Government, and Political Systems

Democracy is a system of government in which power is held by the people, exercised either directly or through elected representatives. Key principles: free and fair elections, rule of law, protection of individual rights, separation of powers.

Types:
- Direct democracy: citizens vote directly on laws (used in referendums, ancient Athens).
- Representative (liberal) democracy: citizens elect representatives to make laws on their behalf (most modern nations).
- Constitutional monarchy: a monarch as head of state, but power is constrained by a constitution and a parliament (UK, Sweden, Japan).

Separation of powers (Montesquieu): legislative (makes laws), executive (implements laws), judicial (interprets laws) — each branch checks the others.

## Neurons and the Nervous System

A neuron (nerve cell) is the basic functional unit of the nervous system. Neurons transmit electrical and chemical signals. Structure:
- Dendrites: receive signals from other neurons.
- Cell body (soma): contains the nucleus; integrates signals.
- Axon: transmits signals away from the cell body.
- Axon terminals (synaptic knobs): release neurotransmitters into the synapse.

At a synapse, an electrical signal in the presynaptic neuron causes release of neurotransmitters (e.g. dopamine, serotonin, acetylcholine) into the synaptic cleft; these bind to receptors on the postsynaptic neuron, triggering or inhibiting a new signal.

The central nervous system (CNS): brain + spinal cord.
The peripheral nervous system (PNS): all nerves outside the CNS.
The autonomic nervous system controls involuntary functions (heart rate, digestion, breathing).

Sleep: adults need 7–9 hours per night. The brain consolidates memories, clears metabolic waste, and repairs tissue during sleep. Chronic sleep deprivation impairs cognition, immunity, and cardiovascular health.

## Blockchain and Cryptocurrency

A blockchain is a distributed ledger — a chain of blocks, each containing a batch of transactions. Each block includes a cryptographic hash of the previous block, making the chain tamper-evident. No single party controls the ledger; copies are maintained by many nodes (decentralised). Bitcoin was the first major blockchain (2009, Satoshi Nakamoto).

Cryptocurrency is a digital currency that uses cryptography to secure transactions and control the creation of new units. Bitcoin is the first and most valuable by market cap. Ethereum adds smart contracts — self-executing code on the blockchain.

Proof of work: miners solve computationally hard puzzles to add blocks; rewarded with cryptocurrency. Proof of stake: validators are chosen in proportion to the cryptocurrency they "stake" as collateral — far more energy-efficient.

## 5G and Mobile Networks

5G is the fifth generation of mobile network technology, succeeding 4G LTE. Key improvements:
- Speed: peak download speeds up to 10 Gbps (vs ~1 Gbps for 4G).
- Latency: as low as 1 ms (vs 20–50 ms for 4G).
- Density: supports many more simultaneous connections per area.
5G uses higher-frequency millimetre-wave spectrum (faster but shorter range) alongside lower bands. Applications include smart cities, autonomous vehicles, industrial automation, and AR/VR.

## The Renaissance

The Renaissance (Italian: "rebirth") was a cultural, intellectual, and artistic movement that began in Italy in the 14th century and spread across Europe through the 16th century. It marked the transition from the Middle Ages to modernity. Key characteristics: revival of classical Greek and Roman ideas, humanism (focus on human potential and dignity), naturalistic art, scientific inquiry.

Key figures: Leonardo da Vinci (art, science, engineering), Michelangelo (sculpture, painting — Sistine Chapel), Raphael, Botticelli (painting), Nicolaus Copernicus (heliocentric model), Galileo Galilei (telescope, physics).

The printing press (Gutenberg, c.1440) spread Renaissance ideas rapidly across Europe.
