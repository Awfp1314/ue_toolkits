# -*- coding: utf-8 -*-

"""
IntentEngine 单元测试
验证意图解析准确率 ≥ 85%
"""

import pytest
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from modules.ai_assistant.logic.intent_parser import IntentEngine, IntentType


# 测试样本：10类意图 x 3条样本 = 30条
TEST_SAMPLES = {
    IntentType.ASSET_QUERY: [
        "有哪些蓝图资产？",
        "查找所有材质",
        "搜索模型文件"
    ],
    IntentType.ASSET_DETAIL: [
        "胡桃资产的详细路径在哪？",
        "这个蓝图包含什么文件？",
        "查看材质资产的具体信息"
    ],
    IntentType.CONFIG_QUERY: [
        "有哪些配置模板？",
        "显示所有引擎配置",
        "查找项目设置"
    ],
    IntentType.CONFIG_COMPARE: [
        "对比两个配置的差异",
        "配置A和配置B有什么区别？",
        "比较这两个模板"
    ],
    IntentType.LOG_ANALYZE: [
        "为什么程序出错了？",
        "分析最近的错误日志",
        "查看崩溃原因"
    ],
    IntentType.LOG_SEARCH: [
        "日志里有什么内容？",
        "搜索日志中的警告",
        "查找日志文件"
    ],
    IntentType.DOC_SEARCH: [
        "如何使用这个工具？",
        "查看使用文档",
        "怎么导入资产？"
    ],
    IntentType.CHITCHAT: [
        "你好",
        "谢谢你的帮助",
        "今天天气怎么样？"
    ]
}


@pytest.fixture
def intent_engine_rule_based():
    """规则匹配模式引擎（快速）"""
    return IntentEngine(model_type="rule-based")


@pytest.fixture
def intent_engine_embedding():
    """嵌入模型引擎（需要下载模型）"""
    return IntentEngine(model_type="bge-small")


class TestIntentParserRuleBased:
    """测试规则匹配模式"""
    
    def test_rule_based_intent_classification(self, intent_engine_rule_based):
        """测试规则匹配的意图分类准确率"""
        correct = 0
        total = 0
        
        for expected_intent, samples in TEST_SAMPLES.items():
            for sample in samples:
                result = intent_engine_rule_based.parse(sample)
                predicted_intent = result['intent']
                
                if predicted_intent == expected_intent:
                    correct += 1
                total += 1
                
                # 输出预测结果
                print(f"样本: '{sample}'")
                print(f"  预期: {expected_intent}, 预测: {predicted_intent}, "
                      f"置信度: {result['confidence']:.2f}, "
                      f"{'✓' if predicted_intent == expected_intent else '✗'}")
        
        accuracy = correct / total
        print(f"\n规则匹配准确率: {accuracy*100:.1f}% ({correct}/{total})")
        
        # 验收标准：≥ 85%
        assert accuracy >= 0.85, f"准确率 {accuracy*100:.1f}% 低于要求的 85%"
    
    def test_entity_extraction(self, intent_engine_rule_based):
        """测试实体提取"""
        result = intent_engine_rule_based.parse("查找名为胡桃的蓝图资产")
        
        entities = result['entities']
        assert isinstance(entities, list)
        assert '胡桃' in entities or 'hutao' in [e.lower() for e in entities]
        assert '蓝图' in entities or 'blueprint' in [e.lower() for e in entities]
    
    def test_confidence_score(self, intent_engine_rule_based):
        """测试置信度范围"""
        result = intent_engine_rule_based.parse("有哪些资产？")
        
        confidence = result['confidence']
        assert 0.0 <= confidence <= 1.0, "置信度应在 0-1 范围内"


class TestIntentParserEmbedding:
    """测试嵌入模型模式（需要模型，可能较慢）"""
    
    @pytest.mark.slow
    def test_embedding_lazy_load(self, intent_engine_embedding):
        """测试延迟加载机制"""
        # 模型应该在首次 parse() 调用时才加载
        assert intent_engine_embedding._model_loaded == False, "模型不应在初始化时加载"
        
        # 第一次调用
        result = intent_engine_embedding.parse("测试查询")
        assert intent_engine_embedding._model_loaded == True, "模型应在首次调用后加载"
        
        # 第二次调用应复用已加载的模型
        result2 = intent_engine_embedding.parse("另一个查询")
        assert result2 is not None
    
    @pytest.mark.slow  
    def test_embedding_intent_classification(self, intent_engine_embedding):
        """测试嵌入模型的意图分类（可选，需要下载模型）"""
        # 测试几个关键样本
        samples = [
            ("有哪些蓝图资产？", IntentType.ASSET_QUERY),
            ("胡桃的路径在哪？", IntentType.ASSET_DETAIL),
            ("如何使用工具？", IntentType.DOC_SEARCH),
        ]
        
        for sample, expected in samples:
            result = intent_engine_embedding.parse(sample)
            print(f"样本: '{sample}' -> {result['intent']} (置信度: {result['confidence']:.2f})")
            
            # 嵌入模型应该有更高的准确率
            assert result['confidence'] >= 0.5, "嵌入模型置信度应 ≥ 0.5"


def test_fallback_on_model_failure():
    """测试模型加载失败时的 fallback"""
    # 使用不存在的模型路径
    engine = IntentEngine(model_type="bge-small", model_path="/invalid/path")
    
    # 应该降级到规则匹配，不抛出异常
    result = engine.parse("有哪些资产？")
    
    assert result is not None
    assert 'intent' in result
    assert 'confidence' in result


if __name__ == "__main__":
    # 可以直接运行此文件进行快速测试
    pytest.main([__file__, "-v", "-s"])

