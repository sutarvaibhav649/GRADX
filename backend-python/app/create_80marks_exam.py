"""
GRADX — 80 Marks Exam PDF Generator
=====================================
Creates:
  - model_80marks.pdf        : 10 questions × 8 marks = 80 marks  (typed, 10+ pages)
  - student_80_excellent.pdf : ~88% quality  (Aryan Mehta)
  - student_80_good.pdf      : ~70% quality  (Priya Sharma)
  - student_80_average.pdf   : ~52% quality  (Rohit Das)
  - student_80_below.pdf     : ~35% quality  (Neha Verma)
  - student_80_weak.pdf      : ~18% quality  (Sanjay Gupta)

Sections per question: Introduction(2) + Core_Concepts(3) + Examples(2) + Conclusion(1) = 8 marks
Run: python -m app.create_80marks_exam
"""

import fitz
import os

OUT_DIR = os.path.dirname(__file__)

# ─────────────────────────────────────────────────────────────────────────────
# MODEL ANSWER  (comprehensive, full-detail for all 10 questions)
# ─────────────────────────────────────────────────────────────────────────────

MODEL = [

  # ── Q1 ───────────────────────────────────────────────────────────────────
  { "q": "Question 1:  Object-Oriented Programming (OOP)", "marks": "[8 marks]",
    "Introduction":
      "Object-Oriented Programming (OOP) is a programming paradigm that structures software "
      "design around objects rather than functions and logic. An object is a self-contained entity "
      "that encapsulates both state (data/attributes) and behaviour (methods/operations). OOP was "
      "developed to address the limitations of procedural programming in managing large, complex "
      "software systems. Languages like Java, C++, Python, C#, and Kotlin are built primarily on "
      "OOP principles, enabling modular, reusable, and maintainable code design.",

    "Core_Concepts":
      "OOP is founded on four core pillars. Encapsulation bundles data and methods within a class "
      "and restricts direct external access to internal state using access modifiers (private, "
      "protected, public), exposing only a controlled interface through getter/setter methods — "
      "this prevents unintended data corruption. Abstraction hides complex implementation details "
      "and exposes only the essential interface through abstract classes and interfaces, reducing "
      "cognitive load for developers. Inheritance allows a child class to acquire attributes and "
      "methods from a parent class, enabling code reuse and establishing IS-A hierarchical "
      "relationships — for example, Car IS-A Vehicle. Multiple inheritance (supported in C++ but "
      "not Java) allows a class to inherit from multiple parents. Polymorphism allows the same "
      "operation to behave differently depending on context: compile-time (method overloading — "
      "same name, different parameters) and runtime (method overriding — subclass redefines parent "
      "method, resolved via dynamic dispatch through virtual method tables). Additional concepts "
      "include Association (HAS-A relationship), Aggregation (whole-part, parts exist "
      "independently), and Composition (whole-part, parts cannot exist independently).",

    "Examples":
      "A BankAccount class encapsulates balance (private) and exposes deposit(amount) and "
      "withdraw(amount) methods — Encapsulation. SavingsAccount extends BankAccount and overrides "
      "calculateInterest() to add 4% per annum — Inheritance and Polymorphism. An abstract class "
      "Shape declares abstract method area(); Circle and Rectangle override it with specific "
      "formulas — Abstraction. In a Vehicle hierarchy: move() is called on a Vehicle reference "
      "pointing to a Car or Truck object; at runtime, the correct subclass method executes — "
      "Runtime Polymorphism. A University HAS-A collection of Department objects (Aggregation); "
      "a Human HAS-A Heart which cannot exist without the Human (Composition).",

    "Conclusion":
      "OOP provides a robust, scalable approach to software development by modelling real-world "
      "entities as objects. Its four pillars collectively reduce code duplication, increase "
      "maintainability, and support team collaboration through clear module boundaries, making "
      "OOP the dominant paradigm in enterprise, mobile, and systems software development."
  },

  # ── Q2 ───────────────────────────────────────────────────────────────────
  { "q": "Question 2:  Database Normalization", "marks": "[8 marks]",
    "Introduction":
      "Database normalization is a systematic process of organizing a relational database schema "
      "to minimize data redundancy and eliminate update, insert, and delete anomalies. It involves "
      "decomposing larger tables into smaller, well-structured tables and defining relationships "
      "between them using foreign keys. Normalization was formalized by Edgar F. Codd (inventor "
      "of the relational model) and follows a series of progressive rules called Normal Forms (NF). "
      "The ultimate goal is a clean, consistent schema where each fact is stored exactly once.",

    "Core_Concepts":
      "First Normal Form (1NF): each column must contain atomic (indivisible) values, every row "
      "must be unique (primary key exists), and there must be no repeating groups or arrays within "
      "a column. Second Normal Form (2NF): the table must be in 1NF and every non-prime attribute "
      "must be fully functionally dependent on the entire primary key — eliminates partial "
      "dependencies (applicable when the key is composite). Third Normal Form (3NF): the table "
      "must be in 2NF and no non-prime attribute may be transitively dependent on the primary key "
      "via another non-prime attribute. Boyce-Codd Normal Form (BCNF): a stricter version of 3NF "
      "where every determinant must be a candidate key — handles anomalies 3NF does not. Fourth "
      "Normal Form (4NF): eliminates multi-valued dependencies. Fifth Normal Form (5NF): "
      "eliminates join dependencies. Denormalization is the intentional reversal of normalization "
      "for performance optimization in read-heavy analytical systems (data warehouses), accepting "
      "some redundancy in exchange for fewer joins.",

    "Examples":
      "Consider Student_Course(StudentID, StudentName, CourseID, CourseName, InstructorName, Grade). "
      "Partial dependency: StudentName depends only on StudentID (violates 2NF). Transitive "
      "dependency: InstructorName depends on CourseID, not directly on the composite key. "
      "Decompose to: Student(StudentID PK, StudentName), Course(CourseID PK, CourseName, "
      "InstructorID FK), Instructor(InstructorID PK, InstructorName), "
      "Enrollment(StudentID FK, CourseID FK, Grade). This eliminates: Update anomaly (changing "
      "a course name requires one update), Insert anomaly (can register a course without "
      "students), Delete anomaly (deleting last enrollment does not lose course data).",

    "Conclusion":
      "Normalization produces clean, anomaly-free database schemas by systematically removing "
      "redundancy. While 3NF or BCNF is sufficient for most OLTP systems, data warehouses may "
      "intentionally denormalize for query performance. Understanding normalization is fundamental "
      "to designing robust, maintainable relational databases."
  },

  # ── Q3 ───────────────────────────────────────────────────────────────────
  { "q": "Question 3:  Operating System Process Management", "marks": "[8 marks]",
    "Introduction":
      "Process management is a core responsibility of the operating system (OS), which must "
      "create, schedule, synchronize, and terminate processes while ensuring CPU utilization, "
      "fairness, and system stability. A process is an instance of a program in execution, "
      "distinct from the program itself (a passive entity stored on disk). Each process has its "
      "own address space (code, data, heap, stack segments), program counter, CPU registers, "
      "and Process Control Block (PCB). The OS kernel maintains a process table and orchestrates "
      "multiprogramming — interleaving multiple processes on a single CPU to maximize throughput.",

    "Core_Concepts":
      "Process States: New → Ready → Running → Waiting/Blocked → Terminated. A process moves "
      "between states based on scheduling decisions and I/O events. PCB stores: PID, state, "
      "program counter, CPU registers, memory limits, open files list, accounting info, I/O "
      "status, and scheduling priority. Context switching saves the current PCB and loads the "
      "next process's PCB — incurs overhead (~1-2 µs on modern hardware). CPU Scheduling "
      "Algorithms — FCFS (First-Come First-Served): non-preemptive, simple, convoy effect. "
      "SJF (Shortest Job First): optimal average waiting time, requires future knowledge; "
      "SRTF is its preemptive variant. Round Robin (RR): preemptive, fixed time quantum "
      "(typically 10-100ms), fair for interactive systems. Priority Scheduling: higher priority "
      "runs first, risk of starvation solved by aging. Multilevel Feedback Queue (MLFQ): "
      "dynamically adjusts priorities based on CPU burst behaviour. Inter-Process Communication "
      "(IPC): Shared Memory, Message Passing, Pipes, Sockets. Synchronization: Mutex locks, "
      "Semaphores, Monitors. Deadlock: four necessary conditions (Mutual Exclusion, Hold & Wait, "
      "No Preemption, Circular Wait); prevented by Banker's Algorithm.",

    "Examples":
      "Round Robin with quantum=4ms on P1(24ms), P2(3ms), P3(3ms): execution order P1(4), "
      "P2(3), P3(3), P1(4)×5. Average waiting time = (6+4+7)/3 = 5.67ms. Context switch "
      "example: P1 at quantum expiry → save P1's PCB, load P2's PCB, resume P2 at saved PC. "
      "Deadlock example: P1 holds Resource A, waits for B; P2 holds B, waits for A — circular "
      "wait. Banker's Algorithm: system grants resources only if allocation keeps it in a safe "
      "state. Fork-exec model in Unix: fork() creates child clone; exec() replaces child image "
      "with new program.",

    "Conclusion":
      "Effective process management is the cornerstone of OS performance. The scheduler must "
      "balance CPU utilization, throughput, turnaround time, waiting time, and response time. "
      "Modern OSes use MLFQ schedulers with multicore-aware load balancing and NUMA-aware "
      "memory allocation to maximize performance on contemporary hardware."
  },

  # ── Q4 ───────────────────────────────────────────────────────────────────
  { "q": "Question 4:  Computer Networks and the OSI Model", "marks": "[8 marks]",
    "Introduction":
      "A computer network is a collection of interconnected devices (hosts, routers, switches) "
      "that communicate by exchanging data packets according to agreed-upon protocols. Networks "
      "range from LANs (room or building), WANs (city or global), MANs (metropolitan), and the "
      "Internet (global WAN). The OSI (Open Systems Interconnection) model, standardized by ISO "
      "in 1984 (ISO/IEC 7498-1), provides a seven-layer reference framework that decomposes "
      "network communication into independent, interoperable layers — enabling products from "
      "different vendors to communicate seamlessly.",

    "Core_Concepts":
      "Layer 7 — Application: provides network services directly to end-user applications. "
      "Protocols: HTTP/HTTPS (web), SMTP/IMAP/POP3 (email), FTP/SFTP (file transfer), "
      "DNS (name resolution), DHCP (address allocation), SNMP (network management). "
      "Layer 6 — Presentation: data translation (encoding/decoding), encryption/decryption "
      "(SSL/TLS), compression. Formats: JPEG, MP3, ASCII, EBCDIC. "
      "Layer 5 — Session: establishes, manages, and terminates sessions. Handles checkpointing "
      "and dialog control (half/full duplex). "
      "Layer 4 — Transport: end-to-end communication, segmentation, flow control, error "
      "recovery, multiplexing. TCP (reliable, connection-oriented, 3-way handshake, "
      "SYN-SYN/ACK-ACK, sliding window flow control, congestion control). "
      "UDP (unreliable, connectionless, low overhead — DNS, VoIP, streaming). "
      "Layer 3 — Network: logical addressing (IPv4/IPv6), routing (OSPF, BGP, RIP), "
      "fragmentation. Devices: Router. "
      "Layer 2 — Data Link: framing, MAC addressing, error detection (CRC), flow control. "
      "Protocols: Ethernet (802.3), Wi-Fi (802.11), PPP. Devices: Switch, Bridge. "
      "Layer 1 — Physical: bit transmission over medium (copper, fibre, radio). Encoding: "
      "NRZ, Manchester. Devices: Hub, Repeater, NIC.",

    "Examples":
      "HTTPS request to www.example.com: DNS resolves domain → IP (Application). TLS encrypts "
      "data (Presentation). TCP session via 3-way handshake (Session + Transport). IP packet "
      "routed across internet (Network). Ethernet frame with MAC addresses traverses LAN (Data "
      "Link). Electrical/optical/radio signals transmitted (Physical). Each layer adds a header "
      "(encapsulation) on send; strips it (decapsulation) on receive. TCP sliding window: sender "
      "transmits up to window-size bytes without waiting for ACK, doubling window each RTT "
      "(slow start) until threshold, then linear increase (congestion avoidance).",

    "Conclusion":
      "The OSI model is the definitive reference for understanding, designing, and troubleshooting "
      "network systems. The practical Internet uses the TCP/IP model (4 layers: Application, "
      "Transport, Internet, Network Access), but OSI remains essential for protocol analysis, "
      "certification curricula, and vendor-neutral communication standards."
  },

  # ── Q5 ───────────────────────────────────────────────────────────────────
  { "q": "Question 5:  Data Structures — Binary Trees and BST", "marks": "[8 marks]",
    "Introduction":
      "A tree is a non-linear hierarchical data structure composed of nodes connected by edges, "
      "with a designated root node and no cycles. A binary tree is a tree where each node has "
      "at most two children: left child and right child. Trees are fundamental in computer "
      "science, used for representing hierarchical data (file systems, XML/DOM), enabling "
      "efficient searching and sorting, and as the foundation for more complex structures like "
      "heaps, tries, and B-trees. The height of a tree determines the time complexity of "
      "most operations.",

    "Core_Concepts":
      "Binary Tree types: Full (every node has 0 or 2 children), Complete (all levels fully "
      "filled except possibly the last, which is filled left-to-right), Perfect (all internal "
      "nodes have 2 children, all leaves at same level), Degenerate/Skewed (each node has only "
      "one child — degenerates to a linked list). "
      "Binary Search Tree (BST): a binary tree with the BST property — for every node N, "
      "all keys in the left subtree are less than N.key, and all keys in the right subtree are "
      "greater. Operations — Search: O(h); Insert: O(h); Delete: O(h); h = height. "
      "In-order traversal of BST gives sorted output in O(n). Worst-case (sorted insertion): "
      "h = n, O(n). Average case (random): h = O(log n). "
      "Self-balancing BSTs: AVL Tree (maintains |balance factor| ≤ 1 using rotations — LL, RR, "
      "LR, RL), Red-Black Tree (used in Java TreeMap, C++ std::map — O(log n) guaranteed). "
      "Tree Traversals: In-order (Left-Root-Right), Pre-order (Root-Left-Right), "
      "Post-order (Left-Right-Root), Level-order (BFS using queue). "
      "Heap: Complete binary tree with heap property; max-heap: parent ≥ children; "
      "used in priority queues and HeapSort.",

    "Examples":
      "BST insertion of [50, 30, 70, 20, 40, 60, 80]: root=50, left=30, right=70, "
      "30's left=20, 30's right=40, 70's left=60, 70's right=80 — perfectly balanced, h=2. "
      "In-order traversal: 20, 30, 40, 50, 60, 70, 80 (sorted). BST search for 40: "
      "50→30→40 (2 comparisons). Delete node 30 (two children): replace with in-order "
      "successor (40), then delete 40 from right subtree. AVL rotation: inserting 10, 20, 30 "
      "into AVL tree causes LL imbalance at root 10; left rotation produces balanced tree "
      "with root 20, left=10, right=30.",

    "Conclusion":
      "Binary trees and BSTs provide efficient O(log n) search, insert, and delete operations "
      "for ordered data when balanced. Self-balancing variants (AVL, Red-Black) guarantee "
      "logarithmic performance regardless of insertion order and are foundational to database "
      "indexing (B-trees) and language runtime libraries."
  },

  # ── Q6 ───────────────────────────────────────────────────────────────────
  { "q": "Question 6:  Sorting Algorithms and Algorithm Analysis", "marks": "[8 marks]",
    "Introduction":
      "Sorting is the process of arranging elements in a defined order (ascending or descending). "
      "It is one of the most fundamental operations in computer science, underpinning database "
      "query optimization, binary search, data compression, and computational geometry. Algorithm "
      "analysis quantifies efficiency using Big-O notation: O(f(n)) describes the upper bound on "
      "time or space as input size n grows. Common classes: O(1) constant, O(log n) logarithmic, "
      "O(n) linear, O(n log n) linearithmic, O(n²) quadratic, O(2ⁿ) exponential.",

    "Core_Concepts":
      "Bubble Sort: repeatedly swaps adjacent out-of-order elements. Best O(n) (already sorted, "
      "with flag), Worst/Average O(n²). Stable, in-place. "
      "Selection Sort: finds minimum element and places at front each pass. Always O(n²). "
      "Unstable, in-place. "
      "Insertion Sort: builds sorted array left-to-right by inserting each element at correct "
      "position. Best O(n), Worst O(n²). Stable, in-place. Preferred for small or nearly-sorted "
      "arrays. Used in TimSort for small sub-arrays. "
      "Merge Sort: divide-and-conquer — split into halves, sort recursively, merge. "
      "Always O(n log n). Stable. O(n) space (not in-place). Preferred for linked lists and "
      "external sorting. "
      "Quick Sort: choose pivot, partition array (elements < pivot left, > pivot right), recurse. "
      "Average O(n log n), Worst O(n²) (sorted array with bad pivot choice). In-place, unstable. "
      "Optimized with random pivot or median-of-three. "
      "Heap Sort: build max-heap, repeatedly extract maximum. Always O(n log n). In-place, "
      "unstable. "
      "Counting Sort / Radix Sort: non-comparison sorts. Counting Sort: O(n+k) where k=range. "
      "Radix Sort: O(d(n+k)) where d=digits. Fastest for integers within known range. "
      "TimSort (Python/Java default): hybrid Merge+Insertion sort. O(n log n) worst case.",

    "Examples":
      "Quick Sort on [3,6,8,10,1,2,1] with pivot=1: partition gives [1,1,3,6,8,10,2] — "
      "recurse on left/right halves. Merge Sort: [38,27,43,3] → split [38,27] [43,3] → "
      "sort [27,38] [3,43] → merge [3,27,38,43]. Counting Sort on [4,2,2,8,3,3,1]: count "
      "array indexed 1-8: [1,2,2,0,0,0,0,1] → output [1,2,2,3,3,4,8]. Binary Search "
      "O(log n): search 7 in [1,3,5,7,9,11] — mid=5<7→right half, mid=9>7→left, mid=7 found.",

    "Conclusion":
      "Choosing the right sorting algorithm depends on input size, data characteristics (nearly "
      "sorted, duplicates, key range), stability requirements, and memory constraints. In "
      "practice, library sorts (TimSort, introsort) use hybrids for O(n log n) guaranteed "
      "performance with excellent cache behaviour."
  },

  # ── Q7 ───────────────────────────────────────────────────────────────────
  { "q": "Question 7:  Software Engineering — SDLC and Agile", "marks": "[8 marks]",
    "Introduction":
      "Software Engineering applies systematic, disciplined, quantifiable approaches to the "
      "development, operation, and maintenance of software — adapting engineering principles "
      "to software systems. The Software Development Life Cycle (SDLC) is a framework that "
      "defines the phases, activities, and deliverables for producing high-quality software "
      "within time and budget constraints. Selecting the right SDLC model is critical: the "
      "wrong model leads to cost overruns, missed requirements, and project failure.",

    "Core_Concepts":
      "Classical SDLC Models: Waterfall — sequential phases (Requirements → Design → "
      "Implementation → Testing → Deployment → Maintenance); simple but inflexible for "
      "changing requirements; suits well-understood, stable domains. V-Model — extends "
      "Waterfall with verification and validation at each phase; each dev phase has a "
      "corresponding test phase. Iterative Model — develops system in iterations, refining "
      "with each cycle. Spiral Model — risk-driven; combines iterative development with "
      "systematic risk assessment; 4 quadrants: Determine Objectives, Identify Risks, "
      "Develop/Test, Plan Next Iteration. "
      "Agile Methodology: values (Agile Manifesto 2001): Individuals & Interactions over "
      "processes, Working Software over documentation, Customer Collaboration over contract "
      "negotiation, Responding to Change over following a plan. "
      "Scrum Framework: work organized in Sprints (1-4 weeks); roles: Product Owner, "
      "Scrum Master, Development Team; ceremonies: Sprint Planning, Daily Standup (15 min), "
      "Sprint Review, Sprint Retrospective; artifacts: Product Backlog, Sprint Backlog, "
      "Increment. Kanban: visualize workflow on board (To Do/In Progress/Done), limit "
      "Work-in-Progress (WIP). Extreme Programming (XP): pair programming, TDD (Test-Driven "
      "Development — write failing test → write code → refactor), continuous integration.",

    "Examples":
      "Waterfall for avionics software: requirements fully frozen, strict V&V, DO-178C "
      "certification requires documented phase gates — Waterfall is appropriate. "
      "Scrum for e-commerce platform: Sprint 1: user authentication, Sprint 2: product "
      "catalogue, Sprint 3: shopping cart — business can reprioritize backlog between sprints. "
      "TDD example: write test assertUser.login(correct_password) == True → implement login() "
      "→ test passes → refactor to add rate limiting. CI/CD pipeline: code push → automated "
      "tests run → Docker image built → deployed to staging → manual approval → production.",

    "Conclusion":
      "Modern software engineering favours Agile methodologies for their ability to accommodate "
      "changing requirements and deliver value incrementally. However, safety-critical and "
      "regulatory-constrained domains still rely on heavyweight models like Waterfall or V-Model. "
      "Effective engineers select the model suited to their project's risk, uncertainty, and "
      "stakeholder dynamics."
  },

  # ── Q8 ───────────────────────────────────────────────────────────────────
  { "q": "Question 8:  Computer Architecture — CPU and Memory Hierarchy", "marks": "[8 marks]",
    "Introduction":
      "Computer architecture defines the functional structure and behaviour of a computer system "
      "at the ISA (Instruction Set Architecture) level — the interface between hardware and "
      "software. The von Neumann architecture (1945) introduced the stored-program concept: "
      "program instructions and data reside in the same memory, fetched and executed sequentially. "
      "Modern CPUs implement this via a pipeline and exploit hierarchy in memory to bridge the "
      "speed gap between fast processors and slow DRAM.",

    "Core_Concepts":
      "CPU Components: ALU (Arithmetic Logic Unit — performs arithmetic and logical operations), "
      "CU (Control Unit — fetches, decodes, and issues micro-operations), Registers (PC/IP, IR, "
      "MAR, MDR, accumulator, general-purpose). Instruction Cycle: Fetch (load instruction from "
      "memory[PC] into IR) → Decode (CU interprets opcode) → Execute (ALU performs operation) "
      "→ Store (write result to register/memory). "
      "Pipelining: overlaps multiple instruction stages (IF/ID/EX/MEM/WB) to increase throughput. "
      "CPI approaches 1 with deep pipeline. Hazards: Data (RAW/WAR/WAW dependencies — solved by "
      "forwarding/stalling), Control (branch prediction — 2-bit saturating counter, BTB), "
      "Structural (resource conflicts — solved by duplication). "
      "Memory Hierarchy (fastest→slowest, smallest→largest): CPU Registers (< 1ns, bytes) → "
      "L1 Cache (1-4ns, 32-256 KB, 4-8 way set-associative) → L2 Cache (4-12ns, 256 KB-4 MB) "
      "→ L3 Cache (20-40ns, 4-32 MB, shared) → Main Memory DRAM (60-100ns, GBs) → SSD "
      "(50-200µs) → HDD (5-20ms). Cache principles: Temporal locality (recently used → likely "
      "reused), Spatial locality (nearby addresses → likely accessed). Cache miss types: "
      "Compulsory (cold), Capacity, Conflict. Replacement policies: LRU, FIFO, Random. "
      "RISC vs CISC: RISC (ARM, MIPS) — fixed-length instructions, load/store architecture, "
      "many registers, simple CU, high IPC. CISC (x86) — variable-length, complex instructions "
      "translated to micro-ops internally.",

    "Examples":
      "5-stage pipeline example: ADD R1,R2,R3 followed by SUB R4,R1,R5 causes RAW hazard on "
      "R1 — solved by forwarding from EX stage output back to EX input, eliminating 2-cycle "
      "stall. Cache hit ratio 95%, hit time 4ns, miss time 100ns: AMAT = 0.95×4 + 0.05×100 "
      "= 3.8 + 5 = 8.8ns. Direct-mapped cache: address tag, set index, block offset — "
      "conflict misses if two hot addresses map to same set.",

    "Conclusion":
      "Modern CPUs achieve high performance through deep pipelines (10-20 stages), out-of-order "
      "execution, superscalar issue (4-8 instructions/cycle), branch prediction (>95% accuracy), "
      "and multi-level caches. The memory hierarchy is carefully tuned to ensure most accesses "
      "hit L1/L2 cache, masking the ~100× latency gap between registers and DRAM."
  },

  # ── Q9 ───────────────────────────────────────────────────────────────────
  { "q": "Question 9:  Web Technologies — Client-Server Architecture and HTTP", "marks": "[8 marks]",
    "Introduction":
      "Web technologies encompass the protocols, languages, and frameworks used to build and "
      "deliver content over the World Wide Web. The client-server architecture is the foundational "
      "model of the web: a client (web browser or app) requests resources, and a server processes "
      "and responds. HTTP (HyperText Transfer Protocol), defined in RFC 2616 (HTTP/1.1) and "
      "RFC 7540 (HTTP/2), is the stateless application-layer protocol governing web communication. "
      "Modern web applications use a rich stack: HTML/CSS/JavaScript on the client, with RESTful "
      "APIs or GraphQL bridging to server-side frameworks.",

    "Core_Concepts":
      "HTTP Request/Response: method (GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS), URL, "
      "headers (Content-Type, Authorization, Cache-Control, Accept), body (for POST/PUT). "
      "Status codes: 2xx Success (200 OK, 201 Created, 204 No Content), 3xx Redirection "
      "(301 Moved Permanently, 302 Found), 4xx Client Error (400 Bad Request, 401 Unauthorized, "
      "403 Forbidden, 404 Not Found, 429 Too Many Requests), 5xx Server Error (500 Internal "
      "Server Error, 503 Service Unavailable). "
      "HTTP/1.1 vs HTTP/2: HTTP/2 introduces multiplexing (multiple streams over one TCP "
      "connection, eliminating head-of-line blocking), header compression (HPACK), server push, "
      "binary framing (not text). HTTP/3 uses QUIC (UDP-based) for further latency reduction. "
      "REST (Representational State Transfer): stateless, resource-identified by URI, "
      "CRUD mapped to HTTP methods, responses in JSON/XML. "
      "Cookies and Sessions: server sets Set-Cookie header; browser sends Cookie header; used "
      "for session management and user tracking. JWT (JSON Web Token): stateless auth token "
      "(header.payload.signature base64-encoded); no server-side session storage needed. "
      "Web Security: XSS (inject client-side script — mitigate with CSP, input sanitization), "
      "CSRF (forge authenticated request — mitigate with CSRF tokens, SameSite cookies), "
      "SQL Injection (parameterized queries), HTTPS (TLS encrypts channel).",

    "Examples":
      "GET /api/users/123 HTTP/1.1 → 200 OK with JSON body {id:123, name:'Alice'}. "
      "POST /api/login with {email, password} → server validates → returns JWT → client "
      "stores in localStorage → subsequent requests include Authorization: Bearer <token>. "
      "React SPA (Single Page Application): HTML shell loaded once; JavaScript fetches data "
      "via Fetch API / Axios; React reconciler updates virtual DOM → efficient real DOM patches. "
      "WebSocket: ws:// protocol enables full-duplex persistent connection — used in real-time "
      "chat, live dashboards, multiplayer games.",

    "Conclusion":
      "Modern web architecture has evolved from simple static pages to complex distributed "
      "systems with microservices, CDNs, and real-time communication. Understanding HTTP, REST, "
      "security, and client-server patterns is essential for building scalable, secure, and "
      "performant web applications."
  },

  # ── Q10 ──────────────────────────────────────────────────────────────────
  { "q": "Question 10:  Cloud Computing — Service Models and Deployment", "marks": "[8 marks]",
    "Introduction":
      "Cloud computing delivers computing resources (servers, storage, databases, networking, "
      "software, analytics) over the internet ('the cloud') on an on-demand, pay-as-you-go "
      "model, eliminating the need for organizations to own and maintain physical infrastructure. "
      "NIST (National Institute of Standards and Technology) defines cloud computing by five "
      "essential characteristics: on-demand self-service, broad network access, resource pooling "
      "(multi-tenancy), rapid elasticity (scale up/down automatically), and measured service "
      "(metered billing). Cloud has transformed IT from CapEx (capital expenditure) to OpEx "
      "(operational expenditure).",

    "Core_Concepts":
      "Service Models — IaaS (Infrastructure as a Service): provides virtualized compute, "
      "storage, and networking. Customer manages OS, middleware, apps. Providers: AWS EC2/S3, "
      "Azure VMs, Google Compute Engine. Use case: hosting custom applications, dev/test "
      "environments. PaaS (Platform as a Service): provides a development platform with runtime, "
      "middleware, OS managed by provider. Customer manages only applications and data. "
      "Providers: Google App Engine, Heroku, AWS Elastic Beanstalk, Azure App Service. "
      "Use case: web application development, APIs. SaaS (Software as a Service): fully managed "
      "application delivered over browser. Customer only uses the software. Providers: "
      "Google Workspace, Microsoft 365, Salesforce CRM, Slack, Zoom. "
      "Deployment Models — Public Cloud: shared infrastructure, owned by CSP (AWS, Azure, GCP), "
      "highly scalable, cost-effective. Private Cloud: dedicated infrastructure, hosted on-prem "
      "or by provider, higher security/compliance (banks, hospitals). Hybrid Cloud: mix of "
      "public and private, connected via VPN/Direct Connect — burst to public for peak loads. "
      "Multi-Cloud: use multiple CSPs to avoid vendor lock-in and optimize cost/performance. "
      "Key Technologies: Virtualization (hypervisor: Type 1 bare-metal — VMware ESXi, "
      "Hyper-V; Type 2 hosted — VirtualBox), Containers (Docker — lightweight OS-level "
      "virtualization, share host kernel), Kubernetes (container orchestration — auto-scaling, "
      "self-healing, rolling updates), Serverless/FaaS (AWS Lambda — event-driven, zero "
      "infrastructure management, pay per invocation).",

    "Examples":
      "Netflix uses AWS IaaS (EC2, S3, CloudFront CDN) with multi-region deployment for "
      "99.99% availability. A startup uses Heroku PaaS to deploy a Node.js API in minutes "
      "without managing servers. A hospital uses Private Cloud (on-prem VMware) for patient "
      "data compliance (HIPAA) with burst to AWS for analytics. Kubernetes deployment: "
      "define Deployment (replicas=3, image=myapp:v2) → K8s schedules pods across nodes → "
      "HPA (Horizontal Pod Autoscaler) adds pods when CPU > 70%.",

    "Conclusion":
      "Cloud computing has democratized access to enterprise-grade infrastructure, enabling "
      "startups to compete with large enterprises. Choosing the right service model (IaaS/PaaS/"
      "SaaS) and deployment model (Public/Private/Hybrid) depends on cost, compliance, "
      "scalability needs, and technical capability. Cloud-native architectures (microservices, "
      "containers, serverless) are the future of scalable software systems."
  },
]


