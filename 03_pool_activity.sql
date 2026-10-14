CREATE VIEW monad_module_a_pool_activity AS
SELECT pool_id,min(symbol0) AS symbol0,min(symbol1) AS symbol1,
count(*) AS swap_events,count(DISTINCT transaction_hash) AS transactions,
count(DISTINCT swap_caller) AS swap_callers,
count(*) FILTER(WHERE NOT opposite_signs) AS nonstandard_sign_events,
min(has_hook::int)::boolean AS has_hook
FROM monad_module_a_swaps GROUP BY pool_id;
