"""
本地 NLU 模块
基于当前AI身份动态生成寒暄模板，零成本处理简单对话
"""

import json
import re
import random
import hashlib
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime
from .nlu_templates import NEUTRAL_TEMPLATES, TEMPLATE_GENERATION_PROMPT
from PyQt6.QtCore import QThread, pyqtSignal


class IntentClassifier:
    """意图分类器（基于语义模型）"""
    
    # 各意图的标准示例（用于计算语义相似度）
    INTENT_EXAMPLES = {
        'greeting': [
            '你好', '早上好', '下午好', '晚上好', '您好', 
            'hi', 'hello', '嗨', '哈喽', '早啊', '嗨喽'
        ],
        'thanks': [
            '谢谢', '多谢', '感谢', 'thanks', 'thank you', 
            '谢了', '非常感谢', '太感谢了'
        ],
        'farewell': [
            '再见', '拜拜', '晚安', 'bye', 'goodbye', 
            '88', '回见', '下次见'
        ],
        'affirmation': [
            '好的', '嗯嗯', '嗯', '行', 'ok', 'okay', 
            '没问题', '收到', '明白了', '知道了'
        ]
    }
    
    # 工具调用相关的示例（用于排除）
    TOOL_CALL_EXAMPLES = [
        '查看资产', '帮我找文件', '列出所有', '显示配置',
        '搜索一下', '打开文件', '创建项目', '删除资产',
        '你能帮我', '可以帮我', '麻烦帮我', '我想看看'
    ]
    
    def __init__(self):
        """初始化分类器（延迟加载embedding服务）"""
        self._embedding_service = None
        self._intent_embeddings = None
        self._tool_embeddings = None
    
    def _get_embedding_service(self):
        """延迟获取embedding服务"""
        if self._embedding_service is None:
            try:
                from .embedding_service import EmbeddingService
                self._embedding_service = EmbeddingService()
            except Exception as e:
                print(f"[WARNING] [NLU] 无法加载embedding服务: {e}")
                return None
        return self._embedding_service
    
    def _compute_intent_embeddings(self):
        """预计算所有意图示例的embeddings"""
        if self._intent_embeddings is not None:
            return
        
        service = self._get_embedding_service()
        if not service:
            return
        
        try:
            self._intent_embeddings = {}
            for intent, examples in self.INTENT_EXAMPLES.items():
                # 为每个意图计算所有示例的平均embedding
                embeddings = [service.get_embedding(ex) for ex in examples]
                # 计算平均值
                import numpy as np
                avg_embedding = np.mean(embeddings, axis=0)
                self._intent_embeddings[intent] = avg_embedding
            
            # 计算工具调用示例的平均embedding
            tool_embeddings = [service.get_embedding(ex) for ex in self.TOOL_CALL_EXAMPLES]
            self._tool_embeddings = np.mean(tool_embeddings, axis=0)
        except Exception as e:
            print(f"[WARNING] [NLU] 计算意图embeddings失败: {e}")
    
    def classify(self, message: str) -> Optional[str]:
        """
        基于语义相似度分类用户意图
        
        Args:
            message: 用户消息
        
        Returns:
            意图类型或None（不适合本地处理）
        """
        message = message.strip()
        
        # 规则1：长度检查（超过30字符不处理）
        if len(message) > 30:
            return None
        
        # 规则2：包含明显的疑问词（快速排除）
        question_words = ['什么', '怎么', '为什么', '如何', '哪里', '哪', '哪些', '怎样', '为何', '谁', '?', '？']
        if any(qw in message for qw in question_words):
            return None
        
        # 使用语义模型判断
        service = self._get_embedding_service()
        if not service:
            # 如果embedding服务不可用，回退到None（交给LLM处理）
            return None
        
        try:
            # 确保意图embeddings已计算
            self._compute_intent_embeddings()
            if not self._intent_embeddings:
                return None
            
            # 计算用户输入的embedding
            message_embedding = service.get_embedding(message)
            
            # 计算与工具调用的相似度
            import numpy as np
            if self._tool_embeddings is not None:
                tool_similarity = np.dot(message_embedding, self._tool_embeddings) / (
                    np.linalg.norm(message_embedding) * np.linalg.norm(self._tool_embeddings)
                )
                # 如果与工具调用相似度较高，不处理
                if tool_similarity > 0.6:
                    return None
            
            # 计算与各意图的相似度
            best_intent = None
            best_score = 0.0
            
            for intent, intent_embedding in self._intent_embeddings.items():
                similarity = np.dot(message_embedding, intent_embedding) / (
                    np.linalg.norm(message_embedding) * np.linalg.norm(intent_embedding)
                )
                if similarity > best_score:
                    best_score = similarity
                    best_intent = intent
            
            # 只有相似度足够高（>0.7）才返回意图
            if best_score > 0.7:
                print(f"[DEBUG] [NLU-语义] 消息: '{message}' -> 意图: {best_intent}, 相似度: {best_score:.3f}")
                return best_intent
            else:
                print(f"[DEBUG] [NLU-语义] 消息: '{message}' -> 相似度不足 ({best_score:.3f})，交给LLM")
                return None
                
        except Exception as e:
            print(f"[WARNING] [NLU] 语义分类失败: {e}")
            return None


