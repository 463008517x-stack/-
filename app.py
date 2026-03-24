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
st.set_page_config(page_title="小红书全自动无水印克隆机", page_icon="🧬", layout="centered")
st.title("🧬 小红书爆款全自动克隆机")
st.markdown("甩进一个链接，AI 自动帮你扒内容、学语气、换卖点、配 **无水印** 绝美图片！")

# 4. 极简输入区
xhs_link = st.text_input("🔗 第一步：在此处粘贴你要参考的小红书/网页链接：")
target_topic = st.text_area("🎯 第二步：你想把爆款套用在什么产品/卖点上？：", value="沉浸式体验：高端spa馆抗衰老面部提升项目，做完皮肤紧致，直接减龄5岁", height=100)

# 升级版稳定器（自动裁剪去水印）
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

# 5. 魔法启动按钮
if st.button("🚀 一键提取并克隆无水印图文"):
    if not DS_KEY or not ZP_KEY or not TIANAPI_KEY:
        st.error("⚠️ 钥匙没配齐哦！请检查设置。")
        st.stop()
        
    text_area = st.container()
    image_area = st.container()

    # 🚀 阶段 A：提取链接内容
    extracted_text = ""
    if xhs_link.strip():
        with st.spinner("🕵️‍♂️ 黑客程序已启动，正在强行直连读取链接内容..."):
            try:
                api_url = "https://apis.tianapi.com/htmltext/index"
                payload = {'key': TIANAPI_KEY, 'url': xhs_link}
                headers = {'Content-type': 'application/x-www-form-urlencoded'}
                
                response = requests.post(
                    api_url, 
                    data=payload, 
                    headers=headers,
                    proxies={"http": None, "https": None},
                    verify=False 
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
                
                # --- 【新增功能：一键下载文案】 ---
                st.download_button(
                    label="📥 一键下载文案 (TXT)",
                    data=text_part,
                    file_name="小红书爆款文案.txt",
                    mime="text/plain"
                )
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
                img_data = download_and_crop_image(img_response.data[0].url)
                if img_data:
                    generated_images_data.append(img_data)
            except Exception as e:
                with image_area:
                    st.error(f"⚠️ 第 {i+1} 张图出错：{e}")

        # 排版展示与下载按钮
        with image_area:
            st.subheader("🖼️ 为你量身定制的 **无水印** 同风格封面图")
            if len(generated_images_data) > 0:
                cols = st.columns(3)
                for i, img_data in enumerate(generated_images_data):
                    with cols[i]:
                        st.image(img_data, use_container_width=True)
                        
                        # --- 【新增功能：一键下载高清原图】 ---
                        st.download_button(
                            label=f"📥 下载高清原图 {i+1}",
                            data=img_data.getvalue(), # 把之前藏在内存里的图片数据拿出来
                            file_name=f"爆款封面图_{i+1}.png",
                            mime="image/png"
                        )
                st.balloons()
            else:
                st.error("⚠️ 哎呀，图片画失败了。")
