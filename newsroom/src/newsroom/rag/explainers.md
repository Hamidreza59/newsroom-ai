# Explainer knowledge base

Curated, plain-language explanations used by the "AI in 30 seconds" segment. Each section is the
only source of facts the Explainer agent may use. Keep entries short, accurate and evergreen.

## gpu | What is a GPU?
A GPU, or graphics processing unit, is a chip built to do thousands of small calculations at the
same time. It was designed for drawing video-game graphics, but the same parallel math is what
training and running AI models needs. That is why AI companies buy huge numbers of GPUs and why
chipmakers that design them have become some of the most valuable companies in the world.
Keywords: chip, nvidia, amd, semiconductor, data center, compute

## llm | What is a large language model?
A large language model is an AI system trained on enormous amounts of text to predict the next
word in a sentence. By learning those patterns at scale, it can answer questions, summarise
documents, write and translate. It does not look facts up by default, so it can sound confident
while being wrong, which is why good AI products check its answers against trusted sources.
Keywords: chatgpt, claude, gemini, llama, model, chatbot, openai, anthropic

## agent | What is an AI agent?
An AI agent is a language model that can take actions, not just write text. It is given tools,
such as search, a code editor or a calendar, and decides which tool to use step by step to finish
a task. Agents are powerful but need guardrails, like limits on which tools they can use and human
approval for important actions.
Keywords: agentic, autonomous, tools, automation, assistant, workflow

## inference | Training versus inference
Training is when an AI model learns: it processes huge datasets over weeks on thousands of chips,
which is very expensive. Inference is when the finished model is used to answer a request. Each
answer is cheap, but billions of requests add up, so companies now compete to make inference
faster and cheaper with specialised chips and smaller models.
Keywords: accelerator, serving, cost, tokens, chips, data center

## token | What is a token?
AI language models read and write text in small pieces called tokens. A token is often part of a
word: roughly three quarters of an English word on average. AI services usually charge by the
number of tokens processed, and a model's context window, how much it can read at once, is also
measured in tokens.
Keywords: pricing, context window, api, cost

## open-weights | What are open-weight models?
An open-weight model is an AI model whose trained parameters, its weights, are published so anyone
can download and run it on their own hardware. That lowers costs and lets companies keep data
private, but it also means the original developer cannot control how the model is used. Closed
models are only available through the company's own apps or services.
Keywords: open source, llama, mistral, qwen, download, local, benchmark

## benchmark | What is an AI benchmark?
A benchmark is a standard test used to compare AI models, such as a set of coding problems or exam
questions. Higher scores suggest a more capable model, but benchmarks only measure what they test,
and models can be tuned to score well on them, so real-world testing still matters.
Keywords: score, leaderboard, test, coding, evaluation

## data-center | Why AI needs data centers
AI models run in data centers: warehouse-sized buildings full of servers, chips, cooling and
network equipment. Training and serving modern AI takes so much computing that tech companies are
spending tens of billions of dollars building new ones, and their electricity use has become a
major issue for power grids and climate goals.
Keywords: power, electricity, energy, cloud, climate, infrastructure

## semiconductor | What is a semiconductor?
A semiconductor is a material, usually silicon, that can be switched between conducting and
blocking electricity. Billions of tiny switches etched onto a silicon chip form processors and
memory. Making advanced chips needs extremely precise factories, called fabs, and only a few
companies in the world can build the most advanced ones.
Keywords: chip, tsmc, fab, foundry, silicon, manufacturing

## market-cap | What is market capitalization?
Market capitalization is the total value of a company's shares: the share price multiplied by the
number of shares. It is how the market values the whole company. A company's market cap changes
every second the market is open, as its share price moves.
Keywords: valuation, trillion, shares, stock, company value

## index | What is a stock index?
A stock index tracks a group of stocks to show how part of the market is doing. The S&P 500 follows
500 large U.S. companies, the Nasdaq Composite is weighted towards technology companies, and the
Dow Jones Industrial Average follows 30 large, well-known companies. When people say the market
went up, they usually mean one of these indices rose.
Keywords: s&p 500, nasdaq, dow, market, stocks, wall street

## earnings | What are earnings reports?
Public companies report their results every quarter: revenue, profit and often a forecast for the
months ahead. Stock prices can move sharply on these earnings reports, because investors compare
the results with what analysts expected, not just with the previous quarter.
Keywords: quarter, revenue, profit, forecast, guidance, results

## zero-day | What is a zero-day vulnerability?
A zero-day is a security flaw that the software maker does not know about yet, so there are zero
days of warning and no fix available. Attackers who find one can break in before a patch exists.
Security teams now use AI to find these flaws faster, and so can attackers.
Keywords: security, hack, exploit, vulnerability, cyberattack, patch

## robotaxi | How do robotaxis work?
A robotaxi is a self-driving car offered as a ride service. It combines cameras, radar and often
lidar sensors with AI software that recognises the road, predicts what others will do and plans a
safe path. Most services start in a few cities with careful testing and remote human support.
Keywords: self-driving, autonomous vehicle, waymo, driverless, uber, lidar

## mcp | What is the Model Context Protocol?
The Model Context Protocol, or MCP, is an open standard for connecting AI assistants to tools and
data. Instead of building a custom integration for every app, a company exposes its tools through
an MCP server once, and any compatible AI assistant can use them, with the user's permission.
Keywords: tools, integration, standard, protocol, connectors, agents
