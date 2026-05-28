---
name: forward-hotspot-prediction
description: Use for forward-looking market, sector, commodity, or thematic hotspot prediction when the user asks what may become popular next, which sectors may heat up, or where expectation gaps exist. Trigger on queries such as “预测接下来什么热点”, “未来什么板块会热”, “不是复盘，是前瞻”, “用前导指标判断市场”, or “based on capex/orders/pricing/policy, what’s next”. Focus on leading indicators such as budgets, capex, orders, backlog, pricing, supply-demand bottlenecks, policy transmission, and consensus expectation gaps. Do not use recent price gains, leaderboards, 涨停数量, or media hype as primary evidence.
---

# Forward Hotspot Prediction

Use this skill to produce forward-looking market or sector hotspot analysis based on leading indicators, not price recaps.

Core doctrine:

**Predict from budgets, orders, prices, bottlenecks, policy transmission, and expectation gaps — not from whatever already went up.**

## Core principles

- Do not use recent涨幅, sector leaderboards,涨停数量, or media hype as primary evidence.
- Use price action and fund flows only as secondary context.
- Prefer causal transmission chains over theme labels.
- Separate **industry trend** from **tradable hotspot**.
- Treat every conclusion as probabilistic, not guaranteed investment advice.
- Always include invalidation risks.

## Default assumptions

When the user is vague, use these defaults and state them briefly:

- Time horizon: 1–3 months
- Market scope:
  - Chinese market language defaults to A-shares / HK
  - US tickers or English sector framing defaults to US / global
  - Commodity-specific questions default to the relevant global supply chain
- Output level: rank sectors/themes first; mention representative company types only when evidence supports them
- Style: analytical, cautious, evidence-based

## Freshness and sourcing rule

For market prediction tasks, use up-to-date sources whenever tools are available. Prefer sources published or updated within the relevant prediction horizon.

Prioritize sources in this order:

1. Company earnings, guidance, investor presentations, IR materials
2. Official government, regulator, budget, procurement, or policy documents
3. Industry research institutions and exchange/association data
4. Vertical trade publications
5. Major financial media
6. Market commentary only as background, not primary evidence

Always include source dates for:

- earnings / guidance
- policy announcements
- capex or budget data
- order / backlog data
- pricing, inventory, or supply-demand claims

If fresh evidence is unavailable, explicitly label the thesis as weak, stale, or speculative.

## What counts as forward-looking evidence

Prioritize:

### 1. Capex / budget / planned spending

Look for:
- hyperscaler capex
- government budget or procurement plans
- utility / grid investment plans
- factory expansion
- equipment purchasing cycles
- defense, energy, infrastructure, or industrial policy budgets

### 2. Orders / backlog / delivery visibility

Look for:
- long-term agreements
- order backlog growth
- customer commitments
- capacity reservation
- delivery lead-time extension
- framework contracts
- tender awards

### 3. Pricing / supply-demand / bottlenecks

Look for:
- contract price changes
- spot price changes
- inventory drawdown or restocking
- component shortages
- capacity constraints
- power, packaging, logistics, labor, or permitting bottlenecks

### 4. Policy / institutional transmission

Look for:
- formal regulations
- subsidy rules
- tariffs or export controls
- procurement mandates
- defense or infrastructure budgets
- power market rules
- grid connection rules
- environmental or safety compliance changes

### 5. Expectation gaps

Look for:
- consensus sees demand but underestimates the bottleneck
- first-order beneficiary is crowded, second-order beneficiary is ignored
- revenue growth is noticed but margin leverage is missed
- policy headline is priced, implementation chain is not
- lower cost is misread as lower total demand instead of adoption expansion

## Required workflow

### Step 1: define the prediction question precisely

Reframe the user’s request into:

- time horizon
- market scope
- asset type
- sector/theme boundary
- whether the user wants sectors, stocks, commodities, or a full chain analysis

If the user is vague, apply the default assumptions and state them.

### Step 2: gather leading indicators first

Search for forward-looking evidence before forming the conclusion.

Extract whenever possible:

- numeric indicators
- dates
- guidance language
- order/backlog direction
- capacity constraints
- pricing direction
- policy implementation schedule
- next catalyst or data release

Do not start from recent winners.

### Step 3: build the transmission chain

For each candidate hotspot, explain:

**Driver → Transmission → Bottleneck → Likely beneficiary → Risk**

Include:

