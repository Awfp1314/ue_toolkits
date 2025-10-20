# -*- coding: utf-8 -*-

from pathlib import Path
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import shutil
import traceback

# 使用统一的日志系统
from core.logger import get_logger
logger = get_logger(__name__)


class ConfigTemplate:
    """配置模板数据类"""
    
    def __init__(self, name: str, description: str = "", data: Optional[Dict[str, Any]] = None, 
                 last_modified: Optional[str] = None, projects: int = 0, path: Optional[Path] = None):
        self.name = name
        self.description = description
        self.data = data or {}
        self.last_modified = last_modified or datetime.now().strftime("%Y-%m-%d %H:%M")
        self.projects = projects
        self.path = path  # 添加配置文件路径属性


class ConfigToolLogic:
    """配置工具业务逻辑类"""
    
    def __init__(self, config_dir: str) -> None:
        self.config_dir: str = config_dir
        self.config_file: str = os.path.join(config_dir, "config_template.json")
        self.config_templates: List[ConfigTemplate] = []
        self.ui_settings: Dict[str, Any] = {
            "button_columns": 3
        }
        self.load_config()
    
    def load_config(self) -> None:
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                if "ui_settings" in config_data:
                    self.ui_settings.update(config_data["ui_settings"])
                
                if "default_templates" in config_data:
                    for template_data in config_data["default_templates"]:
                        template = ConfigTemplate(
                            template_data.get("name", ""),
                            template_data.get("description", ""),
                            template_data.get("data", {}),
                            template_data.get("last_modified"),
                            template_data.get("projects", 0),
                            Path(template_data.get("path")) if template_data.get("path") else None
                        )
                        self.config_templates.append(template)
                logger.info("配置文件加载成功")
        except Exception as e:
            logger.error(f"加载配置文件时出错: {e}")
    
    def save_config(self) -> None:
        """保存配置文件"""
        try:
            # 确保目录存在
            os.makedirs(self.config_dir, exist_ok=True)
            
            # 准备保存的数据
            config_data = {
                "_version": "1.0.0",
                "default_templates": [
                    {
                        "name": template.name,
                        "description": template.description,
                        "data": template.data,
                        "last_modified": template.last_modified,
                        "projects": template.projects,
                        "path": str(template.path) if template.path else None
                    }
                    for template in self.config_templates
                ],
                "recent_projects": [],
                "ui_settings": self.ui_settings
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            logger.info("配置文件保存成功")
        except Exception as e:
            logger.error(f"保存配置文件时出错: {e}")
    
    def add_template(self, name: str, description: str = "") -> ConfigTemplate:
        """添加新的配置模板"""
        template = ConfigTemplate(name, description)
        self.config_templates.append(template)
        self.save_config()
        logger.info(f"添加配置模板: {name}")
        return template
    
    def remove_template(self, template: ConfigTemplate) -> None:
        """删除配置模板"""
        if template in self.config_templates:
            # 删除配置文件夹
            if template.path and template.path.exists():
                try:
                    shutil.rmtree(template.path)
                    logger.info(f"删除配置文件夹: {template.path}")
                except Exception as e:
                    logger.error(f"删除配置文件夹时出错: {e}")
            
            # 从配置列表中移除并保存
            self.config_templates.remove(template)
            self.save_config()
            logger.info(f"删除配置模板: {template.name}")
    
    def get_templates(self) -> List[ConfigTemplate]:
        """获取所有配置模板"""
        logger.info(f"获取配置模板列表，共 {len(self.config_templates)} 个模板")
        return self.config_templates
    
    def get_ui_settings(self) -> Dict[str, Any]:
        """获取UI设置"""
        logger.info("获取UI设置")
        return self.ui_settings
    
    def _validate_path(self, path: Path, base_path: Path) -> bool:
        """验证路径是否安全
        
        此方法检查路径是否在预期的基准路径下，防止路径遍历攻击。
        
        Args:
            path: 待验证的路径
            base_path: 基准路径（允许的根目录）
            
        Returns:
            bool: 路径是否安全
        """
        try:
            # 解析为绝对路径，这会自动处理 '..' 等相对路径符号
            abs_path = path.resolve()
            abs_base = base_path.resolve()
            
            # is_relative_to() 在 Python 3.9+ 可用
            try:
                is_safe = abs_path.is_relative_to(abs_base)
            except AttributeError:
                # Python 3.8 兼容性处理
                try:
                    abs_path.relative_to(abs_base)
                    is_safe = True
                except ValueError:
                    is_safe = False
            
            if not is_safe:
                logger.error(f"路径验证失败: {path} 不在基准路径 {base_path} 下")
                return False
            
            logger.debug(f"路径验证通过: {path}")
            return True
            
        except (ValueError, OSError, RuntimeError) as e:
            logger.error(f"路径验证时发生错误: {e}")
            return False
    
    def _is_safe_filename(self, filename: str) -> bool:
        """验证文件名是否安全
        
        检查文件名是否包含危险字符，防止路径遍历攻击。
        
        Args:
            filename: 待验证的文件名
            
        Returns:
            bool: 文件名是否安全
        """
        dangerous_chars = ['..', '/', '\\', '\x00', '\n', '\r', '\t']
        
        for char in dangerous_chars:
            if char in filename:
                logger.error(f"文件名包含危险字符 '{char}': {filename}")
                return False
        
        if len(filename) > 255:
            logger.error(f"文件名过长（{len(filename)} 字符）: {filename}")
            return False
        
        if not filename.strip():
            logger.error("文件名为空或只包含空格")
            return False
        
        logger.debug(f"文件名验证通过: {filename}")
        return True
    
    def add_config_template(self, config_name: str, source_files: List[Path]) -> bool:
        """添加新的配置模板
        
        Args:
            config_name: 配置名称
            source_files: 源配置文件路径列表
            
        Returns:
            bool: 是否添加成功
        """
        if not config_name.strip():
            logger.warning("配置名称不能为空")
            return False
        
        for template in self.config_templates:
            if template.name == config_name:
                logger.warning(f"配置名称 '{config_name}' 已存在")
                return False
        
        try:
            from core.utils.path_utils import PathUtils
            
            path_utils = PathUtils()
            target_dir = path_utils.get_user_data_dir() / "EditConfig" / config_name
            
            target_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"创建目标目录: {target_dir}")
            
            # 复制文件，只复制.ini文件
            copied_files = 0
            for source_file in source_files:
                # 只处理.ini文件
                if source_file.exists() and source_file.suffix.lower() == '.ini':
                    target_file = target_dir / source_file.name
                    shutil.copy2(source_file, target_file)
                    logger.info(f"复制文件: {source_file} -> {target_file}")
                    copied_files += 1
                else:
                    if not source_file.exists():
                        logger.warning(f"源文件不存在: {source_file}")
                    elif source_file.suffix.lower() != '.ini':
                        logger.info(f"跳过非.ini文件: {source_file}")
            
            # 添加配置模板到配置中，并设置路径
            template = self.add_template(config_name, f"从UE工程导入的配置模板 ({copied_files}个文件)")
            # 设置配置文件路径
            template.path = target_dir
            # 重新保存配置以确保路径被保存
            self.save_config()
            
            return True
        except Exception as e:
            logger.error(f"添加配置模板时发生错误: {e}")
            return False
    
    def apply_config_from_template_to_project(self, template: ConfigTemplate, target_project_path: Path) -> bool:
        """从模板直接应用配置到UE工程，只处理.ini文件
        
        Args:
            template: 配置模板对象
            target_project_path: 目标工程路径
            
        Returns:
            bool: 是否应用成功
        """
        try:
            if not template:
                logger.error("配置模板为空")
                return False
            
            if not template.path:
                logger.error(f"配置模板路径为空: {template.name}")
                return False
                
            if not template.path.exists():
                logger.error(f"配置模板路径不存在: {template.path}")
                return False
            
            # 使用复制文件方法
            return self.copy_config_files_from_template(template, target_project_path)
        except Exception as e:
            logger.error(f"应用配置到工程时发生错误: {e}")
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            return False
            
    def apply_config_to_project(self, config_name: str, target_project_path: Path) -> bool:
        """应用配置到UE工程，只处理.ini文件
        
        Args:
            config_name: 配置名称
            target_project_path: 目标工程路径
            
        Returns:
            bool: 是否应用成功
        """
        # 查找配置模板
        template = None
        for t in self.config_templates:
            if t.name == config_name:
                template = t
                break
        
        if not template:
            logger.error(f"未找到配置模板: {config_name}")
            return False
            
        # 调用新的方法
        return self.apply_config_from_template_to_project(template, target_project_path)
        
    def detect_running_ue_projects(self):
        """检测运行的UE工程
        
        Returns:
            List: 检测到的UE工程列表
        """
        try:
            from core.utils.ue_process_utils import UEProcessUtils
            ue_utils = UEProcessUtils()
            projects = ue_utils.detect_running_ue_projects()
            
            # 如果没有检测到运行的工程，则搜索所有UE工程
            if not projects:
                logger.info("未检测到运行的UE工程，开始搜索所有UE工程")
                projects = ue_utils.search_all_ue_projects()
            
            return projects
        except Exception as e:
            logger.error(f"检测UE工程时发生错误: {e}")
            return []
            
    def copy_config_files_from_template(self, template: ConfigTemplate, target_project_path: Path) -> bool:
        """复制配置文件从模板到目标工程，只处理.ini文件
        
        此方法包含完整的安全检查，防止路径遍历攻击和文件名注入。
        
        Args:
            template: 配置模板对象
            target_project_path: 目标工程路径
            
        Returns:
            bool: 是否复制成功
        """
        try:
            if not template.path or not template.path.exists():
                logger.error("配置模板路径不存在")
                return False
            
            if not target_project_path.exists():
                logger.error(f"目标工程路径不存在: {target_project_path}")
                return False
            
            # 解析为绝对路径，防止相对路径攻击
            target_project_path = target_project_path.resolve()
            logger.info(f"目标工程路径（已标准化）: {target_project_path}")
            
            # 如果 project_path 指向 .uproject 文件，则使用其父目录
            if target_project_path.suffix.lower() == '.uproject':
                target_project_path = target_project_path.parent
                logger.info(f"检测到 .uproject 文件路径，使用项目目录: {target_project_path}")
            
            # 构建目标路径 - 确保是配置目录而不是项目目录
            target_dir = target_project_path / "Saved" / "Config" / "Windows"
            
            if not self._validate_path(target_dir, target_project_path):
                logger.error(f"目标目录路径不安全: {target_dir}")
                return False
            
            try:
                target_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"创建目标目录: {target_dir}")
            except OSError as mkdir_error:
                logger.error(f"创建目标目录失败: {mkdir_error}")
                return False
            
            # 获取源配置文件列表，只处理.ini文件
            try:
                ini_files = list(template.path.glob("*.ini"))
                logger.info(f"找到 {len(ini_files)} 个.ini配置文件")
            except OSError as glob_error:
                logger.error(f"读取模板目录失败: {glob_error}")
                return False
            
            if not ini_files:
                logger.warning(f"模板目录中没有.ini文件: {template.path}")
                return False
            
            # 记录跳过的非.ini文件
            try:
                non_ini_files = [f for f in template.path.iterdir() 
                                if f.is_file() and f.suffix.lower() != '.ini']
                if non_ini_files:
                    logger.info(f"跳过 {len(non_ini_files)} 个非.ini文件: {[f.name for f in non_ini_files]}")
            except OSError:
                # 如果读取失败，只记录警告，不影响主流程
                logger.warning("无法读取模板目录的非.ini文件列表")
            
            # === 5. 复制文件（带安全检查）===
            copied_files = []
            failed_files = []
            
            for source_file in ini_files:
                try:
                    # 确保只处理文件而不是目录，并且是.ini文件
                    if not source_file.is_file():
                        logger.warning(f"跳过非文件对象: {source_file}")
                        continue
                    
                    if source_file.suffix.lower() != '.ini':
                        logger.warning(f"跳过非.ini文件: {source_file.name}")
                        continue
                    
                    file_name = source_file.name
                    if not self._is_safe_filename(file_name):
                        logger.error(f"跳过不安全的文件名: {file_name}")
                        failed_files.append(file_name)
                        continue
                    
                    target_file = target_dir / file_name
                    
                    if not self._validate_path(target_file, target_dir):
                        logger.error(f"跳过不安全的目标路径: {target_file}")
                        failed_files.append(file_name)
                        continue
                    
                    logger.info(f"准备复制文件: {file_name} -> {target_file}")
                    
                    if target_file.exists():
                        logger.info(f"目标文件已存在，将被覆盖: {target_file}")
                    
                    try:
                        # 使用 shutil.copy2 保留元数据
                        shutil.copy2(source_file, target_file)
                        copied_files.append(file_name)
                        logger.info(f"成功复制文件: {source_file} -> {target_file}")
                        
                    except PermissionError as perm_error:
                        # 如果权限不足，尝试使用copyfile（不保留元数据）
                        logger.warning(f"权限不足，尝试使用copyfile: {perm_error}")
                        try:
                            shutil.copyfile(source_file, target_file)
                            copied_files.append(file_name)
                            logger.info(f"使用copyfile成功复制文件: {source_file} -> {target_file}")
                        except Exception as copyfile_error:
                            logger.error(f"使用copyfile复制文件失败: {file_name}, 错误: {copyfile_error}")
                            failed_files.append(file_name)
                            
                    except OSError as os_error:
                        logger.error(f"系统错误，复制文件失败: {file_name}, 错误: {os_error}")
                        failed_files.append(file_name)
                        
                    except Exception as copy_error:
                        logger.error(f"复制文件失败: {file_name}, 错误: {copy_error}")
                        failed_files.append(file_name)
                        
                except Exception as file_error:
                    logger.error(f"处理文件时发生错误: {source_file}, 错误: {file_error}")
                    failed_files.append(source_file.name if hasattr(source_file, 'name') else 'unknown')
                    continue
            
            logger.info(f"配置文件复制完成 - 成功: {len(copied_files)} 个，失败: {len(failed_files)} 个")
            
            if failed_files:
                logger.warning(f"以下文件复制失败: {failed_files}")
            
            # 只要有文件成功复制，就返回True
            return len(copied_files) > 0
            
        except Exception as e:
            logger.error(f"复制配置文件时发生严重错误: {e}")
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            return False