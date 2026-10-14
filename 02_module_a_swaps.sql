CREATE VIEW monad_module_a_swaps AS
SELECT n.*,r.transaction_hash,r.transaction_index,r.log_index,
'0x'||right(lower(split_part(r.topics,',',3)),40) AS swap_caller,
to_timestamp(n.block_timestamp) AS block_time,
monad_v4_uint160(substr(r.data,195,64)) AS active_liquidity,
(('x'||right(substr(r.data,259,64),6))::bit(24)::bigint -
CASE WHEN substr(right(substr(r.data,259,64),6),1,1) ~* '[89a-f]' THEN 16777216 ELSE 0 END) AS tick,
('x'||right(substr(r.data,323,64),6))::bit(24)::bigint AS swap_fee_pips,
(n.amount0_raw*n.amount1_raw<0) AS opposite_signs,
(n.hooks<>'0x0000000000000000000000000000000000000000') AS has_hook
FROM monad_v4_swaps_normalized n JOIN uniswap_v4_raw_logs_7d r USING(id);