# ─────────────────────────────────────────────────────────────────────────────
# STUDENT ANSWERS  (5 different quality levels)
# ─────────────────────────────────────────────────────────────────────────────

# helper: trim content to a fraction of detail
def _q(model_q, intro_f, core_f, ex_f, conc_f, custom=None):
    """Build a student question dict by slicing model answer to given fractions."""
    def _trim(text, frac):
        if frac >= 1.0: return text
        if frac <= 0.0: return ""
        words = text.split()
        return " ".join(words[:max(3, int(len(words) * frac))])
    return {
        "q"           : model_q["q"],
        "marks"       : model_q["marks"],
        "Introduction": _trim(model_q["Introduction"], intro_f),
        "Core_Concepts": _trim(model_q["Core_Concepts"], core_f),
        "Examples"    : _trim(model_q["Examples"], ex_f),
        "Conclusion"  : _trim(model_q["Conclusion"], conc_f),
        **(custom or {}),
    }

# ── Student 1: EXCELLENT  (Aryan Mehta — ~88%) ───────────────────────────────
# Near-complete answers; minor omissions in depth but all sections well-covered
STUDENT_1 = [
    _q(MODEL[0], 0.95, 0.88, 0.90, 0.95),
    _q(MODEL[1], 0.92, 0.85, 0.88, 0.92),
    _q(MODEL[2], 0.90, 0.82, 0.88, 0.92),
    _q(MODEL[3], 0.90, 0.85, 0.85, 0.90),
    _q(MODEL[4], 0.88, 0.82, 0.87, 0.90),
    _q(MODEL[5], 0.90, 0.80, 0.87, 0.88),
    _q(MODEL[6], 0.92, 0.80, 0.90, 0.90),
    _q(MODEL[7], 0.88, 0.78, 0.85, 0.88),
    _q(MODEL[8], 0.90, 0.80, 0.88, 0.88),
    _q(MODEL[9], 0.92, 0.82, 0.88, 0.90),
]

