# 主窗口 UI 优化建议

> 📅 创建日期：2025-11-09  
> 🎯 目标：让主窗口像启动加载界面一样美观现代

---

## 📊 当前状态分析

### 加载窗口的优势 ✨
- ✅ 无边框设计 + 半透明背景
- ✅ 12px 圆角，视觉柔和
- ✅ 精心设计的配色（#1e1e1e 背景 + #4a9eff 强调色）
- ✅ 60fps 平滑动画
- ✅ 内联样式，加载快速

### 主窗口的不足 😐
- ❌ 方形边框，视觉生硬
- ❌ 缺少动画效果
- ❌ 按钮悬停效果不够明显
- ❌ 整体视觉层次感不强

---

## 🎨 优化方案

### 方案 1：添加圆角和阴影效果 ⭐⭐⭐⭐⭐

**难度**：⭐⭐ (简单)  
**效果**：⭐⭐⭐⭐⭐ (显著)  
**实现时间**：10 分钟

#### 修改文件
`resources/qss/components/main_window.qss`

#### 代码示例
```css
/* 主窗口圆角 */
QMainWindow#UEMainWindow {
    background-color: #2b2b2b;
    border: 2px solid #3d3d3d;
    border-radius: 12px;  /* 添加圆角 */
}

/* 侧边栏圆角（左侧） */
QFrame#sidebar {
    background-color: #1e1e1e;
    border-right: 1px solid #555555;
    border-top-left-radius: 12px;
    border-bottom-left-radius: 12px;
}

/* 内容区域圆角（右侧） */
QFrame#rightFrame {
    background-color: #2b2b2b;
    border-top-right-radius: 12px;
    border-bottom-right-radius: 12px;
}
```

#### 添加阴影效果（需要修改 Python 代码）
**文件**：`ui/ue_main_window_core.py`

在 `init_ui()` 方法中添加：
```python
def init_ui(self) -> None:
    """初始化用户界面"""
    self.setWindowTitle("UE Toolkit - 虚幻引擎工具箱")
    self.setGeometry(100, 100, 1300, 800)
    self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
    
    # ⚡ 新增：添加窗口阴影效果
    from PyQt6.QtWidgets import QGraphicsDropShadowEffect
    from PyQt6.QtGui import QColor
    
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(30)           # 模糊半径
    shadow.setColor(QColor(0, 0, 0, 180))  # 阴影颜色（黑色，透明度180）
    shadow.setOffset(0, 5)             # 阴影偏移（向下5px）
    self.centralWidget().setGraphicsEffect(shadow)
    
    # ... 其他代码
```

---

### 方案 2：优化按钮悬停效果 ⭐⭐⭐⭐

**难度**：⭐ (非常简单)  
**效果**：⭐⭐⭐⭐ (明显)  
**实现时间**：5 分钟

#### 修改文件
`resources/qss/components/main_window.qss`

#### 代码示例
```css
/* 侧边栏按钮 - 添加平滑过渡 */
QPushButton#sidebar_button {
    background-color: transparent;
    color: #ffffff;
    border: none;
    padding: 12px;
    min-width: 60px;
    max-width: 60px;
    min-height: 60px;
    font-size: 24px;
    border-radius: 8px;  /* 添加圆角 */
}

QPushButton#sidebar_button:hover {
    background-color: #333333;
    transform: scale(1.05);  /* 悬停时放大 5% */
}

QPushButton#sidebar_button:checked {
    background-color: rgba(0, 122, 204, 0.8);
    color: white;
    border-left: 3px solid #4a9eff;  /* 添加左侧强调线 */
}

/* 标题栏按钮 - 添加过渡效果 */
QPushButton#title_button {
    background-color: transparent;
    color: #ffffff;
    border: none;
    min-width: 40px;
    max-width: 40px;
    min-height: 40px;
    max-height: 40px;
    font-size: 16px;
    border-radius: 4px;  /* 添加圆角 */
}

QPushButton#title_button:hover {
    background-color: #333333;
}

QPushButton#close_button:hover {
    background-color: #e81123;
    color: white;
}
```

---

### 方案 3：添加渐变背景 ⭐⭐⭐

