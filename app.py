# 房源文案生成器 - 网页版 v2(按金姐个人号反馈改版)
import json

import streamlit as st
from openai import OpenAI

# key: 云端从 Secrets 读, 本地用环境变量
try:
    _api_key = st.secrets["OPENAI_API_KEY"]
except Exception:
    _api_key = None
client = OpenAI(api_key=_api_key) if _api_key else OpenAI()

# 访问口令: 云端在 Secrets 里设了 APP_PASSWORD 才生效, 本地自动跳过
try:
    _app_pw = st.secrets["APP_PASSWORD"]
except Exception:
    _app_pw = None
if _app_pw:
    _input_pw = st.text_input("请输入访问口令", type="password")
    if _input_pw != _app_pw:
        st.stop()


def calc_saving(house):
    standard = (house["price_jpy"] * 0.03 + 60000) * 1.1
    return int(round(standard)) - house["brokerage_fee_jpy"]


def generate(house):
    prompt = (
        "你是给在日外国人家庭写小红书卖房文案的助手。文案是经纪人金姐的个人账号发的, 全程用第一人称'我'说话, 不要用'我们''团队'。"
        "我的优势(写文案时自然带出1到2点即可, 不要整段罗列): 我主营自社物件, 自家公司盖的房子由我直接卖, 没有中间环节; "
        "我合作的银行和贷款渠道多, 熟悉各家银行对外国人申请房贷的审查口径; 我会中文、日语、韩语, 熟悉在日外国人买房的手续流程, 全程陪着走完。"
        "规则: 1)正文和封面里禁止出现具体金额数字, 省下的中介费只许填进 brokerage_saving_jpy 字段, 正文里用'省出一笔装修费'这类感觉型表达; "
        "2)只能使用房源信息里给出的事实, 禁止编造或改写房源属性, 卖点只能围绕 selling_points 展开, 交通按 stations 里给的车站和步行分钟写, 不要出现'自有产权''所有权'这类解释交易形态的字眼; "
        "3)标题、正文、封面、标签全部用中文, 卖点里有日文词也要翻译成中文说法; "
        "4)正文要排版成可以直接复制发布的小红书笔记: 分小段, 段与段之间空一行, 每段开头带一个贴切的emoji(如🏠📍🚗✨💡), emoji 适量不要满屏; 正文长度 350 到 480 字, 每个卖点都展开写细节和居住感受, 不要一句话带过;  "
        "5)标签要大小范围结合, 一共给 6 到 9 个: 其中 2 到 3 个用大范围搜索词(如东京买房、东京一户建、日本买房、自社物件), 其余用本地词(地区名、在日生活等); 禁止把户型(3LDK)、建成年月、参数术语放进标签; 每个标签以 # 开头; "
        "6)文案里禁止出现任何中介费的数字、百分比, 也不许写免中介费这类费用说法; 只按房源的 property_type 自然标明这是自社物件还是提携物件, 不解释含义, 让读者来私信问; "
        "7)标题可以带'东京通勤圈''东京周边'这类大词扩大曝光, 但不能谎称房子在东京; "
        "8)标题里必须出现物件类型词: 是自社物件就写自社物件, 是提携物件就写提携物件, 放在标题前半段显眼的位置。"
        "只返回一个 JSON 对象, 不要返回任何解释文字, 字段如下:\n"
        '{"title": "标题, 带钩子, 不超过20字", '
        '"body": "中文正文, 已排版好, 带换行和 emoji, 可直接复制发布", '
        '"body_ja": "日文版正文", '
        '"hashtags": ["话题标签数组"], '
        '"cover_text": "封面大字, 不超过10字", '
        '"brokerage_saving_jpy": 中介费省下的金额(数字)}'
        f"\n房源信息: {json.dumps(house, ensure_ascii=False)}"
    )
    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    data = json.loads(response.choices[0].message.content)
    data["brokerage_saving_jpy"] = calc_saving(house)
    return data


st.title("🏠 房源文案生成器")
st.caption("填房源信息, 一键生成小红书文案")

area = st.text_input("区域", value="蕨市塚越")
col1, col2 = st.columns(2)
with col1:
    station1 = st.text_input("车站1", value="西川口")
    walk1 = st.number_input("车站1步行分钟", min_value=0, max_value=60, value=12)
    station2 = st.text_input("车站2(没有就留空)", value="")
    walk2 = st.number_input("车站2步行分钟", min_value=0, max_value=60, value=0)
with col2:
    layout = st.selectbox("户型", ["2LDK", "3LDK", "4LDK", "5LDK"], index=1)
    orientation = st.selectbox("朝向", ["不填", "南向", "东南向", "西南向", "东向", "西向", "北向"])
    price = st.number_input("售价(日元)", min_value=0, value=41980000, step=100000)
    template = st.selectbox("模板", ["省钱对比型", "房源速递型", "生活型", "流程科普型"])

prop_type = st.selectbox("物件类型", ["自社物件", "提携物件"])
if prop_type == "自社物件":
    fee_pct = 0.0
    st.info("自社物件: 中介费 0%")
else:
    fee_pct = st.number_input("中介费率(%)", min_value=0.0, max_value=3.0, value=1.0, step=0.1)

points_text = st.text_area("卖点(每行一个)", value="2026年11月新建\n三层建, 空间分区灵活")

if st.button("✨ 生成文案", type="primary"):
    stations = [{"name": station1, "walk_min": int(walk1)}]
    if station2.strip():
        stations.append({"name": station2, "walk_min": int(walk2)})
    fee_jpy = int(int(price) * fee_pct / 100)
    house = {
        "area": area,
        "stations": stations,
        "layout": layout,
        "price_jpy": int(price),
        "property_type": prop_type,
        "brokerage_fee_percent": fee_pct,
        "brokerage_fee_jpy": fee_jpy,
        "selling_points": [p.strip() for p in points_text.splitlines() if p.strip()],
        "template_type": template,
    }
    if orientation != "不填":
        house["orientation"] = orientation
    with st.spinner("正在生成..."):
        data = generate(house)
    st.subheader(data["title"])
    st.write(f"封面大字: **{data['cover_text']}**")
    st.text_area("正文(全选复制, 可直接发小红书)", value=data["body"], height=320)
    st.write(" ".join(data["hashtags"]))
    st.metric("中介费差额(内部参考, 不要写进文案)", f"{data['brokerage_saving_jpy']:,} 日元")
    with st.expander("日文版正文"):
        st.write(data["body_ja"])
