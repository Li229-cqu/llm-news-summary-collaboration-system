from app.modules.news.schema import NewsTestData


def get_test_data() -> NewsTestData:
    return NewsTestData(module="news", description="新闻模块基础接口占位")
