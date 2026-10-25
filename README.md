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

- `core/` — 平台检测、反作弊门禁、事务写入、后端抽象
- `backends/` — 平台专属实现（唯一允许平台分支的地方，外加 `platform_detect`）
- `ui/` — PySide6；只依赖 `EnhancementBackend`，反作弊阻断不可绕过
