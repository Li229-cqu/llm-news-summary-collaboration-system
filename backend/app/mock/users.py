"""第 4 阶段用户与权限 Mock 数据。"""

MOCK_USERS = [
    {
        "id": 1,
        "username": "user",
        "password": "123456",
        "role": "user",
        "nickname": "普通用户",
        "avatar": "",
        "status": 1,
        "token": "mock-token-user",
    },
    {
        "id": 2,
        "username": "editor",
        "password": "123456",
        "role": "editor",
        "nickname": "审核编辑",
        "avatar": "",
        "status": 1,
        "token": "mock-token-editor",
    },
    {
        "id": 3,
        "username": "admin",
        "password": "123456",
        "role": "admin",
        "nickname": "系统管理员",
        "avatar": "",
        "status": 1,
        "token": "mock-token-admin",
    },
]
