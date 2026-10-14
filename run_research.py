#!/usr/bin/env python3
"""Reproduce the complete seven-day study from the included frozen inputs."""
import gc
import materialize_inputs,validate_inputs,analyze,enrich_metrics,final_metrics

if __name__=='__main__':
    materialize_inputs.ensure()
    validate_inputs.main()
    analyze.main();gc.collect()
    enrich_metrics.value_trades();enrich_metrics.liquidity_events();enrich_metrics.venue_families();gc.collect()
    final_metrics.main()
