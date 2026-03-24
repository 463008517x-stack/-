import streamlit as st
import os
from dotenv import load_dotenv
from openai import OpenAI
import requests
import io
from PIL import Image

# 1. 打开保险箱，拿出钥匙
load_dotenv()
DS_KEY = os.getenv("DEEPSEEK_API_KEY")
ZP_KEY = os.getenv("ZHIPU_API_KEY")
TIANAPI_KEY = os.getenv("TIANAPI_KEY")

# 2. 聘请大神团队
ds_client = OpenAI(api_key=DS_KEY, base_url="https://api.deepseek.com")
zp_client = OpenAI(api_key=ZP_KEY, base_url="https://open.bigmodel.cn/api/paas/v4/")

# 3. 设置网页颜值 
st.set_page_config(page_title="小红书 AI 运营智能体矩阵 (商业版)", page_icon="💎", layout="wide")

# 稳定器（自动裁剪去水印）
def download_and_crop_image(url):
    try:
        response = requests.get(url, timeout=30, proxies={"http": None, "https": None}, verify=False)
        if response.status_code == 200:
            img = Image.open(io.BytesIO(response.content))
            width, height = img.size
            img_cropped = img.crop((0, 0, width, height - int(height * 0.06)))
            output = io.BytesIO()
            img_cropped.save(output, format="PNG") 
            return output
        return None
    except Exception:
        return None

# ==========================================
# 💎 核心中控台：左侧导航侧边栏
# ==========================================
st.sidebar.title("💎 创作者 SaaS 总控台")
st.sidebar.markdown("欢迎主理人！请调用您的专属 AI 团队：")

agent_mode = st.sidebar.radio(
    "👇 切换工作流",
    [
        "✨ 部门一：爆款图文克隆机", 
        "📅 部门二：7天内容日历规划师",
        "🎬 部门三：爆款短视频分镜编剧",
        "🗣️ 部门四：高情商引流客服中控",
        "📚 部门五：小说/干货图文拆解大师"
    ]
)

st.sidebar.markdown("---")
st.sidebar.markdown("🚀 *系统版本：V3.0 商业全能版*")
st.sidebar.markdown("💡 *未来升级方向：接入会员充值与算力扣除系统*")


# ==========================================
# 🚀 部门一：爆款图文克隆机
# ==========================================
if agent_mode == "✨ 部门一：爆款图文克隆机":
    st.title("🧬 小红书爆款全自动克隆机")
    st.markdown("甩进一个链接，AI 自动帮你扒内容、学语气、换卖点、配 **无水印** 绝美图片！")

    xhs_link = st.text_input("🔗 粘贴你要参考的网页/对标链接：")
    target_topic = st.text_area("🎯 你想把爆款套用在什么产品/卖点上？：", value="高端spa馆抗衰老面部提升项目", height=100)

    if st.button("🚀 一键克隆无水印图文"):
        if not DS_KEY or not ZP_KEY or not TIANAPI_KEY:
            st.error("⚠️ 钥匙没配齐！")
            st.stop()
            
        text_area = st.container()
        image_area = st.container()

        extracted_text = ""
        if xhs_link.strip():
            with st.spinner("🕵️‍♂️ 强行直连读取链接内容..."):
                try:
                    response = requests.post("https://apis.tianapi.com/htmltext/index", data={'key': TIANAPI_KEY, 'url': xhs_link}, headers={'Content-type': 'application/x-www-form-urlencoded'}, proxies={"http": None, "https": None}, verify=False)
                    result = response.json()
                    if result.get('code') == 200:
                        extracted_text = f"【标题】：{result['result'].get('title', '')}\n【正文】：{result['result'].get('content', '')}"
                        st.toast("✅ 提取成功！")
                    else:
                        st.error("⚠️ 链接提取失败。")
                        st.stop()
                except Exception as e:
                    st.error(f"❌ 失败：{e}")
                    st.stop()

        with st.spinner("🧠 仿写中..."):
            try:
                sys_prompt = f"你是一个爆款仿写专家。参考笔记：\n{extracted_text}\n套用到：'{target_topic}'。包含分割线 ---。格式：【标题】\n【正文】\n【标签】\n---\n【画图指令】(英文)" if extracted_text else "你是一个操盘手。生成笔记。包含分割线 ---。格式：【标题】\n【正文】\n【标签】\n---\n【画图指令】(英文)"
                response = ds_client.chat.completions.create(model="deepseek-chat", messages=[{"role": "system", "content": sys_prompt}], temperature=0.7)
                full_text = response.choices[0].message.content
                
                text_part, ds_image_prompt = full_text.split("---", 1) if "---" in full_text else (full_text, "A aesthetic photo, high quality")
                ds_image_prompt = ds_image_prompt.replace("【画图指令】", "").replace("：", "").strip()
                
                with text_area:
                    st.subheader("📝 文案克隆完成！")
                    st.markdown(text_part)
                    st.download_button("📥 下载文案 (TXT)", data=text_part, file_name="文案.txt")
            except Exception as e:
                st.error(f"报错：{e}")

        with st.spinner("🎨 作画并去水印中..."):
            generated_images_data = []
            for i in range(3):
                try:
                    img_response = zp_client.images.generate(model="cogview-3-plus", prompt=ds_image_prompt)
                    img_data = download_and_crop_image(img_response.data[0].url)
                    if img_data: generated_images_data.append(img_data)
                except Exception: pass

            with image_area:
                st.subheader("🖼️ 专属无水印配图")
                cols = st.columns(3)
                for i, img_data in enumerate(generated_images_data):
                    with cols[i]:
                        st.image(img_data, use_container_width=True)
                        st.download_button(f"📥 下载原图 {i+1}", data=img_data.getvalue(), file_name=f"配图_{i+1}.png", mime="image/png")