class TemplateCache:
    """模板缓存（带持久化）"""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        初始化模板缓存
        
        Args:
            cache_dir: 缓存目录（默认：user_data/nlu_templates）
        """
        # 延迟初始化：只在真正需要时创建目录和加载文件
        self._cache_dir = cache_dir
        self._cache = {}
        self._initialized = False
    
    def _ensure_initialized(self):
        """确保已初始化（延迟初始化）"""
        if self._initialized:
            return
        
        # 计算缓存目录
        if self._cache_dir:
            self.cache_dir = Path(self._cache_dir)
        else:
            # 使用 AppData 目录
            import os
            app_data = Path(os.environ.get('APPDATA', Path.home()))
            self.cache_dir = app_data / 'ue_toolkit' / 'user_data' / 'nlu_templates'
        
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self.cache_file = self.cache_dir / 'templates.json'
            self._cache = self._load_cache()
            self._initialized = True
        except Exception as e:
            print(f"[WARNING] [NLU] 初始化模板缓存失败: {e}")
            self._cache = {}
            self._initialized = True
    
    def _load_cache(self) -> Dict:
        """从文件加载缓存"""
        if not self.cache_file.exists():
            return {}
        
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARNING] [NLU] 加载模板缓存失败: {e}")
            return {}
    
    def _save_cache(self):
        """保存缓存到文件"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[WARNING] [NLU] 保存模板缓存失败: {e}")
    
    @staticmethod
    def _hash_identity(identity: str) -> str:
        """生成身份哈希"""
        return hashlib.md5(identity.encode('utf-8')).hexdigest()[:12]
    
    def get(self, identity: str) -> Optional[Dict]:
        """
        获取缓存的模板
        
        Args:
            identity: AI身份描述
        
        Returns:
            模板字典或None
        """
        self._ensure_initialized()
        identity_hash = self._hash_identity(identity)
        
        if identity_hash not in self._cache:
            return None
        
        entry = self._cache[identity_hash]
        
        # 检查是否过期（TTL=24小时）
        created_at = entry.get('created_at', 0)
        elapsed_hours = (datetime.now().timestamp() - created_at) / 3600
        
        if elapsed_hours > 24:
            # 过期，删除并返回None
            del self._cache[identity_hash]
            self._save_cache()
            return None
        
        return entry.get('templates')
    
    def set(self, identity: str, templates: Dict):
        """
        设置模板缓存
        
        Args:
            identity: AI身份描述
            templates: 模板字典
        """
        self._ensure_initialized()
        identity_hash = self._hash_identity(identity)
        
        self._cache[identity_hash] = {
            'identity': identity[:50],  # 保存前50字符以便调试
            'created_at': datetime.now().timestamp(),
            'templates': templates
        }
        
        # LRU淘汰：最多保留5个身份
        if len(self._cache) > 5:
            # 删除最旧的
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k]['created_at'])
            del self._cache[oldest_key]
        
        self._save_cache()
    
    def clear(self):
        """清空缓存"""
        self._ensure_initialized()
        self._cache.clear()
        self._save_cache()


