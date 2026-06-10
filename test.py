import os
from pathlib import Path

import certifi
from langchain.agents import create_agent
from langchain_anthropic import ChatAnthropic


if not os.getenv("ANTHROPIC_API_KEY"):
    raise RuntimeError("ANTHROPIC_API_KEY is not set in the current shell.")

ssl_cert_file = os.getenv("SSL_CERT_FILE")
if ssl_cert_file and not Path(ssl_cert_file).exists():
    os.environ["SSL_CERT_FILE"] = certifi.where()
elif not ssl_cert_file:
    os.environ["SSL_CERT_FILE"] = certifi.where()


def get_weather(city: str) -> str:
    """获取指定城市的天气。"""
    return f"{city}总是阳光明媚！"

model = ChatAnthropic(
    model_name=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
    base_url=os.getenv("ANTHROPIC_BASE_URL", "https://crs.hexai.cn/api"),
)

agent = create_agent(
    model=model,
    tools=[get_weather],
    system_prompt="你是一个乐于助人的助手",
)

# 运行代理
result = agent.invoke(
    {"messages": [{"role": "user", "content": "旧金山的天气怎么样"}]}
)
print(result)
