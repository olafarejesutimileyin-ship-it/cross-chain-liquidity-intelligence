-- ====================================================================
-- Cross-Chain Liquidity Acquisition Intelligence Queries
-- Author: Jesutimileyin Olafare (@the_olafare1)
-- ====================================================================

-- 1. 30-Day Multi-Chain DEX High-Value Flow (Threshold >= $10,000)
WITH high_value_dex AS (
    SELECT 
        blockchain,
        tx_hash,
        block_time,
        taker AS wallet_address,
        project AS dex_name,
        amount_usd
    FROM dex.trades
    WHERE block_time >= NOW() - INTERVAL '30' DAY
      AND amount_usd >= 10000
      AND blockchain IN ('ethereum', 'arbitrum', 'optimism', 'base', 'solana')
)
SELECT 
    blockchain,
    COUNT(DISTINCT wallet_address) AS unique_wallets,
    COUNT(tx_hash) AS trade_count,
    ROUND(SUM(amount_usd), 2) AS total_volume_usd,
    ROUND(AVG(amount_usd), 2) AS avg_trade_usd
FROM high_value_dex
GROUP BY blockchain
ORDER BY total_volume_usd DESC;

-- 2. Entity & Router Screening Filter
-- Excludes routers, MEV bots, exchanges, and protocols
WITH wallet_activity AS (
    SELECT 
        taker AS wallet_address,
        blockchain,
        project AS dex_name,
        amount_usd,
        block_time
    FROM dex.trades
    WHERE block_time >= NOW() - INTERVAL '30' DAY
      AND amount_usd >= 10000
),
known_entities AS (
    SELECT address 
    FROM labels.all 
    WHERE category IN ('dex', 'cex', 'mev', 'router', 'treasury', 'infrastructure')
)
SELECT 
    w.wallet_address,
    w.blockchain,
    COUNT(*) AS total_trades,
    SUM(w.amount_usd) AS total_volume_usd,
    AVG(w.amount_usd) AS avg_ticket_size
FROM wallet_activity w
LEFT JOIN known_entities k ON w.wallet_address = k.address
WHERE k.address IS NULL
GROUP BY w.wallet_address, w.blockchain
HAVING COUNT(*) < 2000 -- Excludes extreme high-frequency automation
ORDER BY total_volume_usd DESC;

-- 3. Solana Venue Flow Intelligence & Routing Concentration
WITH solana_qualified AS (
    SELECT 
        taker AS wallet_address,
        project AS dex_name,
        amount_usd,
        block_time
    FROM dex.trades
    WHERE block_time >= NOW() - INTERVAL '30' DAY
      AND blockchain = 'solana'
      AND amount_usd >= 10000
)
SELECT 
    dex_name,
    COUNT(DISTINCT wallet_address) AS active_qualified_wallets,
    COUNT(*) AS trade_count,
    ROUND(SUM(amount_usd), 2) AS primary_dex_volume
FROM solana_qualified
GROUP BY dex_name
ORDER BY primary_dex_volume DESC;