class TemplateGenerator:
    """模板生成器（调用大模型）"""
    
    @staticmethod
    def generate_templates_sync(identity: str) -> Optional[Dict]:
        """
        同步调用LLM生成模板（使用requests直接调用）
        
        Args:
            identity: AI身份描述
        
        Returns:
            模板字典或None
        """
        try:
            import requests
            import json
            import os
            
            # 构建生成提示词
            prompt = TEMPLATE_GENERATION_PROMPT.format(identity=identity)
            
            messages = [
                {"role": "system", "content": "你是模板生成助手，只输出纯JSON，不要任何解释文字。"},
                {"role": "user", "content": prompt}
            ]
            
            print(f"[DEBUG] [7.0-P10] 正在为身份生成模板: {identity[:50]}...")
            
            # 从配置加载API设置
            try:
                from core.config.config_manager import ConfigManager
                from pathlib import Path
                from modules.ai_assistant.config_schema import get_ai_assistant_schema
                
                template_path = Path(__file__).parent.parent / "config_template.json"
                config_manager = ConfigManager(
                    "ai_assistant",
                    template_path=template_path,
                    config_schema=get_ai_assistant_schema()
                )
                config = config_manager.get_module_config()
                api_settings = config.get('api_settings', {})
                
                api_url = api_settings.get('api_url', 'https://api.openai-hk.com/v1/chat/completions')
                api_key = api_settings.get('api_key', '')
                model = "gemini-2.0-flash"  # 使用最便宜的模型生成模板
                
            except Exception as e:
                print(f"[ERROR] [7.0-P10] 加载API配置失败: {e}")
                return None
            
            # 构建请求
            payload = {
                "model": model,
                "messages": messages,
                "temperature": 0.3,  # 低温度，更稳定的输出
                "stream": False
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            # 调用API
            session = requests.Session()
            session.trust_env = False
            
            response = session.post(
                api_url,
                headers=headers,
                json=payload,
                timeout=30,
                proxies={'http': None, 'https': None}
            )
            
            if response.status_code != 200:
                print(f"[ERROR] [7.0-P10] API调用失败: {response.status_code}")
                return None
            
            # 解析响应
            data = response.json()
            content = data['choices'][0]['message']['content']
            
            # 提取JSON（可能包含markdown代码块）
            import re
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                json_str = json_match.group(0)
                templates = json.loads(json_str)
                print(f"[DEBUG] [7.0-P10] 模板生成成功，共 {sum(len(v) for v in templates.values())} 个模板")
                return templates
            else:
                print(f"[ERROR] [7.0-P10] 无法从响应中提取JSON: {content[:200]}")
                return None
            
        except Exception as e:
            print(f"[ERROR] [7.0-P10] 模板生成失败: {e}")
            import traceback
            traceback.print_exc()
            return None


class AsyncTemplateGeneratorThread(QThread):
    """异步模板生成器（QThread）"""
    
    # 信号
    generation_finished = pyqtSignal(dict)  # 生成成功：templates_dict
    generation_failed = pyqtSignal(str)     # 生成失败：error_message
    
    def __init__(self, identity: str):
        super().__init__()
        self.identity = identity
    
    def run(self):
        """在后台线程中生成模板"""
        try:
            print(f"[DEBUG] [7.0-P10] [异步] 开始生成模板...")
            templates = TemplateGenerator.generate_templates_sync(self.identity)
            
            if templates:
                print(f"[DEBUG] [7.0-P10] [异步] 模板生成成功")
                self.generation_finished.emit(templates)
            else:
                print(f"[WARNING] [7.0-P10] [异步] 模板生成返回空")
                self.generation_failed.emit("模板生成返回空结果")
        except Exception as e:
            error_msg = f"模板生成异常: {e}"
            print(f"[ERROR] [7.0-P10] [异步] {error_msg}")
            import traceback
            traceback.print_exc()
            self.generation_failed.emit(error_msg)


class LocalNLU:
    """本地NLU主类"""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        初始化本地NLU
        
        Args:
            cache_dir: 模板缓存目录
        """
        self.classifier = IntentClassifier()
        self.template_cache = TemplateCache(cache_dir)
        self.stats = {
            'total_handled': 0,
            'by_intent': {intent: 0 for intent in ['greeting', 'thanks', 'farewell', 'affirmation']}
        }
    
    def can_handle_locally(self, message: str) -> Optional[str]:
        """
        判断是否可以本地处理
        
        Args:
            message: 用户消息
        
        Returns:
            意图类型或None
        """
        return self.classifier.classify(message)
    
    def needs_template_generation(self, identity: Optional[str] = None) -> bool:
        """
        检查是否需要生成模板（即缓存未命中）
        
        Args:
            identity: 当前AI身份
        
        Returns:
            是否需要生成模板
        """
        if not identity or len(identity) == 0:
            return False  # 无身份，使用中性模板
        
        if len(identity) > 500:
            return False  # 身份过于复杂，使用中性模板
        
        # 检查缓存
        templates = self.template_cache.get(identity)
        return templates is None  # 缓存未命中则需要生成
    
    def get_cached_response(self, intent: str, identity: Optional[str] = None) -> Optional[str]:
        """
        从缓存获取响应（不生成新模板）
        
        Args:
            intent: 意图类型
            identity: 当前AI身份
        
        Returns:
            响应文本或None（如果缓存未命中）
        """
        if not identity or len(identity) == 0 or len(identity) > 500:
            # 使用中性模板
            if intent in NEUTRAL_TEMPLATES:
                response = random.choice(NEUTRAL_TEMPLATES[intent])
                self.stats['total_handled'] += 1
                self.stats['by_intent'][intent] += 1
                return response
            return None
        
        # 从缓存获取
        templates = self.template_cache.get(identity)
        if templates and intent in templates:
            response = random.choice(templates[intent])
            self.stats['total_handled'] += 1
            self.stats['by_intent'][intent] += 1
            return response
        
        return None  # 缓存未命中
    
    def save_generated_templates(self, identity: str, templates: dict):
        """
        保存生成的模板到缓存
        
        Args:
            identity: AI身份
            templates: 生成的模板字典
        """
        self.template_cache.set(identity, templates)
        print(f"[DEBUG] [7.0-P10] 模板已保存到缓存")
    
    def get_local_response(
        self, 
        intent: str, 
        identity: Optional[str] = None,
        api_client_factory=None
    ) -> str:
        """
        获取本地响应（支持动态模板生成）
        
        Args:
            intent: 意图类型
            identity: 当前AI身份
            api_client_factory: API客户端工厂（未使用，保留兼容性）
        
        Returns:
            响应文本
        """
        templates = None
        
        # 1. 如果有身份，尝试从缓存获取或生成模板
        print(f"[DEBUG] [7.0-P10] 当前身份长度: {len(identity) if identity else 0}")
        if identity:
            print(f"[DEBUG] [7.0-P10] 身份内容: {identity[:100]}...")
        
        if identity and len(identity) > 0:
            # 检查身份是否过于复杂（>500字）
            if len(identity) > 500:
                print(f"[DEBUG] [7.0-P10] 身份过于复杂({len(identity)}字)，降级到中性模板")
            else:
                # 尝试从缓存获取
                templates = self.template_cache.get(identity)
                
                if templates:
                    print(f"[DEBUG] [7.0-P10] 缓存命中！使用已缓存的模板")
                else:
                    # 缓存未命中，动态生成模板
                    print(f"[DEBUG] [7.0-P10] 缓存未命中，调用LLM生成模板...")
                    generated = TemplateGenerator.generate_templates_sync(identity)
                    
                    if generated:
                        # 生成成功，存入缓存
                        self.template_cache.set(identity, generated)
                        templates = generated
                        print(f"[DEBUG] [7.0-P10] 模板生成并缓存成功")
                    else:
                        print(f"[WARNING] [7.0-P10] 模板生成失败，降级到中性模板")
        else:
            print(f"[WARNING] [7.0-P10] 身份为空，直接使用中性模板")
        
        # 2. 如果有模板，随机选择
        if templates and intent in templates:
            response = random.choice(templates[intent])
            print(f"[DEBUG] [7.0-P10] 使用动态生成的模板")
        else:
            # 3. 降级到中性模板
            response = random.choice(NEUTRAL_TEMPLATES.get(intent, NEUTRAL_TEMPLATES['affirmation']))
            print(f"[DEBUG] [7.0-P10] 使用中性降级模板")
        
        # 4. 更新统计
        self.stats['total_handled'] += 1
        if intent in self.stats['by_intent']:
            self.stats['by_intent'][intent] += 1
        
        return response
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return self.stats.copy()

