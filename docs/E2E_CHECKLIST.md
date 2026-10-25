# buusdo 端到端手工测试清单

## 通用
- [ ] 启动 UI，确认 logo 与暗色主题正常
- [ ] 反作弊游戏目录 → 阻断页出现，且无「继续」按钮
- [ ] 配置导出/导入 zip 往返成功
- [ ] 操作历史能看到 install/uninstall 记录

## Windows
- [ ] 扫描 Steam 库；多 userdata 时 Steam 用户下拉可选
- [ ] ReShade D3D11：部署 `dxgi.dll`，卸载逐字节恢复
- [ ] ReShade Vulkan：生成 `ReShade64.json` + bat/注册表写回（可选）
- [ ] OptiScaler 与已部署 ReShade 文件名碰撞 → 阻断
- [ ] Remix 启用后禁止 ReShade `d3d9` 代理
- [ ] 显示/HDR 配置可保存到 per-game JSON
- [ ] DWM HDR 能力显示为不可用（Phase 3）

## Linux（原生）
- [ ] vkBasalt 模式写回所选用户的 `localconfig.vdf`
- [ ] Goverlay 已安装时一键唤起；未安装时能力不可用

## Linux（Proton）
- [ ] Proton 游戏显示 `[Proton]` 徽章
- [ ] ReShade 写入 `steamapps/common/<game>`，不写 `pfx/drive_c`
- [ ] Vulkan 层模式写入启动项 hint

## macOS
- [ ] 发现 GPTK / CrossOver 配置目录
- [ ] MetalFX 配置写入成功；文案无 DLSS 商标表述
- [ ] 未确认兼容层目标 → 默认阻断
