# 灵台明镜 iOS 工程

这个工程把仓库根目录的 PWA 内容、经文、图片和音频作为本地 `WebContent` 资源打进 iOS App。应用不依赖线上站点才能阅读和朗读，线上地址主要用于隐私政策、支持和主动对照 CBETA 底本。

## 构建

使用 Xcode 打开 `LingtaiMirror.xcodeproj`，选择 `LingtaiMirror` scheme。模拟器可直接构建；真机或归档上传前，需要在 Signing & Capabilities 中选择开发者团队，并确认 Bundle ID 与 App Store Connect 一致。

构建脚本会把仓库根目录复制到 App 包中的 `WebContent`，因此不要把这个 iOS 子目录单独移动到仓库外。