**难度**：⭐ (非常简单)  
**效果**：⭐⭐⭐ (中等)  
**实现时间**：3 分钟

#### 修改文件
`resources/qss/themes/dark.qss` 或 `resources/qss/components/main_window.qss`

#### 代码示例
```css
/* 主窗口渐变背景 */
QMainWindow {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #2b2b2b,
        stop:1 #1e1e1e
    );
}

/* 侧边栏渐变背景 */
#leftPanel {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #1a1a1a,
        stop:1 #1e1e1e
    );
}

/* 标题栏渐变背景 */
QFrame#TitleBar {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #252525,
        stop:1 #1e1e1e
    );
}
```

---

### 方案 4：添加微动画效果 ⭐⭐⭐⭐⭐

**难度**：⭐⭐⭐ (中等)
**效果**：⭐⭐⭐⭐⭐ (非常显著)
**实现时间**：30 分钟

#### 实现方式
使用 `QPropertyAnimation` 为按钮、面板添加动画效果。

#### 创建新文件
`ui/animations/ui_animations.py`

#### 代码示例
```python
# -*- coding: utf-8 -*-
"""
UI 动画效果管理器
"""

from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QPoint, QSize
from PyQt6.QtWidgets import QWidget, QPushButton
from PyQt6.QtGui import QColor


class UIAnimations:
    """UI 动画效果管理器"""

    @staticmethod
    def fade_in(widget: QWidget, duration: int = 300):
        """淡入动画

        Args:
            widget: 目标控件
            duration: 动画时长（毫秒）
        """
        animation = QPropertyAnimation(widget, b"windowOpacity")
        animation.setDuration(duration)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        animation.start()
        return animation

    @staticmethod
    def slide_in_from_left(widget: QWidget, duration: int = 300):
        """从左侧滑入动画

        Args:
            widget: 目标控件
            duration: 动画时长（毫秒）
        """
        start_pos = QPoint(-widget.width(), widget.y())
        end_pos = widget.pos()

        animation = QPropertyAnimation(widget, b"pos")
        animation.setDuration(duration)
        animation.setStartValue(start_pos)
        animation.setEndValue(end_pos)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.start()
        return animation

    @staticmethod
    def button_hover_scale(button: QPushButton, scale: float = 1.05):
        """按钮悬停缩放动画

        Args:
            button: 目标按钮
            scale: 缩放比例
        """
        # 注意：需要在按钮的 enterEvent 和 leaveEvent 中调用
        original_size = button.size()
        scaled_size = QSize(
            int(original_size.width() * scale),
            int(original_size.height() * scale)
        )

        animation = QPropertyAnimation(button, b"size")
        animation.setDuration(150)
        animation.setStartValue(original_size)
        animation.setEndValue(scaled_size)
        animation.setEasingCurve(QEasingCurve.Type.OutQuad)
        animation.start()
        return animation

    @staticmethod
    def smooth_scroll(scroll_area, target_value: int, duration: int = 300):
        """平滑滚动动画

        Args:
            scroll_area: 滚动区域
            target_value: 目标滚动位置
            duration: 动画时长（毫秒）
        """
        animation = QPropertyAnimation(scroll_area.verticalScrollBar(), b"value")
        animation.setDuration(duration)
        animation.setStartValue(scroll_area.verticalScrollBar().value())
        animation.setEndValue(target_value)
        animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        animation.start()
        return animation
```

#### 使用示例
在主窗口中使用动画：

```python
from ui.animations.ui_animations import UIAnimations

# 在窗口显示时添加淡入动画
def showEvent(self, event):
    super().showEvent(event)
    UIAnimations.fade_in(self, duration=300)

# 在切换模块时添加滑入动画
def switch_module(self, module_widget):
    UIAnimations.slide_in_from_left(module_widget, duration=250)
```

---

### 方案 5：优化进度条样式 ⭐⭐⭐

**难度**：⭐ (非常简单)
**效果**：⭐⭐⭐ (中等)
**实现时间**：5 分钟

#### 适用场景
如果主窗口中有进度条（如资产加载进度），可以参考启动界面的进度条样式。