# ── Student 2: GOOD  (Priya Sharma — ~70%) ────────────────────────────────────
# Covers main ideas well; lacks advanced details in Core_Concepts; examples are simpler
STUDENT_2 = [
    _q(MODEL[0], 0.80, 0.65, 0.72, 0.78),
    _q(MODEL[1], 0.78, 0.62, 0.68, 0.75),
    _q(MODEL[2], 0.75, 0.60, 0.68, 0.75),
    _q(MODEL[3], 0.75, 0.62, 0.65, 0.73),
    _q(MODEL[4], 0.72, 0.60, 0.65, 0.72),
    _q(MODEL[5], 0.75, 0.58, 0.65, 0.72),
    _q(MODEL[6], 0.78, 0.58, 0.70, 0.75),
    _q(MODEL[7], 0.72, 0.55, 0.62, 0.72),
    _q(MODEL[8], 0.75, 0.58, 0.65, 0.72),
    _q(MODEL[9], 0.78, 0.60, 0.65, 0.75),
]

# ── Student 3: AVERAGE  (Rohit Das — ~52%) ───────────────────────────────────
# Basic understanding; answers correct but very brief; examples are generic
STUDENT_3 = [
    _q(MODEL[0], 0.55, 0.45, 0.50, 0.55),
    _q(MODEL[1], 0.52, 0.42, 0.47, 0.52),
    _q(MODEL[2], 0.50, 0.40, 0.47, 0.52),
    _q(MODEL[3], 0.50, 0.42, 0.45, 0.50),
    _q(MODEL[4], 0.48, 0.40, 0.45, 0.50),
    _q(MODEL[5], 0.52, 0.38, 0.45, 0.50),
    _q(MODEL[6], 0.55, 0.38, 0.50, 0.52),
    _q(MODEL[7], 0.48, 0.35, 0.42, 0.50),
    _q(MODEL[8], 0.50, 0.38, 0.45, 0.50),
    _q(MODEL[9], 0.52, 0.40, 0.45, 0.52),
]

