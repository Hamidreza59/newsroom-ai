# Explainer knowledge base

Curated, plain-language explanations used by the "AI in 30 seconds" segment. Each section is the
only source of facts the Explainer agent may use. Keep entries short, accurate and evergreen.

## gpu | What is a GPU?
A GPU, or graphics processing unit, is a chip built to do thousands of small calculations at the
same time. It was designed for drawing video-game graphics, but the same parallel math is what
training and running AI models needs. That is why AI companies buy huge numbers of GPUs and why
chipmakers that design them have become some of the most valuable companies in the world.
Keywords: chip, nvidia, amd, semiconductor, data center, compute
Track: ai, tech

## llm | What is a large language model?
A large language model is an AI system trained on enormous amounts of text to predict the next
word in a sentence. By learning those patterns at scale, it can answer questions, summarise
documents, write and translate. It does not look facts up by default, so it can sound confident
while being wrong, which is why good AI products check its answers against trusted sources.
Keywords: chatgpt, claude, gemini, llama, model, chatbot, openai, anthropic
Track: ai

## agent | What is an AI agent?
An AI agent is a language model that can take actions, not just write text. It is given tools,
such as search, a code editor or a calendar, and decides which tool to use step by step to finish
a task. Agents are powerful but need guardrails, like limits on which tools they can use and human
approval for important actions.
Keywords: agentic, autonomous, tools, automation, assistant, workflow
Track: ai

## inference | Training versus inference
Training is when an AI model learns: it processes huge datasets over weeks on thousands of chips,
which is very expensive. Inference is when the finished model is used to answer a request. Each
answer is cheap, but billions of requests add up, so companies now compete to make inference
faster and cheaper with specialised chips and smaller models.
Keywords: accelerator, serving, cost, tokens, chips, data center
Track: ai

## token | What is a token?
AI language models read and write text in small pieces called tokens. A token is often part of a
word: roughly three quarters of an English word on average. AI services usually charge by the
number of tokens processed, and a model's context window, how much it can read at once, is also
measured in tokens.
Keywords: pricing, context window, api, cost
Track: ai

## open-weights | What are open-weight models?
An open-weight model is an AI model whose trained parameters, its weights, are published so anyone
can download and run it on their own hardware. That lowers costs and lets companies keep data
private, but it also means the original developer cannot control how the model is used. Closed
models are only available through the company's own apps or services.
Keywords: open source, llama, mistral, qwen, download, local, benchmark
Track: ai

## benchmark | What is an AI benchmark?
A benchmark is a standard test used to compare AI models, such as a set of coding problems or exam
questions. Higher scores suggest a more capable model, but benchmarks only measure what they test,
and models can be tuned to score well on them, so real-world testing still matters.
Keywords: score, leaderboard, test, coding, evaluation
Track: ai

## data-center | Why AI needs data centers
AI models run in data centers: warehouse-sized buildings full of servers, chips, cooling and
network equipment. Training and serving modern AI takes so much computing that tech companies are
spending tens of billions of dollars building new ones, and their electricity use has become a
major issue for power grids and climate goals.
Keywords: power, electricity, energy, cloud, climate, infrastructure
Track: ai, tech

## semiconductor | What is a semiconductor?
A semiconductor is a material, usually silicon, that can be switched between conducting and
blocking electricity. Billions of tiny switches etched onto a silicon chip form processors and
memory. Making advanced chips needs extremely precise factories, called fabs, and only a few
companies in the world can build the most advanced ones.
Keywords: chip, tsmc, fab, foundry, silicon, manufacturing
Track: tech

## market-cap | What is market capitalization?
Market capitalization is the total value of a company's shares: the share price multiplied by the
number of shares. It is how the market values the whole company. A company's market cap changes
every second the market is open, as its share price moves.
Keywords: valuation, trillion, shares, stock, company value
Track: markets

