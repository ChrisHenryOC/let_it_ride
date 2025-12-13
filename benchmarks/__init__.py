"""Performance benchmarking suite for Let It Ride simulator.

This package provides tools for measuring and profiling simulation performance,
including throughput benchmarks, memory profiling, and hotspot analysis.

Performance Targets:
- Hand evaluation (5-card): ~330,000 hands/second (aspirational: 500k/s)
- Hand evaluation (3-card): >1,000,000 hands/second
- Full simulation: >100,000 hands/second
- Memory: <4GB for 10M hand simulation
"""