# ── Student 4: BELOW AVERAGE  (Neha Verma — ~35%) ────────────────────────────
# Superficial answers; introduction barely adequate; core concepts very incomplete;
# examples often missing or minimal; some questions left very thin
STUDENT_4 = [
    _q(MODEL[0], 0.40, 0.28, 0.32, 0.38),
    _q(MODEL[1], 0.38, 0.25, 0.30, 0.35),
    _q(MODEL[2], 0.35, 0.22, 0.28, 0.35),
    _q(MODEL[3], 0.35, 0.25, 0.28, 0.32),
    _q(MODEL[4], 0.32, 0.22, 0.25, 0.32),
    _q(MODEL[5], 0.38, 0.20, 0.28, 0.32),
    _q(MODEL[6], 0.40, 0.22, 0.32, 0.35),
    _q(MODEL[7], 0.32, 0.18, 0.25, 0.32),
    _q(MODEL[8], 0.35, 0.22, 0.28, 0.32),
    _q(MODEL[9], 0.38, 0.22, 0.28, 0.35),
]

# ── Student 5: WEAK  (Sanjay Gupta — ~18%) ───────────────────────────────────
# Very minimal answers; most sections have only 1-2 sentences; Q7-Q10 mostly blank
STUDENT_5 = [
    _q(MODEL[0], 0.22, 0.15, 0.18, 0.20),
    _q(MODEL[1], 0.20, 0.12, 0.15, 0.18),
    _q(MODEL[2], 0.18, 0.10, 0.13, 0.18),
    _q(MODEL[3], 0.18, 0.12, 0.12, 0.16),
    _q(MODEL[4], 0.16, 0.10, 0.10, 0.16),
    _q(MODEL[5], 0.20, 0.08, 0.12, 0.15),
    {  # Q7 - almost blank
        "q": MODEL[6]["q"], "marks": MODEL[6]["marks"],
        "Introduction": "Software Engineering is about building software in a systematic way.",
        "Core_Concepts": "SDLC has phases like requirements, design, coding, and testing.",
        "Examples": "",
        "Conclusion": "Agile is a popular approach.",
    },
    {  # Q8 - almost blank
        "q": MODEL[7]["q"], "marks": MODEL[7]["marks"],
        "Introduction": "CPU stands for Central Processing Unit and is the brain of the computer.",
        "Core_Concepts": "CPU has ALU, Control Unit and registers. It fetches and executes instructions.",
        "Examples": "",
        "Conclusion": "Memory hierarchy includes cache and RAM.",
    },
    {  # Q9 - almost blank
        "q": MODEL[8]["q"], "marks": MODEL[8]["marks"],
        "Introduction": "Web technologies are used to build websites and web applications.",
        "Core_Concepts": "HTTP is the protocol used for web communication. It uses GET and POST methods.",
        "Examples": "",
        "Conclusion": "Web security is important to protect data.",
    },
    {  # Q10 - blank conclusion + empty examples
        "q": MODEL[9]["q"], "marks": MODEL[9]["marks"],
        "Introduction": "Cloud computing provides resources over the internet on demand.",
        "Core_Concepts": "There are three types: IaaS, PaaS and SaaS. AWS and Azure are popular clouds.",
        "Examples": "",
        "Conclusion": "",
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# PDF WRITER
# ─────────────────────────────────────────────────────────────────────────────

def write_pdf(filename, title, subtitle, questions):
    doc   = fitz.open()
    W, H  = 595, 842   # A4
    MX    = 50          # left margin
    MY    = 55          # top margin (after header)
    MAX_Y = H - 40

    def new_page():
        pg = doc.new_page(width=W, height=H)
        # Thin header bar on every page
        pg.draw_rect(fitz.Rect(0, 0, W, 40), color=(0.12, 0.30, 0.60),
                     fill=(0.12, 0.30, 0.60))
        pg.insert_text((12, 26), title, fontsize=10, color=(1, 1, 1))
        pg.insert_text((W - 120, 26), subtitle, fontsize=9, color=(0.85, 0.90, 1.0))
        return pg, MY

    page, y = new_page()

    def need_space(h):
        nonlocal page, y
        if y + h > MAX_Y:
            page, y = new_page()

    def put(text, x, font, size, color, wrap_width=495):
        nonlocal y
        if not text.strip():
            return
        words = text.split()
        line  = ""
        for word in words:
            test = (line + " " + word).strip()
            if fitz.get_text_length(test, fontsize=size) > wrap_width:
                need_space(size + 4)
                page.insert_text((x, y), line, fontsize=size, color=color)
                y += size + 4
                line = word
            else:
                line = test
        if line:
            need_space(size + 4)
            page.insert_text((x, y), line, fontsize=size, color=color)
            y += size + 4

    SECTION_ORDER = ["Introduction", "Core_Concepts", "Examples", "Conclusion"]

    for qi, q in enumerate(questions):
        # ── Question header ──────────────────────────────────────
        need_space(36)
        if y > MY + 10:
            y += 8
        # blue question bar
        bar_y = y - 12
        page.draw_rect(fitz.Rect(MX - 4, bar_y, W - MX + 4, bar_y + 22),
                       color=(0.12, 0.30, 0.60), fill=(0.92, 0.95, 1.0))
        page.insert_text((MX, y), q["q"], fontsize=11, color=(0.10, 0.25, 0.55))
        tw = fitz.get_text_length(q["marks"], fontsize=9)
        page.insert_text((W - MX - tw, y), q["marks"], fontsize=9, color=(0.50, 0.10, 0.10))
        y += 18

        # ── Sections ─────────────────────────────────────────────
        for sec in SECTION_ORDER:
            body = q.get(sec, "").strip()
            display = sec.replace("_", " ")
            marks_map = {"Introduction": "(2 marks)", "Core_Concepts": "(3 marks)",
                         "Examples": "(2 marks)", "Conclusion": "(1 mark)"}
            sec_label = f"{display}:  {marks_map.get(sec, '')}"

            need_space(20)
            y += 5
            page.insert_text((MX, y), sec_label, fontsize=10.5,
                              color=(0.65, 0.15, 0.05))
            y += 16

            if body:
                put(body, MX + 10, font="helv", size=10.5,
                    color=(0.10, 0.10, 0.10), wrap_width=440)
            else:
                # Empty answer — draw blank lines
                for _ in range(2):
                    need_space(14)
                    page.draw_line(fitz.Point(MX + 10, y + 8),
                                   fitz.Point(W - MX, y + 8),
                                   color=(0.75, 0.75, 0.75), width=0.5)
                    y += 14
            y += 4

        # Separator between questions
        need_space(6)
        page.draw_line(fitz.Point(MX, y + 2), fitz.Point(W - MX, y + 2),
                       color=(0.75, 0.75, 0.75), width=0.4)
        y += 8

    pages = len(doc)
    doc.save(filename)
    doc.close()
    print(f"  Saved: {os.path.basename(filename)}  ({pages} pages)")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\nGenerating 80-marks exam PDFs...\n")

    files = [
        ("model_80marks.pdf",        "GRADX Model Answer  |  10 Questions  |  80 Marks",
         "Answer Key", MODEL),
        ("student_80_excellent.pdf", "GRADX Student Answer  |  Aryan Mehta  |  Roll: S001",
         "Excellent ~88%", STUDENT_1),
        ("student_80_good.pdf",      "GRADX Student Answer  |  Priya Sharma  |  Roll: S002",
         "Good ~70%", STUDENT_2),
        ("student_80_average.pdf",   "GRADX Student Answer  |  Rohit Das  |  Roll: S003",
         "Average ~52%", STUDENT_3),
        ("student_80_below.pdf",     "GRADX Student Answer  |  Neha Verma  |  Roll: S004",
         "Below Avg ~35%", STUDENT_4),
        ("student_80_weak.pdf",      "GRADX Student Answer  |  Sanjay Gupta  |  Roll: S005",
         "Weak ~18%", STUDENT_5),
    ]

    for fname, title, subtitle, qs in files:
        path = os.path.join(OUT_DIR, fname)
        write_pdf(path, title, subtitle, qs)

    # Verify embedded text and page counts
    print("\nVerification:")
    for fname, _, _, _ in files:
        path = os.path.join(OUT_DIR, fname)
        doc = fitz.open(path)
        pages = len(doc)
        chars = sum(len(p.get_text().strip()) for p in doc)
        doc.close()
        status = "✓ typed" if chars > 500 else "⚠ scanned"
        print(f"  {fname:<38} {pages:>2} pages  {chars:>6} chars  [{status}]")

    print(f"\nAll 6 PDFs saved to: {OUT_DIR}")
    print("\nQuestion config for GRADX UI:")
    print("  10 questions, sections per question:")
    print("    Introduction (2 marks)")
    print("    Core_Concepts (3 marks)")
    print("    Examples (2 marks)")
    print("    Conclusion (1 mark)")
    print("  Total: 10 × 8 = 80 marks")
