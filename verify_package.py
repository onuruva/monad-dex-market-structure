#!/usr/bin/env python3
"""Check frozen-input hashes and event/origin integrity without credentials."""
import materialize_inputs,validate_inputs
if __name__=='__main__':
    m=materialize_inputs.ensure();print('SHA256 verified for',len(m['inputs']),'frozen inputs')
    validate_inputs.main()
