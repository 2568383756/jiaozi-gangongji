# 角色来源快照

2026-11-11 按用户提供的[角色仓库](https://github.com/2568383756/cartoon-character-assets)导入。源版本固定为 [`86562a37fb6cf75f0ea41419b072b4129f207538`](https://github.com/2568383756/cartoon-character-assets/tree/86562a37fb6cf75f0ea41419b072b4129f207538)。原仓只读，未修改或向原仓推送。

本地 `source_checkout/` 为浅克隆，用于重建与核对，不重复提交完整历史与预览工程。[source_manifest.json](source_manifest.json)记录交付目录所有文件的大小与 SHA-256。加工来源是 `卡通人物_搬运走路.blend` 与 `红衣卡通女孩_搬运走路.blend`；其外观分别对应纸团与印桃。原模型的骨骼、UV、蒙皮及搬运走路为源仓成果，新版动作拆分、尺度、接口、优化与验证见本项目新版资产。

重建源目录：在本目录执行 `git clone https://github.com/2568383756/cartoon-character-assets source_checkout`，再执行 `git -C source_checkout checkout 86562a37fb6cf75f0ea41419b072b4129f207538`。须按清单核对后再运行制作脚本，不依赖源仓今后变化的 main。

新版交付：[首批角色](../../Models/首批角色_v01_20261111/) · [首关道具](../../Models/首关道具_v01_20261111/) · [首关组合展示](../../Models/首关整合_v01_20261111/)。这些是美术资产，Unity 接入仍由维护灰盒的开发者进行。
