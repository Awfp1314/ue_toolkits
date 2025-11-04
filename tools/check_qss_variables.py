#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
QSS 变量检测工具

功能：
1. 扫描 variables.qss 中定义的所有变量
2. 扫描 components/*.qss 中使用的所有变量
3. 检测缺失的变量（使用了但未定义）
4. 检测未使用的变量（定义了但未使用）
5. 生成统计报告

使用方法：
  python tools/check_qss_variables.py
  
  或在项目根目录执行：
  python -m tools.check_qss_variables
"""

import re
import sys
from pathlib import Path
from collections import defaultdict

# 设置 Windows 控制台输出编码为 UTF-8
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass


class QSSVariableChecker:
    """QSS 变量检测器"""
    
    def __init__(self, project_root: Path = None):
        """
        初始化检测器
        
        Args:
            project_root: 项目根目录，默认为当前文件的上两级目录
        """
        if project_root is None:
            # 当前文件: tools/check_qss_variables.py
            # 项目根: ../
            self.project_root = Path(__file__).parent.parent
        else:
            self.project_root = project_root
        
        self.variables_file = self.project_root / "resources" / "qss" / "variables.qss"
        self.components_dir = self.project_root / "resources" / "qss" / "components"
        
        self.defined_vars = {}  # {var_name: value}
        self.used_vars = defaultdict(list)  # {var_name: [file1.qss, file2.qss]}
    
    def scan_defined_variables(self):
        """扫描 variables.qss 中定义的变量"""
        if not self.variables_file.exists():
            print(f"❌ 错误: variables.qss 不存在: {self.variables_file}")
            return
        
        content = self.variables_file.read_text(encoding='utf-8')
        
        # 正则匹配: /* --var-name: value */
        pattern = r'/\*\s*--([\w-]+):\s*([^*]+?)\s*\*/'
        
        for match in re.finditer(pattern, content):
            var_name = match.group(1)
            var_value = match.group(2).strip()
            self.defined_vars[var_name] = var_value
        
        print(f"✅ 扫描到 {len(self.defined_vars)} 个已定义变量\n")
    
    def scan_used_variables(self):
        """扫描 components/*.qss 中使用的变量"""
        if not self.components_dir.exists():
            print(f"❌ 错误: components 目录不存在: {self.components_dir}")
            return
        
        qss_files = list(self.components_dir.glob("*.qss"))
        
        if not qss_files:
            print(f"⚠️ 警告: components 目录下没有 QSS 文件")
            return
        
        # 正则匹配: /* --var-name */ fallback_value
        pattern = r'/\*\s*--([\w-]+)\s*\*/'
        
        for qss_file in qss_files:
            content = qss_file.read_text(encoding='utf-8')
            
            for match in re.finditer(pattern, content):
                var_name = match.group(1)
                self.used_vars[var_name].append(qss_file.name)
        
        print(f"✅ 扫描到 {len(qss_files)} 个 QSS 文件")
        print(f"✅ 使用了 {len(self.used_vars)} 个变量\n")
    
    def check_missing_variables(self):
        """检测缺失的变量（使用了但未定义）"""
        missing_vars = set(self.used_vars.keys()) - set(self.defined_vars.keys())
        
        if not missing_vars:
            print("✅ 所有使用的变量均已定义！\n")
            return []
        
        print(f"❌ 发现 {len(missing_vars)} 个缺失变量:\n")
        
        missing_list = []
        for var_name in sorted(missing_vars):
            files = self.used_vars[var_name]
            usage_count = len(files)
            files_str = ', '.join(set(files))  # 去重
            
            print(f"  --{var_name}")
            print(f"    使用次数: {usage_count}")
            print(f"    使用文件: {files_str}")
            print()
            
            missing_list.append({
                'name': var_name,
                'count': usage_count,
                'files': list(set(files))
            })
        
        return missing_list
    
    def check_unused_variables(self):
        """检测未使用的变量（定义了但未使用）"""
        unused_vars = set(self.defined_vars.keys()) - set(self.used_vars.keys())
        
        if not unused_vars:
            print("✅ 所有定义的变量均有使用！\n")
            return []
        
        print(f"⚠️ 发现 {len(unused_vars)} 个未使用变量:\n")
        
        unused_list = []
        for var_name in sorted(unused_vars):
            value = self.defined_vars[var_name]
            print(f"  --{var_name}: {value}")
            
            unused_list.append({
                'name': var_name,
                'value': value
            })
        
        print()
        return unused_list
    
    def generate_usage_statistics(self):
        """生成变量使用统计"""
        print("="*70)
        print("📊 变量使用统计")
        print("="*70 + "\n")
        
        # 按使用次数排序
        sorted_vars = sorted(
            self.used_vars.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )
        
        print("🔥 使用最频繁的变量 (Top 10):\n")
        
        for i, (var_name, files) in enumerate(sorted_vars[:10], 1):
            count = len(files)
            value = self.defined_vars.get(var_name, "❌ 未定义")
            print(f"  {i}. --{var_name}")
            print(f"     值: {value}")
            print(f"     使用次数: {count}")
            print()
    
    def run(self):
        """运行完整检测"""
        print("\n" + "="*70)
        print("[QSS Variable Checker] QSS 变量检测工具")
        print("="*70 + "\n")
        
        print(f"📂 项目根目录: {self.project_root}")
        print(f"📄 变量文件: {self.variables_file.relative_to(self.project_root)}")
        print(f"📁 组件目录: {self.components_dir.relative_to(self.project_root)}\n")
        
        # 1. 扫描定义的变量
        print("=" * 70)
        print("📋 步骤 1: 扫描已定义变量")
        print("=" * 70 + "\n")
        self.scan_defined_variables()
        
        # 2. 扫描使用的变量
        print("=" * 70)
        print("📋 步骤 2: 扫描已使用变量")
        print("=" * 70 + "\n")
        self.scan_used_variables()
        
        # 3. 检测缺失变量
        print("=" * 70)
        print("📋 步骤 3: 检测缺失变量")
        print("=" * 70 + "\n")
        missing = self.check_missing_variables()
        
        # 4. 检测未使用变量
        print("=" * 70)
        print("📋 步骤 4: 检测未使用变量")
        print("=" * 70 + "\n")
        unused = self.check_unused_variables()
        
        # 5. 生成统计
        self.generate_usage_statistics()
        
        # 6. 总结
        print("=" * 70)
        print("📊 检测总结")
        print("=" * 70 + "\n")
        
        print(f"✅ 已定义变量: {len(self.defined_vars)} 个")
        print(f"✅ 已使用变量: {len(self.used_vars)} 个")
        print(f"❌ 缺失变量: {len(missing)} 个")
        print(f"⚠️ 未使用变量: {len(unused)} 个\n")
        
        if missing:
            print("🛠️ 建议操作:")
            print("  1. 在 variables.qss 中补充缺失的变量定义")
            print("  2. 或在 QSS 文件中提供合适的回退值\n")
        
        if unused:
            print("💡 提示:")
            print("  未使用的变量可能是:")
            print("  - 预留的变量（未来使用）")
            print("  - 已废弃的变量（可以考虑删除）")
            print("  - AI助手模块专用变量（深色/浅色主题变体）\n")
        
        print("=" * 70)
        print("✅ 检测完成！")
        print("=" * 70 + "\n")


def main():
    """主函数"""
    checker = QSSVariableChecker()
    checker.run()


if __name__ == "__main__":
    main()