## index | What is a stock index?
A stock index tracks a group of stocks to show how part of the market is doing. The S&P 500 follows
500 large U.S. companies, the Nasdaq Composite is weighted towards technology companies, and the
Dow Jones Industrial Average follows 30 large, well-known companies. When people say the market
went up, they usually mean one of these indices rose.
Keywords: s&p 500, nasdaq, dow, market, stocks, wall street
Track: markets

## earnings | What are earnings reports?
Public companies report their results every quarter: revenue, profit and often a forecast for the
months ahead. Stock prices can move sharply on these earnings reports, because investors compare
the results with what analysts expected, not just with the previous quarter.
Keywords: quarter, revenue, profit, forecast, guidance, results
Track: markets

## zero-day | What is a zero-day vulnerability?
A zero-day is a security flaw that the software maker does not know about yet, so there are zero
days of warning and no fix available. Attackers who find one can break in before a patch exists.
Security teams now use AI to find these flaws faster, and so can attackers.
Keywords: security, hack, exploit, vulnerability, cyberattack, patch
Track: tech

## robotaxi | How do robotaxis work?
A robotaxi is a self-driving car offered as a ride service. It combines cameras, radar and often
lidar sensors with AI software that recognises the road, predicts what others will do and plans a
safe path. Most services start in a few cities with careful testing and remote human support.
Keywords: self-driving, autonomous vehicle, waymo, driverless, uber, lidar
Track: ai, tech

## mcp | What is the Model Context Protocol?
The Model Context Protocol, or MCP, is an open standard for connecting AI assistants to tools and
data. Instead of building a custom integration for every app, a company exposes its tools through
an MCP server once, and any compatible AI assistant can use them, with the user's permission.
Keywords: tools, integration, standard, protocol, connectors, agents
Track: ai

## protein-folding | How do AI models predict protein shapes?
Proteins are chains of building blocks called amino acids that fold into precise 3D shapes, and
the shape decides what a protein does. Working out a shape in the lab can take months. AI models
such as AlphaFold learned from thousands of known structures to predict a protein's shape from its
amino-acid sequence, which helps scientists study diseases and design new medicines faster.
Keywords: alphafold, protein, structure, folding, deepmind, biology, drug discovery
Track: ai, bio

## protein-design | What is AI protein design?
AI protein design runs the problem in reverse: instead of predicting the shape of a natural protein,
a generative model proposes new amino-acid sequences meant to fold into a shape with a useful job,
such as binding to a virus or speeding up a chemical reaction. Designs still have to be made and
tested in the lab, and responsible teams screen designs for misuse.
Keywords: generative, design, enzyme, binder, synthetic biology, de novo
Track: ai, bio

## crispr | What is CRISPR?
CRISPR is a gene-editing tool adapted from a natural defence system in bacteria. It uses a guide
molecule to find a specific spot in DNA and a protein that cuts it, so scientists can disable,
repair or change a gene. It is used in research and in a small number of approved treatments.
Keywords: gene editing, dna, genetic, therapy, cas9, genome
Track: bio

## mrna | How do mRNA medicines work?
Messenger RNA, or mRNA, carries instructions that tell cells which protein to make. An mRNA vaccine
or medicine delivers those instructions so the body makes a specific protein itself, for example a
harmless piece of a virus that trains the immune system. The instructions break down naturally
after a short time.
Keywords: vaccine, moderna, rna, immune, biontech, therapy
Track: bio

## clinical-trials | How do clinical trials work?
New medicines are tested in people in stages. Phase 1 trials check safety in a small group, phase 2
looks at whether the treatment works and at what dose, and phase 3 compares it with existing care
in a much larger group. Most drugs that enter trials never reach approval, which is why trial
results can move biotech stocks sharply.
Keywords: trial, phase, fda, results, drug, patients, study
Track: bio

## fda-approval | What does FDA approval mean?
The U.S. Food and Drug Administration reviews the evidence from clinical trials to decide whether a
medicine's benefits outweigh its risks for a specific use. Approval lets a company sell the drug in
the United States for that use, and the agency keeps monitoring safety after approval.
Keywords: fda, approval, regulator, drug, label, biotech
Track: bio

