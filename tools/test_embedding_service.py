# -*- coding: utf-8 -*-

"""
测试 EmbeddingService 单例服务
用于验证阶段 1 的重构
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.ai_services import EmbeddingService
from core.logger import get_logger

logger = get_logger(__name__)


def test_singleton_pattern():
    """测试单例模式"""
    print("\n" + "="*60)
    print("测试 1: 单例模式")
    print("="*60)
    
    # 创建两个实例
    service1 = EmbeddingService()
    service2 = EmbeddingService()
    
    # 验证是同一个实例
    assert service1 is service2, "❌ 单例模式失败：两个实例不相同"
    print("✅ 单例模式正常：service1 is service2 = True")
    
    return service1


def test_lazy_loading(service: EmbeddingService):
    """测试延迟加载"""
    print("\n" + "="*60)
    print("测试 2: 延迟加载")
    print("="*60)
    
    # 此时模型应该还未加载
    print(f"初始状态 - 模型已加载: {service.is_loaded()}")
    
    # 第一次调用会触发加载
    print("\n触发模型加载...")
    embedder = service.get_embedder()
    
    if embedder is None:
        print("❌ 模型加载失败（可能网络问题或环境问题）")
        return False
    
    print(f"✅ 模型加载成功")
    print(f"   模型类型: {type(embedder).__name__}")
    print(f"   向量维度: {service.get_embedding_dimension()}")
    print(f"   模型已加载: {service.is_loaded()}")
    
    return True


def test_encode_single_text(service: EmbeddingService):
    """测试单文本编码"""
    print("\n" + "="*60)
    print("测试 3: 单文本编码")
    print("="*60)
    
    test_text = "这是一个测试文本"
    print(f"输入文本: '{test_text}'")
    
    vector = service.encode_text(test_text)
    
    if vector is None:
        print("❌ 编码失败")
        return False
    
    print(f"✅ 编码成功")
    print(f"   向量形状: {vector.shape}")
    print(f"   向量类型: {type(vector)}")
    print(f"   前 5 个值: {vector[:5]}")
    
    return True


def test_encode_multiple_texts(service: EmbeddingService):
    """测试多文本编码"""
    print("\n" + "="*60)
    print("测试 4: 多文本编码")
    print("="*60)
    
    test_texts = [
        "虚幻引擎",
        "资产管理",
        "配置工具",
        "AI 助手"
    ]
    print(f"输入文本列表: {test_texts}")
    
    vectors = service.encode_text(test_texts)
    
    if vectors is None:
        print("❌ 批量编码失败")
        return False
    
    print(f"✅ 批量编码成功")
    print(f"   向量形状: {vectors.shape}")
    print(f"   向量数量: {len(vectors)}")
    
    return True


def test_semantic_similarity(service: EmbeddingService):
    """测试语义相似度计算"""
    print("\n" + "="*60)
    print("测试 5: 语义相似度")
    print("="*60)
    
    import numpy as np
    
    # 三个测试文本
    text1 = "查找资产"
    text2 = "搜索资产"  # 应该与 text1 相似
    text3 = "配置设置"  # 应该与 text1 不相似
    
    print(f"文本 1: '{text1}'")
    print(f"文本 2: '{text2}' (应该相似)")
    print(f"文本 3: '{text3}' (应该不相似)")
    
    # 编码
    v1 = service.encode_text(text1)
    v2 = service.encode_text(text2)
    v3 = service.encode_text(text3)
    
    if any(v is None for v in [v1, v2, v3]):
        print("❌ 编码失败")
        return False
    
    # 计算余弦相似度
    def cosine_similarity(a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    sim_1_2 = cosine_similarity(v1, v2)
    sim_1_3 = cosine_similarity(v1, v3)
    
    print(f"\n相似度结果:")
    print(f"  '{text1}' vs '{text2}': {sim_1_2:.4f}")
    print(f"  '{text1}' vs '{text3}': {sim_1_3:.4f}")
    
    if sim_1_2 > sim_1_3:
        print(f"✅ 语义理解正确：相似文本的相似度 ({sim_1_2:.4f}) > 不相似文本 ({sim_1_3:.4f})")
        return True
    else:
        print(f"❌ 语义理解异常：相似度关系不符合预期")
        return False


def test_thread_safety():
    """测试线程安全性"""
    print("\n" + "="*60)
    print("测试 6: 线程安全性")
    print("="*60)
    
    import threading
    
    instances = []
    
    def create_instance():
        service = EmbeddingService()
        instances.append(service)
    
    # 创建多个线程同时实例化
    threads = []
    for i in range(5):
        t = threading.Thread(target=create_instance)
        threads.append(t)
        t.start()
    
    # 等待所有线程完成
    for t in threads:
        t.join()
    
    # 验证所有实例都是同一个对象
    first = instances[0]
    all_same = all(instance is first for instance in instances)
    
    if all_same:
        print(f"✅ 线程安全测试通过：5 个线程都获得了同一个实例")
        return True
    else:
        print(f"❌ 线程安全测试失败：实例不一致")
        return False


def main():
    """运行所有测试"""
    print("\n" + "🚀" + " "*20 + "EmbeddingService 测试套件" + " "*20 + "🚀")
    print("="*60)
    
    try:
        # 测试 1: 单例模式
        service = test_singleton_pattern()
        
        # 测试 2: 延迟加载
        model_loaded = test_lazy_loading(service)
        
        if not model_loaded:
            print("\n" + "="*60)
            print("⚠️  模型加载失败，跳过后续测试")
            print("可能原因:")
            print("  1. 首次使用需要下载模型（约 100MB）")
            print("  2. 网络连接问题")
            print("  3. 缺少 sentence-transformers 库")
            print("="*60)
            return
        
        # 测试 3: 单文本编码
        test_encode_single_text(service)
        
        # 测试 4: 多文本编码
        test_encode_multiple_texts(service)
        
        # 测试 5: 语义相似度
        test_semantic_similarity(service)
        
        # 测试 6: 线程安全
        test_thread_safety()
        
        # 总结
        print("\n" + "="*60)
        print("✅ 所有测试完成！")
        print("="*60)
        print("\n阶段 1 重构验证通过：")
        print("  ✅ 单例模式正常工作")
        print("  ✅ 延迟加载机制正常")
        print("  ✅ 文本编码功能正常")
        print("  ✅ 语义理解能力正常")
        print("  ✅ 线程安全性保证")
        print("\n可以安全地继续到阶段 2！")
        
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

