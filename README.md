# buusdo

跨平台图形增强**调度器 + 配置协调器**（Windows / Linux / macOS）。

复用各平台已有增强生态；不实现注入底座以外的渲染，不实现光追，不做游戏 mod 制作。

完整产品语义与硬约束见 [docs/PROJECT.md](docs/PROJECT.md)。

## 开发

```bash
# Prefer uv (Homebrew Python on this machine may have a broken platform.mac_ver)
uv venv --python 3.12 .venv
source .venv/bin/activate
uv pip install -e ".[dev,ui]"
pytest
python -m buusdo
```

## 架构要点

- `core/` — 平台检测、Steam 发现、ReShade 部署、反作弊门禁、事务写入
- `backends/` — 平台专属实现（唯一允许平台分支的地方，外加 `platform_detect`）
- `ui/` — PySide6；只依赖 `EnhancementBackend`，反作弊阻断不可绕过

## ReShade 工具包

本项目不附带 ReShade 二进制。从官网安装/解压后，在 UI 中选择含
`ReShade64.dll` 的目录，或：

```python
from buusdo.core.config_store import set_reshade_kit_path
set_reshade_kit_path("/path/to/reshade_kit")
```

Linux 上 Proton 游戏：ReShade 部署到 `steamapps/common/<游戏>`（与 Windows 相同），
不会写入 Proton prefix 的 `drive_c`。
