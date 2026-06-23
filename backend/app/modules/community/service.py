from app.modules.community.schema import CommunityTestData


def get_test_data() -> CommunityTestData:
    return CommunityTestData(module="community", description="社区模块基础接口占位")