#### 代码示例
```css
/* 进度条样式（参考启动界面） */
QProgressBar {
    border: 1px solid #3d3d3d;
    border-radius: 4px;
    background-color: #2d2d2d;
    height: 8px;
    text-align: center;
    color: #ffffff;
}

QProgressBar::chunk {
    background-color: #4a9eff;
    border-radius: 3px;
}

/* 进度条悬停效果 */
QProgressBar:hover {
    border-color: #4a9eff;
}
```

---

## 🎯 推荐优化顺序

### 第一阶段：基础美化（30 分钟）
1. ✅ **方案 1**：添加圆角和阴影效果
2. ✅ **方案 2**：优化按钮悬停效果
3. ✅ **方案 3**：添加渐变背景

**预期效果**：主窗口视觉效果提升 70%

---

### 第二阶段：高级优化（1 小时）
4. ✅ **方案 4**：添加微动画效果
5. ✅ **方案 5**：优化进度条样式

**预期效果**：主窗口视觉效果提升 95%，接近专业级应用

---

## 📝 注意事项

### 1. 圆角窗口的限制
- ⚠️ 无边框窗口 + 圆角可能在某些系统上显示异常
- 💡 建议：保留 1-2px 的边框，避免显示问题

### 2. 阴影效果的性能
- ⚠️ `QGraphicsDropShadowEffect` 可能影响性能
- 💡 建议：只在主窗口使用，不要在每个子控件上使用

### 3. 动画的流畅度
- ⚠️ 动画时长不宜过长（建议 150-300ms）
- 💡 建议：使用 `QEasingCurve` 让动画更自然

### 4. 样式优先级
- ⚠️ 内联样式 > 代码设置样式 > QSS 文件样式
- 💡 建议：统一使用 QSS 文件管理样式，便于维护

---

## 🔧 快速测试

### 测试圆角效果
在主窗口的 QSS 中临时添加：
```css
QMainWindow {
    border: 2px solid red;
    border-radius: 12px;
}
```
如果看到红色圆角边框，说明样式生效。

### 测试阴影效果
在 `init_ui()` 中临时添加：
```python
shadow = QGraphicsDropShadowEffect()
shadow.setBlurRadius(50)
shadow.setColor(QColor(255, 0, 0, 200))  # 红色阴影
self.centralWidget().setGraphicsEffect(shadow)
```
如果看到红色阴影，说明效果生效。

---

## 📚 参考资源

### PyQt6 官方文档
- [QSS 样式表参考](https://doc.qt.io/qt-6/stylesheet-reference.html)
- [QPropertyAnimation 动画](https://doc.qt.io/qt-6/qpropertyanimation.html)
- [QGraphicsEffect 图形效果](https://doc.qt.io/qt-6/qgraphicseffect.html)

### 设计灵感
- **VS Code**：深色主题 + 圆角按钮
- **Spotify**：渐变背景 + 平滑动画
- **Discord**：侧边栏设计 + 悬停效果

---

## 🎨 配色方案建议

### 当前配色（深色主题）
- 主背景：`#2b2b2b`
- 次背景：`#1e1e1e`
- 强调色：`#4a9eff`（蓝色）
- 边框色：`#3d3d3d`

### 可选配色方案

#### 方案 A：科技蓝
- 主背景：`#1a1a2e`
- 次背景：`#16213e`
- 强调色：`#0f3460`
- 高亮色：`#00d4ff`

#### 方案 B：优雅紫
- 主背景：`#1e1e2e`
- 次背景：`#2a2a3e`
- 强调色：`#7c3aed`
- 高亮色：`#a78bfa`

#### 方案 C：现代绿
- 主背景：`#1a1f1e`
- 次背景：`#1e2826`
- 强调色：`#10b981`
- 高亮色：`#34d399`

---

## ✅ 总结

通过以上优化方案，你的主窗口可以达到：
- ✨ 现代化的视觉效果
- 🎯 流畅的交互体验
- 💎 专业级的界面质感

**建议从方案 1 和方案 2 开始**，这两个方案简单易实现，效果显著！

---

> 💡 **提示**：所有优化都是可选的，可以根据实际需求选择性实施。
> 📅 **更新日期**：2025-11-09
> 👨‍💻 **作者**：Augment Agent

