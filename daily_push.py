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

def get_week_number():
    start_date = datetime(2026, 8, 1)
    today = datetime.now()
    days_diff = (today - start_date).days
    return max(1, days_diff // 7 + 1)

def get_current_theme():
    plan = load_plan()
    if not plan or 'weeks' not in plan:
        return {"英国文学史": "基础复习", "美国文学史": "基础复习", 
                "基础英语": "综合训练", "政治": "基础考点", "法语": "基础语法"}
    week_no = get_week_number()
    for w in plan['weeks']:
        if w['id'] == week_no:
            return w
    last = plan['weeks'][-1]
    last['id'] = week_no
    return last

def generate_content():
    themes = get_current_theme()
    main_lines = f"英国文学：{themes.get('英国文学史','')}；美国文学：{themes.get('美国文学史','')}；" \
                 f"基础英语：{themes.get('基础英语','')}；政治：{themes.get('政治','')}；" \
                 f"法语：{themes.get('法语','')}"
    
    system_prompt = """你是考研辅导专家，每天推送五科内容。
结构：
1. 日期、倒计时、一句鼓励
2. 【英国文学史】本周主线{英国文学}。1位作家+作品卡片（作品名、一句话梗概、考点）
3. 【美国文学史】本周主线{美国文学}。同上格式
4. 【基础英语】本周主线{基英}。100词阅读+1道主旨题，2道词汇/语法选择题（带答案解析），1句中译英
5. 【政治】本周主线{政治}。3个考点各附助记口诀
6. 【法语】本周主线{法语}。1个语法点+3个中法对照例句
7. 【明日预告】
标注参考书：文学→王守仁/常耀信；政治→肖秀荣《精讲精练》；法语→孙辉《简明法语教程》
用粗体强调知识点，语气温暖，适当使用📖✏️📌图标。"""

    user_prompt = f"今天是{datetime.now().strftime('%Y年%m月%d日')}，星期{['一','二','三','四','五','六','日'][datetime.now().weekday()]}。本周主线：{main_lines}。请生成今日推送。"

    # 智谱 API 调用（GLM-4-Flash 免费）
    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    headers = {
        "Authorization": f"Bearer {GLM_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "glm-4-flash",   # 免费模型
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 1600
    }
    resp = requests.post(url, headers=headers, json=payload)
    if resp.status_code == 200:
        return resp.json()["choices"][0]["message"]["content"]
    else:
        return f"生成失败：状态码{resp.status_code}，错误信息：{resp.text}"

def send_wechat(content):
    if not WECHAT_SENDKEY:
        print("未配置SendKey")
        return
    url = f"https://sctapi.ftqq.com/{WECHAT_SENDKEY}.send"
    r = requests.post(url, data={"title": f"📚考研推送 {datetime.now().strftime('%m.%d')}", "desp": content})
    print("推送成功" if r.status_code == 200 else f"推送失败：{r.text}")

if __name__ == "__main__":
    text = generate_content()
    print(text)
    send_wechat(text)
