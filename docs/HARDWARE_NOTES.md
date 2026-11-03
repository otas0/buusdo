# Hardware realities (honesty — not product tricks)

buusdo is a **scheduler + config coordinator**. It does **not** turn system RAM
into a GPU, invent compute units, or promise free performance from “wasted”
hardware. These notes are product doctrine (C4).

## 1. Unified memory (Apple Silicon / some APUs)

CPU and GPU already share a memory pool by hardware design. That is not a
buusdo feature and not something an enhancement tool can “enable.”

## 2. Idle iGPU / second GPU

A spare integrated GPU or secondary adapter may help with **extra displays**,
**encode/decode**, or **per-game device selection** when the OS/driver/game
supports it. Gains are workload-specific — **not** a general FPS boost that
buusdo can flip on for every title.

## 3. Resizable BAR / SAM

These let the CPU address more of the discrete GPU’s VRAM more efficiently when
board + BIOS + driver + game cooperate. They do **not** convert system RAM into
video memory.

## 4. VRAM spill into system RAM

When VRAM is exhausted, drivers may page textures into system memory. That is a
**fallback**, usually **slower and stutterier**, not an optimization mode.

## 5. CPU software rasterization (e.g. llvmpipe)

The CPU can produce frames without a discrete GPU. Expect **much lower**
performance than a real GPU; suitable only as a last-resort fallback, never as
a recommended “upgrade path.”

## What buusdo will do

- Keep About / capability copy aligned with the five points above.
- Optionally show a **read-only** host adapter summary when detection is cheap
  and reliable (no claimed acceleration).
- Never market “RAM as GPU,” “enable unified memory,” or similar inflation.

## What buusdo will not do

- Disable SIP or inject on macOS to chase hardware tricks (C5).
- Bundle drivers that rewrite memory as VRAM.
- Treat VRAM spill or soft-raster as default “enhancements.”
