import requests
from datetime import datetime
import os
import yaml

GLM_API_KEY = os.environ['GLM_API_KEY']
WECHAT_SENDKEY = os.environ['WECHAT_SENDKEY']

def load_plan():
    try:
        with open('plan.yaml', 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"读取计划失败: {e}")
        return None

def get_weekly_theme():
    plan = load_plan()
    if not plan or 'weekly_plans' not in plan:
        return {"英国文学史": "综合复习", "美国文学史": "综合复习",
                "基础英语": "综合训练", "政治": "综合考点", "法语": "综合语法"}
    start_date = datetime(2026, 8, 1)
    week_no = max(1, (datetime.now() - start_date).days // 7 + 1)
    for w in plan['weekly_plans']:
        if w['id'] == week_no:
            return w
    if plan['weekly_plans']:
        return plan['weekly_plans'][-1]
    return {"英国文学史": "综合复习", "美国文学史": "综合复习",
            "基础英语": "综合训练", "政治": "综合考点", "法语": "综合语法"}

def call_glm(messages, max_tokens=800, timeout=30, retries=2):
    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    headers = {
        "Authorization": f"Bearer {GLM_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "glm-4-flash",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": max_tokens
    }
    for attempt in range(retries + 1):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"].strip()
            else:
                print(f"API返回错误状态码: {resp.status_code}, 内容: {resp.text}")
                if attempt < retries:
                    print(f"重试中... ({attempt+1}/{retries})")
                    continue
                else:
                    raise Exception(f"API调用失败: {resp.status_code} {resp.text}")
        except requests.exceptions.Timeout:
            print(f"请求超时（{timeout}秒），正在重试... ({attempt+1}/{retries})")
            if attempt == retries:
                raise Exception("API调用多次超时，请稍后再试")
        except requests.exceptions.RequestException as e:
            print(f"网络错误: {e}")
            if attempt == retries:
                raise

def generate_daily_plan(weekly_theme):
    today = datetime.now()
    weekday = ['一','二','三','四','五','六','日'][today.weekday()]
    date_str = today.strftime("%Y年%m月%d日")
    system_prompt = f"""你是考研复习规划师。请根据本周的周主线，为今天（{date_str}，星期{weekday}）生成一份详细、具体、可执行的复习内容计划。
要求：
- 英国文学史：从本周主题（一个世纪）中挑选2-3位重点作家，指定其代表作品名称和要讲解的英文原文选段范围（如“哈姆雷特第三幕独白”）。
- 美国文学史：从本周对应的同一世纪中挑选2-3位重点作家及作品选段。
- 基础英语：指定今天的练习类型（阅读+题目+翻译），注明话题。
- 政治：指定3个具体考点（需来自本周范围）。
- 法语：指定1个语法点，并列出5个要讲解的词汇。
输出为一段清晰的叙述性文字，不要用json格式。"""
    user_prompt = f"本周主线：{weekly_theme}"
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    return call_glm(messages, max_tokens=600)

def generate_push_content(weekly_theme, daily_plan):
    today = datetime.now()
    date_str = today.strftime("%Y年%m月%d日")
    weekday = ['一','二','三','四','五','六','日'][today.weekday()]
    # 计算考研倒计时（假设2026年12月19日初试）
    exam_date = datetime(2026, 12, 19)
    days_left = (exam_date - today).days
    countdown = f"倒计时{days_left}天"

    system_prompt = f"""你是一位权威考研辅导专家。请严格按照下面的【今日详细计划】生成一篇完整的微信复习推送。

## 推送格式（必须逐一执行）
1. **日期、考研倒计时、一句鼓励名言**
2. **🇬🇧 英国文学史**
   - 系统介绍该世纪文学概况（时期特征、主要流派）
   - 挑选2-3位重点作家，每位包含：英文名，代表作品（英文原名），作品情节概要（英文，约50词），英文原文选段（约60-100词），中文翻译（紧接选段之后），考点标签
   - 标注：“参考：王守仁《英国文学选读》”
3. **🇺🇸 美国文学史**
   - 与英国文学同一世纪，格式完全同上
   - 标注：“参考：常耀信《美国文学简史》”
4. **📖 基础英语**
   - 阅读段落（约150词，英文）附1道选择题（英文题目+选项）及正确答案
   - 2道翻译练习（中译英，附参考答案）
   - 标注参考书目，如“选自考研英语真题”
5. **🇨🇳 政治**
   - 列出3个考点，每个附记忆口诀
   - 标注：“参考：肖秀荣《精讲精练》”
6. **🇫🇷 法语**
   - 语法点详解（法文讲解，附中文必要注释）
   - 必背词汇表（5个，含词性、中文释义、法语例句及中文译文）
   - 2句翻译练习（中译法，附参考答案）
   - 标注：“参考：孙辉《简明法语教程》”
7. **明日预告**

## 核心规则
- 全文字数：3500-4000字（必须达到）
- 英文部分（文学选段、阅读、题目、法语例句等）一律使用原语言，仅在要求处添加中文翻译
- 法语部分（语法讲解、例句、词汇）使用法语，必要时可括号加中文
- 知识点用**粗体**，适度使用📖🇬🇧🇺🇸🇫🇷图标
- 今日详细计划如下，请严格依据：
{daily_plan}"""

    user_prompt = f"今天是{date_str}，星期{weekday}，{countdown}。本周主线：{weekly_theme}"
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    return call_glm(messages, max_tokens=4000)  # 确保输出足够长度

def send_wechat(content):
    if not WECHAT_SENDKEY:
        print("未配置SendKey")
        return
    url = f"https://sctapi.ftqq.com/{WECHAT_SENDKEY}.send"
    r = requests.post(url, data={
        "title": f"📚考研推送 {datetime.now().strftime('%m.%d')}",
        "desp": content
    })
    if r.status_code == 200:
        print("微信推送成功")
    else:
        print(f"推送失败：{r.text}")

if __name__ == "__main__":
    try:
        weekly = get_weekly_theme()
        print("本周主线:", weekly)
        daily_plan = generate_daily_plan(weekly)
        print("→ 今日自动计划：\n", daily_plan)
        push_content = generate_push_content(weekly, daily_plan)
        print("→ 推送内容（前200字）：", push_content[:200])
        send_wechat(push_content)
    except Exception as e:
        print("执行出错：", e)
