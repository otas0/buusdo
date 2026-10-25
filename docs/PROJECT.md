# buusdo — 项目说明

## 1. 项目是什么

buusdo 是一个跨平台（Windows / Linux / macOS）的桌面工具，用于提升电脑的
图形使用体验，核心功能是"自动画质增强"和"光追能力管理"，并附带少量强关联的
系统体验项（按游戏切换显示配置、HDR 自动协调）。

它不是一个渲染引擎，也不是一个游戏 mod 制作工具。它的本质是：

  **一个增强能力的调度器 + 配置协调器。**

它复用各平台已有的增强生态，自己不实现注入、不实现渲染、不实现光追。

## 2. 三个平台的能力边界（必须严格遵守）

不同平台的图形管线开放程度不同，本项目不追求三端功能对等。

### Windows（功能最完整）
- 注入底座：ReShade（D3D9/10/11/12、OpenGL、Vulkan）
- 神经画质：DLSS 5，通过 ReShade 附加组件或 OptiScaler 分支注入
- 真光追：仅限管理已有的 RTX Remix mod，不自己重建场景
- 色彩兜底：DWM SDR→HDR 着色器修补（可选模块，Phase 3 才做）

### Linux（调度已有开源生态）
- 原生 Linux 游戏：通过 Vulkan 后处理层实现，调度 vkBasalt / vkSumi
- 调度入口：Goverlay（GUI 包装器）或直接写环境变量 + Steam launch options
- 通过 Proton 运行的 Windows 游戏：可复用 Windows 后端的 ReShade 部署逻辑，
  目标路径是 Proton prefix，不是宿主文件系统
- 不自己实现 Vulkan 层，不自己写 hook

### macOS（配置协调，不做注入）
- 禁止任何 dylib 注入代码。SIP 和 hardened runtime 是系统级约束，
  要求用户关闭 SIP 是不可接受的安全代价。
- 唯一增强路径：MetalFX（通过 Metal 4 / Tahoe 26+），
  以及通过兼容层（Game Porting Toolkit / CrossOver / Bridgeplay）
  把 DLSS 选项路由到 MetalFX
- 后端职责：检测游戏运行环境，配置兼容层的 MetalFX 选项，
  读取兼容层日志确认生效
- 无法确认目标安全时，默认阻断

## 3. 硬约束（违反即视为 bug）

### C1. 反作弊门禁是强制拦截，不是提示
- 任何后端的 install() / 注入 / 配置写入，第一步必须调用
  `core.anticheat_guard.check(target, platform)`
- 检测到反作弊时必须抛出 `UnsafeTargetError`，UI 显示不可绕过的阻断页
- 不得提供"我已知晓风险，继续"的按钮
- 语义是"存在反作弊就拒绝"

### C2. 所有写操作必须是事务性的
- 必须通过 `core.transaction.Transaction` 上下文管理器
- 语义：变更前快照 → 记录每个变更 → 失败时按逆序恢复
- 卸载时必须逐字节恢复原始文件
- 不得留下"半安装"状态

### C3. 平台差异必须封装在 backends/ 内
- `core/` 和 `ui/` 不得出现 `if platform == "windows"` 这类分支
- 平台分派只发生在 `core/platform_detect.py` 和
  `backends/__init__.py` 的后端选择逻辑中
- UI 只与 `EnhancementBackend` 抽象接口交互

### C4. 文案不得夸大能力
- 不得出现"已开启光线追踪"的表述
- 路径追踪（RTX Remix mod）与神经画质增强（DLSS 5）必须明确区分
- 后处理近似必须标注"近似"
- macOS 上不得宣称"DLSS"，只能表述为"MetalFX 兼容层配置"

### C5. macOS 后端禁止注入
- 不得生成任何使用 DYLD_INSERT_LIBRARIES、task_for_pid、
  mach_inject 或类似机制的代码
- macOS 后端只允许：读写兼容层配置文件、设置环境变量、
  读取兼容层日志

## 4. 技术栈（已锁定）

- 语言：Python 3.11+
- UI：PySide6（Qt 6.11+），三端共用
- 进程/模块枚举：psutil
- PE 解析：pefile
- 注入（仅 Windows）：ctypes 调 Win32 API
- 测试：pytest
- 分发：pyside6-deploy
- 配置持久化：JSON（按游戏保存，放在用户配置目录）

不引入：Electron、Tauri、Rust 构建链、内核驱动、自研 Vulkan/D3D hook。
