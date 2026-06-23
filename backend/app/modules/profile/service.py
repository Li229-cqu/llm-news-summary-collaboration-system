from app.modules.profile.schema import ProfileTestData


def get_test_data() -> ProfileTestData:
    return ProfileTestData(module="profile", description="个人中心模块基础接口占位")
