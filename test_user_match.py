# -*- coding: utf-8 -*-
import httpx
import json

# 测试用户匹配问题
print("=== 测试用户匹配问题 ===")

# 登录获取 token
login_response = httpx.post(
    "http://127.0.0.1:8000/api/auth/login",
    json={"username": "user", "password": "123456"},
    timeout=30.0
)
login_result = login_response.json()

if login_result.get("code") != 200:
    print(f"登录失败: {login_result}")
    exit(1)

token = login_result.get("data", {}).get("token")
headers = {"Authorization": f"Bearer {token}"}

# 获取用户信息
user_response = httpx.get("http://127.0.0.1:8000/api/auth/me", headers=headers, timeout=30.0)
user_result = user_response.json()
if user_result.get("code") == 200:
    user_info = user_result.get("data", {})
    print(f"当前登录用户: {user_info.get('username')}, ID: {user_info.get('id')}")

# 获取列表（带认证）
list_response = httpx.get("http://127.0.0.1:8000/api/ai/records", headers=headers, timeout=30.0)
list_result = list_response.json()

if list_result.get("code") == 200:
    records = list_result.get("data", {}).get("records", [])
    print(f"\n带认证找到 {len(records)} 条记录")
    
    # 获取列表（不带认证）
    no_auth_list_response = httpx.get("http://127.0.0.1:8000/api/ai/records", timeout=30.0)
    no_auth_list_result = no_auth_list_response.json()
    
    if no_auth_list_result.get("code") == 200:
        no_auth_records = no_auth_list_result.get("data", {}).get("records", [])
        print(f"不带认证找到 {len(no_auth_records)} 条记录")
        
        # 对比两个列表
        auth_ids = set(r["id"] for r in records)
        no_auth_ids = set(r["id"] for r in no_auth_records)
        
        print(f"\n带认证记录 ID: {auth_ids}")
        print(f"不带认证记录 ID: {no_auth_ids}")
        
        if auth_ids == no_auth_ids:
            print("✅ 两个列表相同")
        else:
            print(f"⚠️ 两个列表不同")
            print(f"   带认证有但不带认证没有: {auth_ids - no_auth_ids}")
            print(f"   不带认证有但带认证没有: {no_auth_ids - auth_ids}")
            
            # 测试获取不在带认证列表中的记录
            missing_ids = no_auth_ids - auth_ids
            for record_id in missing_ids:
                print(f"\n--- 尝试获取记录 ID: {record_id} ---")
                detail_response = httpx.get(f"http://127.0.0.1:8000/api/ai/records/{record_id}", headers=headers, timeout=30.0)
                detail_result = detail_response.json()
                
                if detail_result.get("code") == 200:
                    print("✅ 获取详情成功")
                else:
                    print(f"❌ 获取详情失败: {detail_result.get('message')}")
                    
                    # 尝试不带认证获取
                    no_auth_detail_response = httpx.get(f"http://127.0.0.1:8000/api/ai/records/{record_id}", timeout=30.0)
                    no_auth_detail_result = no_auth_detail_response.json()
                    
                    if no_auth_detail_result.get("code") == 200:
                        print("✅ 不带认证获取详情成功")
                    else:
                        print(f"❌ 不带认证获取详情也失败: {no_auth_detail_result.get('message')}")
