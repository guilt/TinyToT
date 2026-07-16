# Software Engineering Knowledge

## Code Quality and Engineering

Big-O complexity: O(1) constant time, O(log n) for binary search, O(n) for linear scan, O(n log n) for efficient sorts, O(n²) for nested loops.

A memory leak occurs when a program allocates memory but never frees it. In Python, circular references can prevent garbage collection.

A race condition occurs when two threads access shared data concurrently and the result depends on execution order. Fix with locks, semaphores, or atomic operations.

Deadlock: two or more processes permanently blocked, each waiting for the other to release a resource. Prevent with lock ordering, timeouts, or deadlock detection.

SQL injection occurs when user input is included in a SQL query without sanitisation. Prevent with parameterised queries or prepared statements.

XSS (Cross-Site Scripting): malicious scripts injected into web pages viewed by other users. Prevent by escaping HTML output and using Content Security Policy.

SOLID principles: Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion.

DRY (Don't Repeat Yourself): every piece of knowledge should have a single, authoritative representation.

A RESTful API uses HTTP methods: GET (retrieve), POST (create), PUT (update/replace), PATCH (partial update), DELETE (remove).

HTTP status codes: 200 OK, 201 Created, 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 500 Internal Server Error.

## Version Control and CI/CD

Git workflow: git add → git commit → git push. Branching: git checkout -b feature-branch. Merging: git merge feature-branch.

A pull request (PR) is a proposal to merge changes from one branch into another. It enables code review before merging.

CI/CD (Continuous Integration/Continuous Deployment): automatically build, test, and deploy code on every commit.

A Docker container packages code and its dependencies into a portable unit. A Dockerfile defines how to build the image.

Kubernetes orchestrates containers: deployments manage replicas, services expose pods, ingress routes external traffic.

## Algorithms and Data Structures

QuickSort average O(n log n), worst O(n²). MergeSort always O(n log n) but needs O(n) extra space.

A graph is a set of nodes (vertices) connected by edges. BFS uses a queue, DFS uses a stack (or recursion).

Dynamic programming solves problems by breaking them into overlapping subproblems and caching results (memoization).

A trie (prefix tree) stores strings character by character, enabling O(k) search where k is string length.

Dijkstra's algorithm finds shortest paths in graphs with non-negative edge weights. Time O((V+E) log V).

A binary heap enables O(log n) insert and O(log n) extract-min/max. Used to implement priority queues.

## System Design

Horizontal scaling adds more machines; vertical scaling adds more power to existing machines.

A load balancer distributes traffic across multiple servers. Round-robin, least-connections, and IP-hash are common algorithms.

CAP theorem: a distributed system can guarantee at most two of: Consistency, Availability, Partition tolerance.

Database sharding splits data across multiple databases by a shard key. It improves write throughput but complicates queries.

A CDN (Content Delivery Network) serves static assets from servers geographically close to the user, reducing latency.

Caching layers: L1/L2 CPU cache → RAM → disk. In web apps: browser cache → CDN → application cache (Redis/Memcached) → database.
