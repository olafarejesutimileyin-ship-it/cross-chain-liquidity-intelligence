# Portfolio Project: Cross-Chain Liquidity Acquisition Intelligence
**Analyst:** Jesutimileyin Olafare (X: @the_Jtcrypt | Dune: @the_olafare1 | Email: olafarejesutimileyin@gmail.com)
**Role Targeted:** Junior On-Chain / Data Analyst
**Scope:** Ethereum, Arbitrum, Optimism, Base, Solana (30-Day Window, 2026)

## Core Metrics & Dataset
- **Transaction Filter:** DEX swaps ≥ $10,000 threshold (isolates high-value trading, filters retail & spam)
- **Total High-Value DEX Flow:** $156,924,657,999 ($156.9B)
- **Unique Wallets Observed:** 60,371 addresses
- **Average Ticket Execution Size:** $142,837 ($142.8K)
- **Recently Active Wallets (<48h):** 8,289 addresses

## Chain Concentration Breakdown
- **Base:** $91,243,627,503 ($91.24B) — Top concentration
- **Ethereum:** $11,439,023,209 ($11.44B)
- **Arbitrum:** $5,479,638,537 ($5.48B)
- **Solana:** $152,093,353 ($152.09M)
- **Optimism:** $1,000,223 ($1.00M)

## Venue Analysis
- Top venue volume exceeded $103B (Uniswap on Base: $103.23B).
- Aerodrome on Base: $3.59B.
- Curve: $506.0M.
- Finding: Liquidity is heavily clustered, not evenly distributed. Chain concentration shows where flow lives; venue concentration shows who captures it.

## Noise Reduction & Qualification
- **Core Principle:** High Volume ≠ High Acquisition Value ($156.9B observed flow ≠ $156.9B capturable liquidity).
- **Entity Screening:** Screened out exchanges, protocols, routers, treasuries, funds, and MEV bots.
  - Example: The #1 volume address generated ~$96.77B in volume, but was a DEX router (Uniswap, KyberSwap, 0x API).
- **Behavioral Automation Screening:** Screened out addresses with bot-like trade frequency.
  - Solana Wallet A: $983.35M volume, 53,068 trades in 30 days (Very High Risk -> Excluded).
  - Solana Wallet B: $720.15M volume, 37,468 trades in 30 days (Very High Risk -> Excluded).
- **Qualified Candidate Pool:** 221 candidate wallets survived entity & behavioral qualification.
- **Activity Segmentation:**
  - Hot (<48h): Recently active, highest priority for immediate research.
  - Warm (2-7 days): Relatively recent.
  - Lapsed (8-30 days): Historically relevant within window.

## Wallet Routing Behavior & Case Studies
- **Metric Insight:** Venue count ≠ routing flexibility.
- **High Concentration:** Wallet `3cmf...` routed $54.43M across 7 DEXs, but 95.61% was concentrated in Manifest. Wallet `2Sjf...` routed $51.70M 100% through PumpSwap.
- **Multi-Venue Footprint:** Wallet `Ai42...` routed $88.81M across 13 DEXs (Manifest $39.33M / 44.28%, BisonFi $27.46M, Tessera $14.55M, Aquifer $2.29M, Jupiter $1.68M).

## Prioritization Engine & BD Queue
- **Liquidity Impact Score:** Ranks wallets using 30d volume, average ticket size, and behavioral quality.
  - Wallet with $186.15M volume scored 75; top-ranked wallets scored 89.
- **Acquisition Potential Score:** Multi-signal engine evaluating:
  1. Liquidity Impact (economic scale)
  2. Human Likelihood (behavioral filters)
  3. Routing Flexibility (multi-venue activity)
  4. Venue Concentration (primary DEX lock-in)
  5. Automation Risk (commercial relevance)
- **Top 100 Priority Queue + 50-Wallet Reserve:**
  - Candidate #1 ($13.89M flow, 33.2% primary share) scored 95 (Tier A).
  - Candidate #3 ($54.43M flow, 95.6% primary share) scored 92 (Tier A) — larger volume, but high incumbent lock-in lowers switching probability.

## Protocol Opportunity Modeling
- Modeled from Raydium's perspective using conservative (5%) and higher (10%) capture scenarios.
- Example: Modeled wallet with $173.75M flow, $146.17M on JupiterZ -> 5% capture represents $8.69M in potential protocol flow.
- Core Insight: Observed flow is evidence; capture is a scenario.

## The Communication Gap & Infrastructure Testing
- Testing actual wallet-linked communication rails:
  - **Blockscan Chat:** Address accepted, conversation initiated, but sign-in and visibility unknown.
  - **DeBank Hi:** Target located, personalized message prepared, required $1.00 paid-send fee, delivery/response unproven.
  - **XMTP:** Queried target wallet, returned "Address not registered on XMTP", direct messaging blocked.
- **Key Finding:** Addressable ≠ Reachable ≠ Visible ≠ Attention ≠ Response ≠ Acquisition.

## The 8-Stage Protocol Growth Framework
1. Discover (Map high-value DEX flow)
2. Qualify (Remove bot/router/protocol noise)
3. Prioritize (Multi-signal wallet scoring)
4. Value (Model addressable flow & capture scenarios)
5. Incentivize (Design behavior-informed VIP & routing terms)
6. Reach (Test multi-rail web3 communication)
7. Activate (Cryptographic allowlists for conversion)
8. Measure (Attribution, retention, and ROI)
