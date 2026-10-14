"""Inbound ports — stable contracts that inbound adapters depend on.

Each protocol defines the signature of a single use case.  Inbound adapters
(CLI, HTTP, gRPC, …) depend only on these protocols, never on the concrete
use case classes.  The use cases implement these protocols.
"""