- what changed
- who is spending, ordering, or being forced to comply
- where the bottleneck appears
- which part of the chain monetizes first
- why this is forward-looking rather than backward-looking
- what the market may not fully price yet

### Step 4: test tradability

A theme is a tradable hotspot only if at least two of the following are present:

- new forward evidence within the chosen horizon
- identifiable listed beneficiaries or commodity exposure
- near-term catalyst or data release
- bottleneck or pricing power
- consensus expectation gap
- policy/order/capex transmission likely to affect financial results
- plausible narrative recognition by the market

If a theme is structurally important but lacks near-term tradability, label it as a long-term industry trend rather than a near-term hotspot.

### Step 5: score and rank

Score each hotspot from 1–5 on:

- Forward evidence strength
- Cash-flow proximity
- Bottleneck scarcity
- Expectation gap
- Durability
- Tradability / recognition potential

Do not rank a theme #1 if its forward evidence strength is below 3 unless clearly labeled speculative.

### Step 6: run a counter-thesis check

For each ranked hotspot, check:

- Is the demand already fully priced?
- Is the bottleneck temporary or structural?
- Are orders double-counted or pulled forward?
- Is policy funding announced but not executable?
- Are margins likely to be competed away?
- Is the market confusing revenue growth with profit capture?
- Is the theme too crowded because price action already led fundamentals?

### Step 7: separate evidence quality levels

Label claims as:

- **High confidence**: directly supported by primary sources or strong industry data
- **Medium confidence**: supported by multiple secondary sources and a plausible causal chain
- **Low confidence**: thematic inference or speculative extension

Do not present low-confidence claims as conclusions.

## Special framework: substitution vs expansion vs value redistribution

Use this framework mainly for AI, software, automation, cybersecurity, data platforms, digitalization, or technology-cost-collapse themes.

When a technical improvement causes enthusiasm or a selloff, test whether the change is better understood as:

1. **Substitution**  
   An old layer is directly compressed, bypassed, or eliminated.

2. **Expansion**  
   Lower cost or better usability increases adoption and expands total demand.

3. **Value redistribution**  
   The total market grows, but value shifts toward control points, infrastructure, bottlenecks, governance, or workflow ownership.

Core rule:

Do not stop at “this got cheaper, therefore demand falls.”

Use this chain when relevant:

**Capability improvement → adoption friction falls → usage expands → system complexity rises → value shifts to bottlenecks / control points / governance layers**

Look for beneficiaries that:

- own critical data entry or output points
- sit inside core workflows
- control permissions, identity, audit, compliance, or policy
- benefit from higher integration density
- monetize activity volume rather than scarce capability pricing alone

Be cautious with companies that:

- provide shallow wrappers
- lack proprietary data or distribution
- rely on capabilities becoming native to base models
- can be bypassed as adoption broadens

## Output format

Use this structure unless the user asks otherwise.

### 1. Assumptions

- Horizon:
- Market scope:
- Asset/theme scope:
- Evidence freshness:

### 2. Ranked predicted hotspots

| Rank | Hotspot | Core driver | Leading evidence | Transmission chain | Confidence | Horizon | Main invalidation |
|---|---|---|---|---|---|---|---|

### 3. Detailed thesis

For each hotspot:

- **Why now**
- **Leading indicators**
- **Transmission chain**: Driver → Transmission → Bottleneck → Likely beneficiary → Risk
- **Why this is forward-looking**
- **What the market may be missing**
- **Score**: evidence / cash-flow proximity / bottleneck / expectation gap / durability / tradability
- **Invalidation risk**

### 4. Best indicators to track next

List the few data points that would confirm or break the thesis, such as:

- capex revisions
- order intake
- backlog
- contract prices
- inventory levels
- tender announcements
- policy implementation dates
- capacity utilization
- margin guidance

### 5. What not to chase

Mention themes that look hot but are mostly:

- backward-looking
- already priced
- driven mainly by media hype
- lacking near-term cash-flow transmission
- structurally interesting but not yet tradable

## Style rules

- Be analytical, not breathless.
- Prefer “this may be underpriced because...” over “this will surge”.
- Make the causal chain explicit.
- If evidence is weak, say it is weak.
- Distinguish industry trend from tradable hotspot.
- Avoid deterministic investment language such as “must buy”, “guaranteed”, or “一定会涨”.
- Do not recommend individual securities unless the user specifically asks and evidence supports the link.
