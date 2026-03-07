# Performance & Architecture Guide: Arduino Uno Q (2GB Model)

This guide outlines the "Split-Brain" development architecture used to overcome local hardware limitations when running AI-driven agentic tools (like Gemini CLI or Antigravity) on the Arduino Uno Q.

---

## Recommended Architecture: "Split-Brain" Development

To maintain a high-performance IDE experience without crashing the Uno Q, we offload the "Agentic" heavy lifting (Language Servers, AI Indexing, and CLI Companions) to a secondary powerful host (e.g., an Ubuntu NUC or PC).

| Component | Role | Location |
| :--- | :--- | :--- |
| **Source Code** | Primary storage for `.ino`, `.py`, and `.yaml` | **Uno Q** (`/home/arduino/ArduinoApps`) |
| **Logic & AI** | Gemini CLI, Antigravity, and VS Code Extensions | **Powerful Ubuntu Host** (x86_64 / High-RAM ARM) |
| **File Sync** | Real-time mounting via **SSHFS** | **Local Network** (1Gbps recommended) |
| **Execution** | Hardware-level runs & Bridge management | **Uno Q** (via Remote SSH) |

---

## Hardware Limitations of the 2GB Uno Q

The Uno Q is a versatile dual-processor board, but the Linux (MPU) side faces specific constraints when running modern "Agentic" CLI tools locally.

### 1. Memory Exhaustion (The "1.7GB Wall")
Although marketed with 2GB, the usable memory in the Debian environment is approximately **1740 MiB**.
* **Agentic Overhead:** Running the Gemini CLI and its Node.js background processes can consume **40%–60% of available RAM**.
* **Swap Reliance:** Once RAM is depleted, the system relies on the **870MB eMMC swap**. This introduces massive latency in I/O operations and can trigger the **OOM (Out of Memory) Killer**, terminating active builds or sensor bridges.

### 2. Instruction Set Compatibility
Certain AI-driven extensions and binary tools may throw **"Illegal Instruction"** errors when running on the specific `aarch64` implementation of the Qualcomm chip. Running these tools on a more powerful secondary server ensures stable execution and better compatibility.

### 3. CPU Contention & Jitter
High CPU load from an active AI agent (often pushing load averages > 1.0) can introduce **jitter** into the **Bridge library**. This latency can cause dropped packets or "laggy" readings when interacting with high-speed sensors like the **VL53L1X (ToF)** or ultrasonic sensors.

---

## Optimization Checklist

If you are developing directly on the board, follow these "Lean" practices:

1.  **Release Memory Early:** Always `/exit` or `Ctrl+D` out of the Gemini CLI immediately after code generation to return RAM to the system.
2.  **Optimize SFTP:** For stable SSHFS mounting, ensure the Uno Q uses the internal subsystem in `/etc/ssh/sshd_config`:
    ```bash
    Subsystem sftp internal-sftp
    ```
3.  **Monitor Load:** Use `top` or `htop` to ensure the **MainThread** or **node** processes aren't "squatting" on memory while you are testing high-frequency sensor code.