# ==========================================
# 🚀 部门二：7天内容日历规划师
# ==========================================
elif agent_mode == "📅 部门二：7天内容日历规划师":
    st.title("📅 7天爆款内容日历规划师")
    col1, col2 = st.columns(2)
    with col1: core_biz = st.text_input("🎯 核心业务", value="高端SPA馆")
    with col2: target_aud = st.text_input("👥 目标人群", value="30-45岁高净值女性")
    special_demand = st.text_area("📣 近期特殊诉求", value="主推新进的抗衰仪器")

    if st.button("🗓️ 生成 7 天排期表"):
        with st.spinner("🧠 规划中..."):
            prompt = f"你是一线运营总监。业务：{core_biz}，人群：{target_aud}，诉求：{special_demand}。请出具7天小红书内容日历。包含每天的：核心目的、形式、爆款标题备选、视觉建议、评论区钩子。"
            response = ds_client.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": prompt}])
            st.markdown(response.choices[0].message.content)

# ==========================================
# 🚀 部门三：爆款短视频分镜编剧
# ==========================================
elif agent_mode == "🎬 部门三：爆款短视频分镜编剧":
    st.title("🎬 爆款短视频分镜编剧")
    st.markdown("💡 **不懂运镜没关系，输入想法，直接出保姆级拍摄脚本！**")
    video_topic = st.text_area("🎥 你想拍个什么视频？", value="用第一人称视角体验沉浸式SPA洗脸抗衰全过程，主打解压和做完后惊艳的效果。")
    video_length = st.selectbox("⏱️ 预估视频时长", ["15秒 (极速完播流)", "30-45秒 (干货种草流)", "1分钟以上 (深度人设流)"])
    
    if st.button("🎬 场记打板，生成脚本！"):
        with st.spinner("🧠 顶级大导正在构思分镜..."):
            prompt = f"你是一个千万粉丝级短视频导演。帮我写一个短视频拍摄分镜脚本。主题：{video_topic}，时长：{video_length}。请用【Markdown表格】的形式输出，表头包含：序号、时间预估、景别(远/中/近/特写)、画面内容(动作描述)、旁白/字幕、BGM与音效建议。脚本要极具网感，黄金前3秒要能抓住眼球！"
            response = ds_client.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": prompt}])
            st.markdown(response.choices[0].message.content)

# ==========================================
# 🚀 部门四：高情商引流客服中控
# ==========================================
elif agent_mode == "🗣️ 部门四：高情商引流客服中控":
    st.title("🗣️ 高情商安全引流客服")
    st.markdown("💡 **防封号神器！把粉丝评论/私信扔进来，AI 生成高情商且不违规的回复。**")
    customer_msg = st.text_area("💬 粉丝留言/私信内容：", value="这个抗衰项目做一次多少钱啊？能管多久？")
    product_info = st.text_input("📝 你的真实底牌(价格/卖点，选填)：", value="单次1280，办卡880，能管1个月，建议到店面诊")
    
    if st.button("💬 生成神回复"):
        with st.spinner("🧠 金牌客服正在编辑话术..."):
            prompt = f"你是小红书销冠客服，极其擅长把公域流量引导到私域且【绝不违规】（绝对不出现微信、加我、多少钱等敏感词）。粉丝问：{customer_msg}。你的实际情况是：{product_info}。请给出 3 种不同风格的回复话术：1. 热情闺蜜风。2. 欲擒故纵专业风。3. 幽默探店风。核心目的是引导她私信你或者留下线索。"
            response = ds_client.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": prompt}])
            st.success("✅ 安全话术生成完毕，请直接复制使用！")
            st.markdown(response.choices[0].message.content)

# ==========================================
# 🚀 部门五：小说/干货图文拆解大师
# ==========================================
elif agent_mode == "📚 部门五：小说/干货图文拆解大师":
    st.title("📚 小红书图文卡片拆解大师")
    st.markdown("💡 **长文转爆款图文！自动把几千字的长文拆解成适合滑动的 5-8 张图文分页。**")
    long_text = st.text_area("📄 粘贴你的长文/故事/干货：", height=200, placeholder="把你的长篇文章粘贴在这里...")
    
    if st.button("🗂️ 一键拆解为滑动图文"):
        if not long_text:
            st.warning("请先输入长文内容哦！")
            st.stop()
        with st.spinner("🧠 拆解大师正在排版分页..."):
            prompt = f"你是一个小红书图文排版大师。我要把下面这段长文发成小红书的图文笔记（多图滑动形式）。请帮我把它拆解成 5-8 张图片的文本内容。要求：1. 第一张图是【封面大字报标题】极其吸睛。2. 每一张图的文字不能太多，重点突出。3. 如果是故事，最后一张图要留悬念（钩子）。长文内容：{long_text}"
            response = ds_client.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": prompt}])
            st.markdown(response.choices[0].message.content)
