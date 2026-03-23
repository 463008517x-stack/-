import streamlit as st
import os
from dotenv import load_dotenv
from openai import OpenAI
import requests
import io
# --- 【美图修正点1】引入 PIL 图片编辑大工具 ---
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
st.set_page_config(page_title="小红书全自动无水印克隆机", page_icon="🧬", layout="centered")
st.title("🧬 小红书爆款全自动克隆机")
st.markdown("甩进一个链接，AI 自动帮你扒内容、学语气、换卖点、配 ** 无水印 ** 绝美图片！")

# 4. 极简输入区
xhs_link = st.text_input("🔗 第一步：在此处粘贴你要参考的小红书/网页链接：")
target_topic = st.text_area("🎯 第二步：你想把爆款套用在什么产品/卖点上？：", value="沉浸式体验：高端spa馆抗衰老面部提升项目，做完皮肤紧致，直接减龄5岁", height=100)

# --- 【美图修正点2】升级稳定器，让它不仅下载，还自动把底部水印裁掉 ---
def download_and_crop_image(url):
    """
    为了防止本地网络干扰，我们直连接口直连下载图片。
    核心魔法：下载完成后，利用 Pillow 将图片的底部（水印所在位置）自动裁掉，实现无水印。
    """
    try:
        response = requests.get(
            url, 
            timeout=30,
            proxies={"http": None, "https": None}, # 防 10053 拦截
            verify=False # 忽略证书警告
        )
        if response.status_code == 200:
            # 1. 先把数据载入到 Pillow 的图片对象中
            img = Image.open(io.BytesIO(response.content))
            width, height = img.size # 获取图片的宽高
            
            # 2. 核心魔法：计算切割区域
            # 智谱 AI 生成的图右下角有水印，我们裁剪掉底部的 6% 的高度（这个比例大概是水印的高度）。
            crop_height_pixels = int(height * 0.06) 
            new_height = height - crop_height_pixels
            
            # 3. 裁剪 (参数是：左, 上, 右, 下)
            img_cropped = img.crop((0, 0, width, new_height))
            
            # 4. 把裁剪好的图片重新变成 Streamlit 能读取的数据流，返还给程序
            output = io.BytesIO()
            img_cropped.save(output, format="PNG") # 统一保存为 PNG 格式
            return output
        return None
    except Exception:
        return None

# 5. 魔法启动按钮
if st.button("🚀 一键提取并克隆无水印图文"):
    if not DS_KEY or not ZP_KEY or not TIANAPI_KEY:
        st.error("⚠️ 钥匙没配齐哦！请检查 .env 文件。")
        st.stop()
        
    text_area = st.container()
    image_area = st.container()

    # 🚀 阶段 A：提取链接内容（防 10053 版）
    extracted_text = ""
    if xhs_link.strip():
        with st.spinner("🕵️‍♂️ 黑客程序已启动，正在强行直连读取链接内容..."):
            try:
                api_url = "https://apis.tianapi.com/htmltext/index"
                payload = {'key': TIANAPI_KEY, 'url': xhs_link}
                headers = {'Content-type': 'application/x-www-form-urlencoded'}
                
                # --- 【重要提示】这里依然保留防网络干扰的代理设置 ---
                response = requests.post(
                    api_url, 
                    data=payload, 
                    headers=headers,
                    proxies={"http": None, "https": None}, # 这里也很重要，不要漏
                    verify=False # 这里也很重要，不要漏
                )
                result = response.json()
                
                if result.get('code') == 200:
                    extracted_text = f"【参考标题】：{result['result'].get('title', '')}\n【参考正文】：{result['result'].get('content', '')}"
                    st.toast("✅ 链接内容提取成功！AI 正在模仿爆款基因...")
                else:
                    st.error(f"⚠️ 链接提取失败，天行接口提示：{result.get('msg')}。请确认链接是否正确。")
                    st.stop()
            except Exception as e:
                st.error(f"❌ 抓取接口通讯失败：{e}")
                st.stop()

    # 🚀 阶段 B：仿写新文案
    with st.spinner("🧠 最强大脑正在奋笔疾书，大约 10 秒..."):
        try:
            if extracted_text:
                system_prompt = f"""
                你是一个年薪百万的顶级小红书爆款拆解与仿写专家。
                请分析【参考爆款笔记】，提取标题套路、排版节奏、语气人设。
                
                参考爆款笔记内容：
                {extracted_text}
                
                将这些基因套用到【主题/卖点】：'{target_topic}'，写一篇新笔记。
                必须包含分割线 ---。格式：【爆款标题】\n【爆款正文】\n【流量标签】\n---\n【画图指令】(简短英文)
                """
            else:
                st.warning("⚠️ 你没有输入链接哦，AI 将直接为你原创！")
                system_prompt = """
                你是一个顶级小红书爆款操盘手。请根据主题生成笔记。
                必须包含分割线 ---。格式：【爆款标题】\n【爆款正文】\n【流量标签】\n---\n【画图指令】(简短英文)
                """
                
            response = ds_client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": target_topic}
                ],
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
                st.markdown("---")

        except Exception as e:
            st.error(f"❌ 文案克隆出错啦：{e}")
            st.stop()

    # 🚀 阶段 C：画师配图并自动去水印
    with st.spinner("🎨 美术课代表正在为你画 3 张绝美封面，并将自动擦除底部 AI 水印..."):
        generated_images_data = []
        for i in range(3):
            try:
                img_response = zp_client.images.generate(
                    model="cogview-3-plus",
                    prompt=ds_image_prompt,
                )
                
                # --- 【美图修正点3】调用我们升级版的去水印下载器 ---
                img_data = download_and_crop_image(img_response.data[0].url)
                if img_data:
                    generated_images_data.append(img_data)
            except Exception as e:
                with image_area:
                    st.error(f"⚠️ 第 {i+1} 张图出错：{e}")

        # 排版展示
        with image_area:
            st.subheader("🖼️ 为你量身定制的 ** 无水印 ** 同风格封面图")
            if len(generated_images_data) > 0:
                cols = st.columns(3)
                for i, img_data in enumerate(generated_images_data):
                    with cols[i]:
                        st.image(img_data, use_container_width=True)
                st.balloons()
            else:
                st.error("⚠️ 哎呀，图片画失败了。")