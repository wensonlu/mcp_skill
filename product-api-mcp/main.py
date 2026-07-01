"""
商品列表 API —— 基于 FastAPI，自动生成 Swagger 文档
Nginx 统一 Basic Auth 登录，JWT 用于程序化调用。
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# JWT / 安全配置
# ---------------------------------------------------------------------------

SECRET_KEY = "zcode-product-api-secret-key-2026"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120

security = HTTPBearer(auto_error=False)

import bcrypt as _bcrypt


def _hash_pw(pw: str) -> str:
    return _bcrypt.hashpw(pw.encode(), _bcrypt.gensalt()).decode()


def _verify_pw(pw: str, hashed: str) -> bool:
    return _bcrypt.checkpw(pw.encode(), hashed.encode())


MOCK_USERS = {
    "docs": {
        "username": "docs",
        "password": _hash_pw("YOUR_PASSWORD_HERE"),
        "role": "管理员",
    },
}


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT Token")
    token_type: str = Field(default="bearer", description="Token 类型")
    expires_in: int = Field(..., description="过期时间 (分钟)")


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, description="用户名")
    password: str = Field(..., min_length=1, description="密码")


def create_access_token(data: dict) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {**data, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# ---------------------------------------------------------------------------
# 枚举
# ---------------------------------------------------------------------------


class ProductCategory(str, Enum):
    electronics = "电子产品"
    clothing = "服装"
    food = "食品"
    books = "图书"
    home = "家居"
    beauty = "美妆"
    sports = "运动户外"


# ---------------------------------------------------------------------------
# 数据模型
# ---------------------------------------------------------------------------


class SpecItem(BaseModel):
    """商品规格项"""
    name: str = Field(..., description="规格名称，如 颜色、尺寸")
    value: str = Field(..., description="规格值，如 黑色、XL")


class Product(BaseModel):
    # --- 基础信息 ---
    id: int = Field(..., description="商品唯一编号")
    name: str = Field(..., description="商品名称")
    description: str = Field(default="", description="商品描述")
    category: ProductCategory = Field(..., description="商品分类")

    # --- 价格 ---
    price: float = Field(..., description="当前售价 (元)", ge=0)
    original_price: Optional[float] = Field(None, description="原价 (元)，用于显示折扣", ge=0)
    discount: Optional[float] = Field(None, description="折扣率，如 0.85 表示 85 折", ge=0, le=1)

    # --- 图片 ---
    main_image: str = Field(..., description="主图 URL")
    images: list[str] = Field(default_factory=list, description="商品轮播图列表 (含主图)")

    # --- 品牌与标签 ---
    brand: Optional[str] = Field(None, description="品牌")
    tags: list[str] = Field(default_factory=list, description="商品标签，如 新品、热销、限时优惠")

    # --- 库存与销售 ---
    stock: int = Field(..., description="库存数量", ge=0)
    sales: int = Field(default=0, description="累计销量", ge=0)

    # --- 评分 ---
    rating: float = Field(default=5.0, description="评分 (1-5)", ge=1, le=5)
    review_count: int = Field(default=0, description="评价条数", ge=0)

    # --- 规格 ---
    specifications: list[SpecItem] = Field(default_factory=list, description="商品规格选项")

    # --- 状态标记 ---
    is_new: bool = Field(default=False, description="是否新品")
    is_hot: bool = Field(default=False, description="是否热销")
    is_free_shipping: bool = Field(default=False, description="是否包邮")

    # --- 时间 ---
    created_at: Optional[str] = Field(None, description="上架时间")


class ProductListResponse(BaseModel):
    total: int = Field(..., description="符合条件的商品总数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页条数")
    products: list[Product] = Field(..., description="商品列表")


# ---------------------------------------------------------------------------
# 模拟数据
# ---------------------------------------------------------------------------

IMAGE_BASE = "https://picsum.photos/seed"

MOCK_PRODUCTS: list[Product] = [
    Product(
        id=1,
        name="iPhone 16 Pro Max 256GB",
        description="Apple 最新旗舰手机，搭载 A18 Pro 芯片，6.9 英寸超视网膜 XDR 显示屏，钛金属设计，支持 Apple Intelligence。",
        category="电子产品",
        price=9999.00,
        original_price=10999.00,
        discount=0.91,
        main_image=f"{IMAGE_BASE}/iphone16/800/800",
        images=[
            f"{IMAGE_BASE}/iphone16/800/800",
            f"{IMAGE_BASE}/iphone16-2/800/800",
            f"{IMAGE_BASE}/iphone16-3/800/800",
            f"{IMAGE_BASE}/iphone16-4/800/800",
        ],
        brand="Apple",
        tags=["新品", "热销", "限时优惠"],
        stock=120,
        sales=3580,
        rating=4.8,
        review_count=2156,
        specifications=[
            SpecItem(name="颜色", value="原色钛金属"),
            SpecItem(name="存储", value="256GB"),
        ],
        is_new=True,
        is_hot=True,
        is_free_shipping=True,
        created_at="2026-06-10",
    ),
    Product(
        id=2,
        name="MacBook Air M4 15英寸",
        description="全新 M4 芯片，15.3 英寸 Liquid Retina 显示屏，18 小时续航，轻薄仅 1.24kg。",
        category="电子产品",
        price=12999.00,
        original_price=13999.00,
        discount=0.93,
        main_image=f"{IMAGE_BASE}/macbook-air/800/800",
        images=[
            f"{IMAGE_BASE}/macbook-air/800/800",
            f"{IMAGE_BASE}/macbook-air-2/800/800",
            f"{IMAGE_BASE}/macbook-air-3/800/800",
        ],
        brand="Apple",
        tags=["新品", "热销"],
        stock=65,
        sales=1260,
        rating=4.9,
        review_count=892,
        specifications=[
            SpecItem(name="颜色", value="午夜色"),
            SpecItem(name="内存", value="16GB"),
            SpecItem(name="存储", value="512GB"),
        ],
        is_new=True,
        is_hot=True,
        is_free_shipping=True,
        created_at="2026-06-05",
    ),
    Product(
        id=3,
        name="索尼 WH-1000XM6 降噪耳机",
        description="旗舰级无线降噪耳机，搭载集成处理器 V2，30 小时续航，支持 LDAC 高解析音频。",
        category="电子产品",
        price=2799.00,
        original_price=3299.00,
        discount=0.85,
        main_image=f"{IMAGE_BASE}/sony-headphone/800/800",
        images=[
            f"{IMAGE_BASE}/sony-headphone/800/800",
            f"{IMAGE_BASE}/sony-headphone-2/800/800",
        ],
        brand="Sony",
        tags=["热销", "限时优惠"],
        stock=200,
        sales=5200,
        rating=4.7,
        review_count=3842,
        specifications=[
            SpecItem(name="颜色", value="黑色"),
            SpecItem(name="颜色", value="铂金银"),
        ],
        is_hot=True,
        is_free_shipping=True,
        created_at="2026-05-20",
    ),
    Product(
        id=13,
        name="iPad Pro M4 11英寸",
        description="M4 芯片加持，超 XDR 显示屏，极致轻薄，支持 Apple Pencil Pro，创作与办公利器。",
        category="电子产品",
        price=8499.00,
        original_price=8999.00,
        discount=0.94,
        main_image=f"{IMAGE_BASE}/ipad-pro/800/800",
        images=[
            f"{IMAGE_BASE}/ipad-pro/800/800",
            f"{IMAGE_BASE}/ipad-pro-2/800/800",
            f"{IMAGE_BASE}/ipad-pro-3/800/800",
        ],
        brand="Apple",
        tags=["新品"],
        stock=95,
        sales=780,
        rating=4.7,
        review_count=523,
        specifications=[
            SpecItem(name="颜色", value="银色"),
            SpecItem(name="存储", value="256GB"),
            SpecItem(name="连接", value="Wi-Fi + 蜂窝网络"),
        ],
        is_new=True,
        is_free_shipping=True,
        created_at="2026-06-15",
    ),
    Product(
        id=4,
        name="纯棉简约圆领T恤",
        description="100% 新疆长绒棉，亲肤透气，宽松版型，四季百搭基础款。",
        category="服装",
        price=129.00,
        original_price=199.00,
        discount=0.65,
        main_image=f"{IMAGE_BASE}/cotton-tee/800/800",
        images=[
            f"{IMAGE_BASE}/cotton-tee/800/800",
            f"{IMAGE_BASE}/cotton-tee-2/800/800",
            f"{IMAGE_BASE}/cotton-tee-3/800/800",
        ],
        brand="UNIQLO",
        tags=["热销", "限时优惠"],
        stock=500,
        sales=12800,
        rating=4.3,
        review_count=9800,
        specifications=[
            SpecItem(name="颜色", value="白色"),
            SpecItem(name="颜色", value="黑色"),
            SpecItem(name="颜色", value="灰色"),
            SpecItem(name="尺寸", value="S"),
            SpecItem(name="尺寸", value="M"),
            SpecItem(name="尺寸", value="L"),
            SpecItem(name="尺寸", value="XL"),
        ],
        is_hot=True,
        is_free_shipping=False,
        created_at="2026-04-01",
    ),
    Product(
        id=5,
        name="羊毛混纺双排扣大衣",
        description="70% 澳洲美利奴羊毛混纺，内衬保暖层，版型挺括，通勤与休闲兼得。",
        category="服装",
        price=1299.00,
        original_price=1899.00,
        discount=0.68,
        main_image=f"{IMAGE_BASE}/wool-coat/800/800",
        images=[
            f"{IMAGE_BASE}/wool-coat/800/800",
            f"{IMAGE_BASE}/wool-coat-2/800/800",
            f"{IMAGE_BASE}/wool-coat-3/800/800",
        ],
        brand="Massimo Dutti",
        tags=["新品", "限量"],
        stock=80,
        sales=450,
        rating=4.6,
        review_count=312,
        specifications=[
            SpecItem(name="颜色", value="驼色"),
            SpecItem(name="颜色", value="黑色"),
            SpecItem(name="尺寸", value="M"),
            SpecItem(name="尺寸", value="L"),
            SpecItem(name="尺寸", value="XL"),
        ],
        is_new=True,
        is_free_shipping=True,
        created_at="2026-06-12",
    ),
    Product(
        id=6,
        name="Air Max 缓震跑鞋",
        description="全掌 Air Max 气垫，Flyknit 飞织鞋面，回弹缓震，适合日常跑步与健身。",
        category="服装",
        price=899.00,
        original_price=1199.00,
        discount=0.75,
        main_image=f"{IMAGE_BASE}/running-shoe/800/800",
        images=[
            f"{IMAGE_BASE}/running-shoe/800/800",
            f"{IMAGE_BASE}/running-shoe-2/800/800",
            f"{IMAGE_BASE}/running-shoe-3/800/800",
        ],
        brand="Nike",
        tags=["热销"],
        stock=150,
        sales=6800,
        rating=4.5,
        review_count=4210,
        specifications=[
            SpecItem(name="颜色", value="黑白"),
            SpecItem(name="颜色", value="蓝白"),
            SpecItem(name="尺码", value="39"),
            SpecItem(name="尺码", value="40"),
            SpecItem(name="尺码", value="41"),
            SpecItem(name="尺码", value="42"),
            SpecItem(name="尺码", value="43"),
        ],
        is_hot=True,
        is_free_shipping=True,
        created_at="2026-05-10",
    ),
    Product(
        id=14,
        name="真丝印花连衣裙",
        description="100% 桑蚕丝面料，数码印花工艺，收腰 A 字裙摆，优雅气质之选。",
        category="服装",
        price=1699.00,
        original_price=2299.00,
        discount=0.74,
        main_image=f"{IMAGE_BASE}/silk-dress/800/800",
        images=[
            f"{IMAGE_BASE}/silk-dress/800/800",
            f"{IMAGE_BASE}/silk-dress-2/800/800",
            f"{IMAGE_BASE}/silk-dress-3/800/800",
        ],
        brand="Self-Portrait",
        tags=["新品", "限量"],
        stock=40,
        sales=180,
        rating=4.8,
        review_count=92,
        specifications=[
            SpecItem(name="颜色", value="碎花"),
            SpecItem(name="尺寸", value="S"),
            SpecItem(name="尺寸", value="M"),
            SpecItem(name="尺寸", value="L"),
        ],
        is_new=True,
        is_free_shipping=True,
        created_at="2026-06-18",
    ),
    Product(
        id=7,
        name="每日坚果混合礼盒 750g",
        description="6 种坚果果干科学配比：腰果、巴旦木、核桃、榛子、蔓越莓、蓝莓，每日一包。",
        category="食品",
        price=158.00,
        original_price=198.00,
        discount=0.80,
        main_image=f"{IMAGE_BASE}/nuts/800/800",
        images=[
            f"{IMAGE_BASE}/nuts/800/800",
            f"{IMAGE_BASE}/nuts-2/800/800",
        ],
        brand="沃隆",
        tags=["热销"],
        stock=300,
        sales=15200,
        rating=4.4,
        review_count=11200,
        specifications=[
            SpecItem(name="规格", value="750g (30包)"),
            SpecItem(name="规格", value="1.5kg (60包)"),
        ],
        is_hot=True,
        is_free_shipping=True,
        created_at="2026-03-15",
    ),
    Product(
        id=8,
        name="哥伦比亚精品咖啡豆 250g",
        description="单品产区：慧兰，水洗处理法，中度烘焙，风味：焦糖、坚果、巧克力余韵。",
        category="食品",
        price=128.00,
        original_price=168.00,
        discount=0.76,
        main_image=f"{IMAGE_BASE}/coffee-bean/800/800",
        images=[
            f"{IMAGE_BASE}/coffee-bean/800/800",
            f"{IMAGE_BASE}/coffee-bean-2/800/800",
        ],
        brand="星巴克",
        tags=["精选"],
        stock=90,
        sales=3200,
        rating=4.7,
        review_count=2150,
        specifications=[
            SpecItem(name="烘焙程度", value="中度烘焙"),
            SpecItem(name="研磨度", value="咖啡豆 (需研磨)"),
            SpecItem(name="研磨度", value="法压壶专用粉"),
        ],
        is_free_shipping=True,
        created_at="2026-05-01",
    ),
    Product(
        id=15,
        name="比利时黑巧克力礼盒 72%",
        description="精选西非可可豆，72% 可可含量，口感醇厚微苦，铁盒装送礼佳品。",
        category="食品",
        price=118.00,
        original_price=148.00,
        discount=0.80,
        main_image=f"{IMAGE_BASE}/chocolate/800/800",
        images=[
            f"{IMAGE_BASE}/chocolate/800/800",
            f"{IMAGE_BASE}/chocolate-2/800/800",
        ],
        brand="Godiva",
        tags=["礼盒", "热销"],
        stock=350,
        sales=8900,
        rating=4.3,
        review_count=6540,
        specifications=[
            SpecItem(name="规格", value="礼盒装 200g"),
            SpecItem(name="规格", value="礼盒装 400g"),
        ],
        is_hot=True,
        is_free_shipping=True,
        created_at="2026-04-20",
    ),
    Product(
        id=9,
        name="Python 从入门到实践（第4版）",
        description="全球畅销 Python 入门书，累计销量超 300 万册。从基础语法到项目实战，一步到位。",
        category="图书",
        price=89.00,
        original_price=119.00,
        discount=0.75,
        main_image=f"{IMAGE_BASE}/python-book/800/800",
        images=[
            f"{IMAGE_BASE}/python-book/800/800",
            f"{IMAGE_BASE}/python-book-2/800/800",
        ],
        brand="人民邮电出版社",
        tags=["热销", "经典"],
        stock=400,
        sales=25600,
        rating=4.8,
        review_count=18300,
        specifications=[],
        is_hot=True,
        is_free_shipping=True,
        created_at="2025-12-01",
    ),
    Product(
        id=10,
        name="设计模式：可复用面向对象软件的基础",
        description="GoF 经典之作，四位作者合著，讲解 23 种设计模式，软件开发人员必读。",
        category="图书",
        price=69.00,
        main_image=f"{IMAGE_BASE}/design-pattern/800/800",
        images=[
            f"{IMAGE_BASE}/design-pattern/800/800",
        ],
        brand="机械工业出版社",
        tags=["经典"],
        stock=250,
        sales=12000,
        rating=4.6,
        review_count=9200,
        specifications=[],
        is_free_shipping=True,
        created_at="2024-06-01",
    ),
    Product(
        id=11,
        name="智能护眼台灯 Pro",
        description="Ra>95 高显色，无频闪，色温 3000K-5000K 可调，支持智能感光。",
        category="家居",
        price=399.00,
        original_price=499.00,
        discount=0.80,
        main_image=f"{IMAGE_BASE}/desk-lamp/800/800",
        images=[
            f"{IMAGE_BASE}/desk-lamp/800/800",
            f"{IMAGE_BASE}/desk-lamp-2/800/800",
            f"{IMAGE_BASE}/desk-lamp-3/800/800",
        ],
        brand="小米",
        tags=["热销", "智能"],
        stock=180,
        sales=7600,
        rating=4.2,
        review_count=5400,
        specifications=[
            SpecItem(name="颜色", value="白色"),
            SpecItem(name="颜色", value="灰色"),
        ],
        is_hot=True,
        is_free_shipping=True,
        created_at="2026-05-15",
    ),
    Product(
        id=12,
        name="记忆棉人体工学护颈枕",
        description="慢回弹记忆棉内芯，曲面工学设计，贴合颈椎曲线，改善睡眠质量。",
        category="家居",
        price=239.00,
        original_price=299.00,
        discount=0.80,
        main_image=f"{IMAGE_BASE}/neck-pillow/800/800",
        images=[
            f"{IMAGE_BASE}/neck-pillow/800/800",
            f"{IMAGE_BASE}/neck-pillow-2/800/800",
        ],
        brand="泰普尔",
        tags=["精选"],
        stock=220,
        sales=4300,
        rating=4.5,
        review_count=3100,
        specifications=[
            SpecItem(name="高度", value="低枕 8cm"),
            SpecItem(name="高度", value="中枕 10cm"),
            SpecItem(name="高度", value="高枕 12cm"),
        ],
        is_free_shipping=True,
        created_at="2026-04-10",
    ),
    Product(
        id=16,
        name="小黑瓶精华肌底液 50ml",
        description="第二代小黑瓶，微生态科技，修复肌肤屏障，维稳透亮，全球每 2 秒售出一瓶。",
        category="美妆",
        price=1080.00,
        original_price=1280.00,
        discount=0.84,
        main_image=f"{IMAGE_BASE}/serum/800/800",
        images=[
            f"{IMAGE_BASE}/serum/800/800",
            f"{IMAGE_BASE}/serum-2/800/800",
            f"{IMAGE_BASE}/serum-3/800/800",
        ],
        brand="兰蔻",
        tags=["热销", "经典"],
        stock=85,
        sales=12500,
        rating=4.9,
        review_count=9800,
        specifications=[
            SpecItem(name="容量", value="30ml"),
            SpecItem(name="容量", value="50ml"),
            SpecItem(name="容量", value="100ml"),
        ],
        is_hot=True,
        is_free_shipping=True,
        created_at="2026-01-10",
    ),
    Product(
        id=17,
        name="哑光丝绒唇釉 #888",
        description="丝绒哑光质地，一抹显色，不拔干，持久 12 小时。热门色号 888 枫糖红棕。",
        category="美妆",
        price=268.00,
        main_image=f"{IMAGE_BASE}/lipstick/800/800",
        images=[
            f"{IMAGE_BASE}/lipstick/800/800",
            f"{IMAGE_BASE}/lipstick-2/800/800",
        ],
        brand="MAC",
        tags=["新品", "热销"],
        stock=320,
        sales=6800,
        rating=4.6,
        review_count=4800,
        specifications=[
            SpecItem(name="色号", value="#888 枫糖红棕"),
            SpecItem(name="色号", value="#666 蜜桃粉"),
            SpecItem(name="色号", value="#999 正红色"),
        ],
        is_new=True,
        is_hot=True,
        is_free_shipping=False,
        created_at="2026-06-20",
    ),
    Product(
        id=18,
        name="瑜伽垫 TPE 加厚 6mm",
        description="环保 TPE 材质，双面防滑，6mm 加厚缓冲，附赠收纳绑带和背包。",
        category="运动户外",
        price=199.00,
        original_price=259.00,
        discount=0.77,
        main_image=f"{IMAGE_BASE}/yoga-mat/800/800",
        images=[
            f"{IMAGE_BASE}/yoga-mat/800/800",
            f"{IMAGE_BASE}/yoga-mat-2/800/800",
        ],
        brand="Lululemon",
        tags=["热销"],
        stock=260,
        sales=9200,
        rating=4.4,
        review_count=7100,
        specifications=[
            SpecItem(name="颜色", value="紫色"),
            SpecItem(name="颜色", value="蓝色"),
            SpecItem(name="颜色", value="粉色"),
            SpecItem(name="厚度", value="6mm"),
            SpecItem(name="厚度", value="8mm"),
        ],
        is_hot=True,
        is_free_shipping=True,
        created_at="2026-05-01",
    ),
    Product(
        id=19,
        name="户外登山双肩包 40L",
        description="考度拉面料，防泼水，人体工学背负系统，多仓收纳，适合 3-5 天徒步。",
        category="运动户外",
        price=599.00,
        original_price=799.00,
        discount=0.75,
        main_image=f"{IMAGE_BASE}/backpack/800/800",
        images=[
            f"{IMAGE_BASE}/backpack/800/800",
            f"{IMAGE_BASE}/backpack-2/800/800",
            f"{IMAGE_BASE}/backpack-3/800/800",
        ],
        brand="The North Face",
        tags=["精选", "限时优惠"],
        stock=110,
        sales=2100,
        rating=4.7,
        review_count=1350,
        specifications=[
            SpecItem(name="颜色", value="黑色"),
            SpecItem(name="颜色", value="军绿色"),
            SpecItem(name="容量", value="40L"),
            SpecItem(name="容量", value="60L"),
        ],
        is_free_shipping=True,
        created_at="2026-05-25",
    ),
    Product(
        id=20,
        name="智能运动手表 Watch X",
        description="1.5 英寸 AMOLED 屏幕，双频 GPS，心率/血氧/睡眠监测，14 天续航，50 米防水。",
        category="运动户外",
        price=2499.00,
        original_price=2999.00,
        discount=0.83,
        main_image=f"{IMAGE_BASE}/smart-watch/800/800",
        images=[
            f"{IMAGE_BASE}/smart-watch/800/800",
            f"{IMAGE_BASE}/smart-watch-2/800/800",
            f"{IMAGE_BASE}/smart-watch-3/800/800",
        ],
        brand="佳明",
        tags=["新品", "热销"],
        stock=200,
        sales=3400,
        rating=4.8,
        review_count=2100,
        specifications=[
            SpecItem(name="颜色", value="石墨黑"),
            SpecItem(name="颜色", value="霜白色"),
            SpecItem(name="表盘尺寸", value="47mm"),
        ],
        is_new=True,
        is_hot=True,
        is_free_shipping=True,
        created_at="2026-06-08",
    ),
]


# ---------------------------------------------------------------------------
# FastAPI 应用
# ---------------------------------------------------------------------------

app = FastAPI(
    title="商品列表 API",
    description="商品列表查询接口 — Nginx Basic Auth 统一登录。\n\n"
                "**访问所有接口需先登录。**",
    version="2.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# ---------------------------------------------------------------------------
# 公开接口（无需登录）
# ---------------------------------------------------------------------------


@app.post(
    "/auth/login",
    response_model=TokenResponse,
    summary="用户登录（获取 JWT Token）",
    tags=["认证"],
)
async def login(body: LoginRequest):
    """
    用户登录接口，返回 JWT Token。

    | 用户名 | 密码 |
    |--------|------|
    | docs | YOUR_PASSWORD_HERE |

    Token 有效期 **120 分钟**，过期后需重新登录。
    """
    user = MOCK_USERS.get(body.username)
    if not user or not _verify_pw(body.password, user["password"]):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    token = create_access_token({"sub": body.username, "role": user["role"]})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES,
    )


# ---------------------------------------------------------------------------
# 商品接口（Nginx Basic Auth 统一保护，不再单独 JWT 校验）
# ---------------------------------------------------------------------------


@app.get(
    "/products",
    response_model=ProductListResponse,
    summary="获取商品列表",
    tags=["商品"],
)
async def list_products(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页条数"),
    category: Optional[ProductCategory] = Query(None, description="按分类筛选"),
    min_price: Optional[float] = Query(None, ge=0, description="最低价格"),
    max_price: Optional[float] = Query(None, ge=0, description="最高价格"),
    keyword: Optional[str] = Query(None, min_length=1, description="关键词搜索 (名称/描述)"),
    sort_by: Optional[str] = Query(
        None, pattern=r"^(price|rating|stock|sales|created_at)$",
        description="排序字段 (price / rating / stock / sales / created_at)"
    ),
    sort_order: str = Query("asc", pattern=r"^(asc|desc)$", description="升序 asc / 降序 desc"),
    brand: Optional[str] = Query(None, min_length=1, description="按品牌筛选"),
    is_new: Optional[bool] = Query(None, description="是否仅看新品"),
    is_hot: Optional[bool] = Query(None, description="是否仅看热销"),
    tag: Optional[str] = Query(None, min_length=1, description="按标签筛选"),
):
    """
    ## 商品列表查询

    返回分页的商品列表，支持丰富的筛选与排序选项。

    ### 筛选条件
    - **category** — 按商品分类筛选
    - **min_price / max_price** — 价格区间过滤
    - **keyword** — 按名称或描述模糊搜索
    - **brand** — 按品牌筛选
    - **is_new / is_hot** — 新品 / 热销标记
    - **tag** — 按标签筛选

    ### 排序
    - **sort_by** — 可选 price / rating / stock / sales / created_at
    - **sort_order** — asc (升序) 或 desc (降序)

    ### 分页
    - **page** — 页码，从 1 开始
    - **page_size** — 每页条数，默认 10，最大 100
    """
    result = MOCK_PRODUCTS

    if category:
        result = [p for p in result if p.category == category]

    if min_price is not None:
        result = [p for p in result if p.price >= min_price]
    if max_price is not None:
        result = [p for p in result if p.price <= max_price]

    if keyword:
        kw = keyword.lower()
        result = [
            p for p in result
            if kw in p.name.lower()
            or kw in p.description.lower()
            or (p.brand and kw in p.brand.lower())
        ]

    if brand:
        b = brand.lower()
        result = [p for p in result if p.brand and b in p.brand.lower()]

    if is_new is not None:
        result = [p for p in result if p.is_new == is_new]
    if is_hot is not None:
        result = [p for p in result if p.is_hot == is_hot]

    if tag:
        t = tag.lower()
        result = [p for p in result if any(t in tg.lower() for tg in p.tags)]

    if sort_by:
        reverse = sort_order == "desc"
        result = sorted(result, key=lambda p: getattr(p, sort_by), reverse=reverse)

    total = len(result)
    start = (page - 1) * page_size
    end = start + page_size
    page_items = result[start:end]

    return ProductListResponse(
        total=total,
        page=page,
        page_size=page_size,
        products=page_items,
    )


@app.get(
    "/products/{product_id}",
    response_model=Product,
    summary="获取商品详情",
    tags=["商品"],
)
async def get_product(product_id: int):
    """根据商品 ID 获取单个商品的详细信息。"""
    for p in MOCK_PRODUCTS:
        if p.id == product_id:
            return p
    raise HTTPException(status_code=404, detail="商品不存在")


@app.get("/", include_in_schema=False)
async def root():
    return {
        "message": "商品列表 API — 需登录访问",
        "login": "统一账号 docs / YOUR_PASSWORD_HERE",
        "urls": {
            "docs":        "http://YOUR_SERVER_IP/docs          Swagger UI",
            "products":    "http://YOUR_SERVER_IP/api/products   商品列表",
            "login_api":   "http://YOUR_SERVER_IP/api/auth/login JWT 登录",
        },
    }
