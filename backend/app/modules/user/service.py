from app.modules.user.schema import UserTestData


def get_test_data() -> UserTestData:
    return UserTestData(module="user", description="用户模块基础接口占位")
