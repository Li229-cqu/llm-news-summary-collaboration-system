from app.modules.admin.schema import AdminTestData


def get_test_data() -> AdminTestData:
    return AdminTestData(module="admin", description="管理后台模块基础接口占位")
