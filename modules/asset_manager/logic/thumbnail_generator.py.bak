# -*- coding: utf-8 -*-

"""
缩略图生成器
"""

from pathlib import Path
from typing import Optional, Callable
from PIL import Image, ImageDraw, ImageFont
import io

from core.logger import get_logger
from core.utils.thread_utils import get_thread_manager

logger = get_logger(__name__)


class ThumbnailGenerator:
    """缩略图生成器"""
    
    # 支持的图片格式
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tga', '.tif', '.tiff'}
    
    # 默认缩略图尺寸
    THUMBNAIL_SIZE = (200, 200)
    
    # 线程管理器（类级别）
    _thread_manager = None
    
    @classmethod
    def _get_thread_manager(cls):
        """获取线程管理器单例"""
        if cls._thread_manager is None:
            cls._thread_manager = get_thread_manager()
        return cls._thread_manager
    
    @staticmethod
    def generate_thumbnail(asset_path: Path, output_path: Path, asset_type_name: str = "") -> bool:
        """生成缩略图（同步版本）
        
        Args:
            asset_path: 资产路径
            output_path: 输出路径
            asset_type_name: 资产类型名称（用于生成默认图标）
            
        Returns:
            成功返回True，失败返回False
        """
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 如果是图片文件，直接生成缩略图
            if asset_path.is_file() and asset_path.suffix.lower() in ThumbnailGenerator.IMAGE_EXTENSIONS:
                return ThumbnailGenerator._generate_from_image(asset_path, output_path)
            
            # 如果是文件夹，尝试查找文件夹中的图片
            if asset_path.is_dir():
                for ext in ThumbnailGenerator.IMAGE_EXTENSIONS:
                    images = list(asset_path.glob(f"*{ext}"))
                    if images:
                        return ThumbnailGenerator._generate_from_image(images[0], output_path)
            
            # 其他情况生成默认图标
            return ThumbnailGenerator._generate_default_icon(output_path, asset_type_name or asset_path.suffix.upper())
            
        except Exception as e:
            logger.error(f"生成缩略图失败: {e}", exc_info=True)
            # 生成错误图标
            return ThumbnailGenerator._generate_default_icon(output_path, "ERR")
    
    @classmethod
    def generate_thumbnail_async(
        cls,
        asset_path: Path,
        output_path: Path,
        asset_type_name: str = "",
        on_complete: Optional[Callable[[bool], None]] = None,
        on_error: Optional[Callable[[str], None]] = None
    ):
        """异步生成缩略图（推荐使用）
        
        Args:
            asset_path: 资产路径
            output_path: 输出路径
            asset_type_name: 资产类型名称
            on_complete: 完成回调 (success: bool) -> None
            on_error: 错误回调
            
        Example:
            def on_done(success):
                if success:
                    print("缩略图生成成功")
            
            ThumbnailGenerator.generate_thumbnail_async(
                asset_path,
                output_path,
                on_complete=on_done
            )
        """
        logger.info(f"开始异步生成缩略图: {asset_path}")
        
        def generate_task():
            return cls.generate_thumbnail(asset_path, output_path, asset_type_name)
        
        thread_manager = cls._get_thread_manager()
        thread_manager.run_in_thread(
            generate_task,
            on_result=on_complete,
            on_error=on_error
        )
    
    @staticmethod
    def _generate_from_image(image_path: Path, output_path: Path) -> bool:
        """从图片文件生成缩略图"""
        try:
            with Image.open(image_path) as img:
                # 转换为RGB模式
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 生成缩略图（保持宽高比）
                img.thumbnail(ThumbnailGenerator.THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
                
                thumb = Image.new('RGB', ThumbnailGenerator.THUMBNAIL_SIZE, (45, 45, 45))
                
                # 居中粘贴
                offset = ((ThumbnailGenerator.THUMBNAIL_SIZE[0] - img.size[0]) // 2,
                         (ThumbnailGenerator.THUMBNAIL_SIZE[1] - img.size[1]) // 2)
                thumb.paste(img, offset)
                
                # 保存
                thumb.save(output_path, 'PNG', quality=85)
                logger.debug(f"从图片生成缩略图: {image_path.name}")
                return True
                
        except Exception as e:
            logger.error(f"从图片生成缩略图失败: {e}")
            return False
    
    @staticmethod
    def _generate_default_icon(output_path: Path, text: str) -> bool:
        """生成默认图标"""
        try:
            img = Image.new('RGB', ThumbnailGenerator.THUMBNAIL_SIZE, (60, 60, 60))
            draw = ImageDraw.Draw(img)
            
            # 绘制边框
            draw.rectangle([10, 10, 190, 190], outline=(100, 100, 100), width=2)
            
            # 绘制文本
            text = text.replace('.', '').upper()[:5]  # 最多5个字符
            
            # 尝试使用系统字体
            try:
                font = ImageFont.truetype("arial.ttf", 36)
            except:
                font = ImageFont.load_default()
            
            # 计算文本位置（居中）
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            position = ((200 - text_width) // 2, (200 - text_height) // 2)
            
            # 绘制文本
            draw.text(position, text, fill=(180, 180, 180), font=font)
            
            # 保存
            img.save(output_path, 'PNG')
            logger.debug(f"生成默认图标: {text}")
            return True
            
        except Exception as e:
            logger.error(f"生成默认图标失败: {e}")
            return False

