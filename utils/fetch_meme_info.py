#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import json
import yaml
from pathlib import Path

import httpx

MEME_API_URL = "http://127.0.0.1:2233"
OUTPUT_FILE = Path(__file__).parent.parent / "data" / "memes_info.yaml"


async def fetch_all_meme_keys():
    """获取所有表情包的key"""
    url = f"{MEME_API_URL}/memes/keys"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.json()


async def fetch_meme_info(key):
    """获取单个表情包的详细信息"""
    url = f"{MEME_API_URL}/memes/{key}/info"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.json()


async def main():
    """主函数：获取所有表情包信息并保存到yaml文件（key一级格式）"""
    try:
        # 确保输出目录存在
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # 获取所有表情包的key
        print("正在获取所有表情包的key...")
        meme_keys = await fetch_all_meme_keys()
        print(f"共获取到 {len(meme_keys)} 个表情包的key")
        
        # 获取每个表情包的详细信息并构建key一级格式的字典
        memes_info_dict = {}
        for i, key in enumerate(meme_keys, 1):
            print(f"正在获取表情包信息 ({i}/{len(meme_keys)}): {key}")
            try:
                meme_info = await fetch_meme_info(key)
                # 创建一个新字典，不包含key字段（如果存在）
                if 'key' in meme_info:
                    del meme_info['key']
                # 将信息保存到字典中，key作为顶级键
                memes_info_dict[key] = meme_info
            except Exception as e:
                print(f"获取表情包 {key} 信息失败: {str(e)}")
        
        # 保存到yaml文件（key一级格式）
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            yaml.dump(memes_info_dict, f, allow_unicode=True, default_flow_style=False)
        
        print(f"表情包信息已保存到: {OUTPUT_FILE}")
        print(f"成功获取了 {len(memes_info_dict)} 个表情包的详细信息")
        
    except Exception as e:
        print(f"发生错误: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())