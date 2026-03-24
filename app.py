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

# 3. 设置网页颜值 (这次我们把网页设置得更宽，看起来更像专业后台)
st.set_page_config(page_title="小红书 AI 运营智能体平台", page_icon="🤖", layout="wide")

# 升级版稳定器（自动裁剪去水印），供全局调用
def download_and_crop_image(url):
    try:
        response = requests.get(
            url, 
            timeout=30,
            proxies={"http": None, "https": None}, 
            verify=False 
        )
        if response.status_code == 200:
            img = Image.open(io.BytesIO(response.content))
            width, height = img.size
            crop_height_pixels = int(height * 0.06) 
            new_height = height - crop_height_pixels
            img_cropped = img.crop((0, 0, width, new_height))
            output = io.BytesIO()
            img_cropped.save(output, format="PNG") 
            return output
        return None
    except Exception:
        return None

# ==========================================
# 🌟 核心升级：酷炫的左侧导航侧边栏
# ==========================================
st.sidebar.title("🤖 AI 运营总控台")
st.sidebar.markdown("欢迎回来，主理人！请选择今天要调用的 AI 部门：")

# 使用单选框来做网页切换导航
agent_mode = st.sidebar.radio(
    "👇 点击切换智能体",
    ["✨ 部门一：爆款图文克隆机", "📅 部门二：7天内容日历规划师"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("👑 *当前系统版本：V2.0 智能体工作台*")


# ==========================================
# 🚀 部门一：原来的图文克隆机
# ==========================================
if agent_mode == "✨ 部门一：爆款图文克隆机":
    st.title("🧬 小红书爆款全自动克隆机")
    st.markdown("甩进一个链接，AI 自动帮你扒内容、学语气、换卖点、配 **无水印** 绝美图片！")

    xhs_link = st.text_input("🔗 第一步：在此处粘贴你要参考的小红书/网页链接：")
    target_topic = st.text_area("🎯 第二步：你想把爆款套用在什么产品/卖点上？：", value="沉浸式体验：高端spa馆抗衰老面部提升项目，做完皮肤紧致，直接减龄5岁", height=100)

    if st.button("🚀 一键提取并克隆无水印图文"):
        if not DS_KEY or not ZP_KEY or not TIANAPI_KEY:
            st.error("⚠️ 钥匙没配齐哦！请检查设置。")
            st.stop()
            
        text_area = st.container()
        image_area = st.container()

        # 阶段 A：提取链接内容
        extracted_text = ""
        if xhs_link.strip():
            with st.spinner("🕵️‍♂️ 黑客程序已启动，正在强行直连读取链接内容..."):
                try:
                    api_url = "https://apis.tianapi.com/htmltext/index"
                    payload = {'key': TIANAPI_KEY, 'url': xhs_link}
                    headers = {'Content-type': 'application/x-www-form-urlencoded'}
                    response = requests.post(api_url, data=payload, headers=headers, proxies={"http": None, "https": None}, verify=False)
                    result = response.json()
                    if result.get('code') == 200:
                        extracted_text = f"【参考标题】：{result['result'].get('title', '')}\n【参考正文】：{result['result'].get('content', '')}"
                        st.toast("✅ 链接提取成功！")
                    else:
                        st.error(f"⚠️ 链接提取失败，请检查链接。")
                        st.stop()
                except Exception as e:
                    st.error(f"❌ 通讯失败：{e}")
                    st.stop()

        # 阶段 B：仿写新文案
        with st.spinner("🧠 最强大脑正在奋笔疾书，大约 10 秒..."):
            try:
                if extracted_text:
                    system_prompt = f"你是一个顶级爆款仿写专家。参考爆款笔记：\n{extracted_text}\n套用到：'{target_topic}'。包含分割线 ---。格式：【爆款标题】\n【爆款正文】\n【流量标签】\n---\n【画图指令】(英文)"
                else:
                    st.warning("⚠️ 没输入链接，将原创！")
                    system_prompt = "你是一个顶级操盘手。生成笔记。包含分割线 ---。格式：【爆款标题】\n【爆款正文】\n【流量标签】\n---\n【画图指令】(英文)"
                    
                response = ds_client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": target_topic}],
                    temperature=0.7
                )
                full_text = response.choices[0].message.content
                
                if "---" in full_text:
                    text_part, image_prompt_part = full_text.split("---", 1)
                    ds_image_prompt = image_prompt_part.replace("【画图指令】", "").replace("：", "").replace(":", "").strip()
                else:
                    text_part = full_text
                    ds_image_prompt = "A beautiful aesthetic photo, highly detailed, photorealistic"
                
                with text_area:
                    st.subheader("📝 像素级无水印文案克隆完成！")
                    st.markdown(text_part)
                    st.download_button("📥 一键下载文案 (TXT)", data=text_part, file_name="小红书爆款文案.txt", mime="text/plain")
                    st.markdown("---")
            except Exception as e:
                st.error(f"❌ 报错：{e}")
                st.stop()

        # 阶段 C：配图
        with st.spinner("🎨 美术课代表正在作画并去水印..."):
            generated_images_data = []
            for i in range(3):
                try:
                    img_response = zp_client.images.generate(model="cogview-3-plus", prompt=ds_image_prompt)
                    img_data = download_and_crop_image(img_response.data[0].url)
                    if img_data:
                        generated_images_data.append(img_data)
                except Exception as e:
                    with image_area:
                        st.error(f"⚠️ 第{i+1}张报错：{e}")

            with image_area:
                st.subheader("🖼️ 为你量身定制的同风格封面图")
                if len(generated_images_data) > 0:
                    cols = st.columns(3)
                    for i, img_data in enumerate(generated_images_data):
                        with cols[i]:
                            st.image(img_data, use_container_width=True)
                            st.download_button(label=f"📥 下载高清原图 {i+1}", data=img_data.getvalue(), file_name=f"封面图_{i+1}.png", mime="image/png")
                    st.balloons()


# ==========================================
# 🚀 部门二：全新登场的 7天内容日历规划师
# ==========================================
elif agent_mode == "📅 部门二：7天内容日历规划师":
    st.title("📅 7天爆款内容日历规划师")
    st.markdown("💡 **主理人，请告诉我你这周的主打业务，首席运营官来帮你安排每天该发什么！**")
    
    # 获取老板的需求
    col1, col2 = st.columns(2)
    with col1:
        core_biz = st.text_input("🎯 你的核心业务/主推项目是什么？", value="高端SPA馆抗衰老面部提升项目")
    with col2:
        target_aud = st.text_input("👥 你的精准目标人群是谁？", value="30-45岁有抗初老需求、注重生活品质的女性")
        
    special_demand = st.text_area("📣 有什么特别想强调的活动或痛点吗？（选填）", value="最近店里新引进了一台百万级热玛吉平替仪器，性价比很高，想主推。")

    if st.button("🗓️ 一键生成 7 天运营排期表"):
        if not DS_KEY:
            st.error("⚠️ 缺少 DeepSeek 钥匙，大管家无法启动！")
            st.stop()
            
        with st.spinner("🧠 首席运营官正在为你查阅全网对标账号，定制专属排期表，请稍候 10 秒..."):
            try:
                # 给大模型下达 COO 级别的指令
                planner_prompt = f"""
                你是一个操盘过千万粉丝矩阵的小红书顶级运营总监。
                现在你的老板核心业务是：【{core_biz}】
                目标人群是：【{target_aud}】
                近期特殊诉求：【{special_demand}】

                请为老板量身定制一份极其详尽、可直接落地的【为期7天的小红书内容发布日历】。
                
                要求结构严谨，错落有致（不要每天都发一样的广告，要结合干货、人设、痛点、促单）：
                
                请按以下格式输出每一天的安排（Day 1 到 Day 7）：
                
                ### 📅 Day X：[填写当天的策略定位，如：痛点共鸣/干货种草/人设打造/福利促单]
                * **🎯 核心目的**：(这句话要达成什么目的)
                * **📝 笔记形式**：(图文 / 视频 / 拼图)
                * **🔥 爆款标题备选**：(提供2个极具网感的标题)
                * **🖼️ 封面视觉建议**：(告诉美术或摄影师，要配什么画面，比如：大字报/前后对比图/高级环境图)
                * **🎣 评论区/私信钩子**：(文末怎么写，才能让别人忍不住给你留言或发私信求地址)
                
                最后，请给老板写一段 100 字左右的【本周运营心法总结】。多用emoji，排版美观。
                """
                
                response = ds_client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": planner_prompt}
                    ],
                    temperature=0.7
                )
                plan_content = response.choices[0].message.content
                
                st.success("✅ 老板，这是为您定制的一周内容作战地图，请查收！")
                st.markdown(plan_content)
                
                st.download_button(
                    label="📥 一键下载 7天运营日历 (TXT)",
                    data=plan_content,
                    file_name="我的小红书7天运营日历.txt",
                    mime="text/plain"
                )
            except Exception as e:
                st.error(f"❌ 规划师请假了，遇到了点错误：{e}")