## rag | What is retrieval-augmented generation?
Retrieval-augmented generation, or RAG, is a technique where an AI system looks up relevant
documents first and then writes its answer using what it found. The lookup step searches a
collection of trusted text, such as company manuals or news archives, and passes the best matches
to the language model along with the question. This helps the answer stay current and lets the
system point to its sources. It does not make a model perfect, because the model can still
misread the text it is given, but it reduces made-up answers.
Keywords: retrieval, search, grounding, documents, hallucination, sources
Track: ai

## fine-tuning | What is fine-tuning?
Fine-tuning means taking an AI model that has already been trained on broad data and training it
a little more on a smaller, specialised set of examples. The extra training adjusts the model so
it follows a particular style, format or subject area more reliably. It costs far less than
training a model from scratch, because most of what the model knows is already in place. Fine-tuning
changes how a model behaves, but it is not a good way to keep adding fresh facts.
Keywords: training, customise, specialised, adapter, lora, model, examples
Track: ai

## embeddings | What are embeddings and vector search?
An embedding is a list of numbers that represents the meaning of a piece of text, an image or
another item. Items with similar meanings end up with similar numbers, so a computer can compare
them by measuring how close the lists are. Vector search uses this idea to find the items nearest
in meaning to a query, even when they share no exact words. Embeddings and vector search are the
building blocks behind semantic search and many retrieval systems.
Keywords: vector, semantic search, similarity, database, retrieval, meaning
Track: ai

## diffusion | How do diffusion models make images?
A diffusion model is an AI system that creates images by starting from random noise and removing
the noise a little at a time. During training, it sees many real images that are gradually
covered in noise and learns to reverse that process. When generating, a text prompt guides each
cleaning step so the result matches the description. The same approach is also used for video and
audio, and it is why generated pictures can look different every time.
Keywords: image generation, noise, text-to-image, stable diffusion, video, generative
Track: ai

## multimodal | What is a multimodal model?
A multimodal model is an AI system that can work with more than one kind of data, such as text,
images, audio and video. It learns to connect these forms, so it can describe a photo, answer
questions about a chart or turn speech into text. Handling several modes in one model lets people
interact in more natural ways, for example by showing a picture instead of describing it. Like
other models, it can make mistakes, so important results still need checking.
Keywords: vision, image, audio, video, speech, text, model
Track: ai

## rlhf | What is reinforcement learning from human feedback?
Reinforcement learning from human feedback, or RLHF, is a way of teaching an AI model which
answers people prefer. People compare pairs of model responses and mark the better one. Those
choices are used to train a reward model that scores answers, and the language model is then
adjusted to earn higher scores. This step helps make chatbots more helpful and polite, although
it reflects the preferences of the people who gave the feedback.
Keywords: alignment, human feedback, reward model, preference, chatbot, training
Track: ai

## mixture-of-experts | What is a mixture-of-experts model?
A mixture-of-experts model is an AI model built from many smaller specialist parts called
experts. For each piece of input, a routing component chooses only a few experts to do the work,
and the rest stay idle. This means the model can hold a very large amount of knowledge while using
only a fraction of its parameters for any single step. The design can lower the cost of running a
big model, though it needs more memory to store all the experts.
Keywords: experts, routing, sparse, parameters, efficiency, architecture
Track: ai

## edge-ai | What is on-device or edge AI?
On-device AI, also called edge AI, means running an AI model directly on a phone, laptop, car or
sensor instead of in a remote data center. Because the data stays on the device, responses can
be faster and work without an internet connection, and private information does not have to be
sent away. The trade-off is that devices have limited power and memory, so the models are usually
smaller or compressed. Many products combine both, handling simple tasks locally and harder ones
in the cloud.
Keywords: on-device, edge, phone, npu, privacy, latency, compression
Track: ai